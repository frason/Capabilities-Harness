"""State store for Task lifecycle persistence and audit logging."""
from __future__ import annotations

import threading
from datetime import UTC, datetime
from typing import Protocol

from capability_harness.domain.task import VALID_TRANSITIONS, Task, TaskState


class TaskTransitionError(Exception):
    """Raised when a state transition violates the state machine."""


class TaskNotFoundError(Exception):
    """Raised when a task_id cannot be found in the store."""


class StateStore(Protocol):
    """Protocol for task state persistence."""

    def create_task(self, task: Task) -> Task: ...
    def transition(
        self,
        task_id: str,
        new_state: TaskState,
        reason: str = "",
        actor: str = "system",
    ) -> Task: ...
    def get_task(self, task_id: str) -> Task: ...
    def list_tasks(self, state: TaskState | None = None) -> list[Task]: ...


class InMemoryStateStore:
    """Thread-safe in-memory state store for development and testing."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._audit: dict[str, list[tuple[str, str, str, str, str]]] = {}
        self._lock = threading.Lock()

    def create_task(self, task: Task) -> Task:
        with self._lock:
            self._tasks[task.id] = task.model_copy()
            self._audit[task.id] = []
        return task

    def transition(
        self,
        task_id: str,
        new_state: TaskState,
        reason: str = "",
        actor: str = "system",
    ) -> Task:
        with self._lock:
            if task_id not in self._tasks:
                raise TaskNotFoundError(task_id)
            task = self._tasks[task_id]
            allowed = VALID_TRANSITIONS.get(task.state, set())
            if new_state not in allowed:
                raise TaskTransitionError(
                    f"Cannot transition task {task_id} from {task.state!r} to {new_state!r}. "
                    f"Allowed: {[s.value for s in allowed]}"
                )
            now = datetime.now(UTC).isoformat()
            self._audit[task_id].append(
                (task.state.value, new_state.value, reason, actor, now)
            )
            updated = task.model_copy(
                update={"state": new_state, "updated_at": datetime.now(UTC)}
            )
            self._tasks[task_id] = updated
            return updated

    def get_task(self, task_id: str) -> Task:
        with self._lock:
            if task_id not in self._tasks:
                raise TaskNotFoundError(task_id)
            return self._tasks[task_id].model_copy()

    def list_tasks(self, state: TaskState | None = None) -> list[Task]:
        with self._lock:
            tasks = list(self._tasks.values())
        if state is not None:
            tasks = [t for t in tasks if t.state == state]
        return [t.model_copy() for t in tasks]

    def audit_log(self, task_id: str) -> list[tuple[str, str, str, str, str]]:
        """Return audit entries for a task as (from, to, reason, actor, timestamp)."""
        with self._lock:
            return list(self._audit.get(task_id, []))

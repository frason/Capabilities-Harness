"""Unit tests for the Task state machine."""
import pytest

from capability_harness.domain.task import VALID_TRANSITIONS, Task, TaskState
from capability_harness.infrastructure.persistence.state_store import (
    InMemoryStateStore,
    TaskNotFoundError,
    TaskTransitionError,
)


def _store_with_task(capability: str = "noop") -> tuple[InMemoryStateStore, Task]:
    store = InMemoryStateStore()
    task = Task(capability_name=capability)
    store.create_task(task)
    return store, task


def test_task_initial_state():
    task = Task(capability_name="noop")
    assert task.state == TaskState.CREATED


def test_valid_transition_created_to_ready():
    store, task = _store_with_task()
    updated = store.transition(task.id, TaskState.READY)
    assert updated.state == TaskState.READY


def test_valid_transition_full_happy_path():
    store, task = _store_with_task()
    for state in [
        TaskState.READY,
        TaskState.RUNNING,
        TaskState.VALIDATION,
        TaskState.REVIEW,
        TaskState.APPROVED,
        TaskState.MERGED,
        TaskState.ARCHIVED,
    ]:
        task = store.transition(task.id, state)
    assert task.state == TaskState.ARCHIVED


def test_invalid_transition_raises():
    store, task = _store_with_task()
    with pytest.raises(TaskTransitionError):
        store.transition(task.id, TaskState.RUNNING)  # must go through READY first


def test_terminal_states_reject_all_transitions():
    for terminal in (TaskState.CANCELLED, TaskState.ARCHIVED):
        store, task = _store_with_task()
        store.transition(task.id, TaskState.READY)
        if terminal == TaskState.CANCELLED:
            store.transition(task.id, TaskState.CANCELLED)
        else:
            for s in [TaskState.RUNNING, TaskState.VALIDATION, TaskState.REVIEW,
                      TaskState.APPROVED, TaskState.MERGED, TaskState.ARCHIVED]:
                task = store.transition(task.id, s)
        refreshed = store.get_task(task.id)
        allowed = VALID_TRANSITIONS[refreshed.state]
        assert len(allowed) == 0, f"{terminal} should have no valid transitions"


def test_failed_task_can_retry():
    store, task = _store_with_task()
    store.transition(task.id, TaskState.READY)
    store.transition(task.id, TaskState.RUNNING)
    store.transition(task.id, TaskState.FAILED)
    # retry: FAILED → READY is valid
    updated = store.transition(task.id, TaskState.READY)
    assert updated.state == TaskState.READY


def test_get_nonexistent_task_raises():
    store = InMemoryStateStore()
    with pytest.raises(TaskNotFoundError):
        store.get_task("does-not-exist")


def test_list_tasks_filtered_by_state():
    store = InMemoryStateStore()
    t1 = Task(capability_name="a")
    t2 = Task(capability_name="b")
    store.create_task(t1)
    store.create_task(t2)
    store.transition(t1.id, TaskState.READY)

    ready = store.list_tasks(state=TaskState.READY)
    created = store.list_tasks(state=TaskState.CREATED)
    assert len(ready) == 1
    assert ready[0].id == t1.id
    assert len(created) == 1
    assert created[0].id == t2.id


def test_audit_log_records_transitions():
    store, task = _store_with_task()
    store.transition(task.id, TaskState.READY, reason="submitted", actor="cli")
    store.transition(task.id, TaskState.RUNNING, reason="dispatched")
    log = store.audit_log(task.id)
    assert len(log) == 2
    assert log[0][0] == "created"
    assert log[0][1] == "ready"
    assert log[0][2] == "submitted"
    assert log[0][3] == "cli"

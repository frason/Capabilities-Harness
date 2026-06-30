"""Scheduler — owns the task lifecycle and dispatches through the Capability Graph.

The Scheduler never dispatches directly to capabilities.
It always routes through GraphExecutor.
It executes policy; the PolicyEngine defines it.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from capability_harness.application.graph import NOOP_GRAPH, CapabilityGraph, GraphExecutor
from capability_harness.application.policy import PolicyEngine
from capability_harness.domain.events import (
    TaskCompleted,
    TaskCreated,
    TaskFailed,
    TaskStarted,
)
from capability_harness.domain.task import Task, TaskState
from capability_harness.infrastructure.persistence.state_store import InMemoryStateStore

logger = logging.getLogger(__name__)


class HarnessScheduler:
    """Deterministic task scheduler.

    Submits tasks, polls for Ready tasks, and dispatches through the Capability Graph.
    """

    def __init__(
        self,
        graph_executor: GraphExecutor,
        policy: PolicyEngine,
        state_store: InMemoryStateStore,
        event_bus: Any,
        default_graph: CapabilityGraph | None = None,
    ) -> None:
        self._executor = graph_executor
        self._policy = policy
        self._store = state_store
        self._bus = event_bus
        self._default_graph = default_graph or NOOP_GRAPH
        self._running = False
        self._semaphore: asyncio.Semaphore | None = None

    async def start(self) -> None:
        self._running = True
        self._semaphore = asyncio.Semaphore(
            self._policy.concurrency.max_concurrent_tasks
        )
        asyncio.create_task(self._poll_loop())
        logger.info("scheduler started (max_concurrent=%d)", self._policy.concurrency.max_concurrent_tasks)

    async def stop(self) -> None:
        self._running = False
        logger.info("scheduler stopped")

    async def submit_task(self, task: Task) -> str:
        """Persist a task, publish TaskCreated, and transition it to Ready."""
        self._store.create_task(task)
        self._bus.publish(TaskCreated(task_id=task.id, capability_name=task.capability_name))
        self._store.transition(task.id, TaskState.READY, reason="submitted")
        logger.info("task %s submitted capability=%s", task.id, task.capability_name)
        return task.id

    async def _poll_loop(self) -> None:
        while self._running:
            ready_tasks = self._store.list_tasks(state=TaskState.READY)
            for task in ready_tasks:
                if self._semaphore:
                    asyncio.create_task(self._dispatch(task))
            await asyncio.sleep(1.0)

    async def _dispatch(self, task: Task) -> None:
        assert self._semaphore is not None
        async with self._semaphore:
            try:
                self._store.transition(task.id, TaskState.RUNNING, reason="dispatched")
                self._bus.publish(TaskStarted(task_id=task.id))
                result = await self._executor.execute(self._default_graph, task)
                if result.success:
                    self._store.transition(task.id, TaskState.VALIDATION, reason="execution complete")
                    self._bus.publish(TaskCompleted(task_id=task.id, success=True))
                else:
                    self._store.transition(
                        task.id, TaskState.FAILED, reason=result.error or "execution failed"
                    )
                    self._bus.publish(TaskFailed(task_id=task.id, error=result.error or ""))
            except Exception as exc:
                logger.exception("dispatch failed for task %s", task.id)
                try:
                    self._store.transition(task.id, TaskState.FAILED, reason=str(exc))
                    self._bus.publish(TaskFailed(task_id=task.id, error=str(exc)))
                except Exception:
                    pass

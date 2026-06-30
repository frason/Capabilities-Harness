"""Async context manager for isolated git worktree lifecycle."""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from capability_harness.domain.task import Task
from capability_harness.infrastructure.git.repository import GitRepository

logger = logging.getLogger(__name__)


class WorktreeManager:
    """Creates and cleans up a git worktree for a task's execution."""

    def __init__(self, repo: GitRepository) -> None:
        self._repo = repo

    @asynccontextmanager
    async def checkout(
        self, task: Task, base_branch: str = "main"
    ) -> AsyncIterator[str]:
        """Yield a worktree path; remove it on exit even if an exception occurs."""
        worktree_path = self._repo.create_worktree(task.id, base_branch)
        logger.info("worktree created at %s for task %s", worktree_path, task.id)
        try:
            yield worktree_path
        finally:
            try:
                self._repo.remove_worktree(task.id)
                logger.info("worktree removed for task %s", task.id)
            except Exception as exc:
                logger.warning("failed to remove worktree for task %s: %s", task.id, exc)

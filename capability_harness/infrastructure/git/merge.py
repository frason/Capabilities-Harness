"""Merge controller — enforces merge policy before merging task branches."""
from __future__ import annotations

import logging

from capability_harness.application.policy import MergePolicy, PolicyEngine
from capability_harness.domain.task import Task, TaskState

logger = logging.getLogger(__name__)


class MergeController:
    """Controls whether and how a task branch is merged based on policy."""

    def __init__(self, policy: PolicyEngine) -> None:
        self._policy = policy

    def can_merge(self, task: Task) -> bool:
        if self._policy.merge == MergePolicy.HUMAN:
            return task.state == TaskState.APPROVED
        # AUTO: merge is allowed after validation passes
        return task.state in {TaskState.APPROVED, TaskState.REVIEW}

    def merge(
        self,
        task: Task,
        worktree_path: str,
        target_branch: str = "main",
    ) -> bool:
        if not self.can_merge(task):
            logger.info(
                "merge blocked for task %s: state=%s policy=%s",
                task.id, task.state, self._policy.merge,
            )
            return False
        # TODO: implement actual git merge (fast-forward or squash)
        logger.info(
            "merge approved for task %s into %s (stub)", task.id, target_branch
        )
        return True

"""Git repository operations via native subprocess — no GitPython dependency."""
from __future__ import annotations

import subprocess
from pathlib import Path

from capability_harness.application.repository_service import GitMetadata


class GitRepository:
    """Wraps native git commands for repository and worktree management."""

    def __init__(self, path: str) -> None:
        self._path = Path(path)

    def current_branch(self) -> str:
        return self._run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()

    def create_worktree(self, task_id: str, base_branch: str) -> str:
        worktree_path = str(self._path.parent / "worktrees" / task_id)
        self._run([
            "git", "worktree", "add",
            worktree_path,
            "-b", f"task/{task_id}",
            base_branch,
        ])
        return worktree_path

    def remove_worktree(self, task_id: str) -> None:
        worktree_path = str(self._path.parent / "worktrees" / task_id)
        self._run(["git", "worktree", "remove", worktree_path, "--force"])

    def list_worktrees(self) -> list[str]:
        output = self._run(["git", "worktree", "list", "--porcelain"])
        worktrees = []
        for line in output.splitlines():
            if line.startswith("worktree "):
                worktrees.append(line.removeprefix("worktree ").strip())
        return worktrees

    def git_metadata(self) -> GitMetadata:
        branch = self.current_branch()
        try:
            commit_hash = self._run(["git", "rev-parse", "HEAD"]).strip()
        except subprocess.CalledProcessError:
            commit_hash = ""
        try:
            dirty_output = self._run(["git", "status", "--porcelain"]).strip()
            is_dirty = bool(dirty_output)
        except subprocess.CalledProcessError:
            is_dirty = False
        try:
            remote_url = self._run(
                ["git", "remote", "get-url", "origin"]
            ).strip()
        except subprocess.CalledProcessError:
            remote_url = None
        return GitMetadata(
            branch=branch,
            commit_hash=commit_hash,
            is_dirty=is_dirty,
            remote_url=remote_url,
        )

    def _run(self, args: list[str]) -> str:
        result = subprocess.run(
            args,
            cwd=str(self._path),
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout

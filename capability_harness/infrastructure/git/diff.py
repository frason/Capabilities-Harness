"""Patch generation and application via native git subprocess."""
from __future__ import annotations

import subprocess


class DiffGenerator:
    """Generates and applies unified diffs between worktree and base branch."""

    def generate(self, worktree_path: str, base_branch: str = "main") -> str:
        result = subprocess.run(
            ["git", "diff", base_branch],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout

    def apply(self, repo_path: str, patch: str) -> bool:
        try:
            subprocess.run(
                ["git", "apply"],
                cwd=repo_path,
                input=patch,
                text=True,
                capture_output=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def validate_patch(self, patch: str) -> bool:
        return patch.startswith("diff --git") or patch.startswith("---")

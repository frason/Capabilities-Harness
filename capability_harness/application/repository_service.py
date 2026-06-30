"""Repository Service — understands the repository structure and metadata.

The Memory Layer consumes RepositoryService rather than doing its own
filesystem or git analysis. This keeps repository knowledge centralized.
"""
from __future__ import annotations

import os
import subprocess
from typing import Protocol

from pydantic import BaseModel


class FileTree(BaseModel):
    root: str
    files: list[str]
    directories: list[str]


class GitMetadata(BaseModel):
    branch: str = ""
    commit_hash: str = ""
    is_dirty: bool = False
    remote_url: str | None = None


class ImportRef(BaseModel):
    source: str
    target: str
    kind: str = "import"


class RepositoryService(Protocol):
    """Protocol for repository introspection."""

    def file_tree(self) -> FileTree: ...
    def git_metadata(self) -> GitMetadata: ...
    def symbol_index(self) -> dict[str, list[str]]: ...
    def import_relationships(self, path: str) -> list[ImportRef]: ...


class LocalRepositoryService:
    """Repository service backed by os.walk and native git subprocess."""

    def __init__(self, root: str = ".") -> None:
        self._root = root

    def file_tree(self) -> FileTree:
        files: list[str] = []
        directories: list[str] = []
        for dirpath, dirnames, filenames in os.walk(self._root):
            # Skip hidden directories
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            rel = os.path.relpath(dirpath, self._root)
            if rel != ".":
                directories.append(rel)
            for fname in filenames:
                files.append(os.path.join(rel, fname) if rel != "." else fname)
        return FileTree(root=self._root, files=sorted(files), directories=sorted(directories))

    def git_metadata(self) -> GitMetadata:
        def _git(*args: str) -> str:
            try:
                return subprocess.run(
                    ["git", *args],
                    cwd=self._root,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
            except subprocess.CalledProcessError:
                return ""

        branch = _git("rev-parse", "--abbrev-ref", "HEAD")
        commit_hash = _git("rev-parse", "HEAD")
        dirty = bool(_git("status", "--porcelain"))
        remote_url = _git("remote", "get-url", "origin") or None
        return GitMetadata(
            branch=branch,
            commit_hash=commit_hash,
            is_dirty=dirty,
            remote_url=remote_url,
        )

    def symbol_index(self) -> dict[str, list[str]]:
        # TODO: build symbol index from AST parsing
        return {}

    def import_relationships(self, path: str) -> list[ImportRef]:
        # TODO: parse imports via ast module
        return []

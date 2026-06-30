"""Content-addressed artifact store backed by the local filesystem."""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from capability_harness.domain.artifact import Artifact, ArtifactKind


class ArtifactStore(Protocol):
    """Protocol for artifact persistence."""

    def write(self, kind: ArtifactKind, task_id: str, content: bytes | str) -> Artifact: ...
    def read(self, artifact_id: str) -> bytes: ...
    def read_task_artifacts(self, task_id: str) -> list[Artifact]: ...
    def verify(self, artifact_id: str) -> bool: ...


class LocalArtifactStore:
    """Filesystem-backed, content-addressed artifact store.

    Layout: {root}/{task_id}/{kind.value}
    Manifest: {root}/{task_id}/manifest.json
    """

    def __init__(self, root: str = ".harness/artifacts") -> None:
        self._root = Path(root)

    def write(self, kind: ArtifactKind, task_id: str, content: bytes | str) -> Artifact:
        raw = content.encode() if isinstance(content, str) else content
        content_hash = hashlib.sha256(raw).hexdigest()
        task_dir = self._root / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        file_path = task_dir / kind.value
        file_path.write_bytes(raw)

        artifact = Artifact(
            id=content_hash,
            kind=kind,
            task_id=task_id,
            path=str(file_path),
            size_bytes=len(raw),
            created_at=datetime.now(UTC),
            content_hash=content_hash,
        )
        self._update_manifest(task_id, artifact)
        return artifact

    def read(self, artifact_id: str) -> bytes:
        # Search all task directories for this hash
        for manifest_path in self._root.glob("*/manifest.json"):
            manifest = json.loads(manifest_path.read_text())
            for entry in manifest.get("artifacts", []):
                if entry["id"] == artifact_id:
                    return Path(entry["path"]).read_bytes()
        raise FileNotFoundError(f"Artifact {artifact_id!r} not found")

    def read_task_artifacts(self, task_id: str) -> list[Artifact]:
        manifest_path = self._root / task_id / "manifest.json"
        if not manifest_path.exists():
            return []
        manifest = json.loads(manifest_path.read_text())
        return [Artifact(**entry) for entry in manifest.get("artifacts", [])]

    def verify(self, artifact_id: str) -> bool:
        try:
            data = self.read(artifact_id)
            return hashlib.sha256(data).hexdigest() == artifact_id
        except FileNotFoundError:
            return False

    def _update_manifest(self, task_id: str, artifact: Artifact) -> None:
        manifest_path = self._root / task_id / "manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
        else:
            manifest = {"task_id": task_id, "artifacts": []}
        entries = manifest["artifacts"]
        entries = [e for e in entries if e["kind"] != artifact.kind.value]
        entries.append(json.loads(artifact.model_dump_json()))
        manifest["artifacts"] = entries
        manifest_path.write_text(json.dumps(manifest, indent=2, default=str))

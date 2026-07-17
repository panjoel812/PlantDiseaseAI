from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

ValidationStatus = Literal["passed", "failed", "blocked", "not_run"]


def sha256_file(path: Path, chunk_size: int = 1_048_576) -> str:
    """Return the SHA-256 hexadecimal digest of a file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def logical_repo_path(path: Path, repo_root: Path) -> str:
    """Return a repository-relative POSIX path, rejecting outside paths."""

    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"path is outside repository: {path.name}") from exc


@dataclass(frozen=True)
class ArtifactRecord:
    logical_path: str
    status: ValidationStatus
    required: bool
    size_bytes: int | None = None
    sha256: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class ReleaseManifest:
    schema_version: int
    candidate_id: str
    source_commit: str
    release_commit: str | None
    generated_at_utc: str
    environment: dict[str, Any]
    artifacts: list[ArtifactRecord] = field(default_factory=list)
    lanes: dict[str, ValidationStatus] = field(default_factory=dict)
    lane_evidence: dict[str, Any] = field(default_factory=dict)


def write_manifest(manifest: ReleaseManifest, output_path: Path) -> None:
    """Write a release manifest as deterministic UTF-8 JSON."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(asdict(manifest), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

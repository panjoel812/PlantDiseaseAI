import json
import tempfile
from pathlib import Path

import pytest

from plantdisease.release.manifest import (
    ArtifactRecord,
    ReleaseManifest,
    logical_repo_path,
    sha256_file,
    write_manifest,
)


def test_sha256_file_is_deterministic(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(b"PlantDiseaseAI\n")
    first = sha256_file(artifact)
    assert len(first) == 64
    assert first == sha256_file(artifact)


def test_logical_repo_path_rejects_outside(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    inside = repo / "reports" / "metrics.json"
    inside.parent.mkdir(parents=True)
    inside.write_text("{}", encoding="utf-8")
    assert logical_repo_path(inside, repo) == "reports/metrics.json"
    with pytest.raises(ValueError, match="outside repository"):
        logical_repo_path(tmp_path / "private.pt", repo)


def test_write_manifest_is_portable_deterministic_json(tmp_path: Path) -> None:
    readme_sha = "a" * 64
    manifest = ReleaseManifest(
        schema_version=1,
        candidate_id="week8-rc1",
        source_commit="f7c4ed3",
        release_commit=None,
        generated_at_utc="2026-07-16T00:00:00Z",
        environment={"python": "3.12"},
        artifacts=[
            ArtifactRecord(
                logical_path="README.md",
                status="passed",
                required=True,
                size_bytes=42,
                sha256=readme_sha,
            )
        ],
        lanes={"clean": "not_run"},
    )
    output_path = tmp_path / "release-manifest.json"

    write_manifest(manifest, output_path)

    serialized = output_path.read_text(encoding="utf-8")
    loaded = json.loads(serialized)
    assert loaded["candidate_id"] == "week8-rc1"
    assert loaded["lanes"]["clean"] == "not_run"
    assert loaded["artifacts"][0]["sha256"] == readme_sha
    assert serialized.endswith("\n")
    assert serialized == json.dumps(
        loaded, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"
    assert str(Path.home()) not in serialized
    assert tempfile.gettempdir() not in serialized

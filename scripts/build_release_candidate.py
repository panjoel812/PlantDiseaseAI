"""Build an auditable Week8 release-candidate manifest and claim ledger."""

from __future__ import annotations

import argparse
import json
import platform
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import torch
import yaml
from audit_week8_claims import build_audit_payload

from plantdisease.release.manifest import (
    ArtifactRecord,
    ReleaseManifest,
    ValidationStatus,
    logical_repo_path,
    sha256_file,
    write_manifest,
)

_RELEASE_MATERIALS = (
    Path("ASSET_LICENSES.md"),
    Path("docs/release/publication_decisions.md"),
    Path("docs/presentation/plantdisease_ai_complete_bilingual_outline.md"),
    Path("docs/presentation/plantdisease_ai_week8_research_defense.key"),
    Path("docs/presentation/plantdisease_ai_week8_research_defense.pptx"),
    Path("docs/presentation/week8_research_defense_animation_map.md"),
    Path("paper/out/plantdisease_ai_en.pdf"),
    Path("paper/out/plantdisease_ai_zh.pdf"),
    Path("reports/figures/week8_react_demo_desktop.png"),
    Path("reports/figures/week8_react_demo_mobile.png"),
    Path("reports/release/week8_claim_evidence.json"),
    Path("reports/release/week8_paper_audit.json"),
    Path("reports/week8_presentation_qa.md"),
)
_RELEASE_MATERIAL_GLOBS = (
    "docs/presentation/charts/english-transparent/*",
    "docs/presentation/plantdisease_ai_week8_research_defense/slide-*.png",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the Week8 release-candidate command line."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-id", default="week8-rc1")
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--release-commit")
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=Path(
            "outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt"
        ),
    )
    parser.add_argument(
        "--output", type=Path, default=Path("reports/release/week8_rc1_manifest.json")
    )
    parser.add_argument(
        "--claims-output",
        type=Path,
        default=Path("reports/release/week8_claim_evidence.json"),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Write the Week8 candidate manifest and return nonzero on missing evidence."""

    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    config_path = repo_root / "configs/week8_claims.yaml"
    ledger = build_audit_payload(repo_root, config_path, check_links=True)
    claim_status: ValidationStatus = (
        "passed" if ledger["status"] == "passed" else "failed"
    )
    _write_json(ledger, args.claims_output)

    checkpoint_path = _repo_path(args.checkpoint, repo_root)
    lock_path = repo_root / "uv.lock"
    environment = {
        "python": platform.python_version(),
        "pytorch": str(torch.__version__),
        "os": f"{platform.system()} {platform.release()}",
        "machine": platform.machine(),
        "mps_available": torch.backends.mps.is_available(),
        "uv_lock_sha256": sha256_file(lock_path) if lock_path.is_file() else None,
    }
    existing_lanes, existing_lane_evidence = _load_runtime_evidence(
        args.output,
        candidate_id=args.candidate_id,
        source_commit=args.source_commit,
        environment=environment,
        checkpoint_path=checkpoint_path,
        repo_root=repo_root,
    )
    evidence_paths = _required_evidence_paths(config_path, repo_root)
    evidence_paths.update({repo_root / "uv.lock", checkpoint_path, config_path})
    evidence_paths.update(_release_material_paths(repo_root))
    artifacts = [_artifact_record(path, repo_root) for path in sorted(evidence_paths)]
    evidence_status = "passed" if all(item.status == "passed" for item in artifacts) else "failed"
    manifest = ReleaseManifest(
        schema_version=1,
        candidate_id=args.candidate_id,
        source_commit=args.source_commit,
        release_commit=args.release_commit,
        generated_at_utc=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        environment=environment,
        artifacts=artifacts,
        lanes={
            **existing_lanes,
            "claims": claim_status,
            "evidence": evidence_status,
            "clean_reproduction": existing_lanes.get("clean_reproduction", "not_run"),
            "package": existing_lanes.get("package", "not_run"),
            "local_evidence": existing_lanes.get("local_evidence", "not_run"),
            "container": existing_lanes.get("container", "not_run"),
        },
        lane_evidence=existing_lane_evidence,
    )
    write_manifest(manifest, args.output)
    status = "passed" if claim_status == evidence_status == "passed" else "failed"
    print(json.dumps({"candidate_id": args.candidate_id, "status": status}, sort_keys=True))
    return 0 if status == "passed" else 1


def _required_evidence_paths(config_path: Path, repo_root: Path) -> set[Path]:
    payload: Any = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("claim configuration must be a mapping")
    paths: set[Path] = set()
    for section in ("claims", "boundaries"):
        records = payload.get(section)
        if not isinstance(records, list):
            raise ValueError(f"claim configuration must contain a {section} list")
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get("source"), str):
                raise ValueError(f"each {section} record must contain a source path")
            consumers = record.get("consumers")
            if not isinstance(consumers, list) or not all(
                isinstance(consumer, str) for consumer in consumers
            ):
                raise ValueError(f"each {section} record must contain consumer paths")
            paths.add(_repo_path(Path(record["source"]), repo_root))
            paths.update(_repo_path(Path(consumer), repo_root) for consumer in consumers)
    return paths


def _release_material_paths(repo_root: Path) -> set[Path]:
    paths = {_repo_path(path, repo_root) for path in _RELEASE_MATERIALS}
    for pattern in _RELEASE_MATERIAL_GLOBS:
        paths.update(path.resolve() for path in repo_root.glob(pattern) if path.is_file())
    return paths


def _load_runtime_evidence(
    output: Path,
    *,
    candidate_id: str,
    source_commit: str,
    environment: dict[str, Any],
    checkpoint_path: Path,
    repo_root: Path,
) -> tuple[dict[str, ValidationStatus], dict[str, Any]]:
    """Preserve runtime lanes only when their full candidate provenance matches."""

    if not output.is_file():
        return {}, {}
    try:
        payload: Any = json.loads(output.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}, {}
    if not isinstance(payload, dict):
        return {}, {}
    if not _runtime_provenance_matches(
        payload,
        candidate_id=candidate_id,
        source_commit=source_commit,
        environment=environment,
        checkpoint_path=checkpoint_path,
        repo_root=repo_root,
    ):
        return {}, {}
    lanes = payload.get("lanes")
    lane_evidence = payload.get("lane_evidence")
    preserved_lanes: dict[str, ValidationStatus] = {}
    if isinstance(lanes, dict):
        for name, value in lanes.items():
            if isinstance(name, str) and value in {
                "passed",
                "failed",
                "blocked",
                "not_run",
            }:
                preserved_lanes[name] = cast(ValidationStatus, value)
    return (
        preserved_lanes,
        dict(lane_evidence) if isinstance(lane_evidence, dict) else {},
    )


def _runtime_provenance_matches(
    payload: dict[str, Any],
    *,
    candidate_id: str,
    source_commit: str,
    environment: dict[str, Any],
    checkpoint_path: Path,
    repo_root: Path,
) -> bool:
    if payload.get("candidate_id") != candidate_id:
        return False
    if payload.get("source_commit") != source_commit:
        return False
    if payload.get("environment") != environment:
        return False
    if not checkpoint_path.is_file():
        return False

    logical_checkpoint = logical_repo_path(checkpoint_path, repo_root)
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        return False
    expected_sha256 = sha256_file(checkpoint_path)
    expected_size = checkpoint_path.stat().st_size
    return any(
        isinstance(item, dict)
        and item.get("logical_path") == logical_checkpoint
        and item.get("status") == "passed"
        and item.get("sha256") == expected_sha256
        and item.get("size_bytes") == expected_size
        for item in artifacts
    )


def _repo_path(path: Path, repo_root: Path) -> Path:
    resolved = path.resolve() if path.is_absolute() else (repo_root / path).resolve()
    logical_repo_path(resolved, repo_root)
    return resolved


def _artifact_record(path: Path, repo_root: Path) -> ArtifactRecord:
    logical_path = logical_repo_path(path, repo_root)
    if not path.is_file():
        return ArtifactRecord(logical_path, "failed", True, note="required file is unavailable")
    return ArtifactRecord(
        logical_path,
        "passed",
        True,
        size_bytes=path.stat().st_size,
        sha256=sha256_file(path),
    )


def _write_json(payload: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())

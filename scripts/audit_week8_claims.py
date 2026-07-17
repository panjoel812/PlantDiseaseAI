"""Audit locked Week8 claims, publication boundaries, and local links."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from plantdisease.release.claims import (
    ClaimRecord,
    audit_claims,
    find_broken_markdown_links,
    load_claims,
)


@dataclass(frozen=True)
class BoundaryResult:
    """Record whether one configured publication boundary has all files."""

    boundary_id: str
    source: str
    consumers: tuple[str, ...]
    status: str
    missing_sources: tuple[str, ...]
    missing_consumers: tuple[str, ...]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the Week8 claim-audit command line."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/week8_claims.yaml"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/plantvillage/week8_release/week8-rc1/claims.json"),
    )
    parser.add_argument("--check-links", action="store_true")
    return parser.parse_args(argv)


def load_boundary_results(repo_root: Path, config_path: Path) -> list[BoundaryResult]:
    """Audit source and consumer file presence for configured boundaries."""

    payload: Any = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("claim configuration must use schema_version 1")
    raw_boundaries = payload.get("boundaries")
    if not isinstance(raw_boundaries, list):
        raise ValueError("claim configuration must contain a boundaries list")

    results: list[BoundaryResult] = []
    for raw_boundary in raw_boundaries:
        if not isinstance(raw_boundary, dict):
            raise ValueError("each boundary must be a mapping")
        boundary_id = raw_boundary.get("id")
        source = raw_boundary.get("source")
        consumers = raw_boundary.get("consumers")
        if not isinstance(boundary_id, str) or not isinstance(source, str):
            raise ValueError("boundary id and source must be paths")
        if not isinstance(consumers, list) or not all(
            isinstance(consumer, str) for consumer in consumers
        ):
            raise ValueError("boundary consumers must be a list of paths")
        missing_sources = () if (repo_root / source).is_file() else (source,)
        missing_consumers = tuple(
            consumer for consumer in consumers if not (repo_root / consumer).is_file()
        )
        results.append(
            BoundaryResult(
                boundary_id=boundary_id,
                source=source,
                consumers=tuple(consumers),
                status="failed" if missing_sources or missing_consumers else "passed",
                missing_sources=missing_sources,
                missing_consumers=missing_consumers,
            )
        )
    return results


def build_audit_payload(
    repo_root: Path, config_path: Path, *, check_links: bool
) -> dict[str, Any]:
    """Build the schema-version-1 Week8 claim audit payload."""

    claims = load_claims(config_path)
    claim_results = audit_claims(repo_root, claims)
    boundary_results = load_boundary_results(repo_root, config_path)
    markdown_paths = [
        path
        for path in _markdown_paths(claims, boundary_results)
        if (repo_root / path).is_file()
    ]
    broken_links = (
        find_broken_markdown_links(repo_root, markdown_paths) if check_links else []
    )
    passed = sum(result.status == "passed" for result in claim_results)
    passed += sum(result.status == "passed" for result in boundary_results)
    failed = len(claim_results) + len(boundary_results) - passed + len(broken_links)
    return {
        "schema_version": 1,
        "status": "failed" if failed else "passed",
        "claim_results": [asdict(result) for result in claim_results],
        "boundary_results": [asdict(result) for result in boundary_results],
        "broken_links": broken_links,
        "counts": {
            "claims": len(claim_results),
            "boundaries": len(boundary_results),
            "broken_links": len(broken_links),
            "passed": passed,
            "failed": failed,
        },
    }


def write_payload(payload: dict[str, Any], output: Path) -> None:
    """Write sorted UTF-8 JSON for a Week8 audit result."""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    """Run the Week8 claim audit and return nonzero for required failures."""

    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    config_path = args.config if args.config.is_absolute() else repo_root / args.config
    payload = build_audit_payload(repo_root, config_path, check_links=args.check_links)
    write_payload(payload, args.output)
    print(json.dumps({"status": payload["status"], "output": str(args.output)}, sort_keys=True))
    return 0 if payload["status"] == "passed" else 1


def _markdown_paths(
    claims: list[ClaimRecord], boundary_results: list[BoundaryResult]
) -> list[Path]:
    paths = {
        path
        for claim in claims
        for path in (claim.source, *claim.consumers)
        if Path(path).suffix.casefold() in {".md", ".markdown"}
    }
    for result in boundary_results:
        paths.update(
            path
            for path in (result.source, *result.consumers)
            if Path(path).suffix.casefold() in {".md", ".markdown"}
        )
    return [Path(path) for path in sorted(paths)]


if __name__ == "__main__":
    raise SystemExit(main())

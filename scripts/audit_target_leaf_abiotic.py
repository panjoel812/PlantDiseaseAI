"""Audit one target-leaf isolation and Corn morphology-gate decision."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image

from plantdisease.openworld.leaf_pipeline import TargetPoint, isolate_leaf
from plantdisease.serving.abiotic import analyze_corn_abiotic_pattern


def _revision() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unavailable"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _purity_payload(isolation: Any) -> dict[str, Any]:
    payload = asdict(isolation.purity)
    payload["coverage_range"] = list(payload["coverage_range"])
    return payload


def run_audit(image_path: Path, target: TargetPoint) -> dict[str, Any]:
    """Return serializable evidence without invoking a crop or disease model."""

    with Image.open(image_path) as source:
        image = source.convert("RGB")
    isolation = isolate_leaf(image, target_point=target)
    evidence = None
    if isolation.accepted:
        evidence = analyze_corn_abiotic_pattern(image, isolation.mask)

    abiotic_payload = None
    if evidence is not None:
        abiotic_payload = asdict(evidence)
        abiotic_payload.pop("overlay")

    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "code_revision": _revision(),
        "source": {
            "filename": image_path.name,
            "sha256": _sha256(image_path),
            "width": image.width,
            "height": image.height,
            "repository_copy_created": False,
        },
        "target_point": {"x": target.x, "y": target.y},
        "leaf_isolation": {
            "method": isolation.method,
            "selection_mode": isolation.selection_mode,
            "accepted": isolation.accepted,
            "reason": isolation.reason,
            "bounding_box": list(isolation.bounding_box)
            if isolation.bounding_box is not None
            else None,
            "shape": asdict(isolation.shape) if isolation.shape is not None else None,
            "purity": _purity_payload(isolation),
        },
        "abiotic_evidence": abiotic_payload,
        "model_inference_withheld": not isolation.accepted
        or bool(evidence and evidence.suspected),
        "boundary": (
            "OpenCV morphology evidence only; this audit does not establish a "
            "specific nutrient deficiency or professional diagnosis."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--target-x", type=float, required=True)
    parser.add_argument("--target-y", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    target = TargetPoint(args.target_x, args.target_y)
    payload = run_audit(args.image, target)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

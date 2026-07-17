from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import torch

from plantdisease.serving.service import InferenceService


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run one fixed-image demo inference")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", choices=["cpu", "cuda", "mps"], default="cpu")
    parser.add_argument("--target-layer")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--no-gradcam", action="store_true")
    parser.add_argument("--overlay-output", type=Path)
    args = parser.parse_args(argv)

    service = InferenceService.from_checkpoint(
        args.checkpoint,
        device=torch.device(args.device),
        target_layer_name=args.target_layer,
    )
    result = service.predict(
        args.image.read_bytes(),
        top_k=args.top_k,
        include_gradcam=not args.no_gradcam,
    )

    overlay_path = None
    if result.gradcam is not None:
        overlay_path = args.overlay_output or args.output.with_suffix(".overlay.png")
        overlay_path.parent.mkdir(parents=True, exist_ok=True)
        result.gradcam.overlay.save(overlay_path)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "completed",
        "checkpoint": result.checkpoint_path,
        "checkpoint_id": result.checkpoint_id,
        "image": str(args.image),
        "model_name": result.model_name,
        "image_size": result.image_size,
        "target_layer": result.target_layer_name,
        "timings_ms": asdict(result.timings),
        "warnings": result.warnings,
        "knowledge": asdict(result.knowledge),
        "predictions": [asdict(item) for item in result.predictions],
        "gradcam_overlay": str(overlay_path) if overlay_path is not None else None,
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "completed", "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

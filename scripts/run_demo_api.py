from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import uvicorn

from app.api import (
    DEFAULT_CHECKPOINT,
    DEFAULT_CROP_CHECKPOINT,
    DEFAULT_OPENWORLD_INDEX,
    DemoSettings,
    create_app,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the PlantDiseaseAI demo API")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--crop-checkpoint", type=Path, default=DEFAULT_CROP_CHECKPOINT)
    parser.add_argument("--openworld-index", type=Path, default=DEFAULT_OPENWORLD_INDEX)
    parser.add_argument(
        "--no-openworld-gate",
        action="store_true",
        help="disable the experimental prototype novelty gate",
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda", "mps"],
        default="auto",
    )
    parser.add_argument("--target-layer")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    settings = DemoSettings(
        checkpoint=args.checkpoint,
        crop_checkpoint=args.crop_checkpoint,
        openworld_index=None if args.no_openworld_gate else args.openworld_index,
        default_device=args.device,
        target_layer=args.target_layer,
    )
    uvicorn.run(create_app(settings), host=args.host, port=args.port)


if __name__ == "__main__":
    main()

"""Generate PlantVillage EDA figures from the verified dataset adapter."""

import argparse
import json
from pathlib import Path

from plantdisease.data.eda import generate_eda
from plantdisease.data.huggingface import load_plantvillage


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=Path("data/huggingface"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/eda"))
    parser.add_argument("--max-samples", type=int)
    parser.add_argument("--grid-samples", type=int, default=12)
    args = parser.parse_args()
    records, class_names = load_plantvillage(args.cache_dir, args.max_samples)
    artifacts = generate_eda(records, class_names, args.output_dir, args.grid_samples)
    print(json.dumps({name: str(path) for name, path in artifacts.items()}, indent=2))


if __name__ == "__main__":
    main()

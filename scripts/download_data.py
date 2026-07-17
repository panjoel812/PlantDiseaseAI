"""Download PlantVillage into the Hugging Face cache."""

import argparse
import json
from pathlib import Path
from typing import cast

from datasets import DatasetDict, load_dataset

from plantdisease.data.huggingface import plantvillage_script_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=Path("data/huggingface"))
    args = parser.parse_args()
    script_path = plantvillage_script_path(args.cache_dir)
    dataset = cast(
        DatasetDict,
        load_dataset(
            str(script_path),
            name="default",
            trust_remote_code=True,
            cache_dir=str(args.cache_dir),
        ),
    )
    summary = {
        name: {"rows": len(split), "columns": split.column_names} for name, split in dataset.items()
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

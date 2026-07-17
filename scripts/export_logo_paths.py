"""Export the supplied Desmos inner curves as a typed frontend asset."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PATH_PATTERN = re.compile(r'<path id="(expr-(\d{3}))" d="([^"]+)"\s*/>')


def main() -> None:
    """Extract the contiguous inner gesture without altering the source SVG."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source = args.input.read_text(encoding="utf-8")
    paths = [
        (path_id, data)
        for path_id, number, data in PATH_PATTERN.findall(source)
        if 19 <= int(number) <= 54
    ]
    expected_ids = [f"expr-{number:03d}" for number in range(19, 55)]
    if [path_id for path_id, _ in paths] != expected_ids:
        raise SystemExit("Expected contiguous source paths expr-019 through expr-054")

    payload = json.dumps(paths, ensure_ascii=False, indent=2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "// Generated from the supplied Desmos SVG; do not edit by hand.\n"
        f"export const DESMOS_INNER_PATHS = {payload} as const;\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

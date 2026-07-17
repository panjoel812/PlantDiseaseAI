"""Audit bilingual Week 8 paper structure and locked-claim usage."""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Sequence
from pathlib import Path

CLAIM_RE = re.compile(
    r"\\newcommand\{\\(?P<name>PDA[A-Za-z0-9]+)\}\{(?P<value>[^}]*)\}"
)
REQUIRED_SECTION_COUNTS = 13


def parse_claim_macros(path: Path) -> dict[str, str]:
    """Return locked LaTeX command names and values."""

    return {
        match.group("name"): match.group("value")
        for match in CLAIM_RE.finditer(path.read_text(encoding="utf-8"))
    }


def audit_paper_pair(
    zh_path: Path, en_path: Path, claims_path: Path
) -> dict[str, object]:
    """Audit bilingual section count and shared claim-macro usage."""

    claims = parse_claim_macros(claims_path)
    zh_text = zh_path.read_text(encoding="utf-8")
    en_text = en_path.read_text(encoding="utf-8")
    missing_zh = sorted(name for name in claims if f"\\{name}" not in zh_text)
    missing_en = sorted(name for name in claims if f"\\{name}" not in en_text)
    zh_sections = len(re.findall(r"\\section\{", zh_text))
    en_sections = len(re.findall(r"\\section\{", en_text))
    passed = (
        not missing_zh
        and not missing_en
        and zh_sections == REQUIRED_SECTION_COUNTS
        and en_sections == REQUIRED_SECTION_COUNTS
    )
    return {
        "schema_version": 1,
        "status": "passed" if passed else "failed",
        "section_count_zh": zh_sections,
        "section_count_en": en_sections,
        "missing_claims_zh": missing_zh,
        "missing_claims_en": missing_en,
    }


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(
        description="Audit bilingual Week 8 paper structure and claim usage."
    )
    parser.add_argument("--zh", type=Path, required=True, help="Chinese paper entry point")
    parser.add_argument("--en", type=Path, required=True, help="English paper entry point")
    parser.add_argument("--claims", type=Path, required=True, help="Shared LaTeX claim macros")
    parser.add_argument("--output", type=Path, required=True, help="JSON audit report")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the paper audit and return a process exit code."""

    args = build_parser().parse_args(argv)
    result = audit_paper_pair(args.zh, args.en, args.claims)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

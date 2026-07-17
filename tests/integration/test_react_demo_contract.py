"""Static contract for the browser-verified React research demo."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"


def _production_source() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((FRONTEND / "src").rglob("*"))
        if path.suffix in {".ts", ".tsx"} and ".test." not in path.name
    )


def test_react_demo_static_integration_contract() -> None:
    package = json.loads((FRONTEND / "package.json").read_text(encoding="utf-8"))
    source = _production_source()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "liquid-glass-react" in package["dependencies"]
    assert 'from "liquid-glass-react"' in source
    assert "field_corn_leaf.jpeg" in source

    assert "uv run python scripts/run_demo_api.py" in readme
    assert "npm run dev -- --host 127.0.0.1 --port 5173" in readme
    assert "npm ci" in readme
    assert "npm run build" in readme
    assert "Check again" in readme

    assert "11/15" in source
    assert "1/5" in source
    assert "no automatic download" in readme.lower()

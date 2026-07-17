import json
import subprocess
import sys
from pathlib import Path


def test_demo_vlm_assistant_cli_writes_safety_scenarios(tmp_path: Path) -> None:
    output = tmp_path / "assistant_demo.json"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/demo_vlm_assistant.py",
            "--output",
            str(output),
        ],
        cwd=Path(__file__).resolve().parents[2],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "completed"
    assert payload["scenario_count"] == 4
    actions = {example["action"] for example in payload["examples"]}
    assert actions == {
        "educational_summary",
        "refuse_high_risk",
        "refuse_low_confidence",
        "refuse_out_of_scope",
    }

import json
import re
from pathlib import Path


def test_architecture_keeps_vlm_outside_classifier_main_pipeline() -> None:
    source = Path("scripts/build_week7_apple_showcase.mjs").read_text(encoding="utf-8")

    main_match = re.search(
        r"const CLASSIFIER_MAIN_PIPELINE = (\[[^\n]+\]);",
        source,
    )
    branch_match = re.search(
        r"const EXPLORATORY_VLM_BRANCH = (\{[^\n]+\});",
        source,
    )

    assert main_match is not None, "Declare the classifier main-line source contract"
    assert json.loads(main_match.group(1)) == [
        "Data\\nAudit",
        "Train",
        "Evaluate",
        "Explain",
        "Serve",
    ]
    assert branch_match is not None, "Declare VLM as a separate branch contract"
    assert json.loads(branch_match.group(1)) == {
        "from": "Serve",
        "label": "VLM",
        "status": "Exploratory",
    }

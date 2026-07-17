import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).parents[2] / "scripts" / "audit_week8_paper.py"
SPEC = importlib.util.spec_from_file_location("audit_week8_paper", MODULE_PATH)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - static path invariant
    raise RuntimeError(f"Could not load {MODULE_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
audit_paper_pair = MODULE.audit_paper_pair
parse_claim_macros = MODULE.parse_claim_macros


def test_parse_claim_macros_reads_locked_values(tmp_path: Path) -> None:
    claims = tmp_path / "claims.tex"
    claims.write_text(
        r"\newcommand{\PDAFinalAccuracy}{0.9953}" + "\n",
        encoding="utf-8",
    )
    assert parse_claim_macros(claims) == {"PDAFinalAccuracy": "0.9953"}


def test_audit_requires_bilingual_sections_and_claim_usage(tmp_path: Path) -> None:
    claims = tmp_path / "claims.tex"
    claims.write_text(
        r"\newcommand{\PDAFinalAccuracy}{0.9953}" + "\n",
        encoding="utf-8",
    )
    zh = tmp_path / "zh.tex"
    en = tmp_path / "en.tex"
    zh.write_text(r"\section{引言}\PDAFinalAccuracy", encoding="utf-8")
    en.write_text(r"\section{Introduction}", encoding="utf-8")
    result = audit_paper_pair(zh, en, claims)
    assert result["status"] == "failed"
    assert result["missing_claims_en"] == ["PDAFinalAccuracy"]


def test_shared_claims_cover_cross_document_metrics() -> None:
    macros = parse_claim_macros(Path("paper/shared/week8_verified_claims.tex"))
    assert {
        "PDAOfficialOverlap": "227",
        "PDAFinalAccuracy": "0.9953",
        "PDAFinalMacroFOne": "0.9941",
        "PDADemoLatency": "129.8",
        "PDAVLMChoice": "11/15",
        "PDAVLMCondition": "1/5",
        "PDAWeekEightCleanTests": "226",
    }.items() <= macros.items()


def test_bilingual_papers_use_browser_audited_react_demo() -> None:
    expected = "../../reports/figures/week8_react_demo_desktop.png"
    clipped_source = "../../reports/figures/week5_streamlit_demo.jpg"

    for paper_path in (Path("paper/zh/main.tex"), Path("paper/en/main.tex")):
        paper = paper_path.read_text(encoding="utf-8")
        assert expected in paper
        assert clipped_source not in paper


def test_bilingual_papers_do_not_freeze_unset_release_commit_state() -> None:
    zh = Path("paper/zh/main.tex").read_text(encoding="utf-8")
    en = Path("paper/en/main.tex").read_text(encoding="utf-8")

    assert "release commit 仍为空" not in zh
    assert "release commit remains unset" not in en
    assert "未创建或发布远程 release" in zh
    assert "no remote release is created or published" in en

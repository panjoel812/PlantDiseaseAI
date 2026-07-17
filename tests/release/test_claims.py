from __future__ import annotations

import subprocess
from dataclasses import FrozenInstanceError
from pathlib import Path
from zipfile import ZipFile

import pytest

from plantdisease.release.claims import (
    ClaimRecord,
    audit_claims,
    extract_pptx_text,
    find_broken_markdown_links,
    load_claims,
)


def test_load_claims_reads_locked_configuration() -> None:
    claims = load_claims(Path("configs/week8_claims.yaml"))

    assert claims[0] == ClaimRecord(
        "official_split_overlap",
        "227",
        "reports/data_audit.md",
        (
            "README.md",
            "README.zh-CN.md",
            "docs/blog/week7_technical_blog_zh.md",
            "docs/presentation/week7_apple_showcase_deck.pptx",
            "docs/presentation/plantdisease_ai_week8_research_defense.pptx",
            "paper/zh/main.tex",
            "paper/en/main.tex",
            "reports/final_experiment_report.md",
            "reports/model_card.md",
            "reports/data_card.md",
            "docs/release/week8_release_checklist.md",
            "docs/resume/week8_resume_evidence.md",
            "docs/mentor/week8_mentor_summary.md",
        ),
        "field",
    )
    assert {claim.id for claim in claims} == {
        "official_split_overlap",
        "final_accuracy",
        "final_macro_f1",
        "container_observation_ms",
        "qwen_choice_score",
        "qwen_condition_score",
        "clean_test_count",
        "react_field_image_no_ground_truth",
        "react_field_image_out_of_domain",
        "react_classifier_prediction",
        "react_qwen_local_runtime",
    }

    react_claims = {claim.id: claim for claim in claims if claim.id.startswith("react_")}
    assert react_claims["react_field_image_no_ground_truth"].value == (
        "0364ff44229c70666216343057f9ae77d82438a7f842b30af1ffabb786061a7e"
    )
    assert react_claims["react_field_image_no_ground_truth"].required_boundary == (
        "no verified ground truth"
    )
    assert react_claims["react_field_image_out_of_domain"].required_boundary == (
        "out-of-domain"
    )
    assert react_claims["react_classifier_prediction"].value == "0.870144"
    assert react_claims["react_classifier_prediction"].required_boundary == "prediction"
    assert react_claims["react_qwen_local_runtime"].value == (
        "mlx-community/Qwen3-VL-4B-Instruct-4bit"
    )
    assert react_claims["react_qwen_local_runtime"].required_boundary == (
        "no automatic download"
    )


def test_locked_claims_pass_real_consumer_audit() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    results = audit_claims(
        repo_root,
        load_claims(repo_root / "configs/week8_claims.yaml"),
    )
    failures = {
        result.claim_id: {
            "missing_sources": result.missing_sources,
            "missing_value_consumers": result.missing_value_consumers,
            "missing_boundary_consumers": result.missing_boundary_consumers,
        }
        for result in results
        if result.status != "passed"
    }

    assert failures == {}


def test_tracked_text_does_not_publish_personal_macos_paths() -> None:
    personal_prefix = "/" + "Users" + "/"
    result = subprocess.run(
        [
            "git",
            "grep",
            "-n",
            personal_prefix,
            "--",
            ":!*.pptx",
            ":!*.key",
            ":!*.pdf",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1, result.stdout


def test_claim_record_is_frozen() -> None:
    claim = ClaimRecord("accuracy", "0.9953", "report.md", (), "official split")

    with pytest.raises(FrozenInstanceError):
        claim.value = "changed"  # type: ignore[misc]


def test_extract_pptx_text_reads_slide_and_notes(tmp_path: Path) -> None:
    deck = tmp_path / "deck.pptx"
    with ZipFile(deck, "w") as archive:
        archive.writestr("ppt/slides/slide1.xml", "<a:t>0.9953</a:t>")
        archive.writestr(
            "ppt/notesSlides/notesSlide1.xml", "<a:t>official split</a:t>"
        )
    text = extract_pptx_text(deck)
    assert "0.9953" in text
    assert "official split" in text


def test_extract_pptx_text_sorts_parts_and_unescapes_text(tmp_path: Path) -> None:
    deck = tmp_path / "deck.pptx"
    with ZipFile(deck, "w") as archive:
        archive.writestr("ppt/slides/slide2.xml", "<a:t>second &amp; safe</a:t>")
        archive.writestr("ppt/slides/slide1.xml", "<a:t>first</a:t>")

    assert extract_pptx_text(deck).splitlines() == ["first", "second & safe"]


def test_claim_audit_reports_missing_value(tmp_path: Path) -> None:
    (tmp_path / "report.md").write_text("official split", encoding="utf-8")
    result = audit_claims(
        tmp_path,
        [
            ClaimRecord(
                "accuracy",
                "0.9953",
                "report.md",
                ("report.md",),
                "official split",
            )
        ],
    )[0]
    assert result.status == "failed"
    assert result.missing_value_consumers == ("report.md",)


def test_claim_audit_records_missing_source_and_boundary_without_raising(
    tmp_path: Path,
) -> None:
    (tmp_path / "consumer.md").write_text("VALUE", encoding="utf-8")

    result = audit_claims(
        tmp_path,
        [ClaimRecord("claim", "value", "missing.md", ("consumer.md",), "Boundary")],
    )[0]

    assert result.status == "failed"
    assert result.missing_sources == ("missing.md",)
    assert result.missing_value_consumers == ()
    assert result.missing_boundary_consumers == ("consumer.md",)


def test_claim_audit_reads_pptx_and_compares_case_insensitively(tmp_path: Path) -> None:
    (tmp_path / "source.md").write_text("0.9953 OFFICIAL SPLIT", encoding="utf-8")
    deck = tmp_path / "deck.pptx"
    with ZipFile(deck, "w") as archive:
        archive.writestr(
            "ppt/slides/slide1.xml", "<a:t>0.9953 Official Split</a:t>"
        )

    result = audit_claims(
        tmp_path,
        [ClaimRecord("accuracy", "0.9953", "source.md", ("deck.pptx",), "official split")],
    )[0]

    assert result.status == "passed"
    assert result.missing_sources == ()
    assert result.missing_value_consumers == ()
    assert result.missing_boundary_consumers == ()


@pytest.mark.parametrize(
    ("required_boundary", "localized_boundary"),
    (("field", "田间"), ("fixed", "固定")),
)
def test_claim_audit_accepts_locked_chinese_boundary_equivalents(
    tmp_path: Path, required_boundary: str, localized_boundary: str
) -> None:
    (tmp_path / "source.md").write_text("129.8", encoding="utf-8")
    (tmp_path / "consumer.md").write_text(
        f"129.8 {localized_boundary}", encoding="utf-8"
    )

    result = audit_claims(
        tmp_path,
        [
            ClaimRecord(
                "localized_boundary",
                "129.8",
                "source.md",
                ("consumer.md",),
                required_boundary,
            )
        ],
    )[0]

    assert result.status == "passed"


def test_claim_audit_reads_values_from_local_tex_inputs(tmp_path: Path) -> None:
    (tmp_path / "source.md").write_text("0.9953 official split", encoding="utf-8")
    paper = tmp_path / "paper"
    paper.mkdir()
    (paper / "claims.tex").write_text(
        r"\newcommand{\PDAFinalAccuracy}{0.9953}", encoding="utf-8"
    )
    (paper / "main.tex").write_text(
        r"\input{claims}\section{Results} official split",
        encoding="utf-8",
    )

    result = audit_claims(
        tmp_path,
        [
            ClaimRecord(
                "accuracy",
                "0.9953",
                "source.md",
                ("paper/main.tex",),
                "official split",
            )
        ],
    )[0]

    assert result.status == "passed"


def test_claim_audit_rejects_tex_input_outside_repository(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-claims.tex"
    outside.write_text("0.9953", encoding="utf-8")
    (tmp_path / "source.md").write_text("0.9953 official split", encoding="utf-8")
    (tmp_path / "main.tex").write_text(
        r"\input{../outside-claims.tex} official split",
        encoding="utf-8",
    )

    result = audit_claims(
        tmp_path,
        [
            ClaimRecord(
                "accuracy",
                "0.9953",
                "source.md",
                ("main.tex",),
                "official split",
            )
        ],
    )[0]

    assert result.status == "failed"
    assert result.missing_value_consumers == ("main.tex",)


def test_claim_audit_records_unreadable_pptx_without_raising(tmp_path: Path) -> None:
    (tmp_path / "source.md").write_text("value boundary", encoding="utf-8")
    (tmp_path / "broken.pptx").write_text("not a zip", encoding="utf-8")

    result = audit_claims(
        tmp_path,
        [ClaimRecord("claim", "value", "source.md", ("broken.pptx",), "boundary")],
    )[0]

    assert result.status == "failed"
    assert result.missing_value_consumers == ("broken.pptx",)
    assert result.missing_boundary_consumers == ("broken.pptx",)


def test_link_audit_reports_only_missing_local_link(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("[ok](docs/ok.md) [bad](docs/missing.md)", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "ok.md").write_text("ok", encoding="utf-8")
    assert find_broken_markdown_links(tmp_path, [readme]) == [
        "README.md -> docs/missing.md"
    ]


def test_link_audit_accepts_balanced_parentheses_in_local_target(
    tmp_path: Path,
) -> None:
    readme = tmp_path / "README.md"
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "file_(old).md").write_text("old", encoding="utf-8")
    readme.write_text("[old](docs/file_(old).md)", encoding="utf-8")

    assert find_broken_markdown_links(tmp_path, [readme]) == []


def test_link_audit_accepts_angle_target_and_optional_title(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "file old.md").write_text("angle", encoding="utf-8")
    (docs / "titled.md").write_text("title", encoding="utf-8")
    readme.write_text(
        '[angle](<docs/file old.md>) [title](docs/titled.md "Optional title")',
        encoding="utf-8",
    )

    assert find_broken_markdown_links(tmp_path, [readme]) == []


def test_link_audit_skips_external_and_anchor_targets(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        " ".join(
            (
                "[web](https://example.com)",
                "[http](http://example.com)",
                "[mail](mailto:test@example.com)",
                "[data](data:text/plain,ok)",
                "[anchor](#section)",
            )
        ),
        encoding="utf-8",
    )

    assert find_broken_markdown_links(tmp_path, [readme]) == []


def test_link_audit_strips_query_fragment_and_rejects_outside_repo(
    tmp_path: Path,
) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    page = docs / "page.md"
    target = docs / "target.md"
    target.write_text("target", encoding="utf-8")
    page.write_text(
        "[ok](target.md?view=1#part) [outside](../../outside.md)", encoding="utf-8"
    )

    assert find_broken_markdown_links(tmp_path, [page]) == [
        "docs/page.md -> ../../outside.md"
    ]

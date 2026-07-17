import json
import re
from pathlib import Path

from plantdisease.release.manifest import sha256_file

CONTRACT_PATH = Path("docs/presentation/week8_research_defense_content.json")

EXPECTED_SLIDES = [
    (1, "title", "PlantDiseaseAI", "从高分模型到可审计研究系统", "black"),
    (2, "question", "高准确率，等于可信诊断吗？", "研究问题与判断标准", "white"),
    (3, "scope", "38 类受控图像分类", "PlantVillage 定义了任务，也限制了结论", "white"),
    (4, "overlap", "227", "official split 并非实体隔离", "black"),
    (5, "loop", "证据必须形成闭环", "数据、训练、评估、解释与服务", "white"),
    (6, "models", "五个模型，同一协议", "比较架构，而不是比较训练条件", "white"),
    (7, "tradeoff", "一个追求精度，一个追求效率", "ResNet50 与 MobileNetV2", "white"),
    (8, "baseline", "先冻结基线", "ResNet50: 0.9830 / 0.9743", "black"),
    (9, "single", "最强单变量改变优化路径", "Cosine Scheduler: 0.9898", "black"),
    (10, "final", "0.9953 / 0.9941", "seed 42 · official split · 227 overlap", "black"),
    (11, "errors", "50 / 10709", "高分仍需要逐样本错误审计", "white"),
    (12, "confusions", "错误集中在视觉相似病害", "三组主要混淆对", "white"),
    (
        13,
        "calibration",
        "准确率不等于置信度质量",
        "ECE 0.0965 · MCE 0.3348 · Brier 0.0140",
        "white",
    ),
    (14, "gradcam", "解释目标层会改变观察结果", "Grad-CAM 是相关性，不是因果", "black"),
    (15, "demo", "React Demo 也必须可审计", "Top-5 · Grad-CAM · 安全边界", "black"),
    (
        16,
        "serving",
        "工程证据也必须注明条件",
        "MPS · Apple container · fixed-example latency",
        "black",
    ),
    (17, "vlm", "VLM 是探索分支，不是主线替代", "Qwen3-VL smoke exploration", "white"),
    (18, "vlm_boundary", "11/15 与 1/5", "结构化选择提升输出，细粒度病害仍弱", "black"),
    (19, "release", "结果必须能被重新检查", "week8-rc1 · manifest · claim ledger", "white"),
    (20, "future", "下一步不是再堆功能", "实体隔离 · 多 seed · 田间数据 · 人工审计", "black"),
]

EXPECTED_TRANSITION_GROUPS = {
    3: "scope-risk",
    4: "scope-risk",
    6: "models",
    7: "models",
    8: "ablation",
    9: "ablation",
    10: "ablation",
    11: "errors",
    12: "errors",
    13: "explainability",
    14: "explainability",
    15: "demo",
    16: "demo",
    17: "vlm",
    18: "vlm",
}


def _load_contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_week8_research_defense_contract_is_complete() -> None:
    payload = _load_contract()
    slides = payload["slides"]

    assert payload["schema_version"] == 1
    assert isinstance(slides, list)
    assert len(slides) == 20
    assert [slide["number"] for slide in slides] == list(range(1, 21))
    assert all(slide["notes"].strip() for slide in slides)
    assert {
        slide["transition_group"]
        for slide in slides
        if slide["transition_group"]
    } == {
        "scope-risk",
        "models",
        "ablation",
        "errors",
        "explainability",
        "demo",
        "vlm",
    }


def test_week8_research_defense_contract_locks_order_and_narrative() -> None:
    slides = _load_contract()["slides"]
    actual = [
        (
            slide["number"],
            slide["id"],
            slide["title"],
            slide["claim"],
            slide["theme"],
        )
        for slide in slides
    ]
    assert actual == EXPECTED_SLIDES


def test_week8_research_defense_contract_locks_transition_pairs() -> None:
    slides = _load_contract()["slides"]
    actual = {
        slide["number"]: slide["transition_group"]
        for slide in slides
        if slide["transition_group"] is not None
    }
    assert actual == EXPECTED_TRANSITION_GROUPS
    assert _load_contract()["transition_defaults"] == {
        "effect": "Magic Move / Morph",
        "duration_seconds": 0.9,
        "trigger": "click",
    }


def test_week8_research_defense_contract_has_auditable_notes_and_evidence() -> None:
    slides = _load_contract()["slides"]
    required_fields = {
        "number",
        "id",
        "title",
        "claim",
        "visual",
        "notes",
        "theme",
        "transition_group",
        "required_boundary",
        "evidence",
    }

    for slide in slides:
        assert set(slide) == required_fields
        assert re.search(r"[\u4e00-\u9fff]", slide["notes"])
        assert "证据：" in slide["notes"]
        assert "转场：" in slide["notes"]
        assert slide["required_boundary"].strip()
        assert slide["evidence"]
        for evidence_path in slide["evidence"]:
            path = Path(evidence_path)
            assert not path.is_absolute()
            assert path.exists(), evidence_path
            assert evidence_path in slide["notes"]


def test_week8_research_defense_contract_preserves_locked_claim_boundaries() -> None:
    serialized = CONTRACT_PATH.read_text(encoding="utf-8")
    for value in (
        "227",
        "0.9830",
        "0.9743",
        "2.27M",
        "0.31G",
        "644.3",
        "0.9953",
        "0.9941",
        "50 / 10709",
        "0.0965",
        "0.3348",
        "0.0140",
        "129.8",
        "11/15",
        "1/5",
        "seed 42",
        "official split",
        "非因果",
        "smoke",
        "非专业诊断",
        "226 passed",
        "Apple container：passed",
    ):
        assert value in serialized

    final_slide = _load_contract()["slides"][9]
    final_context = " ".join(
        [
            final_slide["title"],
            final_slide["claim"],
            final_slide["notes"],
            final_slide["required_boundary"],
        ]
    )
    assert all(
        phrase in final_context
        for phrase in ("0.9953", "0.9941", "seed 42", "official split", "227")
    )


def test_week8_model_slide_uses_the_verified_week2_roster() -> None:
    model_slide = _load_contract()["slides"][5]
    assert (
        "MobileNetV2、ResNet18、ResNet50、EfficientNet-B0 与 EfficientNetV2-S"
        in model_slide["notes"]
    )
    assert "ViT" not in model_slide["notes"]


def test_week8_gradcam_slide_separates_correction_and_review_evidence() -> None:
    gradcam_slide = _load_contract()["slides"][13]
    assert gradcam_slide["evidence"] == [
        "reports/week4_stage_report.md",
        "reports/week4_frozen_samples.md",
        "reports/week4_attention_review.md",
    ]
    assert (
        "目标层修正证据：reports/week4_stage_report.md、"
        "reports/week4_frozen_samples.md"
    ) in gradcam_slide["notes"]
    assert (
        "最终非因果审阅证据：reports/week4_attention_review.md"
        in gradcam_slide["notes"]
    )


def test_week8_demo_slide_records_react_evidence_and_safety_boundaries() -> None:
    demo_slide = _load_contract()["slides"][14]
    serialized = json.dumps(demo_slide, ensure_ascii=False)
    for phrase in (
        "教育用途",
        "PlantVillage 域",
        "不构成或替代专业诊断",
        "no verified ground truth",
        "out-of-domain",
        "prediction",
        "0.870144",
    ):
        assert phrase in serialized
    assert demo_slide["evidence"] == ["reports/week8_react_demo_qa.md"]
    assert "拒答" not in serialized
    assert "refuse_" not in serialized


def test_week8_presentation_qa_matches_current_binary_identities() -> None:
    qa = Path("reports/week8_presentation_qa.md").read_text(encoding="utf-8")
    for path in (
        Path("docs/presentation/plantdisease_ai_week8_research_defense.pptx"),
        Path("docs/presentation/plantdisease_ai_week8_research_defense.key"),
    ):
        assert f"{path}` | {path.stat().st_size:,} bytes" in qa
        assert f"`{sha256_file(path)}`" in qa

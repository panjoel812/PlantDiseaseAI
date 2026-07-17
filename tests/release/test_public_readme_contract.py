from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
README_ZH = ROOT / "README.zh-CN.md"
CONTAINERFILE = ROOT / "Containerfile"
CLAIMS_CONFIG = ROOT / "configs/week8_claims.yaml"
ASSET_LICENSES = ROOT / "ASSET_LICENSES.md"
PUBLICATION_DECISIONS = ROOT / "docs/release/publication_decisions.md"
RELEASE_DESIGN = (
    ROOT
    / "docs/superpowers/specs/2026-07-17-public-readme-and-docker-release-design.md"
)
RELEASE_PLAN = (
    ROOT / "docs/superpowers/plans/2026-07-17-public-readme-and-docker-release.md"
)


def test_public_readme_has_layered_teaching_structure() -> None:
    text = README.read_text(encoding="utf-8")
    required = (
        "[English](README.md) | [简体中文](README.zh-CN.md)",
        "## What you can try",
        "## Architecture",
        "## Platform support",
        "## Prerequisites",
        "## Five-minute smoke test",
        "## Train and evaluate on PlantVillage",
        "## React + FastAPI demo",
        "## Streamlit demo",
        "## Docker on Linux, macOS, and Windows",
        "## Reproducibility and evidence",
        "## Known limitations",
        "## Safety",
    )
    for fragment in required:
        assert fragment in text


def test_public_readme_has_copyable_cross_platform_docker_commands() -> None:
    text = README.read_text(encoding="utf-8")
    required = (
        "docker build -f Containerfile -t plantdisease-ai:week8 .",
        'MODEL_DIR="$(pwd)/outputs/plantvillage/week3_ablation/09_combo_candidate_seed42"',
        '--mount "type=bind,src=${MODEL_DIR},dst=/models,readonly"',
        '$ModelDir = (Resolve-Path ".\\outputs\\plantvillage\\week3_ablation\\'
        '09_combo_candidate_seed42").Path',
        '--mount "type=bind,source=$ModelDir,target=/models,readonly"',
        "curl --fail http://127.0.0.1:8501/_stcore/health",
        "Invoke-RestMethod http://127.0.0.1:8501/_stcore/health",
        "Docker Desktop with the WSL2 backend",
        "CPU-only Streamlit image",
        "Docker Engine/Desktop execution was not run in this release environment.",
        "Windows PowerShell was statically inspected only.",
        "[publication decision record](docs/release/publication_decisions.md)",
    )
    for fragment in required:
        assert fragment in text
    bash_guard = 'if ! test -f "${MODEL_DIR}/checkpoint.pt"; then'
    guard_start = text.index(bash_guard)
    docker_start = text.index("docker run -d --rm --name plantdisease-ai", guard_start)
    assert "exit 1" in text[guard_start:docker_start]

    docker_section = text.split("## Docker on Linux, macOS, and Windows", 1)[1]
    docker_section = docker_section.split("## Optional Qwen panel", 1)[0]
    bash_section = docker_section.split("### Linux or macOS with Bash", 1)[1]
    bash_section = bash_section.split("### Windows PowerShell with Docker Desktop", 1)[0]
    powershell_section = docker_section.split(
        "### Windows PowerShell with Docker Desktop", 1
    )[1]
    powershell_section = powershell_section.split("### Troubleshooting", 1)[0]
    bash_code = bash_section.split("```bash", 1)[1].split("```", 1)[0]
    powershell_code = powershell_section.split("```powershell", 1)[1].split(
        "```", 1
    )[0]

    assert text.count("docker run -d --rm --name plantdisease-ai") == 2
    assert "docker run --rm --name plantdisease-ai" not in text
    assert bash_section.index("docker run -d --rm --name plantdisease-ai") < (
        bash_section.index("curl --fail http://127.0.0.1:8501/_stcore/health")
    )
    assert bash_section.index("curl --fail") < bash_section.index(
        "docker logs plantdisease-ai"
    )
    assert bash_section.index("docker logs plantdisease-ai") < bash_section.index(
        "docker stop plantdisease-ai"
    )
    assert powershell_section.index("docker run -d --rm --name plantdisease-ai") < (
        powershell_section.index(
            "Invoke-RestMethod http://127.0.0.1:8501/_stcore/health"
        )
    )
    assert powershell_section.index("Invoke-RestMethod") < powershell_section.index(
        "docker logs plantdisease-ai"
    )
    assert powershell_section.index(
        "docker logs plantdisease-ai"
    ) < powershell_section.index("docker stop plantdisease-ai")
    assert bash_code.strip().endswith("docker stop plantdisease-ai")
    assert powershell_code.strip().endswith("docker stop plantdisease-ai")


def test_public_readme_keeps_model_and_research_boundaries() -> None:
    text = README.read_text(encoding="utf-8")
    required = (
        "The final checkpoint is not distributed in this repository",
        "single seed 42",
        "227 overlapping `leaf_id` values",
        "not evidence of field generalization",
        "Grad-CAM is a non-causal relevance visualization",
        "educational and research use only",
        "No automatic download",
        "Apple Silicon",
    )
    for fragment in required:
        assert fragment in text


def test_chinese_entry_is_present_and_links_to_canonical_guide() -> None:
    text = README_ZH.read_text(encoding="utf-8")
    english = README.read_text(encoding="utf-8")
    assert "[English](README.md) | [简体中文](README.zh-CN.md)" in text
    assert "[简体中文](README.zh-CN.md)" in english
    assert len(text) >= 12_000
    assert "process memory" in english
    assert "进程内存" in text
    assert "Management guidance → Configure" in english
    assert "Raw response" in text
    assert "完整英文运行指南" in text
    assert "docs/tutorials/README.md" in text
    assert "paper/out/plantdisease_ai_zh.pdf" in text
    assert "不会自动下载" in text
    assert "仅供教育和研究使用" in text
    assert "seed 42" in text
    assert "仅表示项目预期接口" in text
    assert "reports/week8_reproducibility.md" in text
    assert "Docker Engine/Desktop 未在本次发布环境中运行" in text
    assert "Windows PowerShell 仅经过静态检查" in text
    assert "[资源许可说明](ASSET_LICENSES.md)" in text

    payload = yaml.safe_load(CLAIMS_CONFIG.read_text(encoding="utf-8"))
    claims = {claim["id"]: claim for claim in payload["claims"]}
    for claim_id in ("official_split_overlap", "final_accuracy", "final_macro_f1"):
        assert "README.zh-CN.md" in claims[claim_id]["consumers"]
    boundaries = {boundary["id"]: boundary for boundary in payload["boundaries"]}
    for boundary_id in (
        "gradcam_non_causality",
        "field_limits",
        "no_professional_diagnosis",
    ):
        assert "README.zh-CN.md" in boundaries[boundary_id]["consumers"]


def test_containerfile_matches_documented_runtime_contract() -> None:
    text = CONTAINERFILE.read_text(encoding="utf-8")
    assert "ENV UV_TORCH_BACKEND=cpu" in text
    assert 'EXPOSE 8501' in text
    assert '"--checkpoint", "/models/checkpoint.pt"' in text
    assert "COPY outputs" not in text
    assert "COPY data" not in text


def test_public_asset_license_notice_excludes_supplied_image_from_mit() -> None:
    readme = README.read_text(encoding="utf-8")
    notice = ASSET_LICENSES.read_text(encoding="utf-8")

    assert "[asset license notice](ASSET_LICENSES.md)" in readme
    assert "MIT license applies to project code unless otherwise noted" in notice
    assert "`app/examples/field_corn_leaf.jpeg`" in notice
    assert "supplied by the user for this public repository and demo" in notice
    assert "not licensed under the MIT License" in notice
    assert "No reuse license is granted" in notice
    assert "direct visible reproductions or crops" in notice
    assert "retain their upstream terms" in notice


def test_publication_decision_records_static_waiver_and_release_boundaries() -> None:
    decision = PUBLICATION_DECISIONS.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    readme_zh = README_ZH.read_text(encoding="utf-8")
    required = (
        "Apple `container`",
        "declined Docker installation",
        "`container: not_run`",
        "Windows PowerShell validation is static-only",
        "clean, minimal Git history",
        "noreply metadata",
        "development-only installed skill prose",
        "internal SDD reports",
        "ASSET_LICENSES.md",
    )
    for fragment in required:
        assert fragment in decision
    assert "/" + "Users" + "/" not in decision
    assert "container: not_run" in readme
    assert "container: not_run" in readme_zh
    assert (
        "Neither boundary is evidence of Docker build, health, Linux, or Windows "
        "runtime verification."
        in decision.replace("\n", " ")
    )
    forbidden_runtime_claims = (
        "Docker build passed",
        "Docker build succeeded",
        "Docker health check passed",
        "Docker health check succeeded",
        "Linux runtime verified",
        "Linux runtime validated",
        "Windows runtime verified",
        "Windows runtime validated",
        "Docker runtime verified",
        "Docker runtime validated",
        "tested with Docker Engine",
        "tested with Docker Desktop",
        "Docker 已验证",
        "Docker 已实测",
        "Docker 运行已验证",
        "Linux 已验证",
        "Linux 运行已验证",
        "Linux 运行已实测",
        "Windows 已验证",
        "Windows 运行已验证",
        "Windows 运行已实测",
    )
    public_boundary_documents = (readme, readme_zh, decision)
    for claim in forbidden_runtime_claims:
        for document in public_boundary_documents:
            assert claim not in document


def test_release_design_and_plan_record_dated_docker_gate_override() -> None:
    design = RELEASE_DESIGN.read_text(encoding="utf-8")
    plan = RELEASE_PLAN.read_text(encoding="utf-8")

    assert "If Docker is unavailable, publication stops" in design
    for text in (design, plan):
        assert "2026-07-17 override" in text
        assert "supersedes the original Docker publication gate" in text
        assert "Docker Engine/Desktop runtime remains `not_run`" in text
        assert "Windows PowerShell validation remains static-only" in text


def test_release_design_and_plan_use_detached_normative_docker_workflows() -> None:
    design = RELEASE_DESIGN.read_text(encoding="utf-8")
    plan = RELEASE_PLAN.read_text(encoding="utf-8")
    design_docker = design.split("## Docker Design", 1)[1].split(
        "## Chinese Entry", 1
    )[0]
    plan_docker = plan.split("## Docker on Linux, macOS, and Windows", 1)[1].split(
        "## Optional Qwen panel", 1
    )[0]

    workflows = (
        (
            design_docker.split("### Linux and macOS Bash", 1)[1].split(
                "### Windows PowerShell", 1
            )[0],
            "bash",
            "curl --fail http://127.0.0.1:8501/_stcore/health",
        ),
        (
            design_docker.split("### Windows PowerShell", 1)[1],
            "powershell",
            "Invoke-RestMethod http://127.0.0.1:8501/_stcore/health",
        ),
        (
            plan_docker.split("### Linux or macOS with Bash", 1)[1].split(
                "### Windows PowerShell with Docker Desktop", 1
            )[0],
            "bash",
            "curl --fail http://127.0.0.1:8501/_stcore/health",
        ),
        (
            plan_docker.split("### Windows PowerShell with Docker Desktop", 1)[1],
            "powershell",
            "Invoke-RestMethod http://127.0.0.1:8501/_stcore/health",
        ),
    )

    for section, language, health_command in workflows:
        code = section.split(f"```{language}", 1)[1].split("```", 1)[0]
        run_command = "docker run -d --rm --name plantdisease-ai"
        assert code.count(run_command) == 1
        assert "docker run --rm --name plantdisease-ai" not in code
        assert "/models,readonly" in code
        assert code.index(run_command) < code.index(health_command)
        assert code.index(health_command) < code.index("docker logs plantdisease-ai")
        assert code.index("docker logs plantdisease-ai") < code.index(
            "docker stop plantdisease-ai"
        )
        assert code.strip().endswith("docker stop plantdisease-ai")

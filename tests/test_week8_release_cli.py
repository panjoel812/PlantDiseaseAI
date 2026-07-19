from __future__ import annotations

import hashlib
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

from pytest import MonkeyPatch

from plantdisease.release.runner import CommandSpec


def test_week8_clis_expose_help() -> None:
    for script in (
        "scripts/build_release_candidate.py",
        "scripts/audit_week8_claims.py",
        "scripts/run_week8_repro.py",
    ):
        result = subprocess.run(
            [sys.executable, script, "--help"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        assert "week8" in result.stdout.casefold()


def test_week8_repro_commands_match_locked_contract(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    commands = importlib.import_module("run_week8_repro").COMMANDS

    assert commands == (
        CommandSpec("sync", ("uv", "sync", "--frozen", "--all-groups"), 1800),
        CommandSpec("pytest", ("uv", "run", "pytest", "-q"), 1800),
        CommandSpec("ruff", ("uv", "run", "ruff", "check", "."), 300),
        CommandSpec(
            "typecheck",
            ("uv", "run", "ty", "check", "src/plantdisease", "app", "scripts"),
            600,
        ),
        CommandSpec(
            "claims",
            (
                "uv",
                "run",
                "python",
                "scripts/audit_week8_claims.py",
                "--config",
                "configs/week8_claims.yaml",
                "--output",
                "outputs/plantvillage/week8_release/week8-rc1/claims.json",
                "--check-links",
            ),
            300,
        ),
        CommandSpec(
            "smoke",
            (
                "uv",
                "run",
                "plant-smoke",
                "--output-dir",
                "outputs/plantvillage/week8_release/week8-rc1/clean_smoke",
                "--seed",
                "42",
                "--image-size",
                "32",
            ),
            900,
        ),
        CommandSpec("package", ("uv", "build"), 600),
        CommandSpec("cli_help", ("uv", "run", "plant-smoke", "--help"), 120),
    )


def test_audit_week8_claims_writes_machine_readable_result(tmp_path: Path) -> None:
    output = tmp_path / "claims.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/audit_week8_claims.py",
            "--config",
            "configs/week8_claims.yaml",
            "--output",
            str(output),
            "--check-links",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["status"] == "passed"
    assert payload["counts"] == {
        "boundaries": 4,
        "broken_links": 0,
        "claims": 11,
        "failed": 0,
        "passed": 15,
    }
    assert len(payload["claim_results"]) == 11
    assert len(payload["boundary_results"]) == 4
    overlap = next(
        item
        for item in payload["claim_results"]
        if item["claim_id"] == "official_split_overlap"
    )
    assert overlap["value"] == "227"
    assert overlap["source"] == "reports/data_audit.md"
    assert overlap["required_boundary"] == "field"
    assert "reports/final_experiment_report.md" in overlap["consumers"]
    clean_tests = next(
        item
        for item in payload["claim_results"]
        if item["claim_id"] == "clean_test_count"
    )
    assert clean_tests["value"] == "226"
    assert clean_tests["source"] == "reports/week8_reproducibility.md"
    assert clean_tests["required_boundary"] == "clean"


def test_checked_in_claim_ledger_matches_current_audit(tmp_path: Path) -> None:
    generated = tmp_path / "claims.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/audit_week8_claims.py",
            "--config",
            "configs/week8_claims.yaml",
            "--output",
            str(generated),
            "--check-links",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    committed = Path("reports/release/week8_claim_evidence.json")
    assert committed.read_bytes() == generated.read_bytes()


def test_build_release_candidate_writes_manifest_and_claims(
    tmp_path: Path,
) -> None:
    manifest_output = tmp_path / "manifest.json"
    claims_output = tmp_path / "claims.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/build_release_candidate.py",
            "--candidate-id",
            "week8-rc1",
            "--source-commit",
            "7ed4fbb",
            "--checkpoint",
            "outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt",
            "--output",
            str(manifest_output),
            "--claims-output",
            str(claims_output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    manifest = json.loads(manifest_output.read_text(encoding="utf-8"))
    ledger = json.loads(claims_output.read_text(encoding="utf-8"))
    assert manifest["candidate_id"] == "week8-rc1"
    assert manifest["source_commit"] == "7ed4fbb"
    assert manifest["release_commit"] is None
    assert manifest["environment"]["python"]
    assert manifest["environment"]["pytorch"]
    assert manifest["environment"]["uv_lock_sha256"]
    assert manifest["lanes"]["claims"] == "passed"
    assert all(not Path(item["logical_path"]).is_absolute() for item in manifest["artifacts"])
    artifact_paths = {item["logical_path"] for item in manifest["artifacts"]}
    assert {
        "ASSET_LICENSES.md",
        "docs/release/publication_decisions.md",
        "docs/presentation/plantdisease_ai_week8_research_defense.key",
        "docs/presentation/plantdisease_ai_week8_research_defense.pptx",
        "docs/presentation/plantdisease_ai_complete_bilingual_outline.md",
        "docs/presentation/plantdisease_ai_week8_research_defense/slide-1.png",
        "docs/presentation/charts/english-transparent/01-project-evidence-snapshot.png",
        "docs/presentation/week8_research_defense_animation_map.md",
        "paper/out/plantdisease_ai_zh.pdf",
        "paper/out/plantdisease_ai_en.pdf",
        "reports/release/week8_paper_audit.json",
        "reports/week8_presentation_qa.md",
    } <= artifact_paths
    checkpoint = next(
        item for item in manifest["artifacts"] if item["logical_path"].endswith("checkpoint.pt")
    )
    assert checkpoint["status"] == "passed"
    assert checkpoint["sha256"]
    assert checkpoint["size_bytes"] > 0
    assert ledger["schema_version"] == 1
    assert ledger["status"] == "passed"
    assert ledger["counts"]["claims"] == 11
    assert ledger["counts"]["boundaries"] == 4
    assert ledger["counts"]["broken_links"] == 0


def test_build_release_candidate_preserves_verified_runtime_lanes(
    tmp_path: Path,
) -> None:
    manifest_output = tmp_path / "manifest.json"
    claims_output = tmp_path / "claims.json"
    command = [
        sys.executable,
        "scripts/build_release_candidate.py",
        "--candidate-id",
        "week8-rc1",
        "--source-commit",
        "7ed4fbb",
        "--checkpoint",
        "outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt",
        "--output",
        str(manifest_output),
        "--claims-output",
        str(claims_output),
    ]
    initial = subprocess.run(command, capture_output=True, text=True, check=False)
    assert initial.returncode == 0, initial.stderr
    existing = json.loads(manifest_output.read_text(encoding="utf-8"))
    existing["lanes"].update(
        {
            "clean_reproduction": "passed",
            "package": "passed",
            "local_evidence": "passed",
            "container": "passed",
        }
    )
    existing["lane_evidence"] = {
        "local_evidence": {"status": "passed", "sample_count": 24},
        "container": {"status": "passed", "health_response": "ok"},
    }
    manifest_output.write_text(json.dumps(existing), encoding="utf-8")

    result = subprocess.run(command, capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr
    manifest = json.loads(manifest_output.read_text(encoding="utf-8"))
    assert manifest["lanes"]["clean_reproduction"] == "passed"
    assert manifest["lanes"]["package"] == "passed"
    assert manifest["lanes"]["local_evidence"] == "passed"
    assert manifest["lanes"]["container"] == "passed"
    assert manifest["lane_evidence"]["local_evidence"]["sample_count"] == 24
    assert manifest["lane_evidence"]["container"]["health_response"] == "ok"


def test_build_release_candidate_rejects_runtime_lanes_from_other_source(
    tmp_path: Path,
) -> None:
    manifest_output = tmp_path / "manifest.json"
    claims_output = tmp_path / "claims.json"
    base_command = [
        sys.executable,
        "scripts/build_release_candidate.py",
        "--candidate-id",
        "week8-rc1",
        "--source-commit",
        "7ed4fbb",
        "--checkpoint",
        "outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt",
        "--output",
        str(manifest_output),
        "--claims-output",
        str(claims_output),
    ]
    initial = subprocess.run(base_command, capture_output=True, text=True, check=False)
    assert initial.returncode == 0, initial.stderr
    existing = json.loads(manifest_output.read_text(encoding="utf-8"))
    existing["lanes"]["local_evidence"] = "passed"
    existing["lane_evidence"] = {"local_evidence": {"sample_count": 24}}
    manifest_output.write_text(json.dumps(existing), encoding="utf-8")

    changed_source = [
        "different-source" if value == "7ed4fbb" else value for value in base_command
    ]
    result = subprocess.run(
        changed_source,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    manifest = json.loads(manifest_output.read_text(encoding="utf-8"))
    assert manifest["lanes"].get("local_evidence") != "passed"
    assert "local_evidence" not in manifest["lane_evidence"]


def test_checked_in_release_manifest_matches_manifest_revision_artifacts() -> None:
    manifest_path = Path("reports/release/week8_rc1_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_commit = manifest["source_commit"]
    subprocess.run(
        ["git", "cat-file", "-e", f"{source_commit}^{{commit}}"],
        check=True,
    )
    manifest_revision = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", str(manifest_path)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    tracked = set(
        subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", manifest_revision],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
    )

    artifacts = {item["logical_path"]: item for item in manifest["artifacts"]}
    assert {
        "docs/presentation/plantdisease_ai_complete_bilingual_outline.md",
        "docs/presentation/plantdisease_ai_week8_research_defense/slide-20.png",
        "docs/presentation/charts/english-transparent/24-full-confusion-matrix.svg",
        "reports/release/week8_claim_evidence.json",
    } <= artifacts.keys()
    for logical_path, artifact in artifacts.items():
        if logical_path not in tracked:
            continue
        source_bytes = subprocess.run(
            ["git", "show", f"{manifest_revision}:{logical_path}"],
            capture_output=True,
            check=True,
        ).stdout
        assert artifact["status"] == "passed", logical_path
        assert artifact["size_bytes"] == len(source_bytes), logical_path
        assert artifact["sha256"] == hashlib.sha256(source_bytes).hexdigest(), logical_path


def test_run_week8_repro_runs_locked_commands_and_redacts_environment(
    tmp_path: Path,
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_uv = fake_bin / "uv"
    fake_uv.write_text(
        """#!/usr/bin/env python3
import os
print(os.environ["UV_PROJECT_ENVIRONMENT"])
""",
        encoding="utf-8",
    )
    fake_uv.chmod(0o755)
    output = tmp_path / "repro.json"
    environment = tmp_path / "clean-environment"
    process_env = os.environ.copy()
    process_env["PATH"] = f"{fake_bin}{os.pathsep}{process_env['PATH']}"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_week8_repro.py",
            "--environment",
            str(environment),
            "--output",
            str(output),
            "--smoke-output",
            "outputs/plantvillage/week8_release/week8-rc1/clean_smoke/run_manifest.json",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=process_env,
    )

    assert result.returncode == 0, result.stderr
    serialized = output.read_text(encoding="utf-8")
    payload = json.loads(serialized)
    assert payload["status"] == "passed"
    assert [item["name"] for item in payload["commands"]] == [
        "sync",
        "pytest",
        "ruff",
        "typecheck",
        "claims",
        "smoke",
        "package",
        "cli_help",
    ]
    assert str(environment) not in serialized
    assert str(Path.home()) not in serialized


def test_claim_audit_checks_boundary_only_markdown_links(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    build_audit_payload = importlib.import_module(
        "audit_week8_claims"
    ).build_audit_payload
    (tmp_path / "source.md").write_text("source", encoding="utf-8")
    (tmp_path / "consumer.md").write_text("[missing](not-there.md)", encoding="utf-8")
    config = tmp_path / "claims.yaml"
    config.write_text(
        """schema_version: 1
claims: []
boundaries:
  - id: boundary_only
    source: source.md
    consumers:
      - consumer.md
""",
        encoding="utf-8",
    )

    payload = build_audit_payload(tmp_path, config, check_links=True)

    assert payload["broken_links"] == ["consumer.md -> not-there.md"]
    assert payload["status"] == "failed"


def test_claim_audit_records_missing_markdown_consumer_without_raising(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    build_audit_payload = importlib.import_module(
        "audit_week8_claims"
    ).build_audit_payload
    (tmp_path / "source.md").write_text("value boundary", encoding="utf-8")
    config = tmp_path / "claims.yaml"
    config.write_text(
        """schema_version: 1
claims:
  - id: missing_consumer
    value: value
    source: source.md
    consumers:
      - missing.md
    required_boundary: boundary
boundaries: []
""",
        encoding="utf-8",
    )

    payload = build_audit_payload(tmp_path, config, check_links=True)

    assert payload["status"] == "failed"
    assert payload["claim_results"][0]["missing_value_consumers"] == ("missing.md",)


def test_run_week8_repro_fails_when_last_command_fails(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_uv = fake_bin / "uv"
    fake_uv.write_text(
        """#!/usr/bin/env python3
import sys
raise SystemExit(8 if sys.argv[1:] == ["run", "plant-smoke", "--help"] else 0)
""",
        encoding="utf-8",
    )
    fake_uv.chmod(0o755)
    output = tmp_path / "repro.json"
    process_env = os.environ.copy()
    process_env["PATH"] = f"{fake_bin}{os.pathsep}{process_env['PATH']}"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_week8_repro.py",
            "--environment",
            str(tmp_path / "environment"),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
        env=process_env,
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert result.returncode == 1
    assert payload["status"] == "failed"
    assert payload["commands"][-1]["name"] == "cli_help"
    assert payload["commands"][-1]["exit_code"] == 8


def test_run_week8_repro_marks_commands_not_run_after_first_failure(
    tmp_path: Path,
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_uv = fake_bin / "uv"
    fake_uv.write_text("#!/usr/bin/env python3\nraise SystemExit(5)\n", encoding="utf-8")
    fake_uv.chmod(0o755)
    output = tmp_path / "repro.json"
    process_env = os.environ.copy()
    process_env["PATH"] = f"{fake_bin}{os.pathsep}{process_env['PATH']}"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_week8_repro.py",
            "--environment",
            str(tmp_path / "environment"),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
        env=process_env,
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert result.returncode == 1
    assert len(payload["commands"]) == 8
    assert payload["commands"][0]["status"] == "failed"
    assert all(item["status"] == "not_run" for item in payload["commands"][1:])
    assert all(item["exit_code"] is None for item in payload["commands"][1:])


def test_run_week8_repro_marks_commands_not_run_after_middle_failure(
    tmp_path: Path,
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_uv = fake_bin / "uv"
    fake_uv.write_text(
        """#!/usr/bin/env python3
import sys
raise SystemExit(6 if sys.argv[1:] == ["run", "ruff", "check", "."] else 0)
""",
        encoding="utf-8",
    )
    fake_uv.chmod(0o755)
    output = tmp_path / "repro.json"
    process_env = os.environ.copy()
    process_env["PATH"] = f"{fake_bin}{os.pathsep}{process_env['PATH']}"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_week8_repro.py",
            "--environment",
            str(tmp_path / "environment"),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
        env=process_env,
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert result.returncode == 1
    assert len(payload["commands"]) == 8
    assert [item["status"] for item in payload["commands"]] == [
        "passed",
        "passed",
        "failed",
        "not_run",
        "not_run",
        "not_run",
        "not_run",
        "not_run",
    ]
    assert payload["commands"][2]["exit_code"] == 6


def test_run_week8_repro_rejects_repo_environment_before_commands(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "uv-ran"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_uv = fake_bin / "uv"
    fake_uv.write_text(
        f"#!/usr/bin/env python3\nfrom pathlib import Path\nPath({str(marker)!r}).touch()\n",
        encoding="utf-8",
    )
    fake_uv.chmod(0o755)
    output = tmp_path / "repro.json"
    repo_root = Path(__file__).resolve().parents[1]
    process_env = os.environ.copy()
    process_env["PATH"] = f"{fake_bin}{os.pathsep}{process_env['PATH']}"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_week8_repro.py",
            "--environment",
            str(repo_root / ".venv"),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
        env=process_env,
    )

    assert result.returncode == 2
    assert "runtime temporary" in result.stderr.casefold()
    assert "traceback" not in result.stderr.casefold()
    assert not marker.exists()
    assert not output.exists()

"""Run the locked Week8 clean-environment reproduction command lane."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

from plantdisease.release.manifest import logical_repo_path
from plantdisease.release.runner import CommandResult, CommandSpec, run_command

COMMANDS = (
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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the Week8 clean-reproduction command line."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/plantvillage/week8_release/week8-rc1/repro.json"),
    )
    parser.add_argument(
        "--smoke-output",
        type=Path,
        default=Path(
            "outputs/plantvillage/week8_release/week8-rc1/clean_smoke/run_manifest.json"
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run locked commands, stopping and returning nonzero at the first failure."""

    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    try:
        environment_path = validate_runtime_environment(args.environment, repo_root)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    results: list[CommandResult] = []
    environment = {"UV_PROJECT_ENVIRONMENT": str(environment_path)}
    for index, command in enumerate(COMMANDS):
        result = run_command(command, repo_root=repo_root, env=environment)
        results.append(result)
        if result.status != "passed":
            results.extend(
                CommandResult(spec.name, "not_run", None, "", "")
                for spec in COMMANDS[index + 1 :]
            )
            break

    payload: dict[str, Any] = {
        "schema_version": 1,
        "status": (
            "passed"
            if len(results) == len(COMMANDS)
            and all(result.status == "passed" for result in results)
            else "failed"
        ),
        "commands": [_portable_result(result, environment_path) for result in results],
        "smoke_output": _logical_input_path(args.smoke_output, repo_root),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": payload["status"], "output": str(args.output)}, sort_keys=True))
    return 0 if payload["status"] == "passed" else 1


def validate_runtime_environment(path: Path, repo_root: Path) -> Path:
    """Resolve a clean environment path and require a temporary repo-external child."""

    resolved = path.expanduser().resolve()
    resolved_repo = repo_root.resolve()
    temporary_root = Path(tempfile.gettempdir()).resolve()
    if resolved == resolved_repo or resolved.is_relative_to(resolved_repo):
        raise ValueError("environment must be a runtime temporary path outside the repository")
    if resolved == temporary_root or not resolved.is_relative_to(temporary_root):
        raise ValueError("environment must be a runtime temporary path")
    return resolved


def _logical_input_path(path: Path, repo_root: Path) -> str:
    resolved = path.resolve() if path.is_absolute() else (repo_root / path).resolve()
    return logical_repo_path(resolved, repo_root)


def _portable_result(result: CommandResult, environment_path: Path) -> dict[str, Any]:
    payload: dict[str, Any] = asdict(result)
    for stream in ("stdout", "stderr"):
        payload[stream] = str(payload[stream]).replace(
            str(environment_path), "<ENVIRONMENT>"
        )
    return payload


if __name__ == "__main__":
    raise SystemExit(main())

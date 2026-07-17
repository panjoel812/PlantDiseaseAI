from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from plantdisease.release.runner import CommandSpec, run_command


def test_run_command_records_pass_and_redacts_repo_root(tmp_path: Path) -> None:
    result = run_command(
        CommandSpec("probe", (sys.executable, "-c", "import os; print(os.getcwd())"), 10),
        repo_root=tmp_path,
        env={},
    )

    assert result.status == "passed"
    assert result.exit_code == 0
    assert str(tmp_path) not in result.stdout
    assert "<REPO_ROOT>" in result.stdout


def test_run_command_records_nonzero_without_raising(tmp_path: Path) -> None:
    result = run_command(
        CommandSpec("failure", (sys.executable, "-c", "raise SystemExit(7)"), 10),
        repo_root=tmp_path,
        env={},
    )

    assert result.status == "failed"
    assert result.exit_code == 7


def test_run_command_redacts_home_and_temporary_root(tmp_path: Path) -> None:
    probe = f"print({str(Path.home())!r}); print({tempfile.gettempdir()!r})"

    result = run_command(
        CommandSpec("paths", (sys.executable, "-c", probe), 10),
        repo_root=tmp_path,
        env={},
    )

    assert str(Path.home()) not in result.stdout
    assert tempfile.gettempdir() not in result.stdout
    assert "<HOME>" in result.stdout
    assert "<TMP_ROOT>" in result.stdout


def test_run_command_records_timeout_without_raising(tmp_path: Path) -> None:
    result = run_command(
        CommandSpec(
            "timeout",
            (sys.executable, "-c", "import time; time.sleep(1)"),
            0,
        ),
        repo_root=tmp_path,
        env={},
    )

    assert result.status == "failed"
    assert result.exit_code is None
    assert result.stderr == "command timed out"


def test_run_command_records_start_failure_and_redacts_path(tmp_path: Path) -> None:
    missing_executable = tmp_path / "missing-command"

    result = run_command(
        CommandSpec("missing", (str(missing_executable),), 10),
        repo_root=tmp_path,
        env={},
    )

    assert result.status == "failed"
    assert result.exit_code is None
    assert result.stdout == ""
    assert str(tmp_path) not in result.stderr
    assert "<REPO_ROOT>" in result.stderr

from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommandSpec:
    """Describe one bounded release verification command."""

    name: str
    argv: tuple[str, ...]
    timeout_seconds: int


@dataclass(frozen=True)
class CommandResult:
    """Record the portable outcome of one release verification command."""

    name: str
    status: str
    exit_code: int | None
    stdout: str
    stderr: str


def run_command(
    spec: CommandSpec, *, repo_root: Path, env: dict[str, str]
) -> CommandResult:
    """Run a command from the repository and return a redacted result."""

    merged_env = os.environ.copy()
    merged_env.update(env)
    try:
        completed = subprocess.run(
            spec.argv,
            cwd=repo_root,
            env=merged_env,
            capture_output=True,
            text=True,
            timeout=spec.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            spec.name,
            "failed",
            None,
            _redact(_as_text(exc.stdout), repo_root),
            "command timed out",
        )
    except OSError as exc:
        return CommandResult(
            spec.name,
            "failed",
            None,
            "",
            _redact(f"command could not start: {exc}", repo_root),
        )
    return CommandResult(
        spec.name,
        "passed" if completed.returncode == 0 else "failed",
        completed.returncode,
        _redact(completed.stdout, repo_root),
        _redact(completed.stderr, repo_root),
    )


def _as_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def _redact(value: str, repo_root: Path) -> str:
    replacements = (
        (str(repo_root.resolve()), "<REPO_ROOT>"),
        (str(repo_root), "<REPO_ROOT>"),
        (str(Path.home().resolve()), "<HOME>"),
        (str(Path.home()), "<HOME>"),
        (str(Path(tempfile.gettempdir()).resolve()), "<TMP_ROOT>"),
        (tempfile.gettempdir(), "<TMP_ROOT>"),
    )
    for source, replacement in replacements:
        value = value.replace(source, replacement)
    return value

from __future__ import annotations

import html
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from zipfile import BadZipFile, ZipFile

import yaml

ClaimAuditStatus = Literal["passed", "failed"]

_PPTX_TEXT_RE = re.compile(r"<a:t(?:\s[^>]*)?>(.*?)</a:t>", re.DOTALL)
_MARKDOWN_LINK_START_RE = re.compile(r"!?\[[^\]]*\]\(")
_TEX_INPUT_RE = re.compile(r"\\(?:input|include)\s*\{([^}]+)\}")
_SKIPPED_LINK_PREFIXES = ("http://", "https://", "mailto:", "data:")
_BOUNDARY_EQUIVALENTS = {"field": ("田间",), "fixed": ("固定",)}


@dataclass(frozen=True)
class ClaimRecord:
    id: str
    value: str
    source: str
    consumers: tuple[str, ...]
    required_boundary: str


@dataclass(frozen=True)
class ClaimAuditResult:
    claim_id: str
    value: str
    source: str
    consumers: tuple[str, ...]
    required_boundary: str
    status: ClaimAuditStatus
    missing_sources: tuple[str, ...]
    missing_value_consumers: tuple[str, ...]
    missing_boundary_consumers: tuple[str, ...]


def load_claims(path: Path) -> list[ClaimRecord]:
    """Load locked claim records from a schema-version-1 YAML file."""

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("claim configuration must use schema_version 1")
    raw_claims = payload.get("claims")
    if not isinstance(raw_claims, list):
        raise ValueError("claim configuration must contain a claims list")

    claims: list[ClaimRecord] = []
    for raw_claim in raw_claims:
        if not isinstance(raw_claim, dict):
            raise ValueError("each claim must be a mapping")
        consumers = raw_claim.get("consumers")
        if not isinstance(consumers, list) or not all(
            isinstance(consumer, str) for consumer in consumers
        ):
            raise ValueError("claim consumers must be a list of paths")
        claims.append(
            ClaimRecord(
                id=str(raw_claim["id"]),
                value=str(raw_claim["value"]),
                source=str(raw_claim["source"]),
                consumers=tuple(consumers),
                required_boundary=str(raw_claim["required_boundary"]),
            )
        )
    return claims


def extract_pptx_text(path: Path) -> str:
    """Extract text from sorted PPTX slide and speaker-note XML parts."""

    with ZipFile(path) as archive:
        part_names = sorted(
            name
            for name in archive.namelist()
            if _is_slide_or_notes_xml(name)
        )
        values = [
            html.unescape(match)
            for name in part_names
            for match in _PPTX_TEXT_RE.findall(
                archive.read(name).decode("utf-8", errors="replace")
            )
        ]
    return "\n".join(values)


def audit_claims(
    repo_root: Path, claims: list[ClaimRecord]
) -> list[ClaimAuditResult]:
    """Audit claim sources, published values, and required boundary wording."""

    results: list[ClaimAuditResult] = []
    for claim in claims:
        source_path = repo_root / claim.source
        missing_sources = () if source_path.is_file() else (claim.source,)
        missing_values: list[str] = []
        missing_boundaries: list[str] = []

        for consumer in claim.consumers:
            text = _read_consumer_text(repo_root / consumer, repo_root)
            folded_text = text.casefold() if text is not None else ""
            if claim.value.casefold() not in folded_text:
                missing_values.append(consumer)
            if not _contains_boundary(folded_text, claim.required_boundary):
                missing_boundaries.append(consumer)

        status: ClaimAuditStatus = (
            "failed"
            if missing_sources or missing_values or missing_boundaries
            else "passed"
        )
        results.append(
            ClaimAuditResult(
                claim_id=claim.id,
                value=claim.value,
                source=claim.source,
                consumers=claim.consumers,
                required_boundary=claim.required_boundary,
                status=status,
                missing_sources=missing_sources,
                missing_value_consumers=tuple(missing_values),
                missing_boundary_consumers=tuple(missing_boundaries),
            )
        )
    return results


def find_broken_markdown_links(repo_root: Path, paths: list[Path]) -> list[str]:
    """Return missing or repository-escaping local Markdown link targets."""

    resolved_root = repo_root.resolve()
    broken: list[str] = []
    for path in paths:
        markdown_path = path if path.is_absolute() else repo_root / path
        consumer = markdown_path.resolve().relative_to(resolved_root).as_posix()
        text = markdown_path.read_text(encoding="utf-8")
        for target in _iter_markdown_targets(text):
            if _should_skip_link(target):
                continue
            path_text = re.split(r"[?#]", target, maxsplit=1)[0]
            if not path_text:
                continue
            resolved_target = (markdown_path.parent / path_text).resolve()
            try:
                resolved_target.relative_to(resolved_root)
            except ValueError:
                broken.append(f"{consumer} -> {target}")
                continue
            if not resolved_target.exists():
                broken.append(f"{consumer} -> {target}")
    return sorted(broken)


def _is_slide_or_notes_xml(name: str) -> bool:
    return bool(
        re.fullmatch(r"ppt/slides/slide[^/]*\.xml", name)
        or re.fullmatch(r"ppt/notesSlides/notesSlide[^/]*\.xml", name)
    )


def _read_consumer_text(path: Path, repo_root: Path) -> str | None:
    if not path.is_file():
        return None
    if path.suffix.casefold() == ".pptx":
        try:
            return extract_pptx_text(path)
        except (BadZipFile, OSError, ValueError):
            return None
    if path.suffix.casefold() == ".tex":
        return _read_tex_with_inputs(path, repo_root, seen=set())
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None


def _read_tex_with_inputs(
    path: Path, repo_root: Path, *, seen: set[Path]
) -> str | None:
    """Read a TeX consumer and repository-local input/include files."""

    resolved = path.resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return None
    if resolved in seen:
        return ""
    if not resolved.is_file():
        return None
    try:
        text = resolved.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None

    seen.add(resolved)
    included_text: list[str] = []
    for match in _TEX_INPUT_RE.finditer(text):
        input_path = resolved.parent / match.group(1)
        if not input_path.suffix:
            input_path = input_path.with_suffix(".tex")
        included = _read_tex_with_inputs(input_path, repo_root, seen=seen)
        if included is None:
            return None
        included_text.append(included)
    return "\n".join((text, *included_text))


def _contains_boundary(folded_text: str, boundary: str) -> bool:
    boundary_key = boundary.casefold()
    terms = (boundary_key, *_BOUNDARY_EQUIVALENTS.get(boundary_key, ()))
    return any(term.casefold() in folded_text for term in terms)


def _should_skip_link(target: str) -> bool:
    folded_target = target.casefold()
    return target.startswith("#") or folded_target.startswith(_SKIPPED_LINK_PREFIXES)


def _iter_markdown_targets(text: str) -> Iterator[str]:
    for match in _MARKDOWN_LINK_START_RE.finditer(text):
        start = match.end()
        while start < len(text) and text[start].isspace():
            start += 1
        if start == len(text):
            continue

        if text[start] == "<":
            end = _find_unescaped(text, ">", start + 1)
            if end is not None and _has_valid_link_suffix(text, end + 1):
                yield text[start + 1 : end]
            continue

        depth = 0
        position = start
        while position < len(text):
            character = text[position]
            if character == "\\":
                position += 2
                continue
            if character == "(":
                depth += 1
            elif character == ")":
                if depth == 0:
                    if position > start:
                        yield text[start:position]
                    break
                depth -= 1
            elif character.isspace() and depth == 0:
                if position > start and _has_valid_link_suffix(text, position):
                    yield text[start:position]
                break
            position += 1


def _has_valid_link_suffix(text: str, start: int) -> bool:
    if start < len(text) and text[start] == ")":
        return True

    position = start
    while position < len(text) and text[position].isspace():
        position += 1
    if position == start or position == len(text):
        return False
    if text[position] == ")":
        return True

    closing = {'"': '"', "'": "'", "(": ")"}.get(text[position])
    if closing is None:
        return False
    title_end = _find_unescaped(text, closing, position + 1)
    if title_end is None:
        return False
    position = title_end + 1
    while position < len(text) and text[position].isspace():
        position += 1
    return position < len(text) and text[position] == ")"


def _find_unescaped(text: str, character: str, start: int) -> int | None:
    position = start
    while position < len(text):
        if text[position] == "\\":
            position += 2
            continue
        if text[position] == character:
            return position
        position += 1
    return None

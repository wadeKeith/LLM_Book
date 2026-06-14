#!/usr/bin/env python3
"""Check English chapter abstracts for publication-facing quality."""

from __future__ import annotations

import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAPTER_DIR = ROOT / "book" / "chapters"
EXPECTED_CHAPTERS = 17
MIN_WORDS = 40
MAX_WORDS = 120

ABSTRACT_RE = re.compile(r"\\abstract\b")
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?")
TERMINAL_RE = re.compile(r"[.!?]\s*$")
FORBIDDEN_COMMAND_RE = re.compile(
    r"\\(?:"
    r"cite|citep|citet|citealp|citeauthor|citeyear|"
    r"ref|eqref|autoref|cref|Cref|nameref|pageref|"
    r"label|index"
    r")\b"
)
TODO_RE = re.compile(r"\b(?:TODO|FIXME|TBD|XXX)\b|\?\?\?|待补|lorem|dummy|citation needed|cite needed", re.IGNORECASE)


@dataclass(frozen=True)
class AbstractRecord:
    path: Path
    line: int
    raw: str
    plain: str
    words: int
    normalized: str


def strip_tex_comments(text: str) -> str:
    stripped: list[str] = []
    for line in text.splitlines():
        escaped = False
        kept: list[str] = []
        for char in line:
            if char == "%" and not escaped:
                break
            kept.append(char)
            escaped = char == "\\" and not escaped
            if char != "\\":
                escaped = False
        stripped.append("".join(kept))
    return "\n".join(stripped)


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def parse_braced_argument(text: str, offset: int) -> tuple[str, int] | None:
    cursor = offset
    while cursor < len(text) and text[cursor].isspace():
        cursor += 1
    if cursor >= len(text) or text[cursor] != "{":
        return None

    depth = 1
    cursor += 1
    start = cursor
    while cursor < len(text) and depth:
        char = text[cursor]
        if char == "\\":
            cursor += 2
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        cursor += 1

    if depth:
        return None
    return text[start : cursor - 1], cursor


def plain_text(raw: str) -> str:
    text = raw.replace("\\&", " and ").replace("\\%", " percent ")
    text = re.sub(
        r"\\(?:textbf|textit|emph|texttt|textsc)\*?(?:\[[^\]]*\])?\{([^{}]*)\}",
        r"\1",
        text,
    )
    text = re.sub(r"\\([A-Za-z]+)\*?(?:\[[^\]]*\])?", r" \1 ", text)
    text = re.sub(r"[{}_^$~]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalized_text(plain: str) -> str:
    text = plain.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def chapter_abstract(path: Path, errors: list[str]) -> AbstractRecord | None:
    text = strip_tex_comments(path.read_text(encoding="utf-8"))
    matches = list(ABSTRACT_RE.finditer(text))
    rel = path.relative_to(ROOT).as_posix()

    if len(matches) != 1:
        errors.append(f"{rel}: expected exactly one chapter abstract, found {len(matches)}")
        return None

    match = matches[0]
    parsed = parse_braced_argument(text, match.end())
    if parsed is None:
        errors.append(f"{rel}:{line_number(text, match.start())}: abstract has no balanced braced argument")
        return None

    raw, _ = parsed
    plain = plain_text(raw)
    return AbstractRecord(
        path=path,
        line=line_number(text, match.start()),
        raw=raw,
        plain=plain,
        words=len(WORD_RE.findall(plain)),
        normalized=normalized_text(plain),
    )


def check_record(record: AbstractRecord, errors: list[str]) -> None:
    rel = record.path.relative_to(ROOT).as_posix()
    prefix = f"{rel}:{record.line}"
    if record.words < MIN_WORDS:
        errors.append(f"{prefix}: abstract has {record.words} words, minimum is {MIN_WORDS}")
    if record.words > MAX_WORDS:
        errors.append(f"{prefix}: abstract has {record.words} words, maximum is {MAX_WORDS}")
    if not TERMINAL_RE.search(record.raw.strip()):
        errors.append(f"{prefix}: abstract does not end with terminal punctuation")
    if FORBIDDEN_COMMAND_RE.search(record.raw):
        errors.append(f"{prefix}: abstract contains citation, reference, label, or index commands")
    if TODO_RE.search(record.raw):
        errors.append(f"{prefix}: abstract contains unresolved editorial marker text")
    if not record.normalized:
        errors.append(f"{prefix}: abstract has no normalized prose text")


def main() -> int:
    errors: list[str] = []
    chapter_paths = sorted(CHAPTER_DIR.glob("ch*.tex"))
    if len(chapter_paths) != EXPECTED_CHAPTERS:
        errors.append(f"English chapter files checked: {len(chapter_paths)}, expected {EXPECTED_CHAPTERS}")

    records = [record for path in chapter_paths if (record := chapter_abstract(path, errors)) is not None]
    for record in records:
        check_record(record, errors)

    counts = Counter(record.normalized for record in records if record.normalized)
    duplicate_keys = {text for text, count in counts.items() if count > 1}
    for record in records:
        if record.normalized in duplicate_keys:
            rel = record.path.relative_to(ROOT).as_posix()
            errors.append(f"{rel}:{record.line}: duplicate abstract after normalization")

    words = [record.words for record in records]
    min_words = min(words) if words else 0
    max_words = max(words) if words else 0
    duplicate_count = sum(count - 1 for count in counts.values() if count > 1)

    print(f"English chapter abstracts checked: {len(records)}")
    print(f"minimum abstract words: {min_words} / {MIN_WORDS}")
    print(f"maximum abstract words: {max_words} / {MAX_WORDS}")
    print(f"duplicate abstracts: {duplicate_count}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("abstract quality checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

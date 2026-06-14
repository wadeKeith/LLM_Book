#!/usr/bin/env python3
"""Check English and Chinese headings for publication-facing quality."""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAPTER_DIR = ROOT / "book" / "chapters"
ZH_ROOT = ROOT / "book" / "book_zh.tex"
EXPECTED_CHAPTERS = 17
EXPECTED_CHINESE_HEADING_FILES = 1
MAX_WORDS = 12
MAX_CHINESE_UNITS = 22
MIN_WORDS = 1

HEADING_RE = re.compile(r"\\(chapter|section|subsection|subsubsection)\*?(?:\s*\[[^\]]*\])?\s*\{")
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?")
HAN_RE = re.compile(r"[\u4e00-\u9fff]")
TRAILING_PUNCTUATION_RE = re.compile(r"[.,:;]\s*$")
TODO_RE = re.compile(r"\b(?:TODO|FIXME|TBD|XXX)\b|\?\?\?|待补|lorem|dummy|citation needed|cite needed", re.IGNORECASE)
FORBIDDEN_COMMAND_RE = re.compile(
    r"\\(?:"
    r"cite|citep|citet|citealp|citeauthor|citeyear|"
    r"ref|eqref|autoref|cref|Cref|nameref|pageref|"
    r"label|index|url|href"
    r")\b"
)


@dataclass(frozen=True)
class Heading:
    path: Path
    line: int
    level: str
    raw: str
    plain: str
    words: int
    chinese_units: int
    normalized: str
    scope: str


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
    depth = 1
    chunks: list[str] = []
    while cursor < len(text) and depth:
        char = text[cursor]
        if char == "\\" and cursor + 1 < len(text):
            chunks.append(text[cursor : cursor + 2])
            cursor += 2
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return "".join(chunks), cursor + 1
        chunks.append(char)
        cursor += 1
    return None


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
    text = plain.casefold()
    text = re.sub(r"[^\w\u4e00-\u9fff]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def chinese_text_units(plain: str) -> int:
    without_han = HAN_RE.sub(" ", plain)
    return len(HAN_RE.findall(plain)) + len(WORD_RE.findall(without_han))


def iter_headings(path: Path, errors: list[str], scope_by_chapter: bool = False) -> list[Heading]:
    text = strip_tex_comments(path.read_text(encoding="utf-8"))
    rel = path.relative_to(ROOT).as_posix()
    headings: list[Heading] = []
    current_scope = rel
    for match in HEADING_RE.finditer(text):
        parsed = parse_braced_argument(text, match.end())
        if parsed is None:
            errors.append(f"{rel}:{line_number(text, match.start())}: heading has no balanced braced argument")
            continue
        raw, _ = parsed
        plain = plain_text(raw)
        if scope_by_chapter and match.group(1) == "chapter":
            current_scope = f"{rel}:{line_number(text, match.start())}:{normalized_text(plain)}"
        headings.append(
            Heading(
                path=path,
                line=line_number(text, match.start()),
                level=match.group(1),
                raw=raw,
                plain=plain,
                words=len(WORD_RE.findall(plain)),
                chinese_units=chinese_text_units(plain),
                normalized=normalized_text(plain),
                scope=current_scope,
            )
        )
    return headings


def check_heading(heading: Heading, errors: list[str], chinese: bool = False) -> None:
    rel = heading.path.relative_to(ROOT).as_posix()
    prefix = f"{rel}:{heading.line}"
    if chinese:
        if heading.chinese_units < MIN_WORDS:
            errors.append(f"{prefix}: heading has {heading.chinese_units} text units, minimum is {MIN_WORDS}")
        if heading.chinese_units > MAX_CHINESE_UNITS:
            errors.append(
                f"{prefix}: heading has {heading.chinese_units} text units, "
                f"maximum is {MAX_CHINESE_UNITS}"
            )
    else:
        if heading.words < MIN_WORDS:
            errors.append(f"{prefix}: heading has {heading.words} words, minimum is {MIN_WORDS}")
        if heading.words > MAX_WORDS:
            errors.append(f"{prefix}: heading has {heading.words} words, maximum is {MAX_WORDS}")
    if TRAILING_PUNCTUATION_RE.search(heading.raw.strip()):
        errors.append(f"{prefix}: heading ends with punctuation that should be folded into wording")
    if FORBIDDEN_COMMAND_RE.search(heading.raw):
        errors.append(f"{prefix}: heading contains citation, reference, label, index, or URL commands")
    if TODO_RE.search(heading.raw):
        errors.append(f"{prefix}: heading contains unresolved editorial marker text")
    if not heading.normalized:
        errors.append(f"{prefix}: heading has no normalized text")


def check_duplicates(headings: list[Heading], errors: list[str]) -> int:
    duplicates = 0
    by_scope: dict[str, dict[str, list[Heading]]] = defaultdict(lambda: defaultdict(list))
    for heading in headings:
        if heading.normalized:
            by_scope[heading.scope][f"{heading.level}:{heading.normalized}"].append(heading)

    for scope, groups in by_scope.items():
        rel = scope.split(":", 1)[0]
        for group in groups.values():
            if len(group) <= 1:
                continue
            duplicates += len(group) - 1
            lines = ", ".join(str(heading.line) for heading in group)
            errors.append(f"{rel}: duplicate heading after normalization on lines {lines}")
    return duplicates


def main() -> int:
    errors: list[str] = []
    chapter_paths = sorted(CHAPTER_DIR.glob("ch*.tex"))
    if len(chapter_paths) != EXPECTED_CHAPTERS:
        errors.append(f"English chapter heading files checked: {len(chapter_paths)}, expected {EXPECTED_CHAPTERS}")

    headings: list[Heading] = []
    for path in chapter_paths:
        headings.extend(iter_headings(path, errors))
    for heading in headings:
        check_heading(heading, errors)

    chinese_headings = iter_headings(ZH_ROOT, errors, scope_by_chapter=True)
    for heading in chinese_headings:
        check_heading(heading, errors, chinese=True)

    duplicate_count = check_duplicates(headings, errors)
    chinese_duplicate_count = check_duplicates(chinese_headings, errors)
    words = [heading.words for heading in headings]
    max_words = max(words) if words else 0
    chinese_units = [heading.chinese_units for heading in chinese_headings]
    max_chinese_units = max(chinese_units) if chinese_units else 0

    print(f"English chapter heading files checked: {len(chapter_paths)}")
    print(f"English headings checked: {len(headings)}")
    print(f"maximum heading words: {max_words} / {MAX_WORDS}")
    print(f"duplicate headings within chapters: {duplicate_count}")
    print(f"Chinese heading files checked: {EXPECTED_CHINESE_HEADING_FILES if ZH_ROOT.exists() else 0}")
    print(f"Chinese headings checked: {len(chinese_headings)}")
    print(f"maximum Chinese heading text units: {max_chinese_units} / {MAX_CHINESE_UNITS}")
    print(f"duplicate Chinese headings within chapters: {chinese_duplicate_count}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("heading quality checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

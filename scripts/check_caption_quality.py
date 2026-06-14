#!/usr/bin/env python3
"""Check figure and table captions for publication-facing quality."""

from __future__ import annotations

import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
CHAPTER_DIR = BOOK_DIR / "chapters"
TEX_FILES = [
    BOOK_DIR / "book.tex",
    BOOK_DIR / "book_zh.tex",
    BOOK_DIR / "preface.tex",
    BOOK_DIR / "ethics.tex",
    BOOK_DIR / "appendix.tex",
    *sorted(CHAPTER_DIR.glob("ch*.tex")),
]

EXPECTED_CAPTIONS = 85
MIN_TEXT_UNITS = 5
MAX_TEXT_UNITS = 70

CAPTION_RE = re.compile(r"\\caption(?:\[[^\]]*\])?\s*\{")
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?")
HAN_RE = re.compile(r"[\u4e00-\u9fff]")
TERMINAL_RE = re.compile(r"[。？！.!?](?:\s*[])}]*)\s*$")
TODO_RE = re.compile(r"\b(?:TODO|FIXME|TBD|XXX)\b|\?\?\?|待补|lorem|dummy|citation needed|cite needed", re.IGNORECASE)
FORBIDDEN_COMMAND_RE = re.compile(r"\\(?:label|index)\b")


@dataclass(frozen=True)
class Caption:
    path: Path
    line: int
    raw: str
    plain: str
    text_units: int
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


def remove_balanced_command(text: str, command: str) -> str:
    pattern = re.compile(rf"\\{command}\b")
    position = 0
    chunks: list[str] = []
    for match in pattern.finditer(text):
        chunks.append(text[position : match.start()])
        cursor = match.end()
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        while cursor < len(text) and text[cursor] == "[":
            depth = 1
            cursor += 1
            while cursor < len(text) and depth:
                if text[cursor] == "[":
                    depth += 1
                elif text[cursor] == "]":
                    depth -= 1
                cursor += 1
            while cursor < len(text) and text[cursor].isspace():
                cursor += 1
        if cursor < len(text) and text[cursor] == "{":
            parsed = parse_braced_argument(text, cursor + 1)
            if parsed is not None:
                _, cursor = parsed
        position = cursor
    chunks.append(text[position:])
    return "".join(chunks)


def plain_text(raw: str) -> str:
    text = raw.replace("\\&", " and ").replace("\\%", " percent ")
    for command in ("cite", "citep", "citet", "citealp", "citeauthor", "citeyear", "ref", "autoref", "url"):
        text = remove_balanced_command(text, command)
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
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def iter_captions(path: Path, errors: list[str]) -> list[Caption]:
    text = strip_tex_comments(path.read_text(encoding="utf-8"))
    rel = path.relative_to(ROOT).as_posix()
    captions: list[Caption] = []
    for match in CAPTION_RE.finditer(text):
        parsed = parse_braced_argument(text, match.end())
        if parsed is None:
            errors.append(f"{rel}:{line_number(text, match.start())}: caption has no balanced braced argument")
            continue
        raw, _ = parsed
        plain = plain_text(raw)
        text_units = len(WORD_RE.findall(plain)) + len(HAN_RE.findall(plain))
        captions.append(
            Caption(
                path=path,
                line=line_number(text, match.start()),
                raw=raw,
                plain=plain,
                text_units=text_units,
                normalized=normalized_text(plain),
            )
        )
    return captions


def check_caption(caption: Caption, errors: list[str]) -> None:
    rel = caption.path.relative_to(ROOT).as_posix()
    prefix = f"{rel}:{caption.line}"
    if caption.text_units < MIN_TEXT_UNITS:
        errors.append(f"{prefix}: caption has {caption.text_units} text units, minimum is {MIN_TEXT_UNITS}")
    if caption.text_units > MAX_TEXT_UNITS:
        errors.append(f"{prefix}: caption has {caption.text_units} text units, maximum is {MAX_TEXT_UNITS}")
    if not TERMINAL_RE.search(caption.raw.strip()):
        errors.append(f"{prefix}: caption does not end with terminal punctuation")
    if TODO_RE.search(caption.raw):
        errors.append(f"{prefix}: caption contains unresolved editorial marker text")
    if FORBIDDEN_COMMAND_RE.search(caption.raw):
        errors.append(f"{prefix}: caption contains label or index commands")
    if not caption.normalized:
        errors.append(f"{prefix}: caption has no normalized text")


def main() -> int:
    errors: list[str] = []
    captions: list[Caption] = []
    for path in TEX_FILES:
        captions.extend(iter_captions(path, errors))

    if len(captions) != EXPECTED_CAPTIONS:
        errors.append(f"captions checked: {len(captions)}, expected {EXPECTED_CAPTIONS}")
    for caption in captions:
        check_caption(caption, errors)

    counts = Counter(caption.normalized for caption in captions if caption.normalized)
    duplicate_keys = {text for text, count in counts.items() if count > 1}
    for caption in captions:
        if caption.normalized in duplicate_keys:
            rel = caption.path.relative_to(ROOT).as_posix()
            errors.append(f"{rel}:{caption.line}: duplicate caption after normalization")

    units = [caption.text_units for caption in captions]
    min_units = min(units) if units else 0
    max_units = max(units) if units else 0
    duplicate_count = sum(count - 1 for count in counts.values() if count > 1)

    print(f"captions checked: {len(captions)}")
    print(f"minimum caption text units: {min_units} / {MIN_TEXT_UNITS}")
    print(f"maximum caption text units: {max_units} / {MAX_TEXT_UNITS}")
    print(f"duplicate captions: {duplicate_count}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("caption quality checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

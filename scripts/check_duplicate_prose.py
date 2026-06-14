#!/usr/bin/env python3
"""Check for exact duplicate long prose passages in manuscript sources."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
CHAPTER_DIR = BOOK_DIR / "chapters"

PROSE_FILES = [
    BOOK_DIR / "book.tex",
    BOOK_DIR / "book_zh.tex",
    BOOK_DIR / "preface.tex",
    BOOK_DIR / "ethics.tex",
    BOOK_DIR / "appendix.tex",
    *sorted(CHAPTER_DIR.glob("ch*.tex")),
]

SKIP_ENVIRONMENTS = {
    "align",
    "align*",
    "array",
    "equation",
    "equation*",
    "tikzpicture",
    "tabular",
    "tabular*",
    "verbatim",
}

COMMANDS_WITH_NO_PROSE = (
    "autoref",
    "cite",
    "citealp",
    "citeauthor",
    "citep",
    "citet",
    "citeyear",
    "eqref",
    "index",
    "label",
    "nameref",
    "pageref",
    "ref",
    "url",
)

ENGLISH_PARAGRAPH_MIN_WORDS = 35
ENGLISH_SENTENCE_MIN_WORDS = 18
CHINESE_PARAGRAPH_MIN_HAN = 80
CHINESE_SENTENCE_MIN_HAN = 45

ENGLISH_WORD_RE = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)?")
HAN_RE = re.compile(r"[\u4e00-\u9fff]")
SENTENCE_RE = re.compile(r"[^.!?。？！]+[.!?。？！]?")


@dataclass(frozen=True)
class Segment:
    kind: str
    location: str
    preview: str


def strip_tex_comments(line: str) -> str:
    escaped = False
    kept: list[str] = []
    for char in line:
        if char == "%" and not escaped:
            break
        kept.append(char)
        escaped = char == "\\" and not escaped
        if char != "\\":
            escaped = False
    return "".join(kept)


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
            depth = 1
            cursor += 1
            while cursor < len(text) and depth:
                if text[cursor] == "{":
                    depth += 1
                elif text[cursor] == "}":
                    depth -= 1
                cursor += 1
        position = cursor

    chunks.append(text[position:])
    return "".join(chunks)


def line_to_plain_text(line: str) -> str:
    text = strip_tex_comments(line)
    text = re.sub(r"\$[^$]*\$", " MATH ", text)
    for command in COMMANDS_WITH_NO_PROSE:
        text = remove_balanced_command(text, command)
    text = re.sub(r"\\(?:textbf|textit|emph|texttt|item)\s*(?:\[[^\]]*\])?\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\(?:chapter|section|subsection|paragraph|caption)\*?\s*\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?", " ", text)
    text = text.replace("~", " ")
    text = text.replace("\\&", "and")
    text = text.replace("\\%", " percent")
    text = re.sub(r"[{}_^]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def flush_paragraph(
    path: Path,
    start_line: int | None,
    lines: list[str],
) -> tuple[str, str] | None:
    if start_line is None or not lines:
        return None
    text = re.sub(r"\s+", " ", " ".join(lines)).strip()
    if not text:
        return None
    location = f"{path.relative_to(ROOT).as_posix()}:{start_line}"
    return location, text


def iter_paragraphs(path: Path) -> list[tuple[str, str]]:
    active_envs: list[str] = []
    in_display_math = False
    paragraphs: list[tuple[str, str]] = []
    current_lines: list[str] = []
    start_line: int | None = None
    in_document_body = path.name not in {"book.tex", "book_zh.tex"}

    def flush() -> None:
        nonlocal current_lines, start_line
        paragraph = flush_paragraph(path, start_line, current_lines)
        if paragraph is not None:
            paragraphs.append(paragraph)
        current_lines = []
        start_line = None

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = strip_tex_comments(raw_line)
        if not in_document_body:
            if r"\begin{document}" in line:
                in_document_body = True
            continue

        if r"\[" in line:
            in_display_math = True

        for env in re.findall(r"\\begin\{([^{}]+)\}", line):
            active_envs.append(env)
        skip_line = in_display_math or any(env in SKIP_ENVIRONMENTS for env in active_envs)
        for env in re.findall(r"\\end\{([^{}]+)\}", line):
            if env in active_envs:
                active_envs.remove(env)
        if r"\]" in line:
            in_display_math = False

        plain = "" if skip_line else line_to_plain_text(raw_line)
        if not plain:
            flush()
            continue

        if start_line is None:
            start_line = line_number
        current_lines.append(plain)

    flush()
    return paragraphs


def normalize_english(text: str) -> tuple[str, int]:
    words = ENGLISH_WORD_RE.findall(text.lower())
    return " ".join(words), len(words)


def normalize_chinese(text: str) -> tuple[str, int]:
    chars = HAN_RE.findall(text)
    return "".join(chars), len(chars)


def preview(text: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    return compact[:117] + "..." if len(compact) > 120 else compact


def segment_keys(kind: str, text: str) -> list[tuple[str, str]]:
    keys: list[tuple[str, str]] = []
    english_key, english_words = normalize_english(text)
    chinese_key, chinese_chars = normalize_chinese(text)
    if kind == "paragraph":
        if english_words >= ENGLISH_PARAGRAPH_MIN_WORDS:
            keys.append(("English duplicate paragraph", english_key))
        if chinese_chars >= CHINESE_PARAGRAPH_MIN_HAN:
            keys.append(("Chinese duplicate paragraph", chinese_key))
    else:
        if english_words >= ENGLISH_SENTENCE_MIN_WORDS:
            keys.append(("English duplicate sentence", english_key))
        if chinese_chars >= CHINESE_SENTENCE_MIN_HAN:
            keys.append(("Chinese duplicate sentence", chinese_key))
    return keys


def check_segments(errors: list[str]) -> tuple[int, int]:
    seen: dict[tuple[str, str], Segment] = {}
    paragraph_count = 0
    sentence_count = 0

    for path in PROSE_FILES:
        for location, paragraph in iter_paragraphs(path):
            paragraph_count += 1
            for label, key in segment_keys("paragraph", paragraph):
                segment = Segment(label, location, preview(paragraph))
                existing = seen.get((label, key))
                if existing is None:
                    seen[(label, key)] = segment
                else:
                    errors.append(
                        f"{location}: {label}; first occurrence at {existing.location}; "
                        f"current preview {segment.preview!r}"
                    )

            for match in SENTENCE_RE.finditer(paragraph):
                sentence = match.group(0).strip()
                if not sentence:
                    continue
                sentence_count += 1
                for label, key in segment_keys("sentence", sentence):
                    segment = Segment(label, location, preview(sentence))
                    existing = seen.get((label, key))
                    if existing is None:
                        seen[(label, key)] = segment
                    else:
                        errors.append(
                            f"{location}: {label}; first occurrence at {existing.location}; "
                            f"current preview {segment.preview!r}"
                        )

    return paragraph_count, sentence_count


def main() -> int:
    errors: list[str] = []
    paragraph_count, sentence_count = check_segments(errors)

    print(f"prose files checked: {len(PROSE_FILES)}")
    print(f"paragraphs checked: {paragraph_count}")
    print(f"sentences checked: {sentence_count}")
    print(f"duplicate long prose findings: {len(errors)}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("duplicate prose checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

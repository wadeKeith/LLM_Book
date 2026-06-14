#!/usr/bin/env python3
"""Check ordinary prose paragraphs against readability length budgets."""

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
    "center",
    "description",
    "enumerate",
    "equation",
    "equation*",
    "figure",
    "figure*",
    "itemize",
    "longtable",
    "table",
    "table*",
    "tabular",
    "tabular*",
    "tikzpicture",
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

ENGLISH_MAX_WORDS = 240
CHINESE_MAX_HAN = 420

ENGLISH_WORD_RE = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)?")
HAN_RE = re.compile(r"[\u4e00-\u9fff]")


@dataclass(frozen=True)
class Paragraph:
    location: str
    text: str
    english_words: int
    chinese_han: int


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
    text = re.sub(r"\\verb(.)(.*?)\1", r"\2", text)
    text = re.sub(r"\$[^$]*\$", " MATH ", text)
    for command in COMMANDS_WITH_NO_PROSE:
        text = remove_balanced_command(text, command)
    text = re.sub(r"\\(?:part|chapter|section|subsection|subsubsection|paragraph|caption)\*?\s*\{([^{}]*)\}", " ", text)
    text = re.sub(
        r"\\(?:textbf|textit|emph|texttt|textsc)\s*(?:\[[^\]]*\])?\{([^{}]*)\}",
        r"\1",
        text,
    )
    text = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?", " ", text)
    text = text.replace("~", " ")
    text = text.replace("\\&", "and")
    text = text.replace("\\%", " percent")
    text = re.sub(r"[{}_^]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def flush_paragraph(path: Path, start_line: int | None, lines: list[str]) -> Paragraph | None:
    if start_line is None or not lines:
        return None
    text = re.sub(r"\s+", " ", " ".join(lines)).strip()
    if not text:
        return None
    english_words = len(ENGLISH_WORD_RE.findall(text.lower()))
    chinese_han = len(HAN_RE.findall(text))
    if english_words == 0 and chinese_han == 0:
        return None
    return Paragraph(
        location=f"{path.relative_to(ROOT).as_posix()}:{start_line}",
        text=text,
        english_words=english_words,
        chinese_han=chinese_han,
    )


def iter_paragraphs(path: Path) -> list[Paragraph]:
    active_envs: list[str] = []
    in_display_math = False
    paragraphs: list[Paragraph] = []
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
            flush()
            in_display_math = True

        for env in re.findall(r"\\begin\{([^{}]+)\}", line):
            flush()
            active_envs.append(env)

        skip_line = in_display_math or any(env in SKIP_ENVIRONMENTS for env in active_envs)

        for env in re.findall(r"\\end\{([^{}]+)\}", line):
            if env in active_envs:
                active_envs.remove(env)
            if env in SKIP_ENVIRONMENTS:
                skip_line = True

        if r"\]" in line:
            skip_line = True
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


def preview(text: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    return compact[:117] + "..." if len(compact) > 120 else compact


def main() -> int:
    paragraphs = [paragraph for path in PROSE_FILES for paragraph in iter_paragraphs(path)]
    errors: list[str] = []

    max_english = max(paragraphs, key=lambda paragraph: paragraph.english_words)
    max_chinese = max(paragraphs, key=lambda paragraph: paragraph.chinese_han)

    for paragraph in paragraphs:
        if paragraph.english_words > ENGLISH_MAX_WORDS:
            errors.append(
                f"{paragraph.location}: English ordinary paragraph has "
                f"{paragraph.english_words} words, limit {ENGLISH_MAX_WORDS}; "
                f"preview {preview(paragraph.text)!r}"
            )
        if paragraph.chinese_han > CHINESE_MAX_HAN:
            errors.append(
                f"{paragraph.location}: Chinese ordinary paragraph has "
                f"{paragraph.chinese_han} Han characters, limit {CHINESE_MAX_HAN}; "
                f"preview {preview(paragraph.text)!r}"
            )

    print(f"prose files checked: {len(PROSE_FILES)}")
    print(f"ordinary prose paragraphs checked: {len(paragraphs)}")
    print(f"max English ordinary paragraph: {max_english.english_words} words at {max_english.location}")
    print(f"max Chinese ordinary paragraph: {max_chinese.chinese_han} Han characters at {max_chinese.location}")
    print(f"overlength ordinary paragraphs: {len(errors)}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("paragraph length checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

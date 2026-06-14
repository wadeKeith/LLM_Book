#!/usr/bin/env python3
"""Check conservative copy-editing artifacts in manuscript prose."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
CHAPTER_DIR = BOOK_DIR / "chapters"

PROSE_FILES = [
    BOOK_DIR / "book.tex",
    BOOK_DIR / "preface.tex",
    BOOK_DIR / "ethics.tex",
    BOOK_DIR / "acronym.tex",
    BOOK_DIR / "glossary.tex",
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

COMMON_TYPOS = {
    "acommodate": "accommodate",
    "accomodate": "accommodate",
    "adress": "address",
    "alogrithm": "algorithm",
    "behaviour": "behavior",
    "behaviours": "behaviors",
    "calibraiton": "calibration",
    "definately": "definitely",
    "dependance": "dependence",
    "enviroment": "environment",
    "occured": "occurred",
    "occuring": "occurring",
    "paramter": "parameter",
    "recieve": "receive",
    "seperate": "separate",
    "teh": "the",
    "utilisation": "utilization",
    "utilise": "use",
    "utilised": "used",
    "utilises": "uses",
    "utilising": "using",
    "wierd": "weird",
}

CASE_SENSITIVE_TERMS = {
    "Github": "GitHub",
    "Javascript": "JavaScript",
    "Pytorch": "PyTorch",
}

COMMANDS_WITH_NO_PROSE = (
    "cite",
    "citealp",
    "citeauthor",
    "citep",
    "citet",
    "citeyear",
    "index",
    "label",
    "ref",
    "eqref",
    "autoref",
    "nameref",
    "url",
)

DUPLICATE_WORD_RE = re.compile(r"\b([A-Za-z][A-Za-z'-]{2,})\s+\1\b", re.IGNORECASE)
TYPO_RE = re.compile(r"\b[A-Za-z][A-Za-z'-]*\b")


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
    text = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?", " ", text)
    text = text.replace("~", " ")
    text = text.replace("\\&", "and")
    text = text.replace("\\%", " percent")
    text = re.sub(r"[{}_^]", " ", text)
    return text


def check_file(path: Path, errors: list[str]) -> tuple[int, int]:
    active_envs: list[str] = []
    checked_lines = 0
    checked_words = 0
    in_display_math = False

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = strip_tex_comments(raw_line)
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
        if skip_line:
            continue

        plain = line_to_plain_text(raw_line)
        if not plain.strip():
            continue

        prefix = f"{path.relative_to(ROOT).as_posix()}:{line_number}"
        checked_lines += 1

        if re.search(r"\ban\s+\\llm\b", line):
            errors.append(f"{prefix}: article mismatch before \\llm; macro expands to 'large language model'")

        for match in DUPLICATE_WORD_RE.finditer(plain):
            word = match.group(1)
            if word.lower() not in {"had", "that"}:
                errors.append(f"{prefix}: repeated word {word!r}")

        for match in TYPO_RE.finditer(plain):
            word = match.group(0)
            lower = word.lower()
            checked_words += 1
            if lower in COMMON_TYPOS:
                errors.append(f"{prefix}: possible typo {word!r}; prefer {COMMON_TYPOS[lower]!r}")
            if word in CASE_SENSITIVE_TERMS:
                errors.append(f"{prefix}: casing {word!r}; prefer {CASE_SENSITIVE_TERMS[word]!r}")

        if re.search(r"\s+[,.!?;:]", line):
            errors.append(f"{prefix}: whitespace before punctuation")
        if re.search(r"(?<!\.)\.\.(?!\.)|,,|;;|::", line):
            errors.append(f"{prefix}: repeated punctuation")

    return checked_lines, checked_words


def main() -> int:
    errors: list[str] = []
    total_lines = 0
    total_words = 0

    for path in PROSE_FILES:
        checked_lines, checked_words = check_file(path, errors)
        total_lines += checked_lines
        total_words += checked_words

    print(f"prose files checked: {len(PROSE_FILES)}")
    print(f"prose lines checked: {total_lines}")
    print(f"prose words checked: {total_words}")
    print(f"copy-editing artifacts: {len(errors)}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("prose quality checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

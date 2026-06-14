#!/usr/bin/env python3
"""Check conservative Chinese-source punctuation artifacts."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ZH_ROOT = ROOT / "book" / "book_zh.tex"

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

CJK_PUNCTUATION = "，。；：？！、"
HAN_RE = re.compile(r"[\u4e00-\u9fff]")
CITE_ASCII_PERIOD_RE = re.compile(r"\\cite[a-z]*\s*(?:\[[^\]]*\]\s*){0,2}\{[^{}]+\}\.")
TEXTTT_ASCII_PERIOD_RE = re.compile(r"\\texttt\{[^{}]+\}\.")


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


def body_lines() -> list[tuple[int, str]]:
    text = ZH_ROOT.read_text(encoding="utf-8").splitlines()
    begin_document = next((index for index, line in enumerate(text) if r"\begin{document}" in line), -1)
    start = begin_document + 1 if begin_document != -1 else 0
    return [(line_number, line) for line_number, line in enumerate(text[start:], start=start + 1)]


def check_lines(errors: list[str]) -> tuple[int, int]:
    active_envs: list[str] = []
    in_display_math = False
    checked_lines = 0
    han_chars = 0

    for line_number, raw_line in body_lines():
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
        if skip_line or not line.strip():
            continue

        line_han = len(HAN_RE.findall(line))
        if line_han == 0:
            continue
        checked_lines += 1
        han_chars += line_han
        prefix = f"{ZH_ROOT.relative_to(ROOT).as_posix()}:{line_number}"

        if CITE_ASCII_PERIOD_RE.search(line):
            errors.append(f"{prefix}: citation sentence uses ASCII period; prefer Chinese full stop")
        if TEXTTT_ASCII_PERIOD_RE.search(line):
            errors.append(f"{prefix}: inline code sentence uses ASCII period; prefer Chinese full stop")
        if re.search(rf"[{CJK_PUNCTUATION}]\s+[\u4e00-\u9fff]", line):
            errors.append(f"{prefix}: space after Chinese punctuation before Han text")
        if re.search(rf"\s+[{CJK_PUNCTUATION}]", line):
            errors.append(f"{prefix}: whitespace before Chinese punctuation")
        if re.search(rf"[{CJK_PUNCTUATION}]{{2,}}", line):
            errors.append(f"{prefix}: repeated Chinese punctuation")
        if re.search(r"[\u4e00-\u9fff）】][,;:?!]", line):
            errors.append(f"{prefix}: ASCII punctuation after Chinese text")
        if re.search(r"[\u4e00-\u9fff）】]\.(?:\s|$|[\u4e00-\u9fff])", line):
            errors.append(f"{prefix}: ASCII full stop after Chinese text")

    return checked_lines, han_chars


def main() -> int:
    errors: list[str] = []
    checked_lines, han_chars = check_lines(errors)

    print(f"Chinese prose lines checked: {checked_lines}")
    print(f"Chinese Han characters checked: {han_chars}")
    print(f"Chinese punctuation artifacts: {len(errors)}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("Chinese prose quality checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

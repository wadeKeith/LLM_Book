#!/usr/bin/env python3
"""Check source table styling and basic table substance."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
CHAPTER_DIR = BOOK_DIR / "chapters"
TEX_FILES = [
    BOOK_DIR / "appendix.tex",
    BOOK_DIR / "book_zh.tex",
    *sorted(CHAPTER_DIR.glob("*.tex")),
]

MIN_DATA_ROWS = 3
TABULAR_BEGIN = r"\begin{tabular}"
TABULAR_END = r"\end{tabular}"
TABLE_FLOAT_RE = re.compile(r"\\begin\{table\*?\}")


@dataclass(frozen=True)
class TabularBlock:
    path: Path
    line: int
    column_spec: str
    body: str


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


def parse_braced(text: str, open_brace: int) -> tuple[str, int] | None:
    depth = 0
    escaped = False
    start = open_brace + 1
    for index in range(open_brace, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "{":
            depth += 1
            if depth == 1:
                start = index + 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index], index + 1
            if depth < 0:
                return None
    return None


def tabular_blocks(path: Path) -> list[TabularBlock]:
    text = strip_tex_comments(path.read_text(encoding="utf-8"))
    blocks: list[TabularBlock] = []
    position = 0
    while True:
        start = text.find(TABULAR_BEGIN, position)
        if start == -1:
            break
        spec_start = text.find("{", start + len(TABULAR_BEGIN))
        if spec_start == -1:
            break
        parsed = parse_braced(text, spec_start)
        if parsed is None:
            position = start + len(TABULAR_BEGIN)
            continue
        column_spec, body_start = parsed
        end = text.find(TABULAR_END, body_start)
        if end == -1:
            position = body_start
            continue
        blocks.append(TabularBlock(path, line_number(text, start), column_spec, text[body_start:end]))
        position = end + len(TABULAR_END)
    return blocks


def data_rows(body: str) -> int:
    midrule = body.find(r"\midrule")
    bottomrule = body.find(r"\bottomrule")
    data = body[midrule + len(r"\midrule") : bottomrule] if midrule != -1 and bottomrule != -1 else body
    return sum(1 for line in data.splitlines() if "&" in line and r"\\" in line)


def check_tabular(block: TabularBlock, errors: list[str]) -> None:
    rel = block.path.relative_to(ROOT).as_posix()
    prefix = f"{rel}:{block.line}"
    body = block.body

    if "|" in block.column_spec:
        errors.append(f"{prefix}: tabular column spec uses vertical rules")
    for forbidden in (r"\hline", r"\svhline", r"\cline"):
        if forbidden in body:
            errors.append(f"{prefix}: tabular uses {forbidden} instead of booktabs rules")

    counts = {rule: body.count(rule) for rule in (r"\toprule", r"\midrule", r"\bottomrule")}
    for rule, count in counts.items():
        if count != 1:
            errors.append(f"{prefix}: expected exactly one {rule}, found {count}")

    top = body.find(r"\toprule")
    mid = body.find(r"\midrule")
    bottom = body.find(r"\bottomrule")
    if not (0 <= top < mid < bottom):
        errors.append(f"{prefix}: booktabs rules are not in top/mid/bottom order")

    row_count = data_rows(body)
    if row_count < MIN_DATA_ROWS:
        errors.append(f"{prefix}: tabular has {row_count} data rows, minimum is {MIN_DATA_ROWS}")


def main() -> int:
    errors: list[str] = []
    blocks: list[TabularBlock] = []
    table_floats = 0

    for path in TEX_FILES:
        text = strip_tex_comments(path.read_text(encoding="utf-8"))
        table_floats += len(TABLE_FLOAT_RE.findall(text))
        path_blocks = tabular_blocks(path)
        blocks.extend(path_blocks)
        for block in path_blocks:
            check_tabular(block, errors)

    print(f"tabular environments checked: {len(blocks)}")
    print(f"table floats checked: {table_floats}")
    print(f"minimum data rows required: {MIN_DATA_ROWS}")
    print(f"table style errors: {len(errors)}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("table quality checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

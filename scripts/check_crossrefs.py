#!/usr/bin/env python3
"""Check LaTeX label and cross-reference consistency."""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
CHAPTER_DIR = BOOK_DIR / "chapters"
TEX_FILES = [
    BOOK_DIR / "book.tex",
    BOOK_DIR / "book_zh.tex",
    BOOK_DIR / "preface.tex",
    BOOK_DIR / "ethics.tex",
    BOOK_DIR / "acronym.tex",
    BOOK_DIR / "glossary.tex",
    BOOK_DIR / "appendix.tex",
    *sorted(CHAPTER_DIR.glob("*.tex")),
]

LABEL_RE = re.compile(r"\\label\{([^{}]+)\}")
REF_RE = re.compile(
    r"\\(?:ref|eqref|pageref|autoref|nameref|cref|Cref|vref|Vref)"
    r"\s*(?:\[[^\]]*\]\s*)?\{([^{}]+)\}",
    re.DOTALL,
)
FLOAT_ENV_RE = re.compile(
    r"\\begin\{(figure|table)\*?\}(?:\[[^\]]*\])?(.*?)\\end\{\1\*?\}",
    re.DOTALL,
)
CAPTION_RE = re.compile(r"\\caption(?:\[[^\]]*\])?\{")
FLOAT_LABEL_RE = re.compile(r"\\label\{((?:fig|tab):[^{}]+)\}")


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


def main() -> int:
    labels: dict[str, list[str]] = defaultdict(list)
    refs: list[tuple[str, str, int]] = []
    float_labels_by_file: dict[str, list[tuple[str, int]]] = {}
    first_refs_by_file: dict[str, dict[str, int]] = {}
    float_environments: list[tuple[str, str, int, bool, list[str]]] = []

    for path in TEX_FILES:
        raw = path.read_text(encoding="utf-8")
        text = strip_tex_comments(raw)
        rel = path.relative_to(ROOT).as_posix()
        file_float_labels: list[tuple[str, int]] = []
        file_first_refs: dict[str, int] = {}

        for match in LABEL_RE.finditer(text):
            label = match.group(1)
            labels[label].append(f"{rel}:{line_number(text, match.start())}")
            if label.startswith(("fig:", "tab:")):
                file_float_labels.append((label, match.start()))
        for match in REF_RE.finditer(text):
            for target in match.group(1).split(","):
                target = target.strip()
                if target:
                    refs.append((target, rel, line_number(text, match.start())))
                    file_first_refs.setdefault(target, match.start())

        for match in FLOAT_ENV_RE.finditer(text):
            float_environments.append(
                (
                    rel,
                    match.group(1),
                    line_number(text, match.start()),
                    bool(CAPTION_RE.search(match.group(2))),
                    FLOAT_LABEL_RE.findall(match.group(2)),
                )
            )

        if file_float_labels:
            float_labels_by_file[rel] = file_float_labels
            first_refs_by_file[rel] = file_first_refs

    errors: list[str] = []
    duplicate_labels = sorted((label, locations) for label, locations in labels.items() if len(locations) > 1)
    for label, locations in duplicate_labels:
        errors.append(f"Duplicate label {label}: " + ", ".join(locations))

    label_keys = set(labels)
    missing_refs = sorted({(target, rel, line) for target, rel, line in refs if target not in label_keys})
    for target, rel, line in missing_refs:
        errors.append(f"Missing reference target {target}: {rel}:{line}")

    referenced_labels = {target for target, _, _ in refs}
    unreferenced_floats = sorted(
        (label, locations)
        for label, locations in labels.items()
        if label.startswith(("fig:", "tab:")) and label not in referenced_labels
    )
    for label, locations in unreferenced_floats:
        kind = "Figure" if label.startswith("fig:") else "Table"
        errors.append(f"Unreferenced {kind.lower()} label {label}: " + ", ".join(locations))

    out_of_order_float_files: list[str] = []
    for rel, file_float_labels in float_labels_by_file.items():
        first_refs = first_refs_by_file[rel]
        expected = [label for label, _ in file_float_labels if label in first_refs]
        observed = [label for label, _ in sorted(((label, first_refs[label]) for label in expected), key=lambda item: item[1])]
        if expected != observed:
            out_of_order_float_files.append(rel)
            errors.append(
                f"Out-of-order local figure/table references in {rel}: "
                f"expected {', '.join(expected)}; first references appear as {', '.join(observed)}"
            )

    float_format_errors = 0
    for rel, kind, line, has_caption, float_labels in float_environments:
        expected_prefix = "fig:" if kind == "figure" else "tab:"
        if not has_caption:
            float_format_errors += 1
            errors.append(f"{rel}:{line}: {kind} environment is missing a caption")
        if not any(label.startswith(expected_prefix) for label in float_labels):
            float_format_errors += 1
            errors.append(f"{rel}:{line}: {kind} environment is missing a {expected_prefix} label")

    print(f"labels: {len(label_keys)}")
    print(f"references: {len(refs)}")
    print(f"figure/table environments: {len(float_environments)}")
    print(f"duplicate labels: {len(duplicate_labels)}")
    print(f"missing reference targets: {len(missing_refs)}")
    print(f"unreferenced figure/table labels: {len(unreferenced_floats)}")
    print(f"files with out-of-order local figure/table references: {len(out_of_order_float_files)}")
    print(f"figure/table caption-label format errors: {float_format_errors}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("cross-reference checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Check Springer SNmono figure Description text coverage."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
CHAPTER_DIR = BOOK_DIR / "chapters"
DESCRIPTION_TEXTS = BOOK_DIR / "DescriptionTexts.txt"
TEX_FILES = [
    BOOK_DIR / "book.tex",
    BOOK_DIR / "preface.tex",
    BOOK_DIR / "ethics.tex",
    BOOK_DIR / "acronym.tex",
    BOOK_DIR / "glossary.tex",
    BOOK_DIR / "appendix.tex",
    *sorted(CHAPTER_DIR.glob("*.tex")),
]

FIGURE_ENV_RE = re.compile(r"\\begin\{figure\*?\}(?:\[[^\]]*\])?(.*?)\\end\{figure\*?\}", re.DOTALL)
DESCRIPTION_RE = re.compile(r"\\Description\{([^{}]*)\}", re.DOTALL)
CAPTION_RE = re.compile(r"\\caption(?:\[[^\]]*\])?\{", re.DOTALL)
FIGURE_LABEL_RE = re.compile(r"\\label\{(fig:[^{}]+)\}")
DISALLOWED_DESCRIPTION_RE = re.compile(
    r"\\(?:cite|ref|autoref|nameref|cref|Cref|pageref|index|label)\b|TODO|FIXME|TBD|XXX|\?\?\?",
    re.IGNORECASE,
)
DESCRIPTION_TEXTS_RE = re.compile(r"^(\d+) \(Fig\. ([^)]+)\) - (.+)$")


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


def normalized_description(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def check_generated_description_texts(expected: list[str], errors: list[str]) -> int:
    if not DESCRIPTION_TEXTS.exists():
        errors.append(f"{DESCRIPTION_TEXTS.relative_to(ROOT).as_posix()}: missing generated SNmono DescriptionTexts.txt")
        return 0

    lines = [line.strip() for line in DESCRIPTION_TEXTS.read_text(encoding="utf-8").splitlines() if line.strip()]
    records: list[str] = []
    for index, line in enumerate(lines, start=1):
        match = DESCRIPTION_TEXTS_RE.match(line)
        if not match:
            errors.append(f"{DESCRIPTION_TEXTS.relative_to(ROOT).as_posix()}:{index}: malformed DescriptionTexts record")
            continue

        sequence = int(match.group(1))
        figure_number = match.group(2)
        description = normalized_description(match.group(3))
        if sequence != index:
            errors.append(
                f"{DESCRIPTION_TEXTS.relative_to(ROOT).as_posix()}:{index}: "
                f"record sequence is {sequence}, expected {index}"
            )
        if not re.fullmatch(r"\d+\.\d+", figure_number):
            errors.append(
                f"{DESCRIPTION_TEXTS.relative_to(ROOT).as_posix()}:{index}: "
                f"unexpected figure number {figure_number!r}"
            )
        records.append(description)

    if len(records) != len(expected):
        errors.append(
            f"{DESCRIPTION_TEXTS.relative_to(ROOT).as_posix()}: generated {len(records)} records, "
            f"expected {len(expected)}"
        )

    for index, (actual, wanted) in enumerate(zip(records, expected, strict=False), start=1):
        if actual != wanted:
            errors.append(
                f"{DESCRIPTION_TEXTS.relative_to(ROOT).as_posix()}:{index}: "
                "generated description does not match source Description text"
            )
    return len(records)


def main() -> int:
    errors: list[str] = []
    figure_count = 0
    described_count = 0
    expected_descriptions: list[str] = []

    for path in TEX_FILES:
        raw = path.read_text(encoding="utf-8")
        text = strip_tex_comments(raw)
        rel = path.relative_to(ROOT).as_posix()

        for match in FIGURE_ENV_RE.finditer(text):
            figure_count += 1
            body = match.group(1)
            line = line_number(text, match.start())
            labels = FIGURE_LABEL_RE.findall(body)
            label = labels[0] if labels else f"{rel}:{line}"
            descriptions = DESCRIPTION_RE.findall(body)

            if len(descriptions) != 1:
                errors.append(f"{rel}:{line}: figure {label} has {len(descriptions)} Description commands")
                continue

            described_count += 1
            description = normalized_description(descriptions[0])
            expected_descriptions.append(description)
            description_offset = body.find(r"\Description")
            caption_match = CAPTION_RE.search(body)
            if caption_match and description_offset > caption_match.start():
                errors.append(f"{rel}:{line}: figure {label} places Description after caption")
            if not description:
                errors.append(f"{rel}:{line}: figure {label} has an empty Description")
            if len(description.split()) < 8:
                errors.append(f"{rel}:{line}: figure {label} Description is too short")
            if len(description) > 500:
                errors.append(f"{rel}:{line}: figure {label} Description is too long")
            if "\\" in description or DISALLOWED_DESCRIPTION_RE.search(description):
                errors.append(f"{rel}:{line}: figure {label} Description should be plain alt text")
            if not description.endswith("."):
                errors.append(f"{rel}:{line}: figure {label} Description should end with a period")

    generated_count = check_generated_description_texts(expected_descriptions, errors)

    print(f"English figure environments checked: {figure_count}")
    print(f"figures with Description text: {described_count}")
    print(f"generated DescriptionTexts records: {generated_count}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("figure Description checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

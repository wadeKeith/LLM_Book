#!/usr/bin/env python3
"""Check rendered PDF text for expected structure and source leaks."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
CHAPTER_DIR = BOOK_DIR / "chapters"
CHAPTER_RE = re.compile(r"\\chapter\{([^{}]+)\}")


@dataclass(frozen=True)
class MarkerSpec:
    label: str
    text: str
    min_occurrences: int = 1


@dataclass(frozen=True)
class OrderedMarker:
    text: str
    occurrence: str = "first"


@dataclass(frozen=True)
class PdfSpec:
    label: str
    path: Path
    minimum_text_chars: int
    required_markers: tuple[MarkerSpec, ...]
    ordered_markers: tuple[OrderedMarker, ...]


SOURCE_LEAK_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("raw citation command", re.compile(r"\\(?:cite|citep|citet|parencite|textcite)\b")),
    ("raw reference command", re.compile(r"\\(?:ref|eqref|autoref|nameref|cref|Cref|pageref)\b")),
    (
        "raw manuscript command",
        re.compile(r"\\(?:label|index|begin|end|chapter|section|subsection|includegraphics|Description)\b"),
    ),
    ("unresolved reference marker", re.compile(r"(?:\?\?|\[\?\])")),
    ("raw BibTeX entry marker", re.compile(r"@\w+\{")),
    (
        "unresolved editorial marker",
        re.compile(r"\b(?:TODO|FIXME|TBD|XXX|citation needed|cite needed)\b|待补|lorem ipsum", re.IGNORECASE),
    ),
)


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


def source_title_to_pdf_text(title: str) -> str:
    replacements = {
        r"\Transformer": "Transformer",
        r"\transformer": "Transformer",
        r"\transformers": "Transformers",
        r"\llms": "large language models",
        r"\llm": "large language model",
        r"\rlhf": "RLHF",
        r"\rag": "RAG",
        r"\xspace": "",
    }
    for source, rendered in replacements.items():
        title = title.replace(source, rendered)
    return re.sub(r"\s+", " ", title).strip()


def english_chapter_titles() -> tuple[str, ...]:
    titles: list[str] = []
    for path in sorted(CHAPTER_DIR.glob("ch*.tex")):
        text = strip_tex_comments(path.read_text(encoding="utf-8"))
        match = CHAPTER_RE.search(text)
        if not match:
            raise RuntimeError(f"Missing chapter title in {path.relative_to(ROOT).as_posix()}")
        titles.append(source_title_to_pdf_text(match.group(1)))
    return tuple(titles)


def chinese_chapter_titles() -> tuple[str, ...]:
    text = strip_tex_comments((BOOK_DIR / "book_zh.tex").read_text(encoding="utf-8"))
    titles = [
        source_title_to_pdf_text(match.group(1))
        for match in CHAPTER_RE.finditer(text)
        if not match.group(1).startswith("附录")
    ]
    return tuple(titles)


def chapter_markers(language: str, titles: tuple[str, ...]) -> tuple[MarkerSpec, ...]:
    return tuple(
        MarkerSpec(f"{language} chapter {index} title", title, min_occurrences=2)
        for index, title in enumerate(titles, start=1)
    )


ENGLISH_CHAPTER_TITLES = english_chapter_titles()
CHINESE_CHAPTER_TITLES = chinese_chapter_titles()


ENGLISH = PdfSpec(
    label="English PDF",
    path=BOOK_DIR / "book.pdf",
    minimum_text_chars=100_000,
    required_markers=(
        MarkerSpec("title line", "Large Language and Generative"),
        MarkerSpec("title subtitle", "Foundations, Systems, Alignment, and Applications"),
        MarkerSpec("preface", "Preface"),
        MarkerSpec("ethics note", "Declarations, Provenance, and Responsible Use"),
        MarkerSpec("contents", "Contents"),
        *chapter_markers("English", ENGLISH_CHAPTER_TITLES),
        MarkerSpec("appendix", "Appendix: Reproducibility and Notation", min_occurrences=2),
        MarkerSpec("glossary", "Glossary", min_occurrences=2),
        MarkerSpec("references", "References", min_occurrences=2),
        MarkerSpec("index", "Index", min_occurrences=2),
    ),
    ordered_markers=(
        OrderedMarker("Large Language and Generative"),
        OrderedMarker("Preface"),
        OrderedMarker("Declarations, Provenance, and Responsible Use"),
        OrderedMarker("Contents", occurrence="last"),
        *(OrderedMarker(title, occurrence="after_previous") for title in ENGLISH_CHAPTER_TITLES),
        OrderedMarker("Appendix: Reproducibility and Notation", occurrence="after_previous"),
        OrderedMarker("Glossary", occurrence="after_previous"),
        OrderedMarker("References", occurrence="after_previous"),
        OrderedMarker("Index", occurrence="after_previous"),
    ),
)


CHINESE = PdfSpec(
    label="Chinese PDF",
    path=BOOK_DIR / "book_zh.pdf",
    minimum_text_chars=50_000,
    required_markers=(
        MarkerSpec("title", "大语言模型与生成式基础模型"),
        MarkerSpec("preface", "前言"),
        MarkerSpec("ethics note", "伦理与来源说明"),
        MarkerSpec("contents", "目录"),
        *chapter_markers("Chinese", CHINESE_CHAPTER_TITLES),
        MarkerSpec("appendix", "附录 A 附录：记号、实验记录与术语", min_occurrences=2),
        MarkerSpec("glossary", "术语表", min_occurrences=2),
        MarkerSpec("references", "参考文献", min_occurrences=2),
    ),
    ordered_markers=(
        OrderedMarker("大语言模型与生成式基础模型"),
        OrderedMarker("前言"),
        OrderedMarker("伦理与来源说明"),
        OrderedMarker("目录"),
        OrderedMarker(CHINESE_CHAPTER_TITLES[0], occurrence="last"),
        *(OrderedMarker(title, occurrence="after_previous") for title in CHINESE_CHAPTER_TITLES[1:]),
        OrderedMarker("附录 A 附录：记号、实验记录与术语", occurrence="after_previous"),
        OrderedMarker("术语表", occurrence="after_previous"),
        OrderedMarker("参考文献", occurrence="after_previous"),
    ),
)


def extract_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"{path.relative_to(ROOT)} does not exist")
    pdftotext = os.environ.get("PDFTOTEXT", "pdftotext")
    if shutil.which(pdftotext) is None:
        raise RuntimeError("pdftotext is required for rendered PDF text checks")

    result = subprocess.run(
        [pdftotext, "-layout", str(path), "-"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RuntimeError(f"pdftotext failed for {path.relative_to(ROOT)}: {stderr}")
    return result.stdout


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def marker_regex(marker: str) -> re.Pattern[str]:
    if marker.isascii() and any(char.isalpha() for char in marker):
        return re.compile(r"(?<![A-Za-z])" + re.escape(marker) + r"(?![A-Za-z])")
    return re.compile(re.escape(marker))


def marker_positions(text: str, marker: str) -> list[int]:
    return [match.start() for match in marker_regex(marker).finditer(text)]


def selected_position(text: str, marker: OrderedMarker, min_position: int = -1) -> int:
    positions = marker_positions(text, marker.text)
    if not positions:
        return -1
    if marker.occurrence == "first":
        return positions[0]
    if marker.occurrence == "last":
        return positions[-1]
    if marker.occurrence == "after_previous":
        for position in positions:
            if position > min_position:
                return position
        return -1
    raise ValueError(f"unsupported marker occurrence selector: {marker.occurrence}")


def check_source_leaks(spec: PdfSpec, raw_text: str, errors: list[str]) -> int:
    leak_hits = 0
    for line_number, line in enumerate(raw_text.splitlines(), start=1):
        clean_line = re.sub(r"\s+", " ", line).strip()
        if not clean_line:
            continue
        for label, pattern in SOURCE_LEAK_PATTERNS:
            if pattern.search(clean_line):
                leak_hits += 1
                errors.append(
                    f"{spec.label}: rendered text line {line_number} contains {label}: {clean_line}"
                )
    return leak_hits


def check_pdf(spec: PdfSpec) -> list[str]:
    errors: list[str] = []
    raw_text = extract_text(spec.path)
    text = normalize(raw_text)
    leak_hits = check_source_leaks(spec, raw_text, errors)

    if len(text) < spec.minimum_text_chars:
        errors.append(
            f"{spec.label}: extracted text is unexpectedly short "
            f"({len(text)} chars, expected at least {spec.minimum_text_chars})"
        )

    total_marker_hits = 0
    for marker in spec.required_markers:
        positions = marker_positions(text, marker.text)
        total_marker_hits += len(positions)
        if len(positions) < marker.min_occurrences:
            errors.append(
                f"{spec.label}: expected at least {marker.min_occurrences} "
                f"{marker.label} marker occurrence(s), found {len(positions)}: {marker.text}"
            )

    ordered_positions: list[tuple[str, int]] = []
    for marker in spec.ordered_markers:
        min_position = ordered_positions[-1][1] if marker.occurrence == "after_previous" and ordered_positions else -1
        position = selected_position(text, marker, min_position=min_position)
        if position != -1:
            ordered_positions.append((f"{marker.text} ({marker.occurrence})", position))

    for (prev_marker, prev_pos), (next_marker, next_pos) in zip(ordered_positions, ordered_positions[1:]):
        if prev_pos >= next_pos:
            errors.append(
                f"{spec.label}: marker order regression: "
                f"{prev_marker!r} appears at {prev_pos}, "
                f"but {next_marker!r} appears at {next_pos}"
            )

    if not errors:
        pages = raw_text.count("\f")
        print(
            f"{spec.label}: {len(spec.required_markers)} markers checked, "
            f"{total_marker_hits} marker hits, "
            f"{len(text)} extracted chars, {pages} text pages, "
            f"{leak_hits} source-leak hits"
        )
    return errors


def main() -> int:
    errors: list[str] = []
    for spec in (ENGLISH, CHINESE):
        try:
            errors.extend(check_pdf(spec))
        except (FileNotFoundError, RuntimeError) as exc:
            errors.append(str(exc))

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("rendered PDF text structure and source-leak checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

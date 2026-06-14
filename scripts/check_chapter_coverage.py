#!/usr/bin/env python3
"""Check conservative chapter coverage floors for the manuscript."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
CHAPTER_DIR = BOOK_DIR / "chapters"
ZH_ROOT = BOOK_DIR / "book_zh.tex"
EXPECTED_CHAPTERS = 17

MIN_EN_BODY_WORDS = 1800
MIN_EN_BODY_CITATIONS = 5
MIN_EN_BODY_INDEX_ENTRIES = 20
MIN_EN_BODY_FIGURES = 1
MIN_EN_BODY_TABLES = 1
MIN_ZH_CHAPTER_HAN_CHARS = 1800
MIN_ZH_CHAPTER_CITATIONS = 1
MIN_ZH_CHAPTER_FIGURES = 1
MIN_ZH_CHAPTER_TABLES = 1

CITE_RE = re.compile(
    r"\\(?:cite|citep|citet|citealp|citeauthor|citeyear)\s*(?:\[[^\]]*\]\s*){0,2}\{[^{}]+\}",
    re.DOTALL,
)
ZH_CHAPTER_RE = re.compile(r"\\chapter\{([^{}]+)\}")


@dataclass(frozen=True)
class EnglishChapterMetrics:
    path: Path
    body_words: int
    citations: int
    index_entries: int
    figures: int
    tables: int


@dataclass(frozen=True)
class ChineseChapterMetrics:
    number: int
    title: str
    han_chars: int
    citations: int
    figures: int
    tables: int


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


def text_before_key_terms(text: str) -> str:
    marker = r"\section{Key Terms}"
    index = text.find(marker)
    return text[:index] if index != -1 else text


def english_body_words(text: str) -> int:
    plain = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})?", " ", text)
    return len(re.findall(r"[A-Za-z][A-Za-z0-9'-]*", plain))


def english_metrics(path: Path) -> EnglishChapterMetrics:
    text = strip_tex_comments(path.read_text(encoding="utf-8"))
    body = text_before_key_terms(text)
    return EnglishChapterMetrics(
        path=path,
        body_words=english_body_words(body),
        citations=len(CITE_RE.findall(body)),
        index_entries=body.count(r"\index{"),
        figures=len(re.findall(r"\\begin\{figure\*?\}", body)),
        tables=len(re.findall(r"\\begin\{table\*?\}", body)),
    )


def chinese_metrics() -> list[ChineseChapterMetrics]:
    text = strip_tex_comments(ZH_ROOT.read_text(encoding="utf-8"))
    chapters = list(ZH_CHAPTER_RE.finditer(text))
    content = [match for match in chapters if not match.group(1).startswith("附录")]
    metrics: list[ChineseChapterMetrics] = []

    for number, match in enumerate(content, start=1):
        current_index = chapters.index(match)
        next_match = chapters[current_index + 1] if current_index + 1 < len(chapters) else None
        block = text[match.end() : next_match.start() if next_match else len(text)]
        metrics.append(
            ChineseChapterMetrics(
                number=number,
                title=match.group(1),
                han_chars=len(re.findall(r"[\u4e00-\u9fff]", block)),
                citations=len(CITE_RE.findall(block)),
                figures=len(re.findall(r"\\begin\{figure\*?\}", block)),
                tables=len(re.findall(r"\\begin\{table\*?\}", block)),
            )
        )

    return metrics


def check_english(errors: list[str]) -> tuple[int, int, int, int, int]:
    chapters = [english_metrics(path) for path in sorted(CHAPTER_DIR.glob("ch*.tex"))]
    if len(chapters) != EXPECTED_CHAPTERS:
        errors.append(f"English chapter count is {len(chapters)}, expected {EXPECTED_CHAPTERS}")

    for item in chapters:
        rel = item.path.relative_to(ROOT).as_posix()
        if item.body_words < MIN_EN_BODY_WORDS:
            errors.append(f"{rel}: body has {item.body_words} words, minimum is {MIN_EN_BODY_WORDS}")
        if item.citations < MIN_EN_BODY_CITATIONS:
            errors.append(f"{rel}: body has {item.citations} citation commands, minimum is {MIN_EN_BODY_CITATIONS}")
        if item.index_entries < MIN_EN_BODY_INDEX_ENTRIES:
            errors.append(f"{rel}: body has {item.index_entries} index entries, minimum is {MIN_EN_BODY_INDEX_ENTRIES}")
        if item.figures < MIN_EN_BODY_FIGURES:
            errors.append(f"{rel}: body has {item.figures} figure environments, minimum is {MIN_EN_BODY_FIGURES}")
        if item.tables < MIN_EN_BODY_TABLES:
            errors.append(f"{rel}: body has {item.tables} table environments, minimum is {MIN_EN_BODY_TABLES}")

    return (
        min((item.body_words for item in chapters), default=0),
        min((item.citations for item in chapters), default=0),
        min((item.index_entries for item in chapters), default=0),
        min((item.figures for item in chapters), default=0),
        min((item.tables for item in chapters), default=0),
    )


def check_chinese(errors: list[str]) -> tuple[int, int, int]:
    chapters = chinese_metrics()
    if len(chapters) != EXPECTED_CHAPTERS:
        errors.append(f"Chinese content chapter count is {len(chapters)}, expected {EXPECTED_CHAPTERS}")

    for item in chapters:
        if item.han_chars < MIN_ZH_CHAPTER_HAN_CHARS:
            errors.append(
                f"Chinese chapter {item.number} ({item.title}) has {item.han_chars} Han characters, "
                f"minimum is {MIN_ZH_CHAPTER_HAN_CHARS}"
            )
        if item.citations < MIN_ZH_CHAPTER_CITATIONS:
            errors.append(
                f"Chinese chapter {item.number} ({item.title}) has {item.citations} citation commands, "
                f"minimum is {MIN_ZH_CHAPTER_CITATIONS}"
            )
        if item.figures < MIN_ZH_CHAPTER_FIGURES:
            errors.append(
                f"Chinese chapter {item.number} ({item.title}) has {item.figures} figure environments, "
                f"minimum is {MIN_ZH_CHAPTER_FIGURES}"
            )
        if item.tables < MIN_ZH_CHAPTER_TABLES:
            errors.append(
                f"Chinese chapter {item.number} ({item.title}) has {item.tables} table environments, "
                f"minimum is {MIN_ZH_CHAPTER_TABLES}"
            )

    return (
        min((item.han_chars for item in chapters), default=0),
        min((item.citations for item in chapters), default=0),
        min((item.figures for item in chapters), default=0),
        min((item.tables for item in chapters), default=0),
    )


def main() -> int:
    errors: list[str] = []
    en_words, en_cites, en_index, en_figures, en_tables = check_english(errors)
    zh_han, zh_cites, zh_figures, zh_tables = check_chinese(errors)

    print(f"English chapters checked: {EXPECTED_CHAPTERS}")
    print(f"English minimum body words: {en_words} / {MIN_EN_BODY_WORDS}")
    print(f"English minimum body citation commands: {en_cites} / {MIN_EN_BODY_CITATIONS}")
    print(f"English minimum body index entries: {en_index} / {MIN_EN_BODY_INDEX_ENTRIES}")
    print(f"English minimum body figures: {en_figures} / {MIN_EN_BODY_FIGURES}")
    print(f"English minimum body tables: {en_tables} / {MIN_EN_BODY_TABLES}")
    print(f"Chinese content chapters checked: {EXPECTED_CHAPTERS}")
    print(f"Chinese minimum Han characters: {zh_han} / {MIN_ZH_CHAPTER_HAN_CHARS}")
    print(f"Chinese minimum citation commands: {zh_cites} / {MIN_ZH_CHAPTER_CITATIONS}")
    print(f"Chinese minimum figures: {zh_figures} / {MIN_ZH_CHAPTER_FIGURES}")
    print(f"Chinese minimum tables: {zh_tables} / {MIN_ZH_CHAPTER_TABLES}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("chapter coverage checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

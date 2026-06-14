#!/usr/bin/env python3
"""Check substantive coverage for the Chinese readable edition."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
EN_ROOT = BOOK_DIR / "book.tex"
ZH_ROOT = BOOK_DIR / "book_zh.tex"
CHAPTER_DIR = BOOK_DIR / "chapters"

EXPECTED_CHAPTERS = 17
MIN_CHAPTER_COVERAGE_RATIO = 0.75
MIN_TOTAL_COVERAGE_RATIO = 0.90

CHAPTER_RE = re.compile(r"\\chapter\{([^{}]+)\}")
INCLUDE_RE = re.compile(r"\\include\{chapters/([^{}]+)\}")
HAN_RE = re.compile(r"[\u4e00-\u9fff]")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9'-]*")


@dataclass(frozen=True)
class EnglishChapter:
    number: int
    stem: str
    title: str
    body_words: int


@dataclass(frozen=True)
class ChineseChapter:
    number: int
    title: str
    han_chars: int


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


def plain_word_count(text: str) -> int:
    plain = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})?", " ", text)
    return len(WORD_RE.findall(plain))


def english_chapters() -> list[EnglishChapter]:
    root_text = strip_tex_comments(EN_ROOT.read_text(encoding="utf-8"))
    stems = INCLUDE_RE.findall(root_text)
    chapters: list[EnglishChapter] = []

    for number, stem in enumerate(stems, start=1):
        path = CHAPTER_DIR / f"{stem}.tex"
        text = strip_tex_comments(path.read_text(encoding="utf-8"))
        title_match = CHAPTER_RE.search(text)
        title = title_match.group(1) if title_match else f"<missing title: {stem}>"
        chapters.append(
            EnglishChapter(
                number=number,
                stem=stem,
                title=title,
                body_words=plain_word_count(text_before_key_terms(text)),
            )
        )

    return chapters


def chinese_chapters() -> list[ChineseChapter]:
    text = strip_tex_comments(ZH_ROOT.read_text(encoding="utf-8"))
    matches = list(CHAPTER_RE.finditer(text))
    chapters: list[ChineseChapter] = []

    for index, match in enumerate(matches):
        title = match.group(1)
        if title.startswith("附录"):
            continue
        next_match = matches[index + 1] if index + 1 < len(matches) else None
        block = text[match.end() : next_match.start() if next_match else len(text)]
        chapters.append(
            ChineseChapter(
                number=len(chapters) + 1,
                title=title,
                han_chars=len(HAN_RE.findall(block)),
            )
        )

    return chapters


def ratio(chinese: ChineseChapter, english: EnglishChapter) -> float:
    if english.body_words <= 0:
        return 0.0
    return chinese.han_chars / english.body_words


def main() -> int:
    en = english_chapters()
    zh = chinese_chapters()
    errors: list[str] = []

    if len(en) != EXPECTED_CHAPTERS:
        errors.append(f"English chapter count is {len(en)}, expected {EXPECTED_CHAPTERS}")
    if len(zh) != EXPECTED_CHAPTERS:
        errors.append(f"Chinese chapter count is {len(zh)}, expected {EXPECTED_CHAPTERS}")

    pairs = list(zip(en, zh, strict=False))
    ratio_rows: list[tuple[float, EnglishChapter, ChineseChapter]] = [
        (ratio(chinese, english), english, chinese) for english, chinese in pairs
    ]
    below_floor: list[str] = []
    for current_ratio, english, chinese in ratio_rows:
        if current_ratio < MIN_CHAPTER_COVERAGE_RATIO:
            below_floor.append(
                f"chapter {english.number} ({english.title} / {chinese.title}) "
                f"coverage ratio {current_ratio:.2f}"
            )

    total_en_words = sum(item.body_words for item in en)
    total_zh_han = sum(item.han_chars for item in zh)
    total_ratio = total_zh_han / total_en_words if total_en_words else 0.0
    min_ratio = min((item[0] for item in ratio_rows), default=0.0)
    weakest = min(ratio_rows, default=None, key=lambda item: item[0])

    if total_ratio < MIN_TOTAL_COVERAGE_RATIO:
        errors.append(
            f"Chinese readable edition total coverage ratio is {total_ratio:.2f}, "
            f"minimum is {MIN_TOTAL_COVERAGE_RATIO:.2f}"
        )
    for item in below_floor:
        errors.append(f"{item}; minimum is {MIN_CHAPTER_COVERAGE_RATIO:.2f}")

    print(f"bilingual chapter pairs checked: {len(pairs)}")
    print(f"English controlling body words: {total_en_words}")
    print(f"Chinese readable Han characters: {total_zh_han}")
    print(
        "minimum Chinese-to-English coverage ratio: "
        f"{min_ratio:.2f} / {MIN_CHAPTER_COVERAGE_RATIO:.2f}"
    )
    if weakest is not None:
        weakest_ratio, weakest_en, weakest_zh = weakest
        print(
            "weakest bilingual chapter: "
            f"{weakest_en.number:02d} ratio {weakest_ratio:.3f}; "
            f"{weakest_en.title} / {weakest_zh.title}"
        )
    print(
        "total Chinese-to-English coverage ratio: "
        f"{total_ratio:.2f} / {MIN_TOTAL_COVERAGE_RATIO:.2f}"
    )
    print(f"chapters below coverage floor: {len(below_floor)}")
    for current_ratio, english, chinese in sorted(ratio_rows, key=lambda item: item[0]):
        print(
            "bilingual coverage row: "
            f"{english.number:02d} ratio {current_ratio:.3f}; "
            f"English words {english.body_words}; "
            f"Chinese Han {chinese.han_chars}; "
            f"{english.title} / {chinese.title}"
        )

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("bilingual coverage checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Check exercise sections for basic pedagogical completeness."""

from __future__ import annotations

import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
CHAPTER_DIR = BOOK_DIR / "chapters"
ZH_ROOT = BOOK_DIR / "book_zh.tex"
EXPECTED_CHAPTERS = 17

MIN_EN_EXERCISES = 5
MIN_EN_ITEM_WORDS = 15
MIN_EN_TOTAL_WORDS = 90
MIN_ZH_EXERCISES = 4
MIN_ZH_ITEM_UNITS = 7
MIN_ZH_TOTAL_UNITS = 75

SECTION_RE = re.compile(r"\\section\{Exercises\}(.*?)(?=\\section\{|\\chapter\{|\Z)", re.DOTALL)
EN_ITEM_RE = re.compile(r"\\item\b(.*?)(?=\\item\b|\\end\{enumerate\}|\Z)", re.DOTALL)
ZH_CHAPTER_RE = re.compile(r"\\chapter\{([^{}]+)\}")
ZH_EXERCISE_MARKER = r"\textbf{练习。}"
TERMINAL_RE = re.compile(r"[。？！.!?](?:\s*[])}]*)\s*$")


@dataclass(frozen=True)
class ExerciseItem:
    label: str
    path: Path
    line: int
    raw: str
    plain: str
    units: int


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


def plain_text(raw: str) -> str:
    text = re.sub(
        r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?(?:\{([^{}]*)\})?",
        lambda match: f" {match.group(1) or ''} ",
        raw,
    )
    text = re.sub(r"[{}$]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def english_word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z][A-Za-z0-9'-]*", text))


def chinese_unit_count(text: str) -> int:
    han = len(re.findall(r"[\u4e00-\u9fff]", text))
    english_words = english_word_count(text)
    return han + english_words


def normalized_prompt(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_terminal_source(raw: str) -> str:
    text = re.sub(r"\\end\{enumerate\}\s*$", "", raw.strip())
    return re.sub(r"\s+", " ", text).strip()


def check_item_basics(items: list[ExerciseItem], min_units: int, unit_name: str, errors: list[str]) -> None:
    for item in items:
        rel = item.path.relative_to(ROOT).as_posix()
        if item.units < min_units:
            errors.append(f"{rel}:{item.line}: {item.label} has {item.units} {unit_name}, minimum is {min_units}")
        if not TERMINAL_RE.search(clean_terminal_source(item.raw)):
            errors.append(f"{rel}:{item.line}: {item.label} does not end with terminal punctuation")


def check_duplicates(items: list[ExerciseItem], errors: list[str]) -> None:
    counts = Counter(normalized_prompt(item.plain) for item in items)
    duplicates = {prompt for prompt, count in counts.items() if count > 1 and prompt}
    for item in items:
        prompt = normalized_prompt(item.plain)
        if prompt in duplicates:
            rel = item.path.relative_to(ROOT).as_posix()
            errors.append(f"{rel}:{item.line}: duplicate exercise prompt after normalization")


def english_exercises(path: Path) -> list[ExerciseItem]:
    text = strip_tex_comments(path.read_text(encoding="utf-8"))
    match = SECTION_RE.search(text)
    if not match:
        return []

    items: list[ExerciseItem] = []
    for number, item_match in enumerate(EN_ITEM_RE.finditer(match.group(1)), start=1):
        raw = item_match.group(1).strip()
        plain = plain_text(raw)
        items.append(
            ExerciseItem(
                label=f"English exercise {number}",
                path=path,
                line=line_number(text, match.start(1) + item_match.start()),
                raw=raw,
                plain=plain,
                units=english_word_count(plain),
            )
        )
    return items


def chinese_exercises() -> list[tuple[int, str, list[ExerciseItem]]]:
    text = strip_tex_comments(ZH_ROOT.read_text(encoding="utf-8"))
    chapters = list(ZH_CHAPTER_RE.finditer(text))
    content = [match for match in chapters if not match.group(1).startswith("附录")]
    result: list[tuple[int, str, list[ExerciseItem]]] = []

    for number, match in enumerate(content, start=1):
        current_index = chapters.index(match)
        next_match = chapters[current_index + 1] if current_index + 1 < len(chapters) else None
        block_start = match.end()
        block = text[block_start : next_match.start() if next_match else len(text)]
        marker_offset = block.find(ZH_EXERCISE_MARKER)
        if marker_offset == -1:
            result.append((number, match.group(1), []))
            continue

        exercise_text = block[marker_offset:]
        items: list[ExerciseItem] = []
        for item_number, item_match in enumerate(EN_ITEM_RE.finditer(exercise_text), start=1):
            raw = item_match.group(1).strip()
            plain = plain_text(raw)
            items.append(
                ExerciseItem(
                    label=f"Chinese exercise {number}.{item_number}",
                    path=ZH_ROOT,
                    line=line_number(text, block_start + marker_offset + item_match.start()),
                    raw=raw,
                    plain=plain,
                    units=chinese_unit_count(plain),
                )
            )
        result.append((number, match.group(1), items))

    return result


def main() -> int:
    errors: list[str] = []
    english_chapter_items: list[list[ExerciseItem]] = []
    all_english_items: list[ExerciseItem] = []

    for path in sorted(CHAPTER_DIR.glob("ch*.tex")):
        items = english_exercises(path)
        english_chapter_items.append(items)
        all_english_items.extend(items)
        rel = path.relative_to(ROOT).as_posix()
        total_words = sum(item.units for item in items)
        if len(items) < MIN_EN_EXERCISES:
            errors.append(f"{rel}: has {len(items)} exercises, minimum is {MIN_EN_EXERCISES}")
        if total_words < MIN_EN_TOTAL_WORDS:
            errors.append(f"{rel}: exercise section has {total_words} words, minimum is {MIN_EN_TOTAL_WORDS}")
        check_item_basics(items, MIN_EN_ITEM_WORDS, "words", errors)

    chinese_chapters = chinese_exercises()
    all_chinese_items = [item for _, _, items in chinese_chapters for item in items]
    for number, title, items in chinese_chapters:
        total_units = sum(item.units for item in items)
        if len(items) < MIN_ZH_EXERCISES:
            errors.append(f"Chinese chapter {number} ({title}) has {len(items)} exercises, minimum is {MIN_ZH_EXERCISES}")
        if total_units < MIN_ZH_TOTAL_UNITS:
            errors.append(
                f"Chinese chapter {number} ({title}) exercise section has {total_units} text units, "
                f"minimum is {MIN_ZH_TOTAL_UNITS}"
            )
        check_item_basics(items, MIN_ZH_ITEM_UNITS, "text units", errors)

    check_duplicates(all_english_items, errors)
    check_duplicates(all_chinese_items, errors)

    en_counts = [len(items) for items in english_chapter_items]
    en_totals = [sum(item.units for item in items) for items in english_chapter_items]
    zh_counts = [len(items) for _, _, items in chinese_chapters]
    zh_totals = [sum(item.units for item in items) for _, _, items in chinese_chapters]

    print(f"English exercise chapters checked: {len(english_chapter_items)} / {EXPECTED_CHAPTERS}")
    print(f"English exercise items checked: {len(all_english_items)}")
    print(f"English minimum exercise items per chapter: {min(en_counts, default=0)} / {MIN_EN_EXERCISES}")
    print(f"English minimum exercise-section words: {min(en_totals, default=0)} / {MIN_EN_TOTAL_WORDS}")
    print(f"Chinese exercise chapters checked: {len(chinese_chapters)} / {EXPECTED_CHAPTERS}")
    print(f"Chinese exercise items checked: {len(all_chinese_items)}")
    print(f"Chinese minimum exercise items per chapter: {min(zh_counts, default=0)} / {MIN_ZH_EXERCISES}")
    print(f"Chinese minimum exercise-section text units: {min(zh_totals, default=0)} / {MIN_ZH_TOTAL_UNITS}")

    if len(english_chapter_items) != EXPECTED_CHAPTERS:
        errors.append(f"English exercise chapter count is {len(english_chapter_items)}, expected {EXPECTED_CHAPTERS}")
    if len(chinese_chapters) != EXPECTED_CHAPTERS:
        errors.append(f"Chinese exercise chapter count is {len(chinese_chapters)}, expected {EXPECTED_CHAPTERS}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("exercise quality checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

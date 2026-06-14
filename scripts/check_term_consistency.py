#!/usr/bin/env python3
"""Check front/back matter and chapter term-list consistency."""

from __future__ import annotations

import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
CHAPTER_DIR = BOOK_DIR / "chapters"
ACRONYM_FILE = BOOK_DIR / "acronym.tex"
GLOSSARY_FILE = BOOK_DIR / "glossary.tex"
ZH_ROOT = BOOK_DIR / "book_zh.tex"
CHAPTER_FILES = sorted(CHAPTER_DIR.glob("ch*.tex"))
EXPECTED_CHINESE_CHAPTERS = 17
MIN_CHINESE_KEY_TERMS = 4
MIN_CHINESE_TERM_UNITS = 10
INDEX_SOURCE_FILES = [
    ACRONYM_FILE,
    GLOSSARY_FILE,
    *CHAPTER_FILES,
]
DESCRIPTION_ITEM_RE = re.compile(r"\\item\[([^\]]+)\](.*?)(?=\\item\[|\\end\{description\})", re.DOTALL)
KEY_TERMS_RE = re.compile(r"\\section\{Key Terms\}")
NEXT_SECTION_RE = re.compile(r"\\section\{")
TERMINAL_LABEL_RE = re.compile(r"[.!?]\s*$")
TERMINAL_BODY_RE = re.compile(r"([.!?]|\\\)|\})\s*$")
ZH_CHAPTER_RE = re.compile(r"\\chapter\{([^{}]+)\}")
ZH_KEY_TERMS_MARKER = r"\textbf{关键术语。}"
ZH_KEY_TERMS_END_MARKERS = (
    r"\textbf{实现要点。}",
    r"\textbf{练习。}",
    r"\section{",
    r"\chapter{",
)
FORBIDDEN_TERM_COMMAND_RE = re.compile(r"\\(?:cite|citep|citet|ref|eqref|label|index|url)\b")


@dataclass(frozen=True)
class DescriptionItem:
    label: str
    body: str
    path: Path
    line: int


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


def normalize_label(label: str) -> str:
    label = re.sub(r"\\[A-Za-z]+", " ", label)
    label = label.replace(r"\&", "and")
    return re.sub(r"[^A-Za-z0-9]+", " ", label).strip().lower()


def normalize_chinese_term_item(item: str) -> str:
    return re.sub(r"[\W_]+", "", item, flags=re.UNICODE).casefold()


def tex_to_plain(text: str) -> str:
    text = re.sub(r"\\(?:textbf|textit|emph|texttt|mathrm)\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\[A-Za-z]+", " ", text)
    text = text.replace(r"\&", "&")
    text = re.sub(r"[{}$]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def text_units(text: str) -> int:
    return len(re.sub(r"\s+", "", tex_to_plain(text)))


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def description_items(path: Path, text: str, line_offset: int = 0) -> list[DescriptionItem]:
    items: list[DescriptionItem] = []
    for match in DESCRIPTION_ITEM_RE.finditer(text):
        body = re.sub(r"\s+", " ", match.group(2)).strip()
        items.append(DescriptionItem(match.group(1).strip(), body, path, line_offset + line_number(text, match.start())))
    return items


def key_terms_block(path: Path) -> tuple[str, int] | None:
    text = strip_tex_comments(path.read_text(encoding="utf-8"))
    match = KEY_TERMS_RE.search(text)
    if not match:
        return None
    next_match = NEXT_SECTION_RE.search(text, match.end())
    end = match.end() + next_match.start() if next_match else len(text)
    return text[match.start() : end], line_number(text, match.start()) - 1


def find_braced_argument(text: str, open_brace: int) -> tuple[str, int] | None:
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


def index_entries(path: Path) -> list[str]:
    text = strip_tex_comments(path.read_text(encoding="utf-8"))
    entries: list[str] = []
    marker = r"\index{"
    position = 0
    while True:
        start = text.find(marker, position)
        if start == -1:
            break
        open_brace = start + len(r"\index")
        parsed = find_braced_argument(text, open_brace)
        if parsed is None:
            position = start + len(marker)
            continue
        raw, end = parsed
        entries.append(raw.strip())
        position = end
    return entries


def index_main(entry: str) -> str:
    return re.split(r"[!|]", entry, maxsplit=1)[0].strip()


def check_order_and_duplicates(items: list[DescriptionItem], label: str, errors: list[str]) -> None:
    labels = [item.label for item in items]
    expected = sorted(labels, key=normalize_label)
    if labels != expected:
        errors.append(f"{label}: description items are not in alphabetical order")

    duplicate_labels = sorted(term for term, count in Counter(labels).items() if count > 1)
    for term in duplicate_labels:
        errors.append(f"{label}: duplicate description item label {term}")


def check_frontmatter_terms(errors: list[str]) -> tuple[int, int, int]:
    acronym_text = strip_tex_comments(ACRONYM_FILE.read_text(encoding="utf-8"))
    glossary_text = strip_tex_comments(GLOSSARY_FILE.read_text(encoding="utf-8"))
    acronym_items = description_items(ACRONYM_FILE, acronym_text)
    glossary_items = description_items(GLOSSARY_FILE, glossary_text)

    check_order_and_duplicates(acronym_items, "Acronym list", errors)
    check_order_and_duplicates(glossary_items, "Glossary", errors)

    index_mains = {
        index_main(entry)
        for path in INDEX_SOURCE_FILES
        for entry in index_entries(path)
    }
    indexed_acronyms = 0
    for item in acronym_items:
        if item.label not in index_mains:
            errors.append(
                f"{item.path.relative_to(ROOT).as_posix()}:{item.line}: "
                f"acronym {item.label} has no matching source index entry"
            )
        else:
            indexed_acronyms += 1
        if not TERMINAL_BODY_RE.search(item.body):
            errors.append(
                f"{item.path.relative_to(ROOT).as_posix()}:{item.line}: "
                f"acronym definition for {item.label} does not end with terminal punctuation"
            )

    for item in glossary_items:
        if r"\index{" not in item.body:
            errors.append(
                f"{item.path.relative_to(ROOT).as_posix()}:{item.line}: "
                f"glossary item {item.label} has no index entry"
            )
        if not TERMINAL_BODY_RE.search(item.body):
            errors.append(
                f"{item.path.relative_to(ROOT).as_posix()}:{item.line}: "
                f"glossary definition for {item.label} does not end with terminal punctuation"
            )

    return len(acronym_items), indexed_acronyms, len(glossary_items)


def check_chapter_key_terms(errors: list[str]) -> int:
    total_items = 0
    for path in CHAPTER_FILES:
        block = key_terms_block(path)
        if block is None:
            errors.append(f"{path.relative_to(ROOT).as_posix()}: missing Key Terms section")
            continue
        text, line_offset = block
        items = description_items(path, text, line_offset=line_offset)
        total_items += len(items)

        duplicate_labels = sorted(term for term, count in Counter(item.label for item in items).items() if count > 1)
        for term in duplicate_labels:
            errors.append(f"{path.relative_to(ROOT).as_posix()}: duplicate Key Terms label {term}")

        for item in items:
            rel = path.relative_to(ROOT).as_posix()
            if TERMINAL_LABEL_RE.search(item.label):
                errors.append(f"{rel}:{item.line}: Key Terms label should not include terminal punctuation: {item.label}")
            if not TERMINAL_BODY_RE.search(item.body):
                errors.append(f"{rel}:{item.line}: Key Terms definition for {item.label} lacks terminal punctuation")

    return total_items


def check_chinese_chapter_key_terms(errors: list[str]) -> tuple[int, int, int, int]:
    text = strip_tex_comments(ZH_ROOT.read_text(encoding="utf-8"))
    chapters = list(ZH_CHAPTER_RE.finditer(text))
    content_chapters = [match for match in chapters if not match.group(1).startswith("附录")]

    if len(content_chapters) != EXPECTED_CHINESE_CHAPTERS:
        errors.append(
            f"Chinese edition has {len(content_chapters)} content chapters, "
            f"expected {EXPECTED_CHINESE_CHAPTERS}"
        )

    total_items = 0
    min_items = 0
    min_units = 0

    for index, match in enumerate(content_chapters, start=1):
        next_match = chapters[chapters.index(match) + 1] if chapters.index(match) + 1 < len(chapters) else None
        block_start = match.start()
        block = text[block_start : next_match.start() if next_match else len(text)]
        title = match.group(1)
        marker_start = block.find(ZH_KEY_TERMS_MARKER)
        if marker_start == -1:
            errors.append(f"Chinese chapter {index} ({title}): missing key-term paragraph")
            continue

        paragraph_start = marker_start + len(ZH_KEY_TERMS_MARKER)
        end_candidates = [
            position
            for marker in ZH_KEY_TERMS_END_MARKERS
            if (position := block.find(marker, paragraph_start)) != -1
        ]
        paragraph = block[paragraph_start : min(end_candidates) if end_candidates else len(block)]
        paragraph = re.sub(r"\s+", " ", paragraph).strip()
        line = line_number(text, block_start + marker_start)

        if FORBIDDEN_TERM_COMMAND_RE.search(paragraph):
            errors.append(
                f"{ZH_ROOT.relative_to(ROOT).as_posix()}:{line}: "
                f"Chinese chapter {index} key-term paragraph contains citation/reference/index commands"
            )
        if not paragraph.endswith("。"):
            errors.append(
                f"{ZH_ROOT.relative_to(ROOT).as_posix()}:{line}: "
                f"Chinese chapter {index} key-term paragraph lacks terminal Chinese punctuation"
            )

        items = [item.strip(" \t\n。") for item in paragraph.split("；") if item.strip(" \t\n。")]
        total_items += len(items)
        min_items = len(items) if min_items == 0 else min(min_items, len(items))

        if len(items) < MIN_CHINESE_KEY_TERMS:
            errors.append(
                f"{ZH_ROOT.relative_to(ROOT).as_posix()}:{line}: "
                f"Chinese chapter {index} ({title}) has only {len(items)} key-term entries"
            )

        duplicate_items = sorted(
            item
            for item, count in Counter(normalize_chinese_term_item(item) for item in items).items()
            if count > 1
        )
        for item in duplicate_items:
            errors.append(
                f"{ZH_ROOT.relative_to(ROOT).as_posix()}:{line}: "
                f"Chinese chapter {index} duplicate key-term entry {item}"
            )

        for item in items:
            units = text_units(item)
            min_units = units if min_units == 0 else min(min_units, units)
            if units < MIN_CHINESE_TERM_UNITS:
                errors.append(
                    f"{ZH_ROOT.relative_to(ROOT).as_posix()}:{line}: "
                    f"Chinese chapter {index} key-term entry is too terse: {item}"
                )

    return len(content_chapters), total_items, min_items, min_units


def main() -> int:
    errors: list[str] = []
    acronym_count, indexed_acronyms, glossary_count = check_frontmatter_terms(errors)
    key_term_count = check_chapter_key_terms(errors)
    zh_chapters, zh_key_terms, min_zh_terms, min_zh_units = check_chinese_chapter_key_terms(errors)

    print(f"acronym entries: {acronym_count}")
    print(f"indexed acronym entries: {indexed_acronyms}")
    print(f"glossary entries: {glossary_count}")
    print(f"chapter key-term entries: {key_term_count}")
    print(f"Chinese chapter key-term chapters: {zh_chapters} / {EXPECTED_CHINESE_CHAPTERS}")
    print(f"Chinese chapter key-term entries: {zh_key_terms}")
    print(f"Chinese minimum key-term entries per chapter: {min_zh_terms} / {MIN_CHINESE_KEY_TERMS}")
    print(f"Chinese minimum key-term text units: {min_zh_units} / {MIN_CHINESE_TERM_UNITS}")
    print(f"term consistency errors: {len(errors)}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("front matter and chapter term consistency checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

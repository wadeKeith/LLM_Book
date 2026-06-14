#!/usr/bin/env python3
"""Check PDF outline sources for navigable publication structure."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
CHAPTER_DIR = BOOK_DIR / "chapters"

BOOKMARK_RE = re.compile(
    r"\\BOOKMARK\s+\[(-?\d+)\]\[[^\]]*\]\{([^{}]*)\}\{([^{}]*)\}\{([^{}]*)\}"
)
CHAPTER_RE = re.compile(r"\\chapter\{([^{}]+)\}")


@dataclass(frozen=True)
class BookmarkEntry:
    line_no: int
    level: int
    destination: str
    title: str
    parent: str


@dataclass(frozen=True)
class ExpectedBookmark:
    title: str
    level: int | None = None


@dataclass(frozen=True)
class OutlineSpec:
    label: str
    path: Path
    expected_order: tuple[ExpectedBookmark, ...]
    chapter_titles: tuple[str, ...]
    expected_part_count: int
    min_bookmarks: int


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


def source_title_to_outline(title: str) -> str:
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
    title = title.replace(r"\ ", " ").replace("~", " ")
    title = re.sub(r"\\(?:textbf|textit|emph|texttt)\{([^{}]*)\}", r"\1", title)
    title = re.sub(r"\\[A-Za-z]+", "", title)
    return normalize_title(title.replace("{", "").replace("}", ""))


def normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip()


def title_key(title: str) -> str:
    return re.sub(r"\s+", "", normalize_title(title)).casefold()


def decode_bookmark_title(raw: str) -> str:
    data = bytearray()
    index = 0
    while index < len(raw):
        char = raw[index]
        if (
            char == "\\"
            and index + 3 < len(raw)
            and all("0" <= digit <= "7" for digit in raw[index + 1 : index + 4])
        ):
            data.append(int(raw[index + 1 : index + 4], 8))
            index += 4
            continue
        if char == "\\" and index + 1 < len(raw):
            data.extend(raw[index + 1].encode("latin-1", errors="ignore"))
            index += 2
            continue
        data.extend(char.encode("latin-1", errors="ignore"))
        index += 1

    if data.startswith(b"\xfe\xff"):
        return normalize_title(bytes(data[2:]).decode("utf-16-be"))
    return normalize_title(bytes(data).decode("latin-1"))


def parse_outline(path: Path) -> tuple[list[BookmarkEntry], list[str]]:
    errors: list[str] = []
    if not path.exists():
        return [], [f"{path.relative_to(ROOT).as_posix()}: missing outline source; run make all first"]

    entries: list[BookmarkEntry] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.startswith(r"\BOOKMARK"):
            continue
        match = BOOKMARK_RE.match(line)
        if not match:
            errors.append(f"{path.relative_to(ROOT).as_posix()}:{line_no}: malformed BOOKMARK record")
            continue
        level, destination, raw_title, parent = match.groups()
        try:
            title = decode_bookmark_title(raw_title)
        except UnicodeDecodeError as exc:
            errors.append(
                f"{path.relative_to(ROOT).as_posix()}:{line_no}: cannot decode bookmark title: {exc}"
            )
            title = raw_title
        entries.append(
            BookmarkEntry(
                line_no=line_no,
                level=int(level),
                destination=destination,
                title=title,
                parent=parent,
            )
        )
    return entries, errors


def english_chapter_titles() -> tuple[str, ...]:
    titles: list[str] = []
    for path in sorted(CHAPTER_DIR.glob("ch*.tex")):
        text = strip_tex_comments(path.read_text(encoding="utf-8"))
        match = CHAPTER_RE.search(text)
        if not match:
            raise RuntimeError(f"Missing chapter title in {path.relative_to(ROOT).as_posix()}")
        titles.append(source_title_to_outline(match.group(1)))
    return tuple(titles)


def chinese_chapter_titles() -> tuple[str, ...]:
    text = strip_tex_comments((BOOK_DIR / "book_zh.tex").read_text(encoding="utf-8"))
    return tuple(
        source_title_to_outline(match.group(1))
        for match in CHAPTER_RE.finditer(text)
        if not match.group(1).startswith("附录")
    )


def matching_positions(
    entries: list[BookmarkEntry],
    expected: ExpectedBookmark,
    *,
    after: int = -1,
) -> list[int]:
    expected_key = title_key(expected.title)
    return [
        index
        for index, entry in enumerate(entries)
        if index > after
        and title_key(entry.title) == expected_key
        and (expected.level is None or entry.level == expected.level)
    ]


def check_hierarchy(entries: list[BookmarkEntry], label: str, errors: list[str]) -> None:
    by_destination: dict[str, int] = {}
    for index, entry in enumerate(entries):
        if entry.destination in by_destination:
            previous = entries[by_destination[entry.destination]]
            errors.append(
                f"{label}: duplicate outline destination {entry.destination!r} "
                f"at lines {previous.line_no} and {entry.line_no}"
            )
        by_destination[entry.destination] = index

    for index, entry in enumerate(entries):
        if not entry.parent:
            continue
        parent_index = by_destination.get(entry.parent)
        if parent_index is None:
            errors.append(
                f"{label}: bookmark {entry.title!r} points to missing parent destination {entry.parent!r}"
            )
            continue
        parent = entries[parent_index]
        if parent_index >= index:
            errors.append(f"{label}: bookmark {entry.title!r} appears before its parent {parent.title!r}")
        if entry.level <= parent.level:
            errors.append(
                f"{label}: bookmark {entry.title!r} level {entry.level} "
                f"is not deeper than parent {parent.title!r} level {parent.level}"
            )


def check_outline(spec: OutlineSpec) -> list[str]:
    entries, errors = parse_outline(spec.path)
    if not entries:
        return errors or [f"{spec.label}: no bookmarks found"]

    if len(entries) < spec.min_bookmarks:
        errors.append(f"{spec.label}: has {len(entries)} bookmarks, expected at least {spec.min_bookmarks}")

    check_hierarchy(entries, spec.label, errors)

    part_count = sum(1 for entry in entries if entry.level == -1)
    if part_count != spec.expected_part_count:
        errors.append(f"{spec.label}: has {part_count} part bookmarks, expected {spec.expected_part_count}")

    last_position = -1
    for expected in spec.expected_order:
        positions = matching_positions(entries, expected, after=last_position)
        if not positions:
            level_note = f" at level {expected.level}" if expected.level is not None else ""
            errors.append(f"{spec.label}: missing ordered bookmark {expected.title!r}{level_note}")
            continue
        last_position = positions[0]

    for title in spec.chapter_titles:
        matches = matching_positions(entries, ExpectedBookmark(title, 0))
        if len(matches) != 1:
            errors.append(f"{spec.label}: chapter bookmark {title!r} has {len(matches)} level-0 matches")
            continue
        entry = entries[matches[0]]
        if not entry.parent:
            errors.append(f"{spec.label}: chapter bookmark {title!r} is not nested under a part")
            continue
        parent = next((candidate for candidate in entries if candidate.destination == entry.parent), None)
        if parent is None or parent.level != -1:
            errors.append(f"{spec.label}: chapter bookmark {title!r} parent is not a part bookmark")

    print(
        f"{spec.path.name}: {len(entries)} bookmarks, "
        f"{len(spec.chapter_titles)} chapter bookmarks, {part_count} part bookmarks"
    )
    return errors


def main() -> int:
    try:
        english_titles = english_chapter_titles()
        chinese_titles = chinese_chapter_titles()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    english = OutlineSpec(
        label="English outline",
        path=BOOK_DIR / "book.out",
        expected_part_count=4,
        min_bookmarks=60,
        chapter_titles=english_titles,
        expected_order=(
            ExpectedBookmark("Preface", 0),
            ExpectedBookmark("Declarations, Provenance, and Responsible Use", 0),
            ExpectedBookmark("Contents", 0),
            ExpectedBookmark("Acronyms", 0),
            ExpectedBookmark("Part I Foundations", -1),
            *(ExpectedBookmark(title, 0) for title in english_titles[:2]),
            ExpectedBookmark("Part II Architectures, Optimization, and Systems", -1),
            *(ExpectedBookmark(title, 0) for title in english_titles[2:8]),
            ExpectedBookmark("Part III Adaptation", -1),
            *(ExpectedBookmark(title, 0) for title in english_titles[8:11]),
            ExpectedBookmark("Part IV Alignment, Applications, and Evaluation", -1),
            *(ExpectedBookmark(title, 0) for title in english_titles[11:]),
            ExpectedBookmark("Appendix: Reproducibility and Notation Conventions", 0),
            ExpectedBookmark("Glossary", 0),
            ExpectedBookmark("References", 0),
            ExpectedBookmark("Index", 0),
        ),
    )

    chinese = OutlineSpec(
        label="Chinese outline",
        path=BOOK_DIR / "book_zh.out",
        expected_part_count=4,
        min_bookmarks=60,
        chapter_titles=chinese_titles,
        expected_order=(
            ExpectedBookmark("前言", 0),
            ExpectedBookmark("伦理与来源说明", 0),
            ExpectedBookmark("目录", 0),
            ExpectedBookmark("第一部分 基础", -1),
            *(ExpectedBookmark(title, 0) for title in chinese_titles[:2]),
            ExpectedBookmark("第二部分 架构、优化与系统", -1),
            *(ExpectedBookmark(title, 0) for title in chinese_titles[2:8]),
            ExpectedBookmark("第三部分 适配", -1),
            *(ExpectedBookmark(title, 0) for title in chinese_titles[8:11]),
            ExpectedBookmark("第四部分 对齐、应用与评测", -1),
            *(ExpectedBookmark(title, 0) for title in chinese_titles[11:]),
            ExpectedBookmark("附录：记号、实验记录与术语", 0),
            ExpectedBookmark("术语表", 1),
            ExpectedBookmark("参考文献", 0),
        ),
    )

    errors = [error for spec in (english, chinese) for error in check_outline(spec)]
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("PDF outline checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

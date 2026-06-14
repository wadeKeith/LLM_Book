#!/usr/bin/env python3
"""Check that the local source inventory matches the current source workspace."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path(os.environ.get("SOURCE_ROOT", ROOT.parent)).resolve()
SOURCE_NOTE = ROOT / "notes" / "source_inventory.md"
PROVENANCE_SUFFIXES = {".ipynb", ".md", ".py", ".rst", ".tex", ".txt"}
PROVENANCE_MAX_SOURCE_BYTES = int(os.environ.get("PROVENANCE_MAX_SOURCE_BYTES", "5000000"))


@dataclass(frozen=True)
class OversizeReadableFile:
    relative_path: str
    size_bytes: int


@dataclass(frozen=True)
class InventoryStats:
    total_files: int
    suffix_counts: dict[str, int]
    provenance_readable_files: int
    oversize_readable_files: tuple[OversizeReadableFile, ...]


def rel(path: Path, parent: Path = ROOT) -> str:
    return path.relative_to(parent).as_posix()


def is_inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def is_source_inventory_file(path: Path) -> bool:
    resolved = path.resolve()
    if is_inside(resolved, ROOT):
        return False
    relative_parts = path.relative_to(SOURCE_ROOT).parts
    return not any(part.startswith(".") or part == "__pycache__" for part in relative_parts)


def collect_stats() -> InventoryStats:
    if not SOURCE_ROOT.exists():
        raise RuntimeError(f"SOURCE_ROOT does not exist: {SOURCE_ROOT}")

    total_files = 0
    suffix_counts: dict[str, int] = {}
    provenance_readable_files = 0
    oversize_readable_files: list[OversizeReadableFile] = []

    for path in SOURCE_ROOT.rglob("*"):
        if not path.is_file() or not is_source_inventory_file(path):
            continue

        total_files += 1
        suffix = path.suffix.lower()
        suffix_counts[suffix] = suffix_counts.get(suffix, 0) + 1

        if suffix in PROVENANCE_SUFFIXES:
            size_bytes = path.stat().st_size
            if size_bytes > PROVENANCE_MAX_SOURCE_BYTES:
                oversize_readable_files.append(
                    OversizeReadableFile(
                        relative_path=path.relative_to(SOURCE_ROOT).as_posix(),
                        size_bytes=size_bytes,
                    )
                )
            else:
                provenance_readable_files += 1

    return InventoryStats(
        total_files=total_files,
        suffix_counts=suffix_counts,
        provenance_readable_files=provenance_readable_files,
        oversize_readable_files=tuple(
            sorted(oversize_readable_files, key=lambda item: item.relative_path)
        ),
    )


def require_snippet(text: str, snippet: str, errors: list[str]) -> None:
    if snippet not in text:
        errors.append(f"{rel(SOURCE_NOTE)}: missing current source-inventory snippet {snippet!r}")


def check_note(stats: InventoryStats, errors: list[str]) -> None:
    if not SOURCE_NOTE.exists():
        errors.append(f"Missing source inventory note: {rel(SOURCE_NOTE)}")
        return

    text = SOURCE_NOTE.read_text(encoding="utf-8")
    oversize_count = len(stats.oversize_readable_files)
    snippets = [
        "exclude `LLM_Book`",
        f"{stats.total_files:,} regular source-root files",
        f"{stats.suffix_counts.get('.mp4', 0):,} MP4 files",
        f"{stats.suffix_counts.get('.pdf', 0):,} PDF files",
        f"{stats.suffix_counts.get('.pptx', 0):,} PPTX slide decks",
        f"{stats.suffix_counts.get('.py', 0):,} Python files",
        f"{stats.suffix_counts.get('.ipynb', 0):,} notebooks",
        f"{stats.suffix_counts.get('.md', 0):,} Markdown files",
        f"{stats.suffix_counts.get('.txt', 0):,} text files",
        f"{stats.provenance_readable_files:,} provenance-readable text/code files",
        f"{oversize_count:,} readable files exceeded the {PROVENANCE_MAX_SOURCE_BYTES:,} byte provenance-scan cap",
    ]
    for snippet in snippets:
        require_snippet(text, snippet, errors)
    for item in stats.oversize_readable_files:
        require_snippet(text, f"`{item.relative_path}` ({item.size_bytes:,} bytes)", errors)


def main() -> int:
    errors: list[str] = []

    try:
        stats = collect_stats()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    check_note(stats, errors)

    print(f"source root: {SOURCE_ROOT}")
    print(f"source-root regular files inventoried: {stats.total_files}")
    print(
        "source inventory counts: "
        f"mp4={stats.suffix_counts.get('.mp4', 0)} "
        f"pdf={stats.suffix_counts.get('.pdf', 0)} "
        f"pptx={stats.suffix_counts.get('.pptx', 0)} "
        f"py={stats.suffix_counts.get('.py', 0)} "
        f"ipynb={stats.suffix_counts.get('.ipynb', 0)} "
        f"md={stats.suffix_counts.get('.md', 0)} "
        f"txt={stats.suffix_counts.get('.txt', 0)}"
    )
    print(f"provenance-readable text/code files: {stats.provenance_readable_files}")
    print(f"oversize readable source files skipped by provenance: {len(stats.oversize_readable_files)}")
    print(f"oversize readable source manifest entries checked: {len(stats.oversize_readable_files)}")

    if errors:
        print("source inventory check failures")
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("source inventory checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

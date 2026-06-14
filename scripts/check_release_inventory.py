#!/usr/bin/env python3
"""Check that release-workspace files are documented by the inventory."""

from __future__ import annotations

import fnmatch
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_NOTE = ROOT / "notes" / "release_inventory.md"

IGNORED_BUILD_FILE_PATTERNS = {
    "*.aux",
    "*.bbl",
    "*.blg",
    "*.fdb_latexmk",
    "*.fls",
    "*.idx",
    "*.ilg",
    "*.ind",
    "*.lof",
    "*.log",
    "*.lot",
    "*.out",
    "*.synctex.gz",
    "*.toc",
    "*.xdv",
    "DescriptionTexts.txt",
    ".DS_Store",
    "*.pyc",
}


@dataclass(frozen=True)
class InventoryCategory:
    name: str
    patterns: tuple[str, ...]


CATEGORIES = (
    InventoryCategory(
        "release instructions and repository controls",
        (".gitignore", ".nojekyll", "CITATION.cff", "Makefile", "README.md"),
    ),
    InventoryCategory(
        "publication website assets",
        ("index.html", "assets/site.css", "assets/*.png"),
    ),
    InventoryCategory(
        "Springer template package",
        (
            "SNmono.cls",
            "book/SNmono.cls",
            "book/spbasic.bst",
            "book/spmpsci.bst",
            "book/spphys.bst",
            "book/svind.ist",
            "book/svindd.ist",
            "history.txt",
            "readme.txt",
            "instructions.pdf",
        ),
    ),
    InventoryCategory(
        "English and Chinese manuscript sources",
        (
            "book/book.tex",
            "book/book_zh.tex",
            "book/preface.tex",
            "book/ethics.tex",
            "book/acronym.tex",
            "book/glossary.tex",
            "book/appendix.tex",
            "book/chapters/ch*.tex",
            "book/references.bib",
        ),
    ),
    InventoryCategory(
        "rendered release PDFs",
        ("book/book.pdf", "book/book_zh.pdf"),
    ),
    InventoryCategory(
        "publication audit notes",
        ("notes/*.md",),
    ),
    InventoryCategory(
        "release audit scripts",
        ("scripts/*.py",),
    ),
)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def is_under(path: Path, directory: str) -> bool:
    return directory in path.relative_to(ROOT).parts


def is_ignored_build_file(path: Path) -> bool:
    relative = rel(path)
    if is_under(path, ".git") or is_under(path, "__pycache__"):
        return True
    return any(fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(relative, pattern) for pattern in IGNORED_BUILD_FILE_PATTERNS)


def matched_categories(relative: str) -> list[str]:
    matches: list[str] = []
    for category in CATEGORIES:
        if any(fnmatch.fnmatch(relative, pattern) for pattern in category.patterns):
            matches.append(category.name)
    return matches


def release_files() -> tuple[list[Path], int]:
    files: list[Path] = []
    ignored = 0
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if is_ignored_build_file(path):
            ignored += 1
            continue
        files.append(path)
    return files, ignored


def check_files(errors: list[str]) -> tuple[int, int]:
    files, ignored = release_files()
    for path in files:
        relative = rel(path)
        matches = matched_categories(relative)
        if not matches:
            errors.append(f"Uninventoried release file: {relative}")
        elif len(matches) > 1:
            errors.append(f"Release file matches multiple inventory categories: {relative} -> {', '.join(matches)}")

    return len(files), ignored


def check_required_patterns(errors: list[str]) -> None:
    all_release_files = [rel(path) for path in release_files()[0]]
    for category in CATEGORIES:
        for pattern in category.patterns:
            if not any(fnmatch.fnmatch(relative, pattern) for relative in all_release_files):
                errors.append(f"Inventory pattern has no release file match: {pattern}")


def check_inventory_note(errors: list[str]) -> None:
    if not INVENTORY_NOTE.exists():
        errors.append(f"Missing release inventory note: {rel(INVENTORY_NOTE)}")
        return

    text = INVENTORY_NOTE.read_text(encoding="utf-8")
    required_snippets = [
        "Release Inventory",
        "Publication website assets",
        "Springer template package",
        "English and Chinese manuscript sources",
        "Rendered release PDFs",
        "Publication audit notes",
        "Release audit scripts",
        "No external figures, screenshots, datasets, model weights, model outputs, or code listings",
    ]
    for snippet in required_snippets:
        if snippet not in text:
            errors.append(f"{rel(INVENTORY_NOTE)} is missing inventory snippet: {snippet}")


def main() -> int:
    errors: list[str] = []
    checked_files, ignored_files = check_files(errors)
    check_required_patterns(errors)
    check_inventory_note(errors)

    print(f"release files inventoried: {checked_files}")
    print(f"build/private files ignored: {ignored_files}")
    print(f"inventory categories checked: {len(CATEGORIES)}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("release inventory checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

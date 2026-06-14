#!/usr/bin/env python3
"""Check that ignored build and desktop artifacts were removed after cleanup."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
SCRIPTS_DIR = ROOT / "scripts"
LATEX_SUFFIXES = {
    ".aux",
    ".bbl",
    ".blg",
    ".fdb_latexmk",
    ".fls",
    ".idx",
    ".ilg",
    ".ind",
    ".lof",
    ".log",
    ".lot",
    ".out",
    ".toc",
    ".xdv",
}
LATEX_NAMES = {
    "DescriptionTexts.txt",
}
DESKTOP_NAMES = {
    ".DS_Store",
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def latex_artifacts() -> list[Path]:
    artifacts: list[Path] = []
    for path in BOOK_DIR.rglob("*"):
        if not path.is_file():
            continue
        if path.name in LATEX_NAMES or path.suffix in LATEX_SUFFIXES or path.name.endswith(".synctex.gz"):
            artifacts.append(path)
    return artifacts


def python_cache_artifacts() -> list[Path]:
    return [path for path in SCRIPTS_DIR.rglob("__pycache__") if path.is_dir()]


def desktop_artifacts() -> list[Path]:
    return [path for path in ROOT.rglob("*") if path.name in DESKTOP_NAMES]


def main() -> int:
    artifacts = sorted(latex_artifacts() + python_cache_artifacts() + desktop_artifacts())

    if artifacts:
        print("clean artifacts remain:", file=sys.stderr)
        for path in artifacts:
            print(rel(path), file=sys.stderr)
        return 1

    print("clean artifact check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

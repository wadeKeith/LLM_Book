#!/usr/bin/env python3
"""Check repository-level release hygiene for the manuscript workspace."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
ENGLISH_ROOT = BOOK_DIR / "book.tex"
README = ROOT / "README.md"
GITIGNORE = ROOT / ".gitignore"

REQUIRED_TEMPLATE_FILES = [
    ROOT / "SNmono.cls",
    ROOT / "instructions.pdf",
    ROOT / "history.txt",
    ROOT / "readme.txt",
    BOOK_DIR / "SNmono.cls",
    BOOK_DIR / "spbasic.bst",
    BOOK_DIR / "spmpsci.bst",
    BOOK_DIR / "spphys.bst",
    BOOK_DIR / "svind.ist",
    BOOK_DIR / "svindd.ist",
]
REQUIRED_GITIGNORE_PATTERNS = {
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
    "__pycache__/",
    "*.pyc",
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def check_template_files(errors: list[str]) -> None:
    for path in REQUIRED_TEMPLATE_FILES:
        if not path.exists():
            errors.append(f"Missing required release/template file: {rel(path)}")
        elif path.is_file() and path.stat().st_size == 0:
            errors.append(f"Required release/template file is empty: {rel(path)}")

    root_cls = ROOT / "SNmono.cls"
    book_cls = BOOK_DIR / "SNmono.cls"
    if root_cls.exists() and book_cls.exists() and sha256(root_cls) != sha256(book_cls):
        errors.append("SNmono template copies differ: SNmono.cls and book/SNmono.cls")


def check_root_configuration(errors: list[str]) -> None:
    text = strip_tex_comments(ENGLISH_ROOT.read_text(encoding="utf-8"))
    if not re.search(r"\\documentclass(?:\[[^\]]*\])?\{SNmono\}", text):
        errors.append("book/book.tex must use the local SNmono document class")
    if r"\bibliographystyle{spmpsci}" not in text:
        errors.append("book/book.tex must use the spmpsci bibliography style")
    if r"\bibliography{references}" not in text:
        errors.append("book/book.tex must use the local references.bib bibliography")


def check_gitignore(errors: list[str]) -> None:
    patterns = {line.strip() for line in GITIGNORE.read_text(encoding="utf-8").splitlines() if line.strip()}
    missing = sorted(REQUIRED_GITIGNORE_PATTERNS - patterns)
    for pattern in missing:
        errors.append(f".gitignore is missing required release-artifact pattern: {pattern}")


def check_readme(errors: list[str]) -> None:
    text = README.read_text(encoding="utf-8")
    required_snippets = [
        "book/book.tex",
        "book/book_zh.tex",
        "make manuscript-audit",
        "make clean-check",
    ]
    for snippet in required_snippets:
        if snippet not in text:
            errors.append(f"README.md is missing release instruction snippet: {snippet}")


def main() -> int:
    errors: list[str] = []
    check_template_files(errors)
    check_root_configuration(errors)
    check_gitignore(errors)
    check_readme(errors)

    print(f"release/template files checked: {len(REQUIRED_TEMPLATE_FILES)}")
    print(f"required .gitignore patterns checked: {len(REQUIRED_GITIGNORE_PATTERNS)}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("repository hygiene checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

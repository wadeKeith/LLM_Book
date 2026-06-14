#!/usr/bin/env python3
"""Check for hard provenance-boundary regressions.

This gate is intentionally conservative: it detects long exact English-word and
CJK-character overlap between the manuscript and local source text/code files.
Such overlap is a strong signal of copied prose or copied code comments. It is
not a substitute for a legal or human permissions review of PDFs, slides,
figures, or datasets.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
CHAPTER_DIR = BOOK_DIR / "chapters"
SOURCE_ROOT = Path(os.environ.get("SOURCE_ROOT", ROOT.parent)).resolve()
NGRAM_WORDS = int(os.environ.get("PROVENANCE_NGRAM_WORDS", "18"))
CJK_CHARS = int(os.environ.get("PROVENANCE_CJK_CHARS", "60"))
MAX_SOURCE_BYTES = int(os.environ.get("PROVENANCE_MAX_SOURCE_BYTES", "5000000"))
MAX_REPORTED_HITS = 20

MANUSCRIPT_TEX_FILES = [
    BOOK_DIR / "book.tex",
    BOOK_DIR / "book_zh.tex",
    BOOK_DIR / "preface.tex",
    BOOK_DIR / "ethics.tex",
    BOOK_DIR / "acronym.tex",
    BOOK_DIR / "glossary.tex",
    BOOK_DIR / "appendix.tex",
    *sorted(CHAPTER_DIR.glob("*.tex")),
]
SOURCE_SUFFIXES = {".ipynb", ".md", ".py", ".rst", ".tex", ".txt"}
WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9'-]{2,}")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
DROP_TEX_COMMAND_RE = re.compile(
    r"\\(?:cite|citep|citet|citealp|citeauthor|citeyear|nocite|label|ref|eqref|"
    r"autoref|nameref|cref|Cref|index|url|href)\s*(?:\[[^\]]*\]\s*){0,2}\{[^{}]*\}"
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


def clean_tex_line(line: str) -> str:
    line = DROP_TEX_COMMAND_RE.sub(" ", line)
    line = re.sub(r"\\[A-Za-z]+[A-Za-z*]*(?:\[[^\]]*\])?", " ", line)
    return re.sub(r"[{}\\_^$&#~]", " ", line)


def word_stream(text: str) -> list[tuple[str, int]]:
    words: list[tuple[str, int]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in WORD_RE.finditer(line.lower()):
            words.append((match.group(0), line_number))
    return words


def cjk_stream(text: str) -> tuple[str, list[int]]:
    chars: list[str] = []
    lines: list[int] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in CJK_RE.finditer(line):
            chars.append(match.group(0))
            lines.append(line_number)
    return "".join(chars), lines


def manuscript_word_stream(path: Path) -> list[tuple[str, int]]:
    text = strip_tex_comments(path.read_text(encoding="utf-8"))
    cleaned = "\n".join(clean_tex_line(line) for line in text.splitlines())
    return word_stream(cleaned)


def manuscript_cjk_stream(path: Path) -> tuple[str, list[int]]:
    text = strip_tex_comments(path.read_text(encoding="utf-8"))
    cleaned = "\n".join(clean_tex_line(line) for line in text.splitlines())
    return cjk_stream(cleaned)


def read_source_text(path: Path) -> str:
    if path.suffix.lower() != ".ipynb":
        return path.read_text(encoding="utf-8", errors="ignore")

    data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    chunks: list[str] = []
    for cell in data.get("cells", []):
        source = cell.get("source", "")
        if isinstance(source, list):
            chunks.append("".join(str(part) for part in source))
        else:
            chunks.append(str(source))
    return "\n".join(chunks)


def is_inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def source_paths() -> list[Path]:
    if not SOURCE_ROOT.exists():
        raise FileNotFoundError(f"SOURCE_ROOT does not exist: {SOURCE_ROOT}")

    paths: list[Path] = []
    for path in SOURCE_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if is_inside(path.resolve(), ROOT):
            continue
        if any(part.startswith(".") for part in path.relative_to(SOURCE_ROOT).parts):
            continue
        if path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        if path.stat().st_size > MAX_SOURCE_BYTES:
            continue
        paths.append(path)
    return sorted(paths)


def manuscript_ngrams() -> dict[tuple[str, ...], tuple[str, int]]:
    ngrams: dict[tuple[str, ...], tuple[str, int]] = {}
    for path in MANUSCRIPT_TEX_FILES:
        rel = path.relative_to(ROOT).as_posix()
        words = manuscript_word_stream(path)
        for index in range(len(words) - NGRAM_WORDS + 1):
            gram = tuple(word for word, _ in words[index : index + NGRAM_WORDS])
            ngrams.setdefault(gram, (rel, words[index][1]))
    return ngrams


def manuscript_cjk_ngrams() -> dict[str, tuple[str, int]]:
    ngrams: dict[str, tuple[str, int]] = {}
    if CJK_CHARS <= 0:
        return ngrams

    for path in MANUSCRIPT_TEX_FILES:
        rel = path.relative_to(ROOT).as_posix()
        chars, lines = manuscript_cjk_stream(path)
        for index in range(len(chars) - CJK_CHARS + 1):
            gram = chars[index : index + CJK_CHARS]
            ngrams.setdefault(gram, (rel, lines[index]))
    return ngrams


def main() -> int:
    errors: list[str] = []
    word_ngrams = manuscript_ngrams()
    cjk_ngrams = manuscript_cjk_ngrams()
    scanned_sources = 0

    try:
        candidates = source_paths()
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    for path in candidates:
        try:
            source_text = read_source_text(path)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"Could not read source file {path.relative_to(SOURCE_ROOT).as_posix()}: {exc}")
            continue

        scanned_sources += 1
        words = word_stream(source_text)
        seen_in_file: set[tuple[str, ...]] = set()
        for index in range(len(words) - NGRAM_WORDS + 1):
            gram = tuple(word for word, _ in words[index : index + NGRAM_WORDS])
            if gram not in word_ngrams or gram in seen_in_file:
                continue
            seen_in_file.add(gram)
            manuscript_rel, manuscript_line = word_ngrams[gram]
            errors.append(
                f"Long exact English source overlap: {manuscript_rel}:{manuscript_line} "
                f"matches {path.relative_to(SOURCE_ROOT).as_posix()}:{words[index][1]} "
                f"({NGRAM_WORDS} words): {' '.join(gram)}"
            )
            if len(errors) >= MAX_REPORTED_HITS:
                break

        if len(errors) >= MAX_REPORTED_HITS:
            break

        chars, lines = cjk_stream(source_text)
        seen_cjk_in_file: set[str] = set()
        for index in range(len(chars) - CJK_CHARS + 1):
            gram = chars[index : index + CJK_CHARS]
            if gram not in cjk_ngrams or gram in seen_cjk_in_file:
                continue
            seen_cjk_in_file.add(gram)
            manuscript_rel, manuscript_line = cjk_ngrams[gram]
            errors.append(
                f"Long exact CJK source overlap: {manuscript_rel}:{manuscript_line} "
                f"matches {path.relative_to(SOURCE_ROOT).as_posix()}:{lines[index]} "
                f"({CJK_CHARS} Han chars): {gram}"
            )
            if len(errors) >= MAX_REPORTED_HITS:
                break
        if len(errors) >= MAX_REPORTED_HITS:
            break

    print(f"manuscript TeX files checked: {len(MANUSCRIPT_TEX_FILES)}")
    print(f"external source text files scanned: {scanned_sources}")
    print(f"manuscript {NGRAM_WORDS}-word shingles: {len(word_ngrams)}")
    print(f"manuscript {CJK_CHARS}-Han-character shingles: {len(cjk_ngrams)}")
    print(f"long exact source-overlap hits: {len(errors)}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("provenance boundary checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

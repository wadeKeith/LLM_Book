#!/usr/bin/env python3
"""Check that the TOC review note matches the current manuscript structure."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
CHAPTER_DIR = BOOK_DIR / "chapters"
EN_ROOT = BOOK_DIR / "book.tex"
TOC_REVIEW = ROOT / "notes" / "toc_review.md"
EXPECTED_CHAPTERS = 17

CHAPTER_RE = re.compile(r"\\chapter\{([^{}]+)\}")
INCLUDE_RE = re.compile(r"\\include\{chapters/([^{}]+)\}")
NUMBERED_RE = re.compile(r"^(\d+)\.\s+(.+?)\s*$", re.MULTILINE)


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


def normalize_title(title: str) -> str:
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
    title = title.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", title).strip()


def section(text: str, heading: str) -> str | None:
    start_match = re.search(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE)
    if not start_match:
        return None
    next_match = re.search(r"^##\s+", text[start_match.end() :], re.MULTILINE)
    end = start_match.end() + next_match.start() if next_match else len(text)
    return text[start_match.end() : end]


def manuscript_chapter_titles() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    root_text = strip_tex_comments(EN_ROOT.read_text(encoding="utf-8"))
    includes = INCLUDE_RE.findall(root_text)
    titles: list[str] = []

    for stem in includes:
        path = CHAPTER_DIR / f"{stem}.tex"
        if not path.exists():
            errors.append(f"{path.relative_to(ROOT).as_posix()}: missing included chapter file")
            continue
        text = strip_tex_comments(path.read_text(encoding="utf-8"))
        match = CHAPTER_RE.search(text)
        if not match:
            errors.append(f"{path.relative_to(ROOT).as_posix()}: missing chapter title")
            continue
        titles.append(normalize_title(match.group(1)))

    return titles, errors


def toc_review_titles() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    if not TOC_REVIEW.exists():
        return [], [f"{TOC_REVIEW.relative_to(ROOT).as_posix()}: missing TOC review note"]

    text = TOC_REVIEW.read_text(encoding="utf-8")
    block = section(text, "Converged Structure")
    if block is None:
        return [], [f"{TOC_REVIEW.relative_to(ROOT).as_posix()}: missing Converged Structure section"]

    matches = NUMBERED_RE.findall(block)
    if not matches:
        return [], [f"{TOC_REVIEW.relative_to(ROOT).as_posix()}: missing numbered chapter list"]

    numbers = [int(number) for number, _title in matches]
    expected_numbers = list(range(1, len(matches) + 1))
    if numbers != expected_numbers:
        errors.append(
            f"{TOC_REVIEW.relative_to(ROOT).as_posix()}: numbered chapter list is not consecutive; "
            f"expected {expected_numbers}, found {numbers}"
        )

    titles = [normalize_title(title) for _number, title in matches]
    if len(set(titles)) != len(titles):
        errors.append(f"{TOC_REVIEW.relative_to(ROOT).as_posix()}: duplicate chapter title in TOC review")

    if "17 chapters" not in block:
        errors.append(f"{TOC_REVIEW.relative_to(ROOT).as_posix()}: Converged Structure must state 17 chapters")

    return titles, errors


def main() -> int:
    manuscript_titles, manuscript_errors = manuscript_chapter_titles()
    review_titles, review_errors = toc_review_titles()
    errors = manuscript_errors + review_errors

    if len(manuscript_titles) != EXPECTED_CHAPTERS:
        errors.append(f"English manuscript has {len(manuscript_titles)} chapters, expected {EXPECTED_CHAPTERS}")
    if len(review_titles) != EXPECTED_CHAPTERS:
        errors.append(f"TOC review documents {len(review_titles)} chapters, expected {EXPECTED_CHAPTERS}")
    if manuscript_titles and review_titles and manuscript_titles != review_titles:
        errors.append(
            "notes/toc_review.md: converged chapter list does not match book/book.tex order:\n"
            f"expected: {manuscript_titles}\n"
            f"found:    {review_titles}"
        )

    print(f"TOC review documented chapters: {len(review_titles)}")
    print(f"English manuscript chapters matched: {len(manuscript_titles)}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("TOC review checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

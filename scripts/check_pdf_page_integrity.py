#!/usr/bin/env python3
"""Check all rendered PDF pages for extraction and blank-page regressions."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"


@dataclass(frozen=True)
class PdfPageSpec:
    label: str
    path: Path
    max_blank_pages: int
    allow_even_blank_pages: bool
    expected_blank_pages: tuple[int, ...]
    expected_low_text_pages: tuple[int, ...]


SPECS = (
    PdfPageSpec(
        label="English PDF",
        path=BOOK_DIR / "book.pdf",
        max_blank_pages=30,
        allow_even_blank_pages=True,
        expected_blank_pages=(
            2, 4, 6, 16, 18, 26, 36, 38, 76, 92, 106, 136, 138, 178, 194,
        ),
        expected_low_text_pages=(17, 105),
    ),
    PdfPageSpec(
        label="Chinese PDF",
        path=BOOK_DIR / "book_zh.pdf",
        max_blank_pages=0,
        allow_even_blank_pages=False,
        expected_blank_pages=(),
        expected_low_text_pages=(2, 18, 19, 42, 139, 183),
    ),
)


def require_executable(env_name: str, default: str) -> str:
    executable = os.environ.get(env_name, default)
    if shutil.which(executable) is None:
        raise RuntimeError(f"{executable} is required for PDF page integrity checks")
    return executable


def pdf_page_count(pdfinfo: str, path: Path) -> int:
    result = subprocess.run(
        [pdfinfo, str(path)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pdfinfo failed for {path.relative_to(ROOT)}: {result.stderr.strip()}")

    match = re.search(r"^Pages:\s+(\d+)\s*$", result.stdout, re.MULTILINE)
    if not match:
        raise RuntimeError(f"could not parse page count from pdfinfo output for {path.relative_to(ROOT)}")
    return int(match.group(1))


def extracted_pages(pdftotext: str, path: Path) -> list[str]:
    result = subprocess.run(
        [pdftotext, "-layout", str(path), "-"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pdftotext failed for {path.relative_to(ROOT)}: {result.stderr.strip()}")

    pages = result.stdout.split("\f")
    if pages and pages[-1].strip() == "":
        pages.pop()
    return pages


def text_char_count(page: str) -> int:
    return len(re.sub(r"\s+", "", page))


def consecutive(values: list[int]) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    if not values:
        return runs

    start = values[0]
    previous = values[0]
    for value in values[1:]:
        if value == previous + 1:
            previous = value
            continue
        if previous > start:
            runs.append((start, previous))
        start = previous = value
    if previous > start:
        runs.append((start, previous))
    return runs


def check_pdf(pdfinfo: str, pdftotext: str, spec: PdfPageSpec) -> list[str]:
    errors: list[str] = []
    if not spec.path.exists():
        return [f"missing PDF: {spec.path.relative_to(ROOT).as_posix()}"]

    expected_pages = pdf_page_count(pdfinfo, spec.path)
    pages = extracted_pages(pdftotext, spec.path)
    if len(pages) != expected_pages:
        errors.append(
            f"{spec.label}: pdftotext extracted {len(pages)} pages, "
            f"but pdfinfo reports {expected_pages}"
        )

    counts = [text_char_count(page) for page in pages]
    blank_pages = [index for index, count in enumerate(counts, start=1) if count == 0]
    if len(blank_pages) > spec.max_blank_pages:
        errors.append(
            f"{spec.label}: has {len(blank_pages)} blank extracted pages, "
            f"maximum allowed is {spec.max_blank_pages}: {blank_pages}"
        )

    unexpected_blank_pages = [
        page for page in blank_pages if not (spec.allow_even_blank_pages and page % 2 == 0)
    ]
    if unexpected_blank_pages:
        errors.append(f"{spec.label}: unexpected blank pages: {unexpected_blank_pages}")

    expected_blank_pages = list(spec.expected_blank_pages)
    if blank_pages != expected_blank_pages:
        errors.append(
            f"{spec.label}: blank-page set changed, expected {expected_blank_pages}, "
            f"found {blank_pages}"
        )

    blank_runs = consecutive(blank_pages)
    if blank_runs:
        formatted = ", ".join(f"{start}-{end}" for start, end in blank_runs)
        errors.append(f"{spec.label}: consecutive blank-page runs found: {formatted}")

    nonblank_counts = [count for count in counts if count > 0]
    if not nonblank_counts:
        errors.append(f"{spec.label}: no nonblank extracted pages")
        min_nonblank = 0
        low_pages: list[int] = []
    else:
        min_nonblank = min(nonblank_counts)
        low_pages = [index for index, count in enumerate(counts, start=1) if 0 < count < 20]

    expected_low_pages = list(spec.expected_low_text_pages)
    if low_pages != expected_low_pages:
        errors.append(
            f"{spec.label}: low-text page set changed, expected {expected_low_pages}, "
            f"found {low_pages}"
        )

    if not errors:
        blank_note = (
            f"{len(blank_pages)} even blank pages"
            if spec.allow_even_blank_pages
            else f"{len(blank_pages)} blank pages"
        )
        low_note = f", low-text pages {low_pages}" if low_pages else ""
        print(
            f"{spec.label}: {len(pages)} pages checked, {blank_note}, "
            f"minimum nonblank page text {min_nonblank} chars{low_note}"
        )
    return errors


def main() -> int:
    try:
        pdfinfo = require_executable("PDFINFO", "pdfinfo")
        pdftotext = require_executable("PDFTOTEXT", "pdftotext")
        errors = [error for spec in SPECS for error in check_pdf(pdfinfo, pdftotext, spec)]
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("PDF page integrity checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Check rendered PDF reference locators for publication-safe output."""

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
PDFTOTEXT = os.environ.get("PDFTOTEXT", "pdftotext")

DOI_COMPACT = "DOI10.6028/NIST.AI.100-4"
DOI_RESOLVER_COMPACT = "https://doi.org/10.6028/NIST.AI.100-4"
HTTP_EXCEPTION_COMPACT = "URLhttp://incompleteideas.net/book/the-book-2nd.html"


@dataclass(frozen=True)
class PdfSpec:
    label: str
    path: Path
    bbl_path: Path
    reference_heading: str
    end_heading: str | None
    label_pattern: re.Pattern[str]


PDFS = (
    PdfSpec(
        "English PDF",
        BOOK_DIR / "book.pdf",
        BOOK_DIR / "book.bbl",
        "References",
        "Index",
        re.compile(r"(?m)^\s*(?P<number>\d{1,3})\.\s+"),
    ),
    PdfSpec(
        "Chinese PDF",
        BOOK_DIR / "book_zh.pdf",
        BOOK_DIR / "book_zh.bbl",
        "参考文献",
        None,
        re.compile(r"(?m)^\s*\[(?P<number>\d{1,3})\]\s+"),
    ),
)
BIBITEM_RE = re.compile(r"\\bibitem(?:\[[^\]]*\])?\{[^{}]+\}")


def require_pdftotext() -> None:
    if shutil.which(PDFTOTEXT) is None:
        raise RuntimeError(f"{PDFTOTEXT} is required for rendered reference checks")


def extract_text(path: Path) -> str:
    result = subprocess.run(
        [PDFTOTEXT, "-layout", str(path), "-"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"pdftotext failed for {path}")
    return result.stdout


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def expected_bibliography_count(path: Path) -> int:
    if not path.exists():
        raise RuntimeError(f"{path.relative_to(ROOT)} is missing; run `make all` first")
    return len(BIBITEM_RE.findall(path.read_text(encoding="utf-8", errors="replace")))


def rendered_reference_section(spec: PdfSpec, text: str) -> str:
    heading_re = re.compile(rf"(?m)^\s*{re.escape(spec.reference_heading)}\s*$")
    for heading_match in heading_re.finditer(text):
        section = text[heading_match.end() :]
        first_label = spec.label_pattern.search(section)
        if first_label and int(first_label.group("number")) == 1 and first_label.start() < 800:
            if spec.end_heading:
                end_match = re.search(rf"(?m)^\s*{re.escape(spec.end_heading)}\s*$", section)
                if end_match:
                    section = section[: end_match.start()]
            return section
    raise RuntimeError(f"{spec.path.relative_to(ROOT)}: could not isolate rendered reference section")


def check_rendered_bibliography(spec: PdfSpec, text: str, errors: list[str]) -> int:
    expected = expected_bibliography_count(spec.bbl_path)
    section = rendered_reference_section(spec, text)
    labels = [int(match.group("number")) for match in spec.label_pattern.finditer(section)]
    expected_labels = list(range(1, expected + 1))
    location = spec.path.relative_to(ROOT).as_posix()

    if labels != expected_labels:
        missing = sorted(set(expected_labels) - set(labels))
        extra = sorted(set(labels) - set(expected_labels))
        duplicates = sorted(label for label in set(labels) if labels.count(label) > 1)
        details = []
        if missing:
            details.append(f"missing {missing[:10]}")
        if extra:
            details.append(f"extra {extra[:10]}")
        if duplicates:
            details.append(f"duplicate {duplicates[:10]}")
        detail_text = "; ".join(details) if details else "non-contiguous or out-of-order labels"
        errors.append(
            f"{location}: rendered bibliography labels do not match "
            f"{spec.bbl_path.name} count {expected}: {detail_text}"
        )
    return len(labels)


def check_pdf(spec: PdfSpec, errors: list[str]) -> None:
    error_count = len(errors)
    if not spec.path.exists():
        errors.append(f"missing PDF: {spec.path.relative_to(ROOT).as_posix()}")
        return

    text = extract_text(spec.path)
    normalized = re.sub(r"\s+", " ", text)
    compact_text = compact(text)
    location = spec.path.relative_to(ROOT).as_posix()

    if spec.reference_heading not in text:
        errors.append(f"{location}: missing rendered reference heading {spec.reference_heading!r}")
    if "URL []" in normalized or "URL [" in normalized:
        errors.append(f"{location}: rendered URL locator contains bracket artifacts")
    if DOI_COMPACT not in compact_text:
        errors.append(f"{location}: NIST synthetic-content DOI is not rendered as a DOI locator")
    if DOI_RESOLVER_COMPACT in compact_text:
        errors.append(f"{location}: DOI resolver URL rendered where DOI locator is expected")
    if HTTP_EXCEPTION_COMPACT not in compact_text:
        errors.append(f"{location}: documented Sutton/Barto HTTP URL exception is not rendered")
    rendered_labels = check_rendered_bibliography(spec, text, errors)

    if len(errors) == error_count:
        expected = expected_bibliography_count(spec.bbl_path)
        print(
            f"{spec.path.name}: rendered reference locators checked; "
            f"bibliography labels {rendered_labels} / {expected}"
        )


def main() -> int:
    try:
        require_pdftotext()
        errors: list[str] = []
        for spec in PDFS:
            check_pdf(spec, errors)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("rendered reference locator and bibliography checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

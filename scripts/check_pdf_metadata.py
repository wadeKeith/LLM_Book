#!/usr/bin/env python3
"""Check release PDF metadata and document-level delivery properties."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
PDFINFO = os.environ.get("PDFINFO", "pdfinfo")


@dataclass(frozen=True)
class PdfExpectation:
    path: Path
    title: str
    author: str
    subject: str
    required_keywords: tuple[str, ...]
    expected_pages: int
    min_file_size: int
    max_file_size: int


EXPECTATIONS = [
    PdfExpectation(
        path=BOOK_DIR / "book.pdf",
        title="Large Language and Generative Foundation Models: Foundations, Systems, Alignment, and Applications",
        author="Cheng Yin",
        subject="Large language and generative foundation models",
        required_keywords=(
            "large language models",
            "generative foundation models",
            "transformers",
            "alignment",
            "retrieval",
            "reasoning",
            "multimodal AI",
            "evaluation",
        ),
        expected_pages=238,
        min_file_size=887_900,
        max_file_size=888_000,
    ),
    PdfExpectation(
        path=BOOK_DIR / "book_zh.pdf",
        title="大语言模型与生成式基础模型：基础、系统、对齐与应用",
        author="尹诚",
        subject="大语言模型与生成式基础模型",
        required_keywords=(
            "大语言模型",
            "生成式基础模型",
            "Transformer",
            "对齐",
            "检索增强生成",
            "推理",
            "多模态",
            "评测",
        ),
        expected_pages=308,
        min_file_size=1_593_700,
        max_file_size=1_593_950,
    ),
]


def run_pdfinfo(path: Path) -> dict[str, str]:
    result = subprocess.run(
        [PDFINFO, str(path)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"pdfinfo failed for {path}")

    fields: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


def require_field(fields: dict[str, str], name: str, path: Path, errors: list[str]) -> str:
    value = fields.get(name, "")
    if not value:
        errors.append(f"{path.relative_to(ROOT).as_posix()}: missing PDF metadata field {name}")
    return value


def require_exact(fields: dict[str, str], name: str, expected: str, path: Path, errors: list[str]) -> None:
    actual = require_field(fields, name, path, errors)
    if actual and actual != expected:
        errors.append(
            f"{path.relative_to(ROOT).as_posix()}: {name} is {actual!r}, expected {expected!r}"
        )


def require_int_exact(fields: dict[str, str], name: str, expected: int, path: Path, errors: list[str]) -> int:
    raw = require_field(fields, name, path, errors)
    if not raw:
        return 0
    try:
        value = int(raw.split()[0])
    except ValueError:
        errors.append(f"{path.relative_to(ROOT).as_posix()}: {name} is not an integer value: {raw!r}")
        return 0
    if value != expected:
        errors.append(
            f"{path.relative_to(ROOT).as_posix()}: {name} is {value}, expected {expected}"
        )
    return value


def require_int_range(
    fields: dict[str, str],
    name: str,
    minimum: int,
    maximum: int,
    path: Path,
    errors: list[str],
) -> int:
    raw = require_field(fields, name, path, errors)
    if not raw:
        return 0
    try:
        value = int(raw.split()[0])
    except ValueError:
        errors.append(f"{path.relative_to(ROOT).as_posix()}: {name} is not an integer value: {raw!r}")
        return 0
    if not minimum <= value <= maximum:
        errors.append(
            f"{path.relative_to(ROOT).as_posix()}: {name} is {value}, expected {minimum}--{maximum}"
        )
    return value


def check_keywords(fields: dict[str, str], expectation: PdfExpectation, errors: list[str]) -> None:
    keywords = require_field(fields, "Keywords", expectation.path, errors)
    for keyword in expectation.required_keywords:
        if keyword not in keywords:
            errors.append(
                f"{expectation.path.relative_to(ROOT).as_posix()}: Keywords missing {keyword!r}"
            )


def check_pdf(expectation: PdfExpectation, errors: list[str]) -> tuple[int, int]:
    if not expectation.path.exists():
        errors.append(f"missing PDF: {expectation.path.relative_to(ROOT).as_posix()}")
        return 0, 0

    fields = run_pdfinfo(expectation.path)
    require_exact(fields, "Title", expectation.title, expectation.path, errors)
    require_exact(fields, "Author", expectation.author, expectation.path, errors)
    require_exact(fields, "Subject", expectation.subject, expectation.path, errors)
    require_exact(fields, "Encrypted", "no", expectation.path, errors)
    require_exact(fields, "JavaScript", "no", expectation.path, errors)
    require_exact(fields, "Form", "none", expectation.path, errors)
    require_exact(fields, "Page size", "612 x 792 pts (letter)", expectation.path, errors)
    require_exact(fields, "Page rot", "0", expectation.path, errors)
    require_exact(fields, "PDF version", "1.7", expectation.path, errors)
    check_keywords(fields, expectation, errors)
    pages = require_int_exact(fields, "Pages", expectation.expected_pages, expectation.path, errors)
    file_size = require_int_range(
        fields,
        "File size",
        expectation.min_file_size,
        expectation.max_file_size,
        expectation.path,
        errors,
    )
    return pages, file_size


def main() -> int:
    errors: list[str] = []
    summaries: list[tuple[str, int, int]] = []

    for expectation in EXPECTATIONS:
        pages, file_size = check_pdf(expectation, errors)
        summaries.append((expectation.path.name, pages, file_size))

    for name, pages, file_size in summaries:
        print(f"{name}: {pages} pages, {file_size} bytes")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("PDF metadata checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

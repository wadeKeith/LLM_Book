#!/usr/bin/env python3
"""Check rendered PDF fonts for production-safe embedding."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
PDFFONTS = os.environ.get("PDFFONTS", "pdffonts")


@dataclass(frozen=True)
class FontRecord:
    name: str
    font_type: str
    encoding: str
    embedded: str
    subset: str
    unicode_map: str


PDFS = (
    BOOK_DIR / "book.pdf",
    BOOK_DIR / "book_zh.pdf",
)


def require_pdffonts() -> None:
    if shutil.which(PDFFONTS) is None:
        raise RuntimeError(f"{PDFFONTS} is required for PDF font checks")


def parse_font_line(line: str, path: Path) -> FontRecord:
    parts = line.split()
    if len(parts) < 8:
        raise RuntimeError(f"could not parse pdffonts output for {path.relative_to(ROOT)}: {line!r}")
    return FontRecord(
        name=parts[0],
        font_type=" ".join(parts[1:-6]),
        encoding=parts[-6],
        embedded=parts[-5],
        subset=parts[-4],
        unicode_map=parts[-3],
    )


def read_fonts(path: Path) -> list[FontRecord]:
    result = subprocess.run(
        [PDFFONTS, str(path)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"pdffonts failed for {path}")

    records: list[FontRecord] = []
    for line in result.stdout.splitlines()[2:]:
        if line.strip():
            records.append(parse_font_line(line, path))
    return records


def check_pdf(path: Path, errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"missing PDF: {path.relative_to(ROOT).as_posix()}")
        return

    fonts = read_fonts(path)
    if not fonts:
        errors.append(f"{path.relative_to(ROOT).as_posix()}: no fonts reported by pdffonts")
        return

    for font in fonts:
        location = path.relative_to(ROOT).as_posix()
        if font.font_type == "Type 3":
            errors.append(f"{location}: Type 3 font found: {font.name}")
        if font.embedded != "yes":
            errors.append(f"{location}: font is not embedded: {font.name}")
        if font.subset != "yes":
            errors.append(f"{location}: font is not subset embedded: {font.name}")
        if font.unicode_map != "yes":
            errors.append(f"{location}: font lacks Unicode mapping: {font.name}")

    font_types = ", ".join(sorted({font.font_type for font in fonts}))
    print(f"{path.name}: {len(fonts)} fonts checked ({font_types})")


def main() -> int:
    try:
        require_pdffonts()
        errors: list[str] = []
        for path in PDFS:
            check_pdf(path, errors)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("PDF font checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

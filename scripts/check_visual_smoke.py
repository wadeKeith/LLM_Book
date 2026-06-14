#!/usr/bin/env python3
"""Smoke-check sampled rendered PDF pages for blank or clipped output."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
RENDER_DPI = int(os.environ.get("VISUAL_SMOKE_DPI", "48"))
INK_THRESHOLD = int(os.environ.get("VISUAL_SMOKE_INK_THRESHOLD", "245"))
MIN_INK_RATIO = float(os.environ.get("VISUAL_SMOKE_MIN_INK_RATIO", "0.002"))
MAX_INK_RATIO = float(os.environ.get("VISUAL_SMOKE_MAX_INK_RATIO", "0.45"))


@dataclass(frozen=True)
class PdfSample:
    label: str
    path: Path
    pages: tuple[int, ...]


@dataclass(frozen=True)
class PageMetrics:
    width: int
    height: int
    ink_ratio: float
    min_edge_margin: int


SAMPLES = (
    PdfSample(
        "English PDF",
        BOOK_DIR / "book.pdf",
        (1, 9, 12, 37, 45, 75, 83, 173, 181, 217, 236),
    ),
    PdfSample(
        "Chinese PDF",
        BOOK_DIR / "book_zh.pdf",
        (1, 3, 16, 20, 25, 88, 110, 150, 165, 200, 236),
    ),
)


def require_executable(env_name: str, default: str) -> str:
    executable = os.environ.get(env_name, default)
    if shutil.which(executable) is None:
        raise RuntimeError(f"{executable} is required for visual smoke checks")
    return executable


def page_count(pdfinfo: str, path: Path) -> int:
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


def render_page(pdftoppm: str, sample: PdfSample, page: int, output_dir: Path) -> Path:
    prefix = output_dir / f"{sample.path.stem}_{page}"
    result = subprocess.run(
        [
            pdftoppm,
            "-q",
            "-r",
            str(RENDER_DPI),
            "-f",
            str(page),
            "-l",
            str(page),
            "-singlefile",
            str(sample.path),
            str(prefix),
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"pdftoppm failed for {sample.path.relative_to(ROOT)} page {page}: {result.stderr.strip()}"
        )

    rendered = prefix.with_suffix(".ppm")
    if not rendered.exists():
        raise RuntimeError(f"pdftoppm did not create expected file {rendered}")
    return rendered


def read_ppm_tokens(data: bytes) -> tuple[list[bytes], int]:
    tokens: list[bytes] = []
    index = 0
    while len(tokens) < 4:
        while index < len(data) and chr(data[index]).isspace():
            index += 1
        if index < len(data) and data[index] == ord("#"):
            while index < len(data) and data[index] not in (10, 13):
                index += 1
            continue
        start = index
        while index < len(data) and not chr(data[index]).isspace():
            index += 1
        if start == index:
            break
        tokens.append(data[start:index])

    while index < len(data) and chr(data[index]).isspace():
        index += 1
    return tokens, index


def page_metrics(ppm_path: Path) -> PageMetrics:
    data = ppm_path.read_bytes()
    tokens, pixel_start = read_ppm_tokens(data)
    if len(tokens) != 4 or tokens[0] != b"P6":
        raise RuntimeError(f"unsupported PPM header in {ppm_path}")

    width = int(tokens[1])
    height = int(tokens[2])
    max_value = int(tokens[3])
    if max_value != 255:
        raise RuntimeError(f"unsupported PPM max value {max_value} in {ppm_path}")

    pixels = data[pixel_start:]
    expected_size = width * height * 3
    if len(pixels) != expected_size:
        raise RuntimeError(f"unexpected PPM data size in {ppm_path}: {len(pixels)} != {expected_size}")

    ink_pixels = 0
    min_x = width
    max_x = -1
    min_y = height
    max_y = -1

    for offset in range(0, len(pixels), 3):
        red, green, blue = pixels[offset], pixels[offset + 1], pixels[offset + 2]
        if red < INK_THRESHOLD or green < INK_THRESHOLD or blue < INK_THRESHOLD:
            pixel_index = offset // 3
            y, x = divmod(pixel_index, width)
            ink_pixels += 1
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)

    if ink_pixels == 0:
        return PageMetrics(width, height, 0.0, 0)

    edge_margins = (min_x, min_y, width - max_x - 1, height - max_y - 1)
    return PageMetrics(
        width=width,
        height=height,
        ink_ratio=ink_pixels / (width * height),
        min_edge_margin=min(edge_margins),
    )


def check_sample(pdfinfo: str, pdftoppm: str, sample: PdfSample) -> list[str]:
    errors: list[str] = []
    if not sample.path.exists():
        return [f"missing PDF: {sample.path.relative_to(ROOT)}"]

    pages = page_count(pdfinfo, sample.path)
    for page in sample.pages:
        if page > pages:
            errors.append(f"{sample.label}: sample page {page} exceeds page count {pages}")

    if errors:
        return errors

    metrics: list[tuple[int, PageMetrics]] = []
    with tempfile.TemporaryDirectory(prefix="llm-book-visual-smoke-") as temp_name:
        temp_dir = Path(temp_name)
        for page in sample.pages:
            rendered = render_page(pdftoppm, sample, page, temp_dir)
            page_stat = page_metrics(rendered)
            metrics.append((page, page_stat))

            if page_stat.width < 250 or page_stat.height < 300:
                errors.append(
                    f"{sample.label} page {page}: rendered size is unexpectedly small "
                    f"({page_stat.width}x{page_stat.height})"
                )
            if page_stat.ink_ratio < MIN_INK_RATIO:
                errors.append(
                    f"{sample.label} page {page}: rendered page looks blank "
                    f"(ink ratio {page_stat.ink_ratio:.4f})"
                )
            if page_stat.ink_ratio > MAX_INK_RATIO:
                errors.append(
                    f"{sample.label} page {page}: rendered page is unexpectedly dense "
                    f"(ink ratio {page_stat.ink_ratio:.4f})"
                )

            required_margin = max(2, min(page_stat.width, page_stat.height) // 200)
            if page_stat.min_edge_margin < required_margin:
                errors.append(
                    f"{sample.label} page {page}: dark pixels touch the page edge "
                    f"(minimum margin {page_stat.min_edge_margin}px, expected at least {required_margin}px)"
                )

    if not errors:
        min_ratio = min(page_stat.ink_ratio for _, page_stat in metrics)
        max_ratio = max(page_stat.ink_ratio for _, page_stat in metrics)
        min_margin = min(page_stat.min_edge_margin for _, page_stat in metrics)
        print(
            f"{sample.label}: {len(metrics)} rendered pages checked, "
            f"ink ratio {min_ratio:.4f}--{max_ratio:.4f}, "
            f"minimum edge margin {min_margin}px"
        )
    return errors


def main() -> int:
    try:
        pdfinfo = require_executable("PDFINFO", "pdfinfo")
        pdftoppm = require_executable("PDFTOPPM", "pdftoppm")
        errors: list[str] = []
        for sample in SAMPLES:
            errors.extend(check_sample(pdfinfo, pdftoppm, sample))
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("visual PDF smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

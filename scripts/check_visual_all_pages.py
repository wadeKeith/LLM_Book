#!/usr/bin/env python3
"""Check every rendered PDF page for blank, dense, or edge-clipped output."""

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
RENDER_DPI = int(os.environ.get("VISUAL_FULL_DPI", "72"))
INK_THRESHOLD = int(os.environ.get("VISUAL_FULL_INK_THRESHOLD", "245"))
MIN_INK_RATIO = float(os.environ.get("VISUAL_FULL_MIN_INK_RATIO", "0.001"))
MAX_INK_RATIO = float(os.environ.get("VISUAL_FULL_MAX_INK_RATIO", "0.55"))
MAX_EXPECTED_BLANK_INK_RATIO = float(os.environ.get("VISUAL_FULL_MAX_BLANK_INK_RATIO", "0.0005"))
DARK_CHANNEL_TABLE = bytes(1 if value < INK_THRESHOLD else 0 for value in range(256))


@dataclass(frozen=True)
class PdfSpec:
    label: str
    path: Path
    expected_blank_pages: tuple[int, ...]
    expected_low_ink_pages: tuple[int, ...] = ()


@dataclass(frozen=True)
class PageMetrics:
    width: int
    height: int
    ink_ratio: float
    min_edge_margin: int | None


SPECS = (
    PdfSpec(
        label="English PDF",
        path=BOOK_DIR / "book.pdf",
        expected_blank_pages=(
            2, 4, 6, 16, 18, 26, 36, 38, 76, 92, 106, 136, 138, 178, 194,
        ),
    ),
    PdfSpec(
        label="Chinese PDF",
        path=BOOK_DIR / "book_zh.pdf",
        expected_blank_pages=(),
        expected_low_ink_pages=(2, 18),
    ),
)


def require_executable(env_name: str, default: str) -> str:
    executable = os.environ.get(env_name, default)
    if shutil.which(executable) is None:
        raise RuntimeError(f"{executable} is required for all-page visual checks")
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


def render_page(pdftoppm: str, spec: PdfSpec, page: int, output_dir: Path) -> Path:
    prefix = output_dir / f"{spec.path.stem}_{page}"
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
            str(spec.path),
            str(prefix),
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"pdftoppm failed for {spec.path.relative_to(ROOT)} page {page}: {result.stderr.strip()}"
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
    stride = width * 3
    expected_size = height * stride
    if len(pixels) != expected_size:
        raise RuntimeError(f"unexpected PPM data size in {ppm_path}: {len(pixels)} != {expected_size}")

    ink_pixels = 0
    min_x = width
    max_x = -1
    min_y = height
    max_y = -1

    for y in range(height):
        row = pixels[y * stride : (y + 1) * stride]
        dark_channels = row.translate(DARK_CHANNEL_TABLE)
        first_dark_channel = dark_channels.find(b"\x01")
        if first_dark_channel == -1:
            continue

        last_dark_channel = dark_channels.rfind(b"\x01")
        first_dark_pixel = first_dark_channel // 3
        last_dark_pixel = last_dark_channel // 3
        ink_pixels += max(1, round(dark_channels.count(1) / 3))
        min_x = min(min_x, first_dark_pixel)
        max_x = max(max_x, last_dark_pixel)
        min_y = min(min_y, y)
        max_y = max(max_y, y)

    if ink_pixels == 0:
        return PageMetrics(width=width, height=height, ink_ratio=0.0, min_edge_margin=None)

    edge_margins = (min_x, min_y, width - max_x - 1, height - max_y - 1)
    return PageMetrics(
        width=width,
        height=height,
        ink_ratio=ink_pixels / (width * height),
        min_edge_margin=min(edge_margins),
    )


def check_pdf(pdfinfo: str, pdftoppm: str, spec: PdfSpec) -> list[str]:
    errors: list[str] = []
    if not spec.path.exists():
        return [f"missing PDF: {spec.path.relative_to(ROOT).as_posix()}"]

    pages = pdf_page_count(pdfinfo, spec.path)
    expected_width = round(8.5 * RENDER_DPI)
    expected_height = round(11 * RENDER_DPI)
    required_margin = max(2, min(expected_width, expected_height) // 250)
    expected_blank_pages = set(spec.expected_blank_pages)
    expected_low_ink_pages = set(spec.expected_low_ink_pages)
    actual_blank_pages: list[int] = []
    actual_low_ink_pages: list[int] = []
    nonblank_metrics: list[PageMetrics] = []

    with tempfile.TemporaryDirectory(prefix="llm-book-visual-full-") as temp_name:
        temp_dir = Path(temp_name)
        for page in range(1, pages + 1):
            rendered = render_page(pdftoppm, spec, page, temp_dir)
            metrics = page_metrics(rendered)
            rendered.unlink(missing_ok=True)

            if metrics.width != expected_width or metrics.height != expected_height:
                errors.append(
                    f"{spec.label} page {page}: rendered size is {metrics.width}x{metrics.height}, "
                    f"expected {expected_width}x{expected_height} at {RENDER_DPI} dpi"
                )

            if page in expected_blank_pages:
                actual_blank_pages.append(page)
                if metrics.ink_ratio > MAX_EXPECTED_BLANK_INK_RATIO:
                    errors.append(
                        f"{spec.label} page {page}: expected blank page has ink ratio "
                        f"{metrics.ink_ratio:.4f}, expected at most {MAX_EXPECTED_BLANK_INK_RATIO:.4f}"
                    )
                continue

            nonblank_metrics.append(metrics)
            if page in expected_low_ink_pages:
                actual_low_ink_pages.append(page)
                if metrics.ink_ratio <= 0:
                    errors.append(f"{spec.label} page {page}: expected low-ink page is visually blank")
            elif metrics.ink_ratio < MIN_INK_RATIO:
                errors.append(f"{spec.label} page {page}: rendered page looks blank (ink ratio {metrics.ink_ratio:.4f})")
            if metrics.ink_ratio > MAX_INK_RATIO:
                errors.append(
                    f"{spec.label} page {page}: rendered page is unexpectedly dense "
                    f"(ink ratio {metrics.ink_ratio:.4f})"
                )
            if metrics.min_edge_margin is None or metrics.min_edge_margin < required_margin:
                errors.append(
                    f"{spec.label} page {page}: dark pixels touch the page edge "
                    f"(minimum margin {metrics.min_edge_margin}px, expected at least {required_margin}px)"
                )

    if actual_blank_pages != list(spec.expected_blank_pages):
        errors.append(
            f"{spec.label}: expected blank visual pages {list(spec.expected_blank_pages)}, "
            f"checked {actual_blank_pages}"
        )
    if actual_low_ink_pages != list(spec.expected_low_ink_pages):
        errors.append(
            f"{spec.label}: expected low-ink visual pages {list(spec.expected_low_ink_pages)}, "
            f"checked {actual_low_ink_pages}"
        )

    if not nonblank_metrics:
        errors.append(f"{spec.label}: no nonblank rendered pages")

    if not errors and nonblank_metrics:
        min_ratio = min(metric.ink_ratio for metric in nonblank_metrics)
        max_ratio = max(metric.ink_ratio for metric in nonblank_metrics)
        min_margin = min(metric.min_edge_margin or 0 for metric in nonblank_metrics)
        print(
            f"{spec.label}: {pages} visual pages checked at {RENDER_DPI} dpi, "
            f"{len(spec.expected_blank_pages)} expected blank pages, "
            f"{len(spec.expected_low_ink_pages)} expected low-ink pages, "
            f"nonblank ink ratio {min_ratio:.4f}--{max_ratio:.4f}, "
            f"minimum nonblank edge margin {min_margin}px"
        )

    return errors


def main() -> int:
    try:
        pdfinfo = require_executable("PDFINFO", "pdfinfo")
        pdftoppm = require_executable("PDFTOPPM", "pdftoppm")
        errors = [error for spec in SPECS for error in check_pdf(pdfinfo, pdftoppm, spec)]
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("all-page visual PDF checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

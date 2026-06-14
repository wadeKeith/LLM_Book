#!/usr/bin/env python3
"""Check the rendered PNG set produced by ``make visual-audit``."""

from __future__ import annotations

import os
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = Path(os.environ.get("VISUAL_AUDIT_DIR", "/tmp/llm_book_visual_audit"))
EXPECTED_PNGS = int(os.environ.get("VISUAL_AUDIT_EXPECTED_PNGS", "360"))
AUDIT_DPI = int(os.environ.get("VISUAL_AUDIT_DPI", "130"))
INK_THRESHOLD = int(os.environ.get("VISUAL_AUDIT_INK_THRESHOLD", "245"))
MIN_INK_RATIO = float(os.environ.get("VISUAL_AUDIT_MIN_INK_RATIO", "0.0015"))
MAX_INK_RATIO = float(os.environ.get("VISUAL_AUDIT_MAX_INK_RATIO", "0.45"))
MAX_EXPECTED_BLANK_INK_RATIO = float(os.environ.get("VISUAL_AUDIT_MAX_BLANK_INK_RATIO", "0.0005"))
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
DARK_CHANNEL_TABLE = bytes(1 if value < INK_THRESHOLD else 0 for value in range(256))


@dataclass(frozen=True)
class AuditRange:
    prefix: str
    first_page: int
    last_page: int
    expected_blank_pages: tuple[int, ...] = ()


@dataclass(frozen=True)
class PngMetrics:
    width: int
    height: int
    ink_ratio: float
    min_edge_margin: int | None


AUDIT_RANGES = (
    AuditRange("en_title", 1, 1),
    AuditRange("en_toc", 9, 12),
    AuditRange("en_architecture", 37, 45, expected_blank_pages=(38,)),
    AuditRange("en_serving", 75, 83, expected_blank_pages=(76,)),
    AuditRange("en_multimodal", 173, 181, expected_blank_pages=(178,)),
    AuditRange("en_backmatter", 217, 238),
    AuditRange("zh_title", 1, 1),
    AuditRange("zh_toc", 3, 16),
    AuditRange("zh_data", 20, 42),
    AuditRange("zh_transformer", 43, 53),
    AuditRange("zh_gpt", 54, 65),
    AuditRange("zh_llama", 66, 81),
    AuditRange("zh_optimization", 82, 96),
    AuditRange("zh_distributed", 97, 119),
    AuditRange("zh_serving", 120, 139),
    AuditRange("zh_sft", 140, 153),
    AuditRange("zh_peft", 154, 170),
    AuditRange("zh_domain", 171, 183),
    AuditRange("zh_alignment", 184, 235),
    AuditRange("zh_multimodal", 236, 253),
    AuditRange("zh_evaluation", 254, 268),
    AuditRange("zh_appendix", 279, 280),
    AuditRange("zh_backmatter", 269, 308),
)


def expected_names() -> dict[str, bool]:
    names: dict[str, bool] = {}
    for audit_range in AUDIT_RANGES:
        blanks = set(audit_range.expected_blank_pages)
        for page in range(audit_range.first_page, audit_range.last_page + 1):
            names[f"{audit_range.prefix}-{page:03d}.png"] = page in blanks
    return names


def paeth_predictor(left: int, above: int, upper_left: int) -> int:
    estimate = left + above - upper_left
    distance_left = abs(estimate - left)
    distance_above = abs(estimate - above)
    distance_upper_left = abs(estimate - upper_left)
    if distance_left <= distance_above and distance_left <= distance_upper_left:
        return left
    if distance_above <= distance_upper_left:
        return above
    return upper_left


def png_chunks(data: bytes, path: Path) -> list[tuple[bytes, bytes]]:
    if not data.startswith(PNG_SIGNATURE):
        raise RuntimeError(f"{path}: not a PNG file")

    chunks: list[tuple[bytes, bytes]] = []
    index = len(PNG_SIGNATURE)
    while index < len(data):
        if index + 12 > len(data):
            raise RuntimeError(f"{path}: truncated PNG chunk header")
        length = int.from_bytes(data[index : index + 4], "big")
        chunk_type = data[index + 4 : index + 8]
        chunk_start = index + 8
        chunk_end = chunk_start + length
        crc_end = chunk_end + 4
        if crc_end > len(data):
            raise RuntimeError(f"{path}: truncated PNG chunk {chunk_type!r}")
        chunks.append((chunk_type, data[chunk_start:chunk_end]))
        index = crc_end
        if chunk_type == b"IEND":
            break
    return chunks


def unfilter_scanlines(raw: bytes, width: int, height: int, bytes_per_pixel: int) -> list[bytes]:
    stride = width * bytes_per_pixel
    expected = height * (stride + 1)
    if len(raw) != expected:
        raise RuntimeError(f"unexpected decompressed PNG data size: {len(raw)} != {expected}")

    rows: list[bytes] = []
    previous = bytearray(stride)
    index = 0
    for _ in range(height):
        filter_type = raw[index]
        index += 1
        row = bytearray(raw[index : index + stride])
        index += stride

        if filter_type == 0:
            pass
        elif filter_type == 1:
            for i, value in enumerate(row):
                left = row[i - bytes_per_pixel] if i >= bytes_per_pixel else 0
                row[i] = (value + left) & 0xFF
        elif filter_type == 2:
            for i, value in enumerate(row):
                row[i] = (value + previous[i]) & 0xFF
        elif filter_type == 3:
            for i, value in enumerate(row):
                left = row[i - bytes_per_pixel] if i >= bytes_per_pixel else 0
                row[i] = (value + ((left + previous[i]) // 2)) & 0xFF
        elif filter_type == 4:
            for i, value in enumerate(row):
                left = row[i - bytes_per_pixel] if i >= bytes_per_pixel else 0
                upper_left = previous[i - bytes_per_pixel] if i >= bytes_per_pixel else 0
                row[i] = (value + paeth_predictor(left, previous[i], upper_left)) & 0xFF
        else:
            raise RuntimeError(f"unsupported PNG filter type {filter_type}")

        rows.append(bytes(row))
        previous = row
    return rows


def png_metrics(path: Path) -> PngMetrics:
    chunks = png_chunks(path.read_bytes(), path)
    ihdr = next((chunk_data for chunk_type, chunk_data in chunks if chunk_type == b"IHDR"), None)
    if ihdr is None:
        raise RuntimeError(f"{path}: missing PNG IHDR chunk")
    if len(ihdr) != 13:
        raise RuntimeError(f"{path}: malformed PNG IHDR chunk")

    width = int.from_bytes(ihdr[0:4], "big")
    height = int.from_bytes(ihdr[4:8], "big")
    bit_depth = ihdr[8]
    color_type = ihdr[9]
    compression = ihdr[10]
    png_filter = ihdr[11]
    interlace = ihdr[12]

    bytes_per_pixel_by_color = {0: 1, 2: 3, 6: 4}
    if bit_depth != 8 or color_type not in bytes_per_pixel_by_color:
        raise RuntimeError(f"{path}: unsupported PNG color format bit_depth={bit_depth} color_type={color_type}")
    if compression != 0 or png_filter != 0 or interlace != 0:
        raise RuntimeError(f"{path}: unsupported PNG compression/filter/interlace settings")

    image_data = b"".join(chunk_data for chunk_type, chunk_data in chunks if chunk_type == b"IDAT")
    if not image_data:
        raise RuntimeError(f"{path}: missing PNG image data")
    rows = unfilter_scanlines(zlib.decompress(image_data), width, height, bytes_per_pixel_by_color[color_type])

    ink_pixels = 0
    min_x = width
    max_x = -1
    min_y = height
    max_y = -1
    bytes_per_pixel = bytes_per_pixel_by_color[color_type]

    for y, row in enumerate(rows):
        dark_channels = row.translate(DARK_CHANNEL_TABLE)
        first_dark_channel = dark_channels.find(b"\x01")
        if first_dark_channel == -1:
            continue

        last_dark_channel = dark_channels.rfind(b"\x01")
        first_dark_pixel = first_dark_channel // bytes_per_pixel
        last_dark_pixel = last_dark_channel // bytes_per_pixel
        # Poppler's RGB output for black/gray text has matching dark channels; counting
        # channel hits keeps this all-Python check fast enough for the 100-page audit set.
        ink_pixels += max(1, round(dark_channels.count(1) / bytes_per_pixel))
        min_x = min(min_x, first_dark_pixel)
        max_x = max(max_x, last_dark_pixel)
        min_y = min(min_y, y)
        max_y = max(max_y, y)

    if ink_pixels == 0:
        return PngMetrics(width=width, height=height, ink_ratio=0.0, min_edge_margin=None)

    margins = (min_x, min_y, width - max_x - 1, height - max_y - 1)
    return PngMetrics(
        width=width,
        height=height,
        ink_ratio=ink_pixels / (width * height),
        min_edge_margin=min(margins),
    )


def check_file_set(expected: dict[str, bool], actual_files: list[Path], errors: list[str]) -> None:
    actual_names = {path.name for path in actual_files}
    expected_name_set = set(expected)

    if len(expected_name_set) != EXPECTED_PNGS:
        errors.append(f"visual audit expects {len(expected_name_set)} PNG names but configured count is {EXPECTED_PNGS}")
    if len(actual_names) != EXPECTED_PNGS:
        errors.append(f"visual audit PNG count {len(actual_names)}, expected {EXPECTED_PNGS}")

    for name in sorted(expected_name_set - actual_names):
        errors.append(f"missing visual audit PNG: {name}")
    for name in sorted(actual_names - expected_name_set):
        errors.append(f"unexpected visual audit PNG: {name}")


def check_metrics(expected: dict[str, bool], errors: list[str]) -> None:
    expected_width = round(8.5 * AUDIT_DPI)
    expected_height = round(11 * AUDIT_DPI)
    required_margin = max(2, min(expected_width, expected_height) // 200)

    blank_pages = 0
    nonblank_metrics: list[PngMetrics] = []
    all_metrics: list[PngMetrics] = []
    for name, expected_blank in sorted(expected.items()):
        path = AUDIT_DIR / name
        if not path.exists():
            continue
        try:
            metrics = png_metrics(path)
        except (RuntimeError, zlib.error) as exc:
            errors.append(str(exc))
            continue

        all_metrics.append(metrics)
        if metrics.width != expected_width or metrics.height != expected_height:
            errors.append(
                f"{name}: rendered size is {metrics.width}x{metrics.height}, "
                f"expected {expected_width}x{expected_height} at {AUDIT_DPI} dpi"
            )

        if expected_blank:
            blank_pages += 1
            if metrics.ink_ratio > MAX_EXPECTED_BLANK_INK_RATIO:
                errors.append(
                    f"{name}: expected blank visual page has ink ratio {metrics.ink_ratio:.4f}, "
                    f"expected at most {MAX_EXPECTED_BLANK_INK_RATIO:.4f}"
                )
            continue

        nonblank_metrics.append(metrics)
        if metrics.ink_ratio < MIN_INK_RATIO:
            errors.append(f"{name}: rendered page looks blank (ink ratio {metrics.ink_ratio:.4f})")
        if metrics.ink_ratio > MAX_INK_RATIO:
            errors.append(f"{name}: rendered page is unexpectedly dense (ink ratio {metrics.ink_ratio:.4f})")
        if metrics.min_edge_margin is None or metrics.min_edge_margin < required_margin:
            errors.append(
                f"{name}: dark pixels touch the page edge "
                f"(minimum margin {metrics.min_edge_margin}px, expected at least {required_margin}px)"
            )

    if not errors and nonblank_metrics and all_metrics:
        min_ratio = min(metric.ink_ratio for metric in nonblank_metrics)
        max_ratio = max(metric.ink_ratio for metric in nonblank_metrics)
        min_margin = min(metric.min_edge_margin or 0 for metric in nonblank_metrics)
        print(f"visual audit images checked: {len(all_metrics)} PNGs")
        print(f"visual audit dimensions: {expected_width}x{expected_height} at {AUDIT_DPI} dpi")
        print(f"nonblank ink ratio: {min_ratio:.4f}--{max_ratio:.4f}")
        print(f"minimum nonblank edge margin: {min_margin}px")
        print(f"expected blank visual pages: {blank_pages}")


def main() -> int:
    errors: list[str] = []
    expected = expected_names()

    if not AUDIT_DIR.exists():
        print(f"missing visual audit directory: {AUDIT_DIR}", file=sys.stderr)
        return 1

    actual_files = sorted(AUDIT_DIR.glob("*.png"))
    check_file_set(expected, actual_files, errors)
    check_metrics(expected, errors)

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("visual audit image checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

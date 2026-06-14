#!/usr/bin/env python3
"""Check that the visual-audit page plan is documented and synchronized."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import check_visual_audit_images


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
MAKEFILE = ROOT / "Makefile"
VISUAL_AUDIT_NOTE = ROOT / "notes" / "visual_audit.md"


@dataclass(frozen=True)
class MakefileAuditRange:
    prefix: str
    first_page: int
    last_page: int
    pdf_name: str


@dataclass(frozen=True)
class VisualArtifact:
    edition: str
    path: Path


ARTIFACTS = (
    VisualArtifact("English", BOOK_DIR / "book.pdf"),
    VisualArtifact("Chinese", BOOK_DIR / "book_zh.pdf"),
)
TEXT_HASH_RE = re.compile(
    r"^- (?P<edition>English|Chinese) PDF text SHA-256: "
    r"`(?P<digest>[0-9a-f]{64})`\.$",
    re.MULTILINE,
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def makefile_variable(name: str) -> str:
    match = re.search(rf"^{re.escape(name)}\s*\?=\s*(.+)$", read(MAKEFILE), re.MULTILINE)
    if not match:
        raise RuntimeError(f"Makefile is missing {name}")
    return match.group(1).strip()


def makefile_visual_ranges() -> tuple[MakefileAuditRange, ...]:
    pattern = re.compile(
        r"\$\(PDFTOPPM\)\s+-png\s+-r\s+\$\(VISUAL_AUDIT_DPI\)\s+"
        r"-f\s+(\d+)\s+-l\s+(\d+)\s+"
        r"(book(?:_zh)?\.pdf)\s+\"\$\(VISUAL_AUDIT_DIR\)/([^\"]+)\""
    )
    ranges = [
        MakefileAuditRange(
            prefix=match.group(4),
            first_page=int(match.group(1)),
            last_page=int(match.group(2)),
            pdf_name=match.group(3),
        )
        for match in pattern.finditer(read(MAKEFILE))
    ]
    if not ranges:
        raise RuntimeError("Makefile visual-audit target has no pdftoppm page ranges")
    return tuple(ranges)


def checker_visual_ranges() -> tuple[MakefileAuditRange, ...]:
    ranges: list[MakefileAuditRange] = []
    for audit_range in check_visual_audit_images.AUDIT_RANGES:
        pdf_name = "book_zh.pdf" if audit_range.prefix.startswith("zh_") else "book.pdf"
        ranges.append(
            MakefileAuditRange(
                prefix=audit_range.prefix,
                first_page=audit_range.first_page,
                last_page=audit_range.last_page,
                pdf_name=pdf_name,
            )
        )
    return tuple(ranges)


def page_count(ranges: tuple[MakefileAuditRange, ...]) -> int:
    return sum(item.last_page - item.first_page + 1 for item in ranges)


def blank_pages() -> tuple[int, ...]:
    pages: list[int] = []
    for audit_range in check_visual_audit_images.AUDIT_RANGES:
        pages.extend(audit_range.expected_blank_pages)
    return tuple(sorted(pages))


def recorded_text_hashes(text: str, errors: list[str]) -> dict[str, str]:
    recorded: dict[str, str] = {}
    for match in TEXT_HASH_RE.finditer(text):
        edition = match.group("edition")
        if edition in recorded:
            errors.append(f"{relative(VISUAL_AUDIT_NOTE)}: duplicate {edition} rendered text fingerprint")
        recorded[edition] = match.group("digest")

    for artifact in ARTIFACTS:
        if artifact.edition not in recorded:
            errors.append(f"{relative(VISUAL_AUDIT_NOTE)}: missing {artifact.edition} rendered text fingerprint")
    return recorded


def current_text_hashes() -> dict[str, str]:
    pdftotext_name = os.environ.get("PDFTOTEXT", "pdftotext")
    pdftotext = shutil.which(pdftotext_name)
    if pdftotext is None:
        raise RuntimeError(f"{pdftotext_name} is required for visual-audit artifact fingerprint checks")

    hashes: dict[str, str] = {}
    for artifact in ARTIFACTS:
        if not artifact.path.exists():
            raise RuntimeError(f"missing PDF: {relative(artifact.path)}")
        result = subprocess.run(
            [pdftotext, "-layout", str(artifact.path), "-"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"pdftotext failed for {relative(artifact.path)}: {stderr}")
        hashes[artifact.edition] = sha256(result.stdout).hexdigest()
    return hashes


def check_text_hashes(
    recorded_hashes: dict[str, str],
    current_hashes: dict[str, str],
    errors: list[str],
) -> None:
    for artifact in ARTIFACTS:
        recorded = recorded_hashes.get(artifact.edition)
        current = current_hashes[artifact.edition]
        if recorded and recorded != current:
            errors.append(
                f"{relative(VISUAL_AUDIT_NOTE)}: {artifact.edition} rendered text fingerprint "
                f"is {recorded}, expected current {current}"
            )


def page_snippet(audit_range: MakefileAuditRange) -> str:
    if audit_range.first_page == audit_range.last_page:
        return f"`{audit_range.first_page}`"
    return f"`{audit_range.first_page}--{audit_range.last_page}`"


def check_makefile_and_checker(errors: list[str]) -> tuple[int, int, int]:
    make_ranges = makefile_visual_ranges()
    checker_ranges = checker_visual_ranges()

    if make_ranges != checker_ranges:
        errors.append(
            "visual-audit Makefile ranges differ from scripts/check_visual_audit_images.py "
            f"ranges; Makefile={make_ranges!r}, checker={checker_ranges!r}"
        )

    configured_pngs = int(makefile_variable("VISUAL_AUDIT_EXPECTED_PNGS"))
    if configured_pngs != check_visual_audit_images.EXPECTED_PNGS:
        errors.append(
            "VISUAL_AUDIT_EXPECTED_PNGS differs between Makefile and checker defaults: "
            f"{configured_pngs} != {check_visual_audit_images.EXPECTED_PNGS}"
        )

    configured_dpi = int(makefile_variable("VISUAL_AUDIT_DPI"))
    if configured_dpi != check_visual_audit_images.AUDIT_DPI:
        errors.append(
            "VISUAL_AUDIT_DPI differs between Makefile and checker defaults: "
            f"{configured_dpi} != {check_visual_audit_images.AUDIT_DPI}"
        )

    expected_pngs = page_count(make_ranges)
    if configured_pngs != expected_pngs:
        errors.append(
            f"visual-audit page ranges produce {expected_pngs} PNGs, "
            f"but VISUAL_AUDIT_EXPECTED_PNGS is {configured_pngs}"
        )

    return len(make_ranges), expected_pngs, len(blank_pages())


def check_note(
    ranges: tuple[MakefileAuditRange, ...],
    current_hashes: dict[str, str],
    errors: list[str],
) -> None:
    text = read(VISUAL_AUDIT_NOTE)
    required_snippets = (
        "make visual-smoke-check",
        "make visual-audit",
        "/tmp/llm_book_visual_audit",
        "360 PNG",
        "English pages 38, 76, and 178",
        "Current Rendered Text Fingerprints",
        "3 expected blank visual pages",
        "23 visual-audit page ranges",
        "360 visual-audit PNGs",
    )
    for snippet in required_snippets:
        if snippet not in text:
            errors.append(f"{relative(VISUAL_AUDIT_NOTE)}: missing required snippet {snippet!r}")

    for audit_range in ranges:
        snippet = page_snippet(audit_range)
        if snippet not in text:
            errors.append(
                f"{relative(VISUAL_AUDIT_NOTE)}: missing visual-audit page-range snippet {snippet}"
            )
    check_text_hashes(recorded_text_hashes(text, errors), current_hashes, errors)


def main() -> int:
    errors: list[str] = []
    try:
        make_ranges = makefile_visual_ranges()
        range_count, png_count, blank_count = check_makefile_and_checker(errors)
        current_hashes = current_text_hashes()
        check_note(make_ranges, current_hashes, errors)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"visual-audit page ranges: {range_count}")
    print(f"visual-audit PNGs: {png_count}")
    print(f"expected blank visual pages: {blank_count}")
    print(f"English visual-audit text SHA-256: {current_hashes.get('English', 'missing')}")
    print(f"Chinese visual-audit text SHA-256: {current_hashes.get('Chinese', 'missing')}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("visual-audit plan checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

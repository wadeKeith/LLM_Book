#!/usr/bin/env python3
"""Check the source-level bilingual alignment manifest."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from report_bilingual_print_plan import all_source_units


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "notes" / "bilingual_alignment_manifest.md"
ALLOWED_STATUSES = {"Draft", "Aligned", "Proofed"}
HAN_RE = re.compile(r"[\u4e00-\u9fff]")
UNRESOLVED_RE = re.compile(r"TODO|FIXME|TBD|XXX|\?\?\?|待补|citation needed|cite needed", re.IGNORECASE)


@dataclass(frozen=True)
class AlignmentRow:
    unit_id: str
    status: str
    proofing: str
    chinese: str


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def markdown_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def parse_rows(text: str, errors: list[str]) -> list[AlignmentRow]:
    rows: list[AlignmentRow] = []
    for cells in markdown_rows(text):
        if len(cells) != 4 or cells[0] == "Unit ID":
            continue
        if not cells[0].startswith(("ch", "front-", "back-")):
            continue
        rows.append(AlignmentRow(unit_id=cells[0], status=cells[1], proofing=cells[2], chinese=cells[3]))

    if not rows:
        errors.append(f"{rel(MANIFEST)}: no alignment records found")
    return rows


def required_snippets(text: str, errors: list[str]) -> None:
    for snippet in (
        "Bilingual Alignment Manifest",
        "paragraph-level bilingual print edition",
        "Status Legend",
        "Aligned",
        "Proofed",
        "Records",
    ):
        if snippet not in text:
            errors.append(f"{rel(MANIFEST)}: missing required snippet {snippet!r}")


def check_rows(rows: list[AlignmentRow], errors: list[str]) -> tuple[int, int]:
    source_unit_ids = {unit.unit_id for unit in all_source_units()}
    seen: set[str] = set()
    aligned = 0
    proofed = 0

    for row in rows:
        if row.unit_id in seen:
            errors.append(f"{rel(MANIFEST)}: duplicate alignment unit {row.unit_id}")
        seen.add(row.unit_id)

        if row.unit_id not in source_unit_ids:
            errors.append(f"{rel(MANIFEST)}: unknown source unit {row.unit_id}")
        if row.status not in ALLOWED_STATUSES:
            errors.append(f"{rel(MANIFEST)}: {row.unit_id} has invalid status {row.status!r}")
        if row.status in {"Aligned", "Proofed"}:
            aligned += 1
        if row.status == "Proofed":
            proofed += 1
            if row.proofing == "Not proofed":
                errors.append(f"{rel(MANIFEST)}: {row.unit_id} is Proofed but proofing is marked Not proofed")

        han_chars = len(HAN_RE.findall(row.chinese))
        if row.status in {"Aligned", "Proofed"} and han_chars < 20:
            errors.append(f"{rel(MANIFEST)}: {row.unit_id} has only {han_chars} Han characters")
        if UNRESOLVED_RE.search(row.chinese):
            errors.append(f"{rel(MANIFEST)}: {row.unit_id} contains an unresolved marker")

    return aligned, proofed


def main() -> int:
    errors: list[str] = []
    if not MANIFEST.exists():
        print(f"{rel(MANIFEST)}: missing alignment manifest", file=sys.stderr)
        return 1

    text = MANIFEST.read_text(encoding="utf-8")
    required_snippets(text, errors)
    rows = parse_rows(text, errors)
    aligned, proofed = check_rows(rows, errors)
    total = len(all_source_units())

    print(f"bilingual alignment source units available: {total}")
    print(f"bilingual alignment manifest rows: {len(rows)}")
    print(f"bilingual alignment aligned units: {aligned}")
    print(f"bilingual alignment proofed units: {proofed}")
    print(f"bilingual alignment open units: {total - aligned}")
    print(f"bilingual alignment manifest errors: {len(errors)}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("bilingual alignment manifest checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

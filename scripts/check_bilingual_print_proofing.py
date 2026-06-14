#!/usr/bin/env python3
"""Check bilingual print proofing log coverage against the rendered artifact."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from report_bilingual_print_plan import alignment_records, all_source_units


ROOT = Path(__file__).resolve().parents[1]
PROOFING_LOG = ROOT / "notes" / "bilingual_print_proofing_log.md"
DEFAULT_TEX = Path("/tmp/llm_book_bilingual_print/book_bilingual_print.tex")
ALLOWED_STATUSES = {"Planned", "In review", "Reviewed"}


@dataclass(frozen=True)
class ProofingBatch:
    batch_id: str
    unit_scope: str
    first_unit: str
    last_unit: str
    units: int
    first_page: int
    last_page: int
    status: str
    digest: str
    evidence: str


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


def parse_page_range(raw: str, errors: list[str], batch_id: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+)--(\d+)", raw)
    if not match:
        errors.append(f"{rel(PROOFING_LOG)}: batch {batch_id} has malformed page range {raw!r}")
        return 0, 0
    first, last = int(match.group(1)), int(match.group(2))
    if first > last:
        errors.append(f"{rel(PROOFING_LOG)}: batch {batch_id} has descending page range {raw!r}")
    return first, last


def parse_unit_range(raw: str, errors: list[str], batch_id: str) -> tuple[str, str]:
    parts = raw.split("--")
    if len(parts) != 2 or not all(parts):
        errors.append(f"{rel(PROOFING_LOG)}: batch {batch_id} has malformed unit range {raw!r}")
        return "", ""
    return parts[0], parts[1]


def parse_digest(raw: str, errors: list[str], batch_id: str) -> str:
    match = re.search(r"[0-9a-f]{64}", raw)
    if not match:
        errors.append(f"{rel(PROOFING_LOG)}: batch {batch_id} has malformed digest {raw!r}")
        return ""
    return match.group(0)


def parse_batches(text: str, errors: list[str]) -> list[ProofingBatch]:
    batches: list[ProofingBatch] = []
    seen: set[str] = set()

    for row in markdown_rows(text):
        if len(row) != 8 or not re.fullmatch(r"BP-\d{2}", row[0]):
            continue
        batch_id, unit_scope, unit_range, units_raw, pages, status, digest_raw, evidence = row
        first_unit, last_unit = parse_unit_range(unit_range, errors, batch_id)
        first_page, last_page = parse_page_range(pages, errors, batch_id)
        digest = parse_digest(digest_raw, errors, batch_id)
        try:
            units = int(units_raw)
        except ValueError:
            units = 0
            errors.append(f"{rel(PROOFING_LOG)}: batch {batch_id} has non-integer unit count {units_raw!r}")

        if batch_id in seen:
            errors.append(f"{rel(PROOFING_LOG)}: duplicate proofing batch {batch_id}")
        seen.add(batch_id)
        if status not in ALLOWED_STATUSES:
            errors.append(f"{rel(PROOFING_LOG)}: batch {batch_id} has invalid status {status!r}")
        if not evidence or evidence == "-":
            errors.append(f"{rel(PROOFING_LOG)}: batch {batch_id} is missing evidence")

        batches.append(
            ProofingBatch(
                batch_id=batch_id,
                unit_scope=unit_scope,
                first_unit=first_unit,
                last_unit=last_unit,
                units=units,
                first_page=first_page,
                last_page=last_page,
                status=status,
                digest=digest,
                evidence=evidence,
            )
        )

    if not batches:
        errors.append(f"{rel(PROOFING_LOG)}: no bilingual print proofing batches found")
    return batches


def required_snippets(text: str, errors: list[str]) -> str:
    for snippet in (
        "Bilingual Print Proofing Log",
        "paragraph-level bilingual print edition",
        "make bilingual-print-proofing-check",
        "Current Rendered Artifact",
        "Current Proofing Status",
        "Status Legend",
        "Proofing Log",
    ):
        if snippet not in text:
            errors.append(f"{rel(PROOFING_LOG)}: missing required snippet {snippet!r}")

    status_match = re.search(r"^Current proofing status:\s+(.+)$", text, re.MULTILINE)
    if not status_match:
        errors.append(f"{rel(PROOFING_LOG)}: missing current proofing status line")
        return ""
    status = status_match.group(1).strip()
    if status not in {"Not started", "In progress", "Complete"}:
        errors.append(f"{rel(PROOFING_LOG)}: invalid current proofing status {status!r}")
    return status


def artifact_paths() -> tuple[Path, Path]:
    tex_path = Path(os.environ.get("BILINGUAL_PRINT_TEX", str(DEFAULT_TEX)))
    pdf_path = Path(os.environ.get("BILINGUAL_PRINT_PDF", str(tex_path.with_suffix(".pdf"))))
    return tex_path, pdf_path


def command_output(command: list[str]) -> bytes:
    result = subprocess.run(command, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        stdout = result.stdout.decode("utf-8", errors="replace").strip()
        detail = stderr or stdout or "no diagnostic output"
        raise RuntimeError(f"{command[0]} failed: {detail}")
    return result.stdout


def current_artifact(pdf_path: Path) -> tuple[int, str, list[str]]:
    pdfinfo = os.environ.get("PDFINFO", "pdfinfo")
    pdftotext = os.environ.get("PDFTOTEXT", "pdftotext")

    info = command_output([pdfinfo, str(pdf_path)]).decode("utf-8", errors="replace")
    pages = 0
    for line in info.splitlines():
        if line.startswith("Pages:"):
            pages = int(line.split(":", 1)[1].strip())
            break
    if pages < 1:
        raise RuntimeError(f"could not parse page count from {pdf_path}")

    rendered_bytes = command_output([pdftotext, "-layout", str(pdf_path), "-"])
    rendered_text = rendered_bytes.decode("utf-8", errors="replace")
    return pages, sha256(rendered_bytes).hexdigest(), rendered_text.split("\f")


def units_for_scope(scope: str) -> list[str]:
    return [unit.unit_id for unit in all_source_units() if unit.unit_id.startswith(f"{scope}-")]


def check_batch_units(
    batch: ProofingBatch,
    pages: list[str],
    current_digest: str,
    errors: list[str],
) -> set[str]:
    if batch.status != "Reviewed":
        return set()

    selected = units_for_scope(batch.unit_scope)
    if not selected:
        errors.append(f"{rel(PROOFING_LOG)}: batch {batch.batch_id} has unknown unit scope {batch.unit_scope!r}")
        return set()
    if selected[0] != batch.first_unit or selected[-1] != batch.last_unit:
        errors.append(
            f"{rel(PROOFING_LOG)}: batch {batch.batch_id} unit range "
            f"{batch.first_unit}--{batch.last_unit} does not match scope {batch.unit_scope} "
            f"({selected[0]}--{selected[-1]})"
        )
    if len(selected) != batch.units:
        errors.append(
            f"{rel(PROOFING_LOG)}: batch {batch.batch_id} declares {batch.units} units, "
            f"expected {len(selected)}"
        )
    if batch.digest != current_digest:
        errors.append(
            f"{rel(PROOFING_LOG)}: batch {batch.batch_id} digest is {batch.digest}, "
            f"expected current {current_digest}"
        )

    if batch.first_page < 1 or batch.last_page > len(pages):
        errors.append(
            f"{rel(PROOFING_LOG)}: batch {batch.batch_id} page range "
            f"{batch.first_page}--{batch.last_page} exceeds artifact page count {len(pages)}"
        )
        return set(selected)

    page_text = "\n".join(pages[batch.first_page - 1 : batch.last_page])
    missing = [unit_id for unit_id in selected if unit_id not in page_text]
    if missing:
        errors.append(
            f"{rel(PROOFING_LOG)}: batch {batch.batch_id} page range is missing "
            f"{len(missing)} unit ids; first missing unit: {missing[0]}"
        )
    return set(selected)


def check_manifest_proofing(
    reviewed_units: set[str],
    reviewed_batch_ids: set[str],
    errors: list[str],
) -> int:
    records = alignment_records()
    proofed_units = {unit_id for unit_id, record in records.items() if record.status == "Proofed"}
    if proofed_units != reviewed_units:
        missing_from_manifest = sorted(reviewed_units - proofed_units)
        missing_from_log = sorted(proofed_units - reviewed_units)
        if missing_from_manifest:
            errors.append(
                "reviewed proofing units not marked Proofed in manifest: "
                + ", ".join(missing_from_manifest[:5])
            )
        if missing_from_log:
            errors.append(
                "manifest Proofed units not covered by reviewed proofing batches: "
                + ", ".join(missing_from_log[:5])
            )

    for unit_id in sorted(proofed_units):
        proofing = records[unit_id].proofing
        if "Not proofed" in proofing:
            errors.append(f"{unit_id} is Proofed but proofing text says Not proofed")
        if not any(batch_id in proofing for batch_id in reviewed_batch_ids):
            errors.append(f"{unit_id} is Proofed but proofing text lacks a reviewed batch id")
    return len(proofed_units)


def check_count_snippets(text: str, proofed: int, total: int, errors: list[str]) -> None:
    expected = (
        f"Proofed source units: {proofed} / {total}.",
        f"Remaining source units: {total - proofed}.",
    )
    for snippet in expected:
        if snippet not in text:
            errors.append(f"{rel(PROOFING_LOG)}: missing current proofing count snippet {snippet!r}")


def main() -> int:
    errors: list[str] = []
    if not PROOFING_LOG.exists():
        print(f"{rel(PROOFING_LOG)}: missing bilingual print proofing log", file=sys.stderr)
        return 1

    tex_path, pdf_path = artifact_paths()
    if not tex_path.exists():
        errors.append(f"missing bilingual print TeX artifact: {tex_path}")
    if not pdf_path.exists():
        errors.append(f"missing bilingual print PDF artifact: {pdf_path}")

    text = PROOFING_LOG.read_text(encoding="utf-8")
    current_status = required_snippets(text, errors)
    batches = parse_batches(text, errors)
    pages = 0
    current_digest = ""
    rendered_pages: list[str] = []
    if pdf_path.exists():
        try:
            pages, current_digest, rendered_pages = current_artifact(pdf_path)
        except RuntimeError as exc:
            errors.append(str(exc))

    reviewed_units: set[str] = set()
    reviewed_batch_ids = {batch.batch_id for batch in batches if batch.status == "Reviewed"}
    if rendered_pages and current_digest:
        for batch in batches:
            reviewed_units.update(check_batch_units(batch, rendered_pages, current_digest, errors))

    total_units = len(all_source_units())
    proofed_units = check_manifest_proofing(reviewed_units, reviewed_batch_ids, errors)
    check_count_snippets(text, proofed_units, total_units, errors)

    if current_status == "Complete" and proofed_units != total_units:
        errors.append(
            f"{rel(PROOFING_LOG)}: Complete status requires {total_units} proofed units, "
            f"found {proofed_units}"
        )

    print(f"bilingual print proofing batches checked: {len(batches)}")
    print(f"bilingual print proofing reviewed batches: {len(reviewed_batch_ids)}")
    print(f"bilingual print proofing proofed units: {proofed_units} / {total_units}")
    print(f"bilingual print proofing artifact pages: {pages}")
    if current_digest:
        print(f"bilingual print proofing text SHA-256: {current_digest}")
    print(f"bilingual print proofing errors: {len(errors)}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("bilingual print proofing checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

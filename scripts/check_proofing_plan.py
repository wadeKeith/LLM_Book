#!/usr/bin/env python3
"""Check full-manuscript human proofing plan coverage."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
PROOFING_NOTE = ROOT / "notes" / "proofing_plan.md"

EXPECTED_PAGES = {
    "English": 238,
    "Chinese": 308,
}
ALLOWED_STATUSES = {"Planned", "In review", "Reviewed"}


@dataclass(frozen=True)
class ProofingBatch:
    batch_id: str
    edition: str
    first_page: int
    last_page: int
    status: str


@dataclass(frozen=True)
class ProofingReviewLog:
    batch_id: str
    text: str


@dataclass(frozen=True)
class ProofingArtifact:
    edition: str
    path: Path


ARTIFACTS = (
    ProofingArtifact("English", BOOK_DIR / "book.pdf"),
    ProofingArtifact("Chinese", BOOK_DIR / "book_zh.pdf"),
)
TEXT_HASH_RE = re.compile(
    r"^- (?P<edition>English|Chinese) PDF text SHA-256: "
    r"`(?P<digest>[0-9a-f]{64})`\.$",
    re.MULTILINE,
)


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
        errors.append(f"{rel(PROOFING_NOTE)}: batch {batch_id} has malformed page range {raw!r}")
        return 0, 0
    first, last = int(match.group(1)), int(match.group(2))
    if first > last:
        errors.append(f"{rel(PROOFING_NOTE)}: batch {batch_id} has descending page range {raw!r}")
    return first, last


def parse_batches(text: str, errors: list[str]) -> list[ProofingBatch]:
    batches: list[ProofingBatch] = []
    seen: set[str] = set()

    for row in markdown_rows(text):
        if len(row) < 5 or not re.fullmatch(r"(EN|ZH)-\d{2}", row[0]):
            continue
        batch_id, edition, pages, status = row[0], row[1], row[2], row[3]
        first, last = parse_page_range(pages, errors, batch_id)
        if batch_id in seen:
            errors.append(f"{rel(PROOFING_NOTE)}: duplicate proofing batch {batch_id}")
        seen.add(batch_id)
        if edition not in EXPECTED_PAGES:
            errors.append(f"{rel(PROOFING_NOTE)}: batch {batch_id} has unknown edition {edition!r}")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{rel(PROOFING_NOTE)}: batch {batch_id} has invalid status {status!r}")
        batches.append(ProofingBatch(batch_id, edition, first, last, status))

    return batches


def parse_review_logs(text: str, errors: list[str]) -> dict[str, ProofingReviewLog]:
    logs: dict[str, ProofingReviewLog] = {}
    for row in markdown_rows(text):
        if len(row) < 4 or not re.fullmatch(r"(EN|ZH)-\d{2}", row[0]):
            continue
        if not re.search(r"[0-9a-f]{64}", " ".join(row[1:])):
            continue
        batch_id = row[0]
        if batch_id in logs:
            errors.append(f"{rel(PROOFING_NOTE)}: duplicate proofing review log for {batch_id}")
        logs[batch_id] = ProofingReviewLog(batch_id=batch_id, text=" | ".join(row[1:]))
    return logs


def required_snippets(text: str, errors: list[str]) -> str:
    snippets = (
        "Full-Manuscript Proofing Plan",
        "make proofing-plan-check",
        "English `book.pdf`: 238 pages.",
        "Chinese `book_zh.pdf`: 308 pages.",
        "Current Rendered Text Fingerprints",
        "This plan marks the proofread complete",
        "Status Legend",
        "Proofing Log",
    )
    for snippet in snippets:
        if snippet not in text:
            errors.append(f"{rel(PROOFING_NOTE)}: missing required snippet {snippet!r}")

    status_match = re.search(r"^Current proofread status:\s+(.+)$", text, re.MULTILINE)
    if not status_match:
        errors.append(f"{rel(PROOFING_NOTE)}: missing current proofread status line")
        return ""
    status = status_match.group(1).strip()
    if status not in {"Not started", "In progress", "Complete"}:
        errors.append(f"{rel(PROOFING_NOTE)}: invalid current proofread status {status!r}")
    return status


def rendered_text_hashes(text: str, errors: list[str]) -> dict[str, str]:
    recorded: dict[str, str] = {}
    for match in TEXT_HASH_RE.finditer(text):
        edition = match.group("edition")
        if edition in recorded:
            errors.append(f"{rel(PROOFING_NOTE)}: duplicate {edition} rendered text fingerprint")
        recorded[edition] = match.group("digest")

    for artifact in ARTIFACTS:
        if artifact.edition not in recorded:
            errors.append(f"{rel(PROOFING_NOTE)}: missing {artifact.edition} rendered text fingerprint")
    return recorded


def current_text_hashes() -> dict[str, str]:
    pdftotext_name = os.environ.get("PDFTOTEXT", "pdftotext")
    pdftotext = shutil.which(pdftotext_name)
    if pdftotext is None:
        raise RuntimeError(f"{pdftotext_name} is required for proofing artifact fingerprint checks")

    hashes: dict[str, str] = {}
    for artifact in ARTIFACTS:
        if not artifact.path.exists():
            raise RuntimeError(f"missing PDF: {rel(artifact.path)}")
        result = subprocess.run(
            [pdftotext, "-layout", str(artifact.path), "-"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"pdftotext failed for {rel(artifact.path)}: {stderr}")
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
                f"{rel(PROOFING_NOTE)}: {artifact.edition} rendered text fingerprint "
                f"is {recorded}, expected current {current}"
            )


def check_coverage(batches: list[ProofingBatch], errors: list[str]) -> dict[str, int]:
    covered_counts: dict[str, int] = {}
    for edition, expected_pages in EXPECTED_PAGES.items():
        coverage: dict[int, str] = {}
        edition_batches = [batch for batch in batches if batch.edition == edition]
        if not edition_batches:
            errors.append(f"{rel(PROOFING_NOTE)}: missing proofing batches for {edition}")
            covered_counts[edition] = 0
            continue

        for batch in edition_batches:
            if batch.first_page < 1 or batch.last_page > expected_pages:
                errors.append(
                    f"{rel(PROOFING_NOTE)}: batch {batch.batch_id} range "
                    f"{batch.first_page}--{batch.last_page} exceeds {edition} page count {expected_pages}"
                )
            for page in range(batch.first_page, batch.last_page + 1):
                previous = coverage.get(page)
                if previous:
                    errors.append(
                        f"{rel(PROOFING_NOTE)}: {edition} page {page} appears in both "
                        f"{previous} and {batch.batch_id}"
                    )
                coverage[page] = batch.batch_id

        missing = [page for page in range(1, expected_pages + 1) if page not in coverage]
        if missing:
            preview = ", ".join(str(page) for page in missing[:10])
            suffix = "..." if len(missing) > 10 else ""
            errors.append(f"{rel(PROOFING_NOTE)}: {edition} missing proofing pages {preview}{suffix}")

        covered_counts[edition] = len([page for page in coverage if 1 <= page <= expected_pages])

    return covered_counts


def check_review_logs(
    batches: list[ProofingBatch],
    review_logs: dict[str, ProofingReviewLog],
    current_hashes: dict[str, str],
    errors: list[str],
) -> None:
    batch_ids = {batch.batch_id for batch in batches}
    for batch_id in review_logs:
        if batch_id not in batch_ids:
            errors.append(f"{rel(PROOFING_NOTE)}: proofing review log references unknown batch {batch_id}")

    for batch in batches:
        if batch.status != "Reviewed":
            continue
        review_log = review_logs.get(batch.batch_id)
        if review_log is None:
            errors.append(f"{rel(PROOFING_NOTE)}: reviewed batch {batch.batch_id} has no proofing review log")
            continue
        expected_hash = current_hashes[batch.edition]
        if expected_hash not in review_log.text:
            errors.append(
                f"{rel(PROOFING_NOTE)}: reviewed batch {batch.batch_id} log is not tied "
                f"to current {batch.edition} text fingerprint {expected_hash}"
            )


def main() -> int:
    errors: list[str] = []
    if not PROOFING_NOTE.exists():
        print(f"Missing proofing plan: {rel(PROOFING_NOTE)}", file=sys.stderr)
        return 1

    text = PROOFING_NOTE.read_text(encoding="utf-8")
    proofread_status = required_snippets(text, errors)
    recorded_hashes = rendered_text_hashes(text, errors)
    try:
        current_hashes = current_text_hashes()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    check_text_hashes(recorded_hashes, current_hashes, errors)
    batches = parse_batches(text, errors)
    review_logs = parse_review_logs(text, errors)
    covered_counts = check_coverage(batches, errors)
    reviewed_batches = sum(1 for batch in batches if batch.status == "Reviewed")
    active_batches = sum(1 for batch in batches if batch.status != "Planned")
    check_review_logs(batches, review_logs, current_hashes, errors)

    if proofread_status == "Not started" and active_batches:
        errors.append(
            f"{rel(PROOFING_NOTE)}: proofread status is Not started but "
            f"{active_batches} proofing batches are no longer Planned"
        )
    if proofread_status == "Complete" and reviewed_batches != len(batches):
        errors.append(
            f"{rel(PROOFING_NOTE)}: proofread status is Complete but only "
            f"{reviewed_batches}/{len(batches)} batches are Reviewed"
        )

    print(f"proofing batches checked: {len(batches)}")
    print(f"English proofing pages covered: {covered_counts.get('English', 0)} / {EXPECTED_PAGES['English']}")
    print(f"Chinese proofing pages covered: {covered_counts.get('Chinese', 0)} / {EXPECTED_PAGES['Chinese']}")
    print(f"reviewed proofing batches: {reviewed_batches} / {len(batches)}")
    print(f"full proofread status: {proofread_status or 'missing'}")
    print(f"English proofing text SHA-256: {current_hashes.get('English', 'missing')}")
    print(f"Chinese proofing text SHA-256: {current_hashes.get('Chinese', 'missing')}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("proofing plan checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

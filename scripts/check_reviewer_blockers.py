#!/usr/bin/env python3
"""Check the professor-review register for open blocking issues."""

from __future__ import annotations

import re
import sys
from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
CHAPTER_DIR = BOOK_DIR / "chapters"
REVIEW_NOTE = ROOT / "notes" / "professor_review.md"

BLOCKING_SEVERITIES = {"P0", "P1"}
OPEN_STATUSES = {"Open", "Reopened"}
HASH_RE = re.compile(r"`?([0-9a-f]{64})`?")


def strip_tex_comments(text: str) -> str:
    stripped: list[str] = []
    for line in text.splitlines():
        escaped = False
        kept: list[str] = []
        for char in line:
            if char == "%" and not escaped:
                break
            kept.append(char)
            escaped = char == "\\" and not escaped
            if char != "\\":
                escaped = False
        stripped.append("".join(kept))
    return "\n".join(stripped)


def chapter_titles() -> dict[str, str]:
    chapters: dict[str, str] = {}
    for path in sorted(CHAPTER_DIR.glob("ch*.tex")):
        text = strip_tex_comments(path.read_text(encoding="utf-8"))
        match = re.search(r"\\chapter\{([^{}]+)\}", text)
        if match:
            chapters[path.relative_to(ROOT).as_posix()] = match.group(1)
    return chapters


def chapter_source_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(CHAPTER_DIR.glob("ch*.tex")):
        text = strip_tex_comments(path.read_text(encoding="utf-8"))
        hashes[path.relative_to(ROOT).as_posix()] = sha256(text.encode("utf-8")).hexdigest()
    return hashes


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


def check_note_scaffolding(text: str, errors: list[str]) -> None:
    required_snippets = [
        "Professor Review Register",
        "Review Basis",
        "Open P0/P1 blockers: 0",
        "make manuscript-audit",
        "make visual-audit",
        "Current Chapter Source Fingerprints",
    ]
    for snippet in required_snippets:
        if snippet not in text:
            errors.append(f"{REVIEW_NOTE.relative_to(ROOT).as_posix()}: missing review snippet {snippet!r}")


def check_chapter_matrix(text: str, errors: list[str]) -> int:
    chapters = chapter_titles()
    rows = markdown_rows(text)
    matrix_rows = [row for row in rows if len(row) >= 7 and row[0].startswith("book/chapters/")]
    seen: dict[str, str] = {}

    for row in matrix_rows:
        path, title = row[0], row[1]
        status = row[-1]
        if path not in chapters:
            errors.append(f"{REVIEW_NOTE.relative_to(ROOT).as_posix()}: unknown chapter in review matrix: {path}")
            continue
        if chapters[path] != title:
            errors.append(
                f"{REVIEW_NOTE.relative_to(ROOT).as_posix()}: title mismatch for {path}: "
                f"review has {title!r}, source has {chapters[path]!r}"
            )
        if status != "Pass":
            errors.append(f"{REVIEW_NOTE.relative_to(ROOT).as_posix()}: chapter review row is not Pass: {path} -> {status}")
        seen[path] = title

    for path in sorted(set(chapters) - set(seen)):
        errors.append(f"{REVIEW_NOTE.relative_to(ROOT).as_posix()}: missing chapter review row for {path}")

    return len(seen)


def check_chapter_fingerprints(text: str, errors: list[str]) -> int:
    hashes = chapter_source_hashes()
    rows = markdown_rows(text)
    fingerprint_rows = [
        row
        for row in rows
        if len(row) >= 2 and row[0].startswith("book/chapters/") and HASH_RE.fullmatch(row[1])
    ]
    seen: dict[str, str] = {}

    for row in fingerprint_rows:
        path = row[0]
        match = HASH_RE.fullmatch(row[1])
        assert match is not None
        digest = match.group(1)
        if path not in hashes:
            errors.append(f"{REVIEW_NOTE.relative_to(ROOT).as_posix()}: unknown chapter fingerprint path: {path}")
            continue
        if path in seen:
            errors.append(f"{REVIEW_NOTE.relative_to(ROOT).as_posix()}: duplicate chapter fingerprint for {path}")
        if hashes[path] != digest:
            errors.append(
                f"{REVIEW_NOTE.relative_to(ROOT).as_posix()}: source fingerprint mismatch for {path}: "
                f"review has {digest}, source has {hashes[path]}"
            )
        seen[path] = digest

    for path in sorted(set(hashes) - set(seen)):
        errors.append(f"{REVIEW_NOTE.relative_to(ROOT).as_posix()}: missing source fingerprint for {path}")

    return len(seen)


def check_blocker_table(text: str, errors: list[str]) -> tuple[int, int]:
    rows = markdown_rows(text)
    open_blockers = 0
    closed_blockers = 0

    for row in rows:
        if len(row) < 6:
            continue
        issue_id, severity, status = row[0], row[1], row[2]
        if not re.fullmatch(r"(P[0-3]|Info)", severity):
            continue
        if severity in BLOCKING_SEVERITIES and status in OPEN_STATUSES:
            open_blockers += 1
            errors.append(
                f"{REVIEW_NOTE.relative_to(ROOT).as_posix()}: open blocking review issue "
                f"{issue_id} has severity {severity}"
            )
        if severity in BLOCKING_SEVERITIES and status == "Closed":
            closed_blockers += 1

    return open_blockers, closed_blockers


def main() -> int:
    errors: list[str] = []
    if not REVIEW_NOTE.exists():
        print(f"Missing review register: {REVIEW_NOTE.relative_to(ROOT).as_posix()}", file=sys.stderr)
        return 1

    text = REVIEW_NOTE.read_text(encoding="utf-8")
    check_note_scaffolding(text, errors)
    reviewed_chapters = check_chapter_matrix(text, errors)
    fingerprinted_chapters = check_chapter_fingerprints(text, errors)
    open_blockers, closed_blockers = check_blocker_table(text, errors)

    print(f"chapter review rows checked: {reviewed_chapters}")
    print(f"chapter source fingerprints checked: {fingerprinted_chapters}")
    print(f"open P0/P1 blockers: {open_blockers}")
    print(f"closed P0/P1 blockers recorded: {closed_blockers}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("reviewer blocker checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

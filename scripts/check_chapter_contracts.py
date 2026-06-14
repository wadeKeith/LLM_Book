#!/usr/bin/env python3
"""Check chapter-opening reader contracts for publication readiness."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAPTER_DIR = ROOT / "book" / "chapters"
EXPECTED_CHAPTERS = 17
MIN_WORDS = 35
MAX_WORDS = 70
CONTRACT_HEADING = r"\paragraph{Chapter contract.}"
REQUIRED_PHRASE = "The reader should leave this chapter able to"
TODO_RE = re.compile(r"\b(?:TODO|FIXME|TBD|XXX)\b|\?\?\?|待补|lorem|dummy|citation needed|cite needed", re.IGNORECASE)
FORBIDDEN_COMMAND_RE = re.compile(r"\\(?:cite|citep|citet|ref|pageref|label|index|begin|end)\b")
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*|\\[A-Za-z]+")


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


def word_count(text: str) -> int:
    return len(WORD_RE.findall(text))


def chapter_title(text: str) -> str:
    match = re.search(r"\\chapter\{([^{}]+)\}", text)
    return match.group(1) if match else "unknown chapter"


def first_index(text: str, pattern: str) -> int:
    match = re.search(pattern, text)
    return match.start() if match else -1


def contract_body(text: str) -> str | None:
    match = re.search(
        re.escape(CONTRACT_HEADING) + r"(.*?)(?=\\section\{|\\chapter\{|\\paragraph\{|\\subsection\{|\Z)",
        text,
        re.DOTALL,
    )
    return match.group(1).strip() if match else None


def main() -> int:
    errors: list[str] = []
    contract_counts: list[int] = []
    marker_hits = 0
    marker_total = 0
    chapters_checked = 0

    for path in sorted(CHAPTER_DIR.glob("ch*.tex")):
        chapters_checked += 1
        rel = path.relative_to(ROOT).as_posix()
        text = strip_tex_comments(path.read_text(encoding="utf-8"))
        title = chapter_title(text)

        abstract_index = first_index(text, r"\\abstract\{")
        contract_index = text.find(CONTRACT_HEADING)
        first_section_index = first_index(text, r"\\section\{")

        if text.count(CONTRACT_HEADING) != 1:
            errors.append(f"{rel}: expected exactly one Chapter contract paragraph")
            continue
        if abstract_index == -1:
            errors.append(f"{rel}: missing abstract before chapter contract")
        if first_section_index == -1:
            errors.append(f"{rel}: missing first section after chapter contract")
        if not (abstract_index < contract_index < first_section_index):
            errors.append(f"{rel}: Chapter contract must appear after the abstract and before the first section")

        body = contract_body(text)
        if body is None:
            errors.append(f"{rel}: could not parse Chapter contract body")
            continue

        count = word_count(body)
        contract_counts.append(count)
        if count < MIN_WORDS:
            errors.append(f"{rel}: Chapter contract for {title!r} has {count} words, minimum is {MIN_WORDS}")
        if count > MAX_WORDS:
            errors.append(f"{rel}: Chapter contract for {title!r} has {count} words, maximum is {MAX_WORDS}")
        if TODO_RE.search(body):
            errors.append(f"{rel}: Chapter contract contains unresolved editorial marker text")
        if FORBIDDEN_COMMAND_RE.search(body):
            errors.append(f"{rel}: Chapter contract should be plain reader-facing prose without citations, refs, labels, or index commands")
        if not body.endswith("."):
            errors.append(f"{rel}: Chapter contract should end with a period")

        for marker in (REQUIRED_PHRASE, "reader", "able to"):
            marker_total += 1
            if marker in body:
                marker_hits += 1
            else:
                errors.append(f"{rel}: Chapter contract missing marker {marker!r}")

    if chapters_checked != EXPECTED_CHAPTERS:
        errors.append(f"English chapter contracts checked {chapters_checked}, expected {EXPECTED_CHAPTERS}")

    print(f"English chapter contracts checked: {chapters_checked}")
    if contract_counts:
        print(f"minimum contract words: {min(contract_counts)} / {MIN_WORDS}")
        print(f"maximum contract words: {max(contract_counts)} / {MAX_WORDS}")
    else:
        print(f"minimum contract words: 0 / {MIN_WORDS}")
        print(f"maximum contract words: 0 / {MAX_WORDS}")
    print(f"chapter contract marker hits: {marker_hits} / {marker_total}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("chapter contract checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

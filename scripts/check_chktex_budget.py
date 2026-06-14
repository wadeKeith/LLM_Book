#!/usr/bin/env python3
"""Check the full ChkTeX warning distribution against triaged budgets."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
CHKTEX_FILES = [
    "book.tex",
    "preface.tex",
    "ethics.tex",
    "acronym.tex",
    "glossary.tex",
    "appendix.tex",
    *[f"chapters/{path.name}" for path in sorted((BOOK_DIR / "chapters").glob("*.tex"))],
]

WARNING_BUDGETS = {
    "1": 45,
    "2": 278,
    "12": 4,
    "13": 17,
    "24": 366,
    "38": 9,
    "44": 0,
}


def run_chktex() -> str:
    chktex = os.environ.get("CHKTEX", "chktex")
    if shutil.which(chktex) is None:
        raise RuntimeError(f"{chktex} is required for ChkTeX budget checks")

    result = subprocess.run(
        [chktex, "-q", "-I0", "-v0", *CHKTEX_FILES],
        cwd=BOOK_DIR,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode not in (0, 1, 2):
        stderr = result.stderr.strip()
        raise RuntimeError(f"chktex failed with status {result.returncode}: {stderr}")
    if result.stderr.strip():
        raise RuntimeError(f"chktex wrote to stderr: {result.stderr.strip()}")
    return result.stdout


def warning_counts(output: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for line in output.splitlines():
        parts = line.split(":", 4)
        if len(parts) < 5:
            continue
        warning = parts[3].strip()
        if warning:
            counts[warning] += 1
    return counts


def main() -> int:
    try:
        counts = warning_counts(run_chktex())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    errors: list[str] = []
    for warning in sorted(counts, key=lambda item: int(item) if item.isdigit() else item):
        budget = WARNING_BUDGETS.get(warning)
        count = counts[warning]
        if budget is None:
            errors.append(f"ChkTeX warning {warning}: {count} untriaged warning(s)")
            continue
        if count > budget:
            errors.append(f"ChkTeX warning {warning}: {count} exceeds budget {budget}")

    for warning in sorted(WARNING_BUDGETS, key=int):
        print(f"ChkTeX warning {warning}: {counts.get(warning, 0)} / {WARNING_BUDGETS[warning]}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("ChkTeX budget checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

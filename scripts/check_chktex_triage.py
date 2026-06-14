#!/usr/bin/env python3
"""Check that ChkTeX triage notes match the current budget gate."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import check_chktex_budget


ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = ROOT / "Makefile"
TRIAGE_NOTE = ROOT / "notes" / "chktex_triage.md"
STYLE_GUIDE = ROOT / "notes" / "style_guide.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def makefile_mutes() -> set[str]:
    text = read(MAKEFILE)
    match = re.search(r"^CHKTEX_REVIEW_MUTES\s*:=\s*(.+)$", text, re.MULTILINE)
    if not match:
        raise RuntimeError("Makefile is missing CHKTEX_REVIEW_MUTES")
    return set(re.findall(r"-n(\d+)", match.group(1)))


def current_counts() -> dict[str, int]:
    output = check_chktex_budget.run_chktex()
    return dict(check_chktex_budget.warning_counts(output))


def check_triage_note(counts: dict[str, int], errors: list[str]) -> None:
    text = read(TRIAGE_NOTE)
    budgets = check_chktex_budget.WARNING_BUDGETS

    for warning, budget in sorted(budgets.items(), key=lambda item: int(item[0])):
        count = counts.get(warning, 0)
        if not re.search(rf"^{re.escape(warning)}\s+{count}\s+", text, re.MULTILINE):
            errors.append(
                f"{relative(TRIAGE_NOTE)}: missing current distribution row for warning "
                f"{warning} with count {count}"
            )
        if f"`{warning}`:" not in text:
            errors.append(f"{relative(TRIAGE_NOTE)}: missing disposition bullet for warning {warning}")
        if f"{warning}:{budget}" not in text:
            errors.append(f"{relative(TRIAGE_NOTE)}: missing current budget snippet {warning}:{budget}")
        if f"{warning}:{count}/{budget}" not in text:
            errors.append(
                f"{relative(TRIAGE_NOTE)}: missing latest count/budget snippet {warning}:{count}/{budget}"
            )

    required_snippets = (
        "make chktex-budget-check",
        "make chktex-focused-check",
        "make chktex-review",
        "notes/style_guide.md",
    )
    for snippet in required_snippets:
        if snippet not in text:
            errors.append(f"{relative(TRIAGE_NOTE)}: missing required snippet {snippet!r}")


def check_makefile_mutes(errors: list[str]) -> None:
    budgeted = {
        warning
        for warning, budget in check_chktex_budget.WARNING_BUDGETS.items()
        if budget > 0
    }
    muted = makefile_mutes()
    if muted != budgeted:
        errors.append(
            "Makefile: CHKTEX_REVIEW_MUTES must match positive-budget warning classes; "
            f"expected {sorted(budgeted, key=int)}, found {sorted(muted, key=int)}"
        )


def check_style_guide(errors: list[str]) -> None:
    text = read(STYLE_GUIDE)
    required_snippets = (
        "American quote punctuation",
        "notes/chktex_triage.md",
        "make chktex-budget-check",
        "make chktex-focused-check",
        "make log-quality-check",
        "make table-quality-check",
        "make reproducibility-check",
        "make chinese-prose-quality-check",
        "make paragraph-length-check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            errors.append(f"{relative(STYLE_GUIDE)}: missing required style-guide snippet {snippet!r}")


def main() -> int:
    errors: list[str] = []

    try:
        counts = current_counts()
        check_makefile_mutes(errors)
        check_triage_note(counts, errors)
        check_style_guide(errors)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    warning_classes = len(check_chktex_budget.WARNING_BUDGETS)
    warning_hits = sum(counts.get(warning, 0) for warning in check_chktex_budget.WARNING_BUDGETS)
    print(f"ChkTeX triaged warning classes: {warning_classes}")
    print(f"ChkTeX documented warning hits: {warning_hits}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("ChkTeX triage checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

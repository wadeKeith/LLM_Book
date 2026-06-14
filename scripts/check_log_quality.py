#!/usr/bin/env python3
"""Check TeX log warning counts against layout-noise budgets."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"

LOG_BUDGETS = {
    "book.log": {
        "underfull_hbox": 85,
        "underfull_vbox": 0,
        "badness_10000_hbox": 37,
        "badness_10000_vbox": 0,
    },
    "book_zh.log": {
        "underfull_hbox": 61,
        "underfull_vbox": 71,
        "badness_10000_hbox": 16,
        "badness_10000_vbox": 39,
    },
}

UNDERFULL_RE = re.compile(r"Underfull \\(?P<box>[hv])box \(badness (?P<badness>\d+)\)")


def analyze_log(path: Path) -> tuple[dict[str, int], dict[str, int]]:
    if not path.exists():
        raise RuntimeError(f"{path.relative_to(ROOT)} is missing; run `make all` first")

    counts = {
        "underfull_hbox": 0,
        "underfull_vbox": 0,
        "badness_10000_hbox": 0,
        "badness_10000_vbox": 0,
    }
    max_badness = {"hbox": 0, "vbox": 0}

    for match in UNDERFULL_RE.finditer(path.read_text(encoding="utf-8", errors="replace")):
        box = "hbox" if match.group("box") == "h" else "vbox"
        badness = int(match.group("badness"))
        counts[f"underfull_{box}"] += 1
        max_badness[box] = max(max_badness[box], badness)
        if badness == 10000:
            counts[f"badness_10000_{box}"] += 1

    return counts, max_badness


def main() -> int:
    errors: list[str] = []

    try:
        for log_name, budgets in LOG_BUDGETS.items():
            counts, max_badness = analyze_log(BOOK_DIR / log_name)
            print(
                f"{log_name}: "
                f"Underfull hbox {counts['underfull_hbox']} / {budgets['underfull_hbox']}; "
                f"Underfull vbox {counts['underfull_vbox']} / {budgets['underfull_vbox']}; "
                f"badness-10000 hbox {counts['badness_10000_hbox']} / {budgets['badness_10000_hbox']}; "
                f"badness-10000 vbox {counts['badness_10000_vbox']} / {budgets['badness_10000_vbox']}; "
                f"max badness hbox {max_badness['hbox']}; "
                f"max badness vbox {max_badness['vbox']}"
            )
            for metric, budget in budgets.items():
                count = counts[metric]
                if count > budget:
                    errors.append(f"{log_name}: {metric} count {count} exceeds budget {budget}")
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("TeX log-quality checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

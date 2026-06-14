#!/usr/bin/env python3
"""Check Makefile audit target topology and release-gate wiring."""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = ROOT / "Makefile"
ASSIGNMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+\s*(?::=|\?=|\+=|=)")
TARGET_RE = re.compile(r"^([A-Za-z0-9_.-]+(?:\s+[A-Za-z0-9_.-]+)*):(?:\s*(.*))?$")
CHECK_TARGET_EXEMPTIONS = {"clean-check"}


def load_makefile() -> str:
    return MAKEFILE.read_text(encoding="utf-8")


def logical_lines(text: str) -> list[str]:
    lines: list[str] = []
    current = ""
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not current:
            current = line
        else:
            current = f"{current} {line.lstrip()}"

        if current.endswith("\\"):
            current = current[:-1].rstrip()
            continue

        lines.append(current)
        current = ""

    if current:
        lines.append(current)
    return lines


def parse_targets(text: str) -> tuple[list[str], dict[str, list[str]], list[str]]:
    definitions: list[str] = []
    dependencies: dict[str, list[str]] = {}
    phony_targets: list[str] = []

    for line in logical_lines(text):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or line.startswith("\t"):
            continue
        if ASSIGNMENT_RE.match(stripped):
            continue

        match = TARGET_RE.match(stripped)
        if not match:
            continue

        target_names = match.group(1).split()
        deps = [dep for dep in (match.group(2) or "").split() if dep]
        if target_names == [".PHONY"]:
            phony_targets.extend(deps)
            continue
        if any(target.startswith(".") for target in target_names):
            continue

        for target in target_names:
            definitions.append(target)
            dependencies[target] = deps

    return definitions, dependencies, phony_targets


def check_dependency_exact(
    dependencies: dict[str, list[str]],
    target: str,
    expected: list[str],
    errors: list[str],
) -> None:
    actual = dependencies.get(target)
    if actual is None:
        errors.append(f"Makefile: missing {target} target")
    elif actual != expected:
        errors.append(f"Makefile: {target} dependencies are {actual}, expected {expected}")


def target_recipe_lines(text: str, target: str) -> list[str]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith(f"{target}:"):
            recipe: list[str] = []
            for candidate in lines[index + 1 :]:
                if not candidate.strip():
                    if recipe:
                        break
                    continue
                if not candidate.startswith("\t"):
                    break
                recipe.append(candidate.strip())
            return recipe
    return []


def check_release_candidate_target(
    text: str,
    dependencies: dict[str, list[str]],
    errors: list[str],
) -> int:
    check_dependency_exact(dependencies, "release-candidate", ["manuscript-audit"], errors)

    expected_recipe = [
        "$(MAKE) clean",
        "$(MAKE) clean-check",
        "$(GIT) diff --check",
        "$(MAKE) release-inventory-check",
    ]
    recipe = target_recipe_lines(text, "release-candidate")
    if recipe != expected_recipe:
        errors.append(f"Makefile: release-candidate recipe is {recipe}, expected {expected_recipe}")
    return len(recipe)


def main() -> int:
    text = load_makefile()
    definitions, dependencies, phony_targets = parse_targets(text)
    errors: list[str] = []

    definition_counts = Counter(definitions)
    duplicate_definitions = sorted(target for target, count in definition_counts.items() if count > 1)
    if duplicate_definitions:
        errors.append(f"Makefile: duplicate target definitions: {', '.join(duplicate_definitions)}")

    phony_counts = Counter(phony_targets)
    duplicate_phony = sorted(target for target, count in phony_counts.items() if count > 1)
    if duplicate_phony:
        errors.append(f"Makefile: duplicate .PHONY targets: {', '.join(duplicate_phony)}")

    defined_targets = set(definitions)
    phony_target_set = set(phony_targets)

    missing_definitions = sorted(phony_target_set - defined_targets)
    if missing_definitions:
        errors.append(f"Makefile: .PHONY targets without recipes: {', '.join(missing_definitions)}")

    missing_phony = sorted(defined_targets - phony_target_set)
    if missing_phony:
        errors.append(f"Makefile: defined targets missing from .PHONY: {', '.join(missing_phony)}")

    manuscript_audit_targets = dependencies.get("manuscript-audit", [])
    for target in manuscript_audit_targets:
        if target not in defined_targets:
            errors.append(f"Makefile: manuscript-audit dependency {target} has no target definition")
        if target not in phony_target_set:
            errors.append(f"Makefile: manuscript-audit dependency {target} is not listed in .PHONY")

    check_targets = sorted(
        target
        for target in phony_target_set
        if target.endswith("-check") and target not in CHECK_TARGET_EXEMPTIONS
    )
    missing_from_audit = sorted(set(check_targets) - set(manuscript_audit_targets))
    if missing_from_audit:
        errors.append(
            "Makefile: check targets missing from manuscript-audit: "
            + ", ".join(missing_from_audit)
        )

    if "makefile-consistency-check" not in manuscript_audit_targets:
        errors.append("Makefile: manuscript-audit does not include makefile-consistency-check")

    check_dependency_exact(dependencies, "all", ["english", "zh", "check"], errors)
    check_dependency_exact(dependencies, "check", ["english", "zh"], errors)
    release_candidate_steps = check_release_candidate_target(text, dependencies, errors)

    print(f"Makefile phony targets checked: {len(phony_targets)}")
    print(f"Makefile targets defined: {len(definitions)}")
    print(f"manuscript-audit dependencies checked: {len(manuscript_audit_targets)}")
    print(f"release-candidate recipe steps checked: {release_candidate_steps}")
    print(f"Makefile consistency errors: {len(errors)}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("Makefile consistency checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

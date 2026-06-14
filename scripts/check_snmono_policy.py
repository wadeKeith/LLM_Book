#!/usr/bin/env python3
"""Check Springer SNmono portability constraints for the English manuscript."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
ENGLISH_ROOT = BOOK_DIR / "book.tex"
ENGLISH_FILES = [
    ENGLISH_ROOT,
    BOOK_DIR / "preface.tex",
    BOOK_DIR / "ethics.tex",
    BOOK_DIR / "acronym.tex",
    BOOK_DIR / "glossary.tex",
    BOOK_DIR / "appendix.tex",
    *sorted((BOOK_DIR / "chapters").glob("ch*.tex")),
]


@dataclass(frozen=True)
class PatternRule:
    pattern: re.Pattern[str]
    message: str


DISALLOWED_COMMANDS = [
    PatternRule(re.compile(r"\\def\b"), "use \\newcommand instead of \\def"),
    PatternRule(re.compile(r"\\renewcommand\b"), "avoid overriding existing commands in SNmono sources"),
    PatternRule(re.compile(r"\\pageref\b"), "avoid \\pageref because page links are not portable beyond PDF"),
    PatternRule(re.compile(r"\\(?:enlargethispage|pagebreak|newpage|clearpage)\b"), "avoid fixed page-break commands"),
    PatternRule(re.compile(r"\\(?:mbox|hbox)\b"), "use semantic LaTeX such as \\text{...} instead of box commands"),
    PatternRule(re.compile(r"\\(?:wrapfigure|subfigure)\b"), "avoid wrapfigure/subfigure-style constructs"),
]
DISALLOWED_PACKAGES = {
    "a4wide": "changes the standard layout",
    "bbm": "adds extra math fonts discouraged by SNmono guidance",
    "dsfont": "adds extra math fonts discouraged by SNmono guidance",
    "enumitem": "changes standard list/enumeration settings",
    "enumerate": "changes standard list/enumeration settings",
    "eucal": "adds extra math fonts discouraged by SNmono guidance",
    "fancyhdr": "changes standard running-head layout",
    "mathabx": "adds extra math fonts discouraged by SNmono guidance",
    "mathrsfs": "adds extra math fonts discouraged by SNmono guidance",
    "mathtools": "is discouraged alongside the standard SNmono math setup",
    "subfigure": "is not recommended for Springer production",
    "wrapfig": "creates circumfluent figures discouraged by SNmono guidance",
}
PACKAGE_RE = re.compile(r"\\usepackage(?:\[[^\]]*\])?\{([^{}]+)\}")


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


def line_number(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def used_packages(text: str) -> set[str]:
    packages: set[str] = set()
    for match in PACKAGE_RE.finditer(text):
        for name in match.group(1).split(","):
            cleaned = name.strip()
            if cleaned:
                packages.add(cleaned)
    return packages


def main() -> int:
    errors: list[str] = []

    for path in ENGLISH_FILES:
        text = strip_tex_comments(path.read_text(encoding="utf-8"))
        for rule in DISALLOWED_COMMANDS:
            for match in rule.pattern.finditer(text):
                rel = path.relative_to(ROOT).as_posix()
                errors.append(f"{rel}:{line_number(text, match.start())}: {rule.message}")

    root_text = strip_tex_comments(ENGLISH_ROOT.read_text(encoding="utf-8"))
    packages = used_packages(root_text)
    for package in sorted(packages & DISALLOWED_PACKAGES.keys()):
        errors.append(f"book/book.tex: package {package} is discouraged: {DISALLOWED_PACKAGES[package]}")

    if "newtxmath" in packages and "amsmath" in packages:
        errors.append(
            "book/book.tex: newtxmath already loads amsmath; do not load amsmath separately "
            "under the SNmono instructions"
        )

    print(f"SNmono English files checked: {len(ENGLISH_FILES)}")
    print(f"English root packages checked: {len(packages)}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("SNmono policy checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

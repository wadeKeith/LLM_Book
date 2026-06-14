#!/usr/bin/env python3
"""Check repeatable structural gates for the manuscript."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
CHAPTER_DIR = BOOK_DIR / "chapters"
EN_ROOT = BOOK_DIR / "book.tex"
ZH_ROOT = BOOK_DIR / "book_zh.tex"
EXPECTED_CHAPTERS = 17
EN_ROOT_MARKERS = [
    r"\maketitle",
    r"\frontmatter",
    r"\include{preface}",
    r"\include{ethics}",
    r"\tableofcontents",
    r"\include{acronym}",
    r"\mainmatter",
    r"\appendix",
    r"\include{appendix}",
    r"\backmatter",
    r"\include{glossary}",
    r"\bibliographystyle{spmpsci}",
    r"\bibliography{references}",
    r"\printindex",
]
ZH_ROOT_MARKERS = [
    r"\maketitle",
    r"\frontmatter",
    r"\chapter*{前言}",
    r"\chapter*{伦理与来源说明}",
    r"\tableofcontents",
    r"\mainmatter",
    r"\appendix",
    r"\chapter{附录：记号、实验记录与术语}",
    r"\section{常用记号}",
    r"\section{实验记录清单}",
    r"\section{术语表}",
    r"\backmatter",
    r"\bibliographystyle{spmpsci}",
    r"\bibliography{references}",
]

CITE_RE = re.compile(
    r"\\(?:cite|citep|citet|citealp|citeauthor|citeyear)\s*(?:\[[^\]]*\]\s*){0,2}\{[^{}]+\}",
    re.DOTALL,
)
SECTION_RE = re.compile(r"\\section\{([^{}]+)\}")
ZH_CHAPTER_RE = re.compile(r"\\chapter\{([^{}]+)\}")


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


def section_span(text: str, section_name: str) -> tuple[int, int] | None:
    pattern = re.compile(rf"\\section\{{{re.escape(section_name)}\}}")
    match = pattern.search(text)
    if not match:
        return None
    next_match = re.search(r"\\section\{", text[match.end() :])
    end = match.end() + next_match.start() if next_match else len(text)
    return match.start(), end


def check_marker_order(text: str, markers: list[str], label: str, errors: list[str]) -> None:
    position = -1
    for marker in markers:
        index = text.find(marker)
        if index == -1:
            errors.append(f"{label}: missing required root marker {marker}")
            continue
        if index <= position:
            errors.append(f"{label}: root marker {marker} appears out of publication order")
        position = index


def check_root_scaffolding(errors: list[str]) -> None:
    en_root = strip_tex_comments(EN_ROOT.read_text(encoding="utf-8"))
    zh_root = strip_tex_comments(ZH_ROOT.read_text(encoding="utf-8"))

    check_marker_order(en_root, EN_ROOT_MARKERS, "English root", errors)
    check_marker_order(zh_root, ZH_ROOT_MARKERS, "Chinese root", errors)

    required_en_files = [
        BOOK_DIR / "preface.tex",
        BOOK_DIR / "ethics.tex",
        BOOK_DIR / "acronym.tex",
        BOOK_DIR / "appendix.tex",
        BOOK_DIR / "glossary.tex",
        BOOK_DIR / "references.bib",
    ]
    for path in required_en_files:
        if not path.exists():
            errors.append(f"Missing required publication file: {path.relative_to(ROOT).as_posix()}")

    if r"\makeindex" not in en_root:
        errors.append("English root: missing \\makeindex")
    if r"\printindex" in zh_root:
        errors.append("Chinese root: should not print the English makeindex index")

    en_front = en_root.find(r"\frontmatter")
    en_main = en_root.find(r"\mainmatter")
    en_appendix = en_root.find(r"\appendix")
    en_back = en_root.find(r"\backmatter")
    en_chapters = [en_root.find(rf"\include{{chapters/{path.stem}}}") for path in sorted(CHAPTER_DIR.glob("ch*.tex"))]
    if min(en_chapters, default=-1) < en_main or max(en_chapters, default=-1) > en_appendix:
        errors.append("English root: chapter includes must appear between \\mainmatter and \\appendix")
    if not (en_front < en_main < en_appendix < en_back):
        errors.append("English root: frontmatter/mainmatter/appendix/backmatter order is invalid")

    zh_main = zh_root.find(r"\mainmatter")
    zh_appendix = zh_root.find(r"\appendix")
    zh_back = zh_root.find(r"\backmatter")
    zh_content_chapters = [
        match.start()
        for match in ZH_CHAPTER_RE.finditer(zh_root)
        if not match.group(1).startswith("附录")
    ]
    if min(zh_content_chapters, default=-1) < zh_main or max(zh_content_chapters, default=-1) > zh_appendix:
        errors.append("Chinese root: content chapters must appear between \\mainmatter and \\appendix")
    if not (zh_main < zh_appendix < zh_back):
        errors.append("Chinese root: mainmatter/appendix/backmatter order is invalid")


def check_english_chapters(errors: list[str]) -> None:
    root = strip_tex_comments(EN_ROOT.read_text(encoding="utf-8"))
    include_names = re.findall(r"\\include\{chapters/([^{}]+)\}", root)
    included_paths = [CHAPTER_DIR / f"{name}.tex" for name in include_names]
    chapter_paths = sorted(CHAPTER_DIR.glob("ch*.tex"))

    if len(include_names) != EXPECTED_CHAPTERS:
        errors.append(f"English root includes {len(include_names)} chapters, expected {EXPECTED_CHAPTERS}")
    if set(included_paths) != set(chapter_paths):
        missing = sorted(path.name for path in set(chapter_paths) - set(included_paths))
        extra = sorted(path.name for path in set(included_paths) - set(chapter_paths))
        if missing:
            errors.append("English chapter files not included: " + ", ".join(missing))
        if extra:
            errors.append("English root includes missing chapter files: " + ", ".join(extra))

    for path in included_paths:
        text = strip_tex_comments(path.read_text(encoding="utf-8"))
        prefix = path.relative_to(ROOT).as_posix()

        if text.count(r"\chapter{") != 1:
            errors.append(f"{prefix}: expected exactly one chapter command")
        if not re.search(r"\\label\{ch:[^{}]+\}", text):
            errors.append(f"{prefix}: missing chapter label")
        if r"\abstract{" not in text:
            errors.append(f"{prefix}: missing chapter abstract")

        sections = SECTION_RE.findall(text)
        if len(sections) < 4:
            errors.append(f"{prefix}: has only {len(sections)} sections")
        for required in ("Key Terms", "Exercises"):
            if required not in sections:
                errors.append(f"{prefix}: missing {required} section")
        if "Key Terms" in sections and "Exercises" in sections and sections.index("Key Terms") > sections.index("Exercises"):
            errors.append(f"{prefix}: Exercises appears before Key Terms")

        key_span = section_span(text, "Key Terms")
        exercise_span = section_span(text, "Exercises")
        if key_span:
            key_items = len(re.findall(r"\\item\[", text[key_span[0] : key_span[1]]))
            if key_items < 4:
                errors.append(f"{prefix}: Key Terms section has only {key_items} definition items")
        if exercise_span:
            exercise_items = len(re.findall(r"\\item\b", text[exercise_span[0] : exercise_span[1]]))
            if exercise_items < 4:
                errors.append(f"{prefix}: Exercises section has only {exercise_items} items")

        body_end = key_span[0] if key_span else len(text)
        body = text[:body_end]
        if not CITE_RE.search(body):
            errors.append(f"{prefix}: body has no citations before Key Terms")
        if r"\index{" not in body:
            errors.append(f"{prefix}: body has no index entries before Key Terms")


def check_chinese_edition(errors: list[str]) -> None:
    text = strip_tex_comments(ZH_ROOT.read_text(encoding="utf-8"))
    chapters = list(ZH_CHAPTER_RE.finditer(text))
    non_appendix = [match for match in chapters if not match.group(1).startswith("附录")]

    if len(non_appendix) != EXPECTED_CHAPTERS:
        errors.append(f"Chinese edition has {len(non_appendix)} numbered content chapters, expected {EXPECTED_CHAPTERS}")

    for index, match in enumerate(non_appendix, start=1):
        next_match = chapters[chapters.index(match) + 1] if chapters.index(match) + 1 < len(chapters) else None
        block = text[match.start() : next_match.start() if next_match else len(text)]
        title = match.group(1)
        if r"\textbf{关键术语。}" not in block:
            errors.append(f"Chinese chapter {index} ({title}): missing key-term paragraph")
        if r"\textbf{练习。}" not in block:
            errors.append(f"Chinese chapter {index} ({title}): missing exercise paragraph")
        exercise_start = block.find(r"\textbf{练习。}")
        if exercise_start != -1:
            exercise_items = len(re.findall(r"\\item\b", block[exercise_start:]))
            if exercise_items < 3:
                errors.append(f"Chinese chapter {index} ({title}): exercise paragraph has only {exercise_items} items")


def check_source_boundaries(errors: list[str]) -> None:
    tex_files = [
        EN_ROOT,
        ZH_ROOT,
        BOOK_DIR / "preface.tex",
        BOOK_DIR / "ethics.tex",
        BOOK_DIR / "acronym.tex",
        BOOK_DIR / "glossary.tex",
        BOOK_DIR / "appendix.tex",
        *sorted(CHAPTER_DIR.glob("*.tex")),
    ]
    forbidden = {
        r"\includegraphics": "external image inclusion",
        r"\lstinputlisting": "external code listing",
        r"\verbatiminput": "external verbatim input",
        r"\inputminted": "external minted input",
    }
    for path in tex_files:
        text = strip_tex_comments(path.read_text(encoding="utf-8"))
        for marker, label in forbidden.items():
            if marker in text:
                errors.append(f"{path.relative_to(ROOT).as_posix()}: uses {label} ({marker})")


def main() -> int:
    errors: list[str] = []
    check_root_scaffolding(errors)
    check_english_chapters(errors)
    check_chinese_edition(errors)
    check_source_boundaries(errors)

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print(f"English chapters checked: {EXPECTED_CHAPTERS}")
    print(f"Chinese content chapters checked: {EXPECTED_CHAPTERS}")
    print("root publication structure, chapter structure, and source-boundary checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

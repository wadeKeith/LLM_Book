#!/usr/bin/env python3
"""Check appendix, acronym, and glossary back matter for publication readiness."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
EN_APPENDIX = BOOK_DIR / "appendix.tex"
ACRONYM_FILE = BOOK_DIR / "acronym.tex"
GLOSSARY_FILE = BOOK_DIR / "glossary.tex"
ZH_ROOT = BOOK_DIR / "book_zh.tex"

EXPECTED_EN_SECTIONS = ("Notation", "Experiment Records", "Source Provenance")
EXPECTED_ZH_SECTIONS = ("常用记号", "实验记录清单", "术语表")
EXPECTED_ACRONYMS = 20
EXPECTED_GLOSSARY_ENTRIES = 24
MIN_ZH_GLOSSARY_ENTRIES = 16

EN_NOTATION_MARKERS = (r"$T$", r"$d_{\mathrm{model}}$", r"$h$", r"$V$")
EN_RUN_CARD_MARKERS = (
    "Run identity",
    "Data contract",
    "Tokenization",
    "Model contract",
    "Optimization",
    "Execution",
    "Evaluation",
    "Failure analysis",
)
EN_PROVENANCE_MARKERS = (
    "original",
    "public primary sources",
    "does not include copied",
    "Exercises",
    "cited",
)

ZH_NOTATION_MARKERS = ("B 表示", "T 表示", "d 表示", "V 表示", "theta", "policy theta", "p theta")
ZH_RUN_CARD_MARKERS = (
    "代码版本",
    "数据版本",
    "数据许可证",
    "来源说明",
    "tokenizer",
    "聊天模板",
    "模型配置",
    "随机种子",
    "优化器",
    "学习率",
    "batch",
    "精度",
    "硬件",
    "预计运行时间",
    "checkpoint",
    "恢复语义",
    "验证集",
    "主要指标",
    "回归指标",
    "失败样例",
    "结论",
)

TODO_RE = re.compile(r"\b(?:TODO|FIXME|TBD|XXX)\b|\?\?\?|待补|lorem|dummy|citation needed|cite needed", re.IGNORECASE)
FORBIDDEN_SOURCE_RE = re.compile(r"\\(?:includegraphics|lstinputlisting|verbatiminput|inputminted)\b")
SECTION_RE = re.compile(r"\\section\{([^{}]+)\}")
ITEM_RE = re.compile(r"\\item\[([^{}\]]+)\]")


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


def section_body(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"\\section\{{{re.escape(heading)}\}}(.*?)(?=\\section\{{|\\chapter\{{|\\backmatter|\\end\{{document\}}|\Z)",
        re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1) if match else ""


def zh_appendix_text(text: str) -> str:
    match = re.search(r"\\chapter\{附录：记号、实验记录与术语\}(.*?)(?=\\backmatter|\Z)", text, re.DOTALL)
    return match.group(1) if match else ""


def description_items(text: str) -> list[str]:
    return [match.group(1).strip() for match in ITEM_RE.finditer(text)]


def check_source_clean(path: Path, text: str, errors: list[str]) -> None:
    rel = path.relative_to(ROOT).as_posix()
    if TODO_RE.search(text):
        errors.append(f"{rel}: back matter contains unresolved editorial marker text")
    if FORBIDDEN_SOURCE_RE.search(text):
        errors.append(f"{rel}: back matter imports external images or code listings")


def check_ordered_sections(found: list[str], expected: tuple[str, ...], label: str, errors: list[str]) -> int:
    hits = 0
    position = -1
    for heading in expected:
        if heading not in found:
            errors.append(f"{label}: missing section {heading!r}")
            continue
        hits += 1
        index = found.index(heading)
        if index <= position:
            errors.append(f"{label}: section {heading!r} appears out of order")
        position = index
    return hits


def marker_hits(markers: tuple[str, ...], body: str, label: str, errors: list[str]) -> int:
    hits = 0
    for marker in markers:
        if marker in body:
            hits += 1
        else:
            errors.append(f"{label}: missing marker {marker!r}")
    return hits


def check_duplicate_items(items: list[str], label: str, errors: list[str]) -> None:
    seen: set[str] = set()
    for item in items:
        key = re.sub(r"\s+", " ", item.casefold()).strip()
        if key in seen:
            errors.append(f"{label}: duplicate description item {item!r}")
        seen.add(key)


def main() -> int:
    errors: list[str] = []

    en_appendix = strip_tex_comments(EN_APPENDIX.read_text(encoding="utf-8"))
    acronym_text = strip_tex_comments(ACRONYM_FILE.read_text(encoding="utf-8"))
    glossary_text = strip_tex_comments(GLOSSARY_FILE.read_text(encoding="utf-8"))
    zh_text = strip_tex_comments(ZH_ROOT.read_text(encoding="utf-8"))
    zh_appendix = zh_appendix_text(zh_text)

    for path, text in (
        (EN_APPENDIX, en_appendix),
        (ACRONYM_FILE, acronym_text),
        (GLOSSARY_FILE, glossary_text),
        (ZH_ROOT, zh_appendix),
    ):
        check_source_clean(path, text, errors)

    en_sections = SECTION_RE.findall(en_appendix)
    en_section_hits = check_ordered_sections(en_sections, EXPECTED_EN_SECTIONS, "English appendix", errors)
    en_marker_hits = 0
    en_marker_total = len(EN_NOTATION_MARKERS) + len(EN_RUN_CARD_MARKERS) + len(EN_PROVENANCE_MARKERS)
    en_marker_hits += marker_hits(EN_NOTATION_MARKERS, section_body(en_appendix, "Notation"), "English appendix Notation", errors)
    en_marker_hits += marker_hits(EN_RUN_CARD_MARKERS, section_body(en_appendix, "Experiment Records"), "English appendix Experiment Records", errors)
    en_marker_hits += marker_hits(EN_PROVENANCE_MARKERS, section_body(en_appendix, "Source Provenance"), "English appendix Source Provenance", errors)
    if r"\label{tab:run-card-template}" not in en_appendix:
        errors.append("book/appendix.tex: missing tab:run-card-template label")
    if r"Table~\ref{tab:run-card-template}" not in en_appendix:
        errors.append("book/appendix.tex: run-card table is not referenced")

    acronym_items = description_items(acronym_text)
    glossary_items = description_items(glossary_text)
    check_duplicate_items(acronym_items, "Acronym list", errors)
    check_duplicate_items(glossary_items, "Glossary", errors)
    if len(acronym_items) != EXPECTED_ACRONYMS:
        errors.append(f"book/acronym.tex: acronym entries {len(acronym_items)}, expected {EXPECTED_ACRONYMS}")
    if len(glossary_items) != EXPECTED_GLOSSARY_ENTRIES:
        errors.append(f"book/glossary.tex: glossary entries {len(glossary_items)}, expected {EXPECTED_GLOSSARY_ENTRIES}")

    zh_sections = SECTION_RE.findall(zh_appendix)
    zh_section_hits = check_ordered_sections(zh_sections, EXPECTED_ZH_SECTIONS, "Chinese appendix", errors)
    zh_marker_hits = 0
    zh_marker_total = len(ZH_NOTATION_MARKERS) + len(ZH_RUN_CARD_MARKERS)
    zh_marker_hits += marker_hits(ZH_NOTATION_MARKERS, section_body(zh_appendix, "常用记号"), "Chinese appendix 常用记号", errors)
    zh_marker_hits += marker_hits(ZH_RUN_CARD_MARKERS, section_body(zh_appendix, "实验记录清单"), "Chinese appendix 实验记录清单", errors)
    zh_glossary_items = description_items(section_body(zh_appendix, "术语表"))
    check_duplicate_items(zh_glossary_items, "Chinese appendix glossary", errors)
    if len(zh_glossary_items) < MIN_ZH_GLOSSARY_ENTRIES:
        errors.append(
            f"book/book_zh.tex: Chinese appendix glossary entries {len(zh_glossary_items)}, "
            f"minimum is {MIN_ZH_GLOSSARY_ENTRIES}"
        )

    print(f"English appendix sections: {en_section_hits} / {len(EXPECTED_EN_SECTIONS)}")
    print(f"English appendix marker hits: {en_marker_hits} / {en_marker_total}")
    print(f"acronym entries: {len(acronym_items)}")
    print(f"glossary entries: {len(glossary_items)}")
    print(f"Chinese appendix sections: {zh_section_hits} / {len(EXPECTED_ZH_SECTIONS)}")
    print(f"Chinese appendix marker hits: {zh_marker_hits} / {zh_marker_total}")
    print(f"Chinese appendix glossary entries: {len(zh_glossary_items)}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("back-matter quality checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

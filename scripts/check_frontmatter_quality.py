#!/usr/bin/env python3
"""Check bilingual front-matter prose for publication-facing substance."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
EN_PREFACE = BOOK_DIR / "preface.tex"
EN_ETHICS = BOOK_DIR / "ethics.tex"
ZH_ROOT = BOOK_DIR / "book_zh.tex"

MIN_EN_PREFACE_WORDS = 300
MIN_EN_ETHICS_WORDS = 220
MIN_ZH_PREFACE_HAN = 350
MIN_ZH_ETHICS_HAN = 160

WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?")
HAN_RE = re.compile(r"[\u4e00-\u9fff]")
TODO_RE = re.compile(r"\b(?:TODO|FIXME|TBD|XXX)\b|\?\?\?|待补|lorem|dummy|citation needed|cite needed", re.IGNORECASE)
SOURCE_LEAK_RE = re.compile(r"\\(?:cite|ref|label|index|includegraphics|lstinputlisting|verbatiminput|inputminted)\b")


@dataclass(frozen=True)
class FrontMatterRecord:
    label: str
    path: Path
    raw: str
    plain: str
    word_count: int
    han_count: int
    required_markers: tuple[str, ...]


EN_PREFACE_MARKERS = (
    "original",
    "lifecycle",
    "evidence-first",
    "primary papers",
    "not a catalog",
    "coverage map",
)
EN_ETHICS_MARKERS = (
    "provenance",
    "does not reproduce",
    "privacy",
    "copyright",
    "benchmark contamination",
    "high-stakes",
    "legal advice",
)
ZH_PREFACE_MARKERS = (
    "中文可读版",
    "同一条论证路径",
    "原创",
    "公开论文",
    "生成式基础模型",
)
ZH_ETHICS_MARKERS = (
    "公开研究",
    "不复制",
    "许可证",
    "个人信息",
    "评测污染",
    "高风险",
)


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


def plain_text(raw: str) -> str:
    text = raw.replace("\\&", " and ").replace("\\%", " percent ")
    text = re.sub(
        r"\\(?:textbf|textit|emph|texttt|textsc)\*?(?:\[[^\]]*\])?\{([^{}]*)\}",
        r"\1",
        text,
    )
    text = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})?", " ", text)
    text = re.sub(r"[{}_^$~]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def zh_frontmatter_block(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"\\chapter\*\{{{re.escape(heading)}\}}(.*?)(?=\\chapter\*|\\tableofcontents|\\mainmatter|\Z)",
        re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1) if match else ""


def record(label: str, path: Path, raw: str, markers: tuple[str, ...]) -> FrontMatterRecord:
    plain = plain_text(raw)
    return FrontMatterRecord(
        label=label,
        path=path,
        raw=raw,
        plain=plain,
        word_count=len(WORD_RE.findall(plain)),
        han_count=len(HAN_RE.findall(plain)),
        required_markers=markers,
    )


def check_record(record: FrontMatterRecord, errors: list[str]) -> int:
    rel = record.path.relative_to(ROOT).as_posix()
    if TODO_RE.search(record.raw):
        errors.append(f"{rel}: {record.label} contains unresolved editorial marker text")
    if SOURCE_LEAK_RE.search(record.raw):
        errors.append(f"{rel}: {record.label} contains citation/reference/source-import commands")

    haystack = record.plain.lower()
    missing = 0
    for marker in record.required_markers:
        if marker.lower() not in haystack:
            errors.append(f"{rel}: {record.label} missing front-matter marker {marker!r}")
            missing += 1
    return len(record.required_markers) - missing


def main() -> int:
    errors: list[str] = []
    en_preface_text = strip_tex_comments(EN_PREFACE.read_text(encoding="utf-8"))
    en_ethics_text = strip_tex_comments(EN_ETHICS.read_text(encoding="utf-8"))
    zh_text = strip_tex_comments(ZH_ROOT.read_text(encoding="utf-8"))

    zh_preface_text = zh_frontmatter_block(zh_text, "前言")
    zh_ethics_text = zh_frontmatter_block(zh_text, "伦理与来源说明")
    if not zh_preface_text:
        errors.append("book/book_zh.tex: missing Chinese front-matter preface block")
    if not zh_ethics_text:
        errors.append("book/book_zh.tex: missing Chinese front-matter ethics block")

    records = [
        record("English preface", EN_PREFACE, en_preface_text, EN_PREFACE_MARKERS),
        record("English ethics", EN_ETHICS, en_ethics_text, EN_ETHICS_MARKERS),
        record("Chinese preface", ZH_ROOT, zh_preface_text, ZH_PREFACE_MARKERS),
        record("Chinese ethics", ZH_ROOT, zh_ethics_text, ZH_ETHICS_MARKERS),
    ]

    marker_hits = sum(check_record(item, errors) for item in records)
    marker_total = sum(len(item.required_markers) for item in records)

    if records[0].word_count < MIN_EN_PREFACE_WORDS:
        errors.append(f"book/preface.tex: English preface has {records[0].word_count} words, minimum is {MIN_EN_PREFACE_WORDS}")
    if records[1].word_count < MIN_EN_ETHICS_WORDS:
        errors.append(f"book/ethics.tex: English ethics has {records[1].word_count} words, minimum is {MIN_EN_ETHICS_WORDS}")
    if records[2].han_count < MIN_ZH_PREFACE_HAN:
        errors.append(f"book/book_zh.tex: Chinese preface has {records[2].han_count} Han characters, minimum is {MIN_ZH_PREFACE_HAN}")
    if records[3].han_count < MIN_ZH_ETHICS_HAN:
        errors.append(f"book/book_zh.tex: Chinese ethics has {records[3].han_count} Han characters, minimum is {MIN_ZH_ETHICS_HAN}")

    print(f"English preface words: {records[0].word_count} / {MIN_EN_PREFACE_WORDS}")
    print(f"English ethics words: {records[1].word_count} / {MIN_EN_ETHICS_WORDS}")
    print(f"Chinese preface Han characters: {records[2].han_count} / {MIN_ZH_PREFACE_HAN}")
    print(f"Chinese ethics Han characters: {records[3].han_count} / {MIN_ZH_ETHICS_HAN}")
    print(f"front-matter marker hits: {marker_hits} / {marker_total}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("front-matter quality checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

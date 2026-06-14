#!/usr/bin/env python3
"""Check that documented frontier coverage remains present in the manuscripts."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
CHAPTER_DIR = BOOK_DIR / "chapters"
ZH_ROOT = BOOK_DIR / "book_zh.tex"
BIBLIOGRAPHY = BOOK_DIR / "references.bib"

EN_SOURCES = [
    *sorted(CHAPTER_DIR.glob("ch*.tex")),
    BOOK_DIR / "preface.tex",
    BOOK_DIR / "ethics.tex",
    BOOK_DIR / "acronym.tex",
    BOOK_DIR / "glossary.tex",
    BOOK_DIR / "appendix.tex",
]

FRONTIER_CITATIONS = {
    "stanfordcs3362026",
    "feng2025frontier",
    "deepseek2025r1",
    "wen2025rlvr",
    "srivastava2025rlsurvey",
    "qwen2025qwen3vl",
    "qwen2025qwen3omni",
    "chen2025januspro",
    "yang2025mmada",
    "ye2025dream7b",
    "peebles2023dit",
    "esser2024rectifiedflow",
    "shen2025mammothmoda2",
    "cheng2026aromni",
    "brohan2023rt2",
    "kim2024openvla",
    "uddin2025vlasurvey",
    "huang2024vbenchpp",
    "guo2025t2vphysbench",
    "chen2026tocbench",
    "qiu2025unlearning",
    "kirchenbauer2023watermark",
    "nist2024syntheticcontent",
    "c2pa2026spec",
}


@dataclass(frozen=True)
class TopicCheck:
    label: str
    path: Path
    required_terms: tuple[str, ...]


EN_TOPIC_CHECKS = [
    TopicCheck(
        label="context engineering and typed memory",
        path=CHAPTER_DIR / "ch12_retrieval_tools_agents.tex",
        required_terms=("context engineering", "typed memory", "audit trail"),
    ),
    TopicCheck(
        label="post-DPO preference objectives",
        path=CHAPTER_DIR / "ch13_preference_learning_alignment.tex",
        required_terms=("IPO", "KTO", "ORPO", "SimPO"),
    ),
    TopicCheck(
        label="reasoning RL and adaptive compute",
        path=CHAPTER_DIR / "ch14_reasoning_test_time_compute.tex",
        required_terms=(
            "Reinforcement learning with verifiable rewards",
            "GRPO-style objectives",
            "Budget forcing",
        ),
    ),
    TopicCheck(
        label="unified multimodal generation objectives",
        path=CHAPTER_DIR / "ch15_multimodal_llms.tex",
        required_terms=(
            "Unified Understanding and Generation",
            "Diffusion and Rectified Flow",
            "Hybrid AR-Diffusion Systems",
        ),
    ),
    TopicCheck(
        label="VLA and world-model coverage",
        path=CHAPTER_DIR / "ch15_multimodal_llms.tex",
        required_terms=("Action, Embodiment, and World Models", "VLA report", "World models"),
    ),
    TopicCheck(
        label="generative and video evaluation",
        path=CHAPTER_DIR / "ch16_evaluation_safety_governance.tex",
        required_terms=("Generative multimodal systems", "VBench++", "T2VPhysBench", "TOC-Bench"),
    ),
    TopicCheck(
        label="technical governance levers",
        path=CHAPTER_DIR / "ch16_evaluation_safety_governance.tex",
        required_terms=("Unlearning", "Watermarking and provenance", "C2PA"),
    ),
    TopicCheck(
        label="frontier practice roadmap",
        path=CHAPTER_DIR / "ch17_research_frontiers_practice.tex",
        required_terms=(
            "Stanford's CS336",
            "resource accounting",
            "disaggregated inference",
            "RLVR and GRPO-style training",
            "Diffusion and rectified-flow",
            "VLA and action models",
        ),
    ),
]

ZH_TOPIC_TERMS = (
    "CS336",
    "context engineering",
    "typed memory",
    "KTO",
    "ORPO",
    "SimPO",
    "RLVR",
    "GRPO",
    "disaggregated inference",
    "统一多模态",
    "rectified flow",
    "Hybrid AR-diffusion",
    "VLA",
    "世界模型",
    "VBench++",
    "T2VPhysBench",
    "TOC-Bench",
    "Unlearning",
    "水印",
    "C2PA",
    "内容凭证",
)

CITE_RE = re.compile(
    r"\\(?:cite|citep|citet|citealp|citeauthor|citeyear)\s*(?:\[[^\]]*\]\s*){0,2}\{([^{}]+)\}",
    re.DOTALL,
)
BIB_KEY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)", re.MULTILINE)


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


def read_tex(path: Path) -> str:
    return strip_tex_comments(path.read_text(encoding="utf-8"))


def citation_keys(text: str) -> set[str]:
    keys: set[str] = set()
    for match in CITE_RE.finditer(text):
        keys.update(key.strip() for key in match.group(1).split(",") if key.strip())
    return keys


def contains_term(text: str, term: str) -> bool:
    return term.casefold() in text.casefold()


def check_bibliography(errors: list[str]) -> None:
    bib_keys = set(BIB_KEY_RE.findall(BIBLIOGRAPHY.read_text(encoding="utf-8")))
    missing = sorted(FRONTIER_CITATIONS - bib_keys)
    for key in missing:
        errors.append(f"book/references.bib: missing frontier bibliography key {key}")


def check_citations(errors: list[str]) -> tuple[int, int]:
    en_text = "\n".join(read_tex(path) for path in EN_SOURCES)
    zh_text = read_tex(ZH_ROOT)
    en_cites = citation_keys(en_text)
    zh_cites = citation_keys(zh_text)

    for key in sorted(FRONTIER_CITATIONS - en_cites):
        errors.append(f"English manuscript: missing frontier citation {key}")
    for key in sorted(FRONTIER_CITATIONS - zh_cites):
        errors.append(f"Chinese edition: missing frontier citation {key}")

    return len(FRONTIER_CITATIONS & en_cites), len(FRONTIER_CITATIONS & zh_cites)


def check_english_topics(errors: list[str]) -> int:
    hits = 0
    for check in EN_TOPIC_CHECKS:
        text = read_tex(check.path)
        prefix = check.path.relative_to(ROOT).as_posix()
        for term in check.required_terms:
            if contains_term(text, term):
                hits += 1
            else:
                errors.append(f"{prefix}: frontier topic '{check.label}' is missing term {term!r}")
    return hits


def check_chinese_topics(errors: list[str]) -> int:
    text = read_tex(ZH_ROOT)
    hits = 0
    for term in ZH_TOPIC_TERMS:
        if contains_term(text, term):
            hits += 1
        else:
            errors.append(f"book/book_zh.tex: missing Chinese frontier coverage term {term!r}")
    return hits


def main() -> int:
    errors: list[str] = []
    check_bibliography(errors)
    en_citation_hits, zh_citation_hits = check_citations(errors)
    en_topic_hits = check_english_topics(errors)
    zh_topic_hits = check_chinese_topics(errors)
    en_topic_total = sum(len(check.required_terms) for check in EN_TOPIC_CHECKS)

    print(f"frontier bibliography keys checked: {len(FRONTIER_CITATIONS)}")
    print(f"English frontier citation hits: {en_citation_hits} / {len(FRONTIER_CITATIONS)}")
    print(f"Chinese frontier citation hits: {zh_citation_hits} / {len(FRONTIER_CITATIONS)}")
    print(f"English frontier topic markers: {en_topic_hits} / {en_topic_total}")
    print(f"Chinese frontier topic markers: {zh_topic_hits} / {len(ZH_TOPIC_TERMS)}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("frontier coverage checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

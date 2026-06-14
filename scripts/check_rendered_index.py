#!/usr/bin/env python3
"""Check that the rendered English PDF index exposes key reader lookups."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
PDF = BOOK_DIR / "book.pdf"

REQUIRED_TERMS = (
    "ablation",
    "attention",
    "FlashAttention",
    "data",
    "provenance",
    "distributed training",
    "tensor parallelism",
    "evaluation",
    "benchmark contamination",
    "governance",
    "risk management",
    "inference serving",
    "continuous batching",
    "KV cache",
    "paged attention",
    "mixture of experts",
    "routing",
    "multimodal model",
    "unified generation",
    "parameter-efficient adaptation",
    "full fine-tuning",
    "preference objective",
    "direct preference optimization",
    "retrieval-augmented generation",
    "prompt injection",
    "safety",
    "red teaming",
    "test-time compute",
    "verification",
    "tokenization",
    "coverage",
    "Transformer",
    "decoder-only",
    "ZeRO",
)

REQUIRED_SEE_LINES = (
    ("agents", "agent"),
    ("BPE", "byte pair encoding"),
    ("CoT", "chain-of-thought prompting"),
    ("DPO", "direct preference optimization"),
    ("embeddings", "embedding model"),
    ("FFN", "feed-forward network"),
    ("fine-tuning", "parameter-efficient adaptation"),
    ("FSDP", "fully sharded data parallel"),
    ("GQA", "grouped-query attention"),
    ("GRPO", "group relative policy optimization"),
    ("human feedback", "RLHF"),
    ("KV", "KV cache"),
    ("LLM", "large language model"),
    ("long context", "context window"),
    ("MHA", "multi-head attention"),
    ("MLA", "multi-head latent attention"),
    ("model judge", "LLM-as-judge"),
    ("MoE", "mixture of experts"),
    ("MQA", "multi-query attention"),
    ("PEFT", "parameter-efficient adaptation"),
    ("PPO", "proximal policy optimization"),
    ("RAG", "retrieval-augmented generation"),
    ("red team", "red teaming"),
    ("reinforcement learning from human feedback", "RLHF"),
    ("reinforcement learning with verifiable rewards", "RLVR"),
    ("RoPE", "rotary position embedding"),
    ("SFT", "supervised instruction tuning"),
    ("supervised fine tuning", "instruction tuning"),
    ("tools", "tool use"),
    ("vector database", "vector index"),
    ("VLM", "vision-language model"),
)

INDEX_HEADER_RE = re.compile(r"^(?:\d+\s+)?Index(?:\s+\d+)?$")
RAW_INDEX_LEAK_RE = re.compile(r"\\(?:item|subitem|subsubitem|hyperpage|indexspace)\b")


def extract_pdf_text() -> str:
    if not PDF.exists():
        raise FileNotFoundError(f"{PDF.relative_to(ROOT).as_posix()} does not exist")
    pdftotext = os.environ.get("PDFTOTEXT", "pdftotext")
    if shutil.which(pdftotext) is None:
        raise RuntimeError("pdftotext is required for rendered index checks")

    result = subprocess.run(
        [pdftotext, "-layout", str(PDF), "-"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RuntimeError(f"pdftotext failed for {PDF.relative_to(ROOT).as_posix()}: {stderr}")
    return result.stdout


def nonempty_lines(page_text: str) -> list[str]:
    return [line.rstrip() for line in page_text.splitlines() if line.strip()]


def is_index_page(page_text: str) -> bool:
    lines = nonempty_lines(page_text)
    if not lines:
        return False
    header = re.sub(r"\s+", " ", lines[0]).strip()
    return bool(INDEX_HEADER_RE.fullmatch(header))


def last_contiguous_cluster(page_numbers: list[int]) -> list[int]:
    clusters: list[list[int]] = []
    for number in page_numbers:
        if not clusters or number != clusters[-1][-1] + 1:
            clusters.append([number])
        else:
            clusters[-1].append(number)
    return clusters[-1] if clusters else []


def rendered_index_pages(raw_text: str) -> tuple[list[int], str, list[str]]:
    pages = raw_text.split("\f")
    page_numbers = [index for index, page in enumerate(pages, start=1) if is_index_page(page)]
    cluster = last_contiguous_cluster(page_numbers)
    if not cluster:
        return [], "", []

    index_pages = [pages[number - 1] for number in cluster]
    body_lines: list[str] = []
    for page in index_pages:
        lines = nonempty_lines(page)
        if lines and INDEX_HEADER_RE.fullmatch(re.sub(r"\s+", " ", lines[0]).strip()):
            lines = lines[1:]
        body_lines.extend(lines)

    return cluster, "\n".join(index_pages), body_lines


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def term_pattern(term: str) -> re.Pattern[str]:
    if term.isascii() and re.search(r"[A-Za-z0-9]", term):
        return re.compile(r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])")
    return re.compile(re.escape(term))


def main() -> int:
    errors: list[str] = []
    try:
        raw_text = extract_pdf_text()
    except (FileNotFoundError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    page_numbers, index_text, body_lines = rendered_index_pages(raw_text)
    normalized = normalize(index_text)

    if not page_numbers:
        errors.append("English PDF: could not isolate the rendered index pages")
    elif len(page_numbers) < 4:
        errors.append(f"English PDF: rendered index has only {len(page_numbers)} pages; expected at least 4")

    if len(body_lines) < 180:
        errors.append(f"English PDF: rendered index has only {len(body_lines)} nonempty body lines")

    if RAW_INDEX_LEAK_RE.search(index_text):
        errors.append("English PDF: rendered index contains raw makeindex commands")

    missing_terms = [term for term in REQUIRED_TERMS if not term_pattern(term).search(normalized)]
    for term in missing_terms:
        errors.append(f"English PDF: rendered index is missing required term {term!r}")

    missing_see_lines: list[str] = []
    for alias, target in REQUIRED_SEE_LINES:
        see_line = f"{alias}, see {target}"
        see_pattern = re.compile(re.escape(alias) + r",.{0,140}?see " + re.escape(target))
        if not see_pattern.search(normalized):
            missing_see_lines.append(see_line)
    for see_line in missing_see_lines:
        errors.append(f"English PDF: rendered index is missing see line {see_line!r}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    span = f"{page_numbers[0]}--{page_numbers[-1]}" if page_numbers else "n/a"
    print(f"rendered index pages: {len(page_numbers)}")
    print(f"rendered index PDF page span: {span}")
    print(f"rendered index nonempty body lines: {len(body_lines)}")
    print(f"rendered index required terms: {len(REQUIRED_TERMS) - len(missing_terms)} / {len(REQUIRED_TERMS)}")
    print(f"rendered index see aliases: {len(REQUIRED_SEE_LINES) - len(missing_see_lines)} / {len(REQUIRED_SEE_LINES)}")
    print("rendered index checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

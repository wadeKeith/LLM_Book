#!/usr/bin/env python3
"""Check chapter-level alignment between English and Chinese editions."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
CHAPTER_DIR = BOOK_DIR / "chapters"
EN_ROOT = BOOK_DIR / "book.tex"
ZH_ROOT = BOOK_DIR / "book_zh.tex"


@dataclass(frozen=True)
class EditionChapter:
    english_file: str
    english_title: str
    chinese_title: str
    chinese_anchor_terms: tuple[str, ...]


EXPECTED_CHAPTERS = (
    EditionChapter(
        "ch01_what_makes_language_models_large",
        "What Makes a Language Model Large",
        "什么使语言模型变大",
        ("条件语言模型", "基础模型", "后训练", "推理预算", "系统边界"),
    ),
    EditionChapter(
        "ch02_tokens_corpora_training_signals",
        "Tokens, Corpora, and Training Signals",
        "Token、语料与训练信号",
        ("Token fertility", "data manifest", "去重", "评测污染", "label mask"),
    ),
    EditionChapter(
        "ch03_transformer_mechanics",
        "Transformer Mechanics",
        r"\Transformer 机制",
        ("Residual stream", "causal mask", "multi-head attention", "pre-norm", "attention weights"),
    ),
    EditionChapter(
        "ch04_from_transformer_to_gpt",
        "From Transformer to GPT",
        r"从 \Transformer 到 GPT",
        ("Decoder-only model", "in-context learning", "weight tying", "chat template", "structured output"),
    ),
    EditionChapter(
        "ch05_llama_class_architectures",
        "LLaMA-Class Architectures",
        "LLaMA 类架构",
        ("RoPE", "YaRN", "RMSNorm", "SwiGLU", "GQA", "MLA", "MoE"),
    ),
    EditionChapter(
        "ch06_optimization_pretraining",
        "Optimization and Pretraining",
        "优化与预训练",
        ("Scaling law", "Chinchilla-optimal", "MTP", "AdamW", "warmup", "FP8 scaling"),
    ),
    EditionChapter(
        "ch07_distributed_training_systems",
        "Distributed Training Systems",
        "分布式训练系统",
        ("Data parallelism", "FSDP", "ZeRO", "tensor parallelism", "pipeline parallelism", "expert parallelism"),
    ),
    EditionChapter(
        "ch08_inference_serving",
        "Inference and Serving",
        "推理与服务",
        ("Prefill", "decode", "KV cache", "paged attention", "Medusa", "chunk-prefill", "tail latency"),
    ),
    EditionChapter(
        "ch09_supervised_instruction_tuning",
        "Supervised Instruction Tuning",
        "监督指令微调",
        ("Demonstration data", "assistant-only loss", "self-instruction", "distillation", "capability regression"),
    ),
    EditionChapter(
        "ch10_parameter_efficient_adaptation",
        "Parameter-Efficient Adaptation",
        "参数高效适配",
        ("Adapter", "zero-gated prompt adapter", "prefix tuning", "LoRA", "QLoRA", "NF4", "double quantization"),
    ),
    EditionChapter(
        "ch11_domain_language_adaptation",
        "Domain and Language Adaptation",
        "领域与语言适配",
        ("Continual pretraining", "domain adaptation", "token fertility", "vocabulary extension", "RAG", "NL2SQL"),
    ),
    EditionChapter(
        "ch12_retrieval_tools_agents",
        "Retrieval, Tools, and Agents",
        "检索、工具与 Agent",
        (
            "Chunk",
            "dense retrieval",
            "hybrid retrieval",
            "reranker",
            "latent-document marginalization",
            "non-parametric memory",
            "context engineering",
            "prompt injection",
        ),
    ),
    EditionChapter(
        "ch13_preference_learning_alignment",
        "Preference Learning and Alignment",
        "偏好学习与对齐",
        (
            "Preference data",
            "reward model",
            "MDP",
            "advantage",
            "KL regularization",
            "DPO",
            "response-only log probability",
            "reference-free objective",
            "reward hacking",
        ),
    ),
    EditionChapter(
        "ch14_reasoning_test_time_compute",
        "Reasoning and Test-Time Compute",
        "推理与测试时计算",
        ("Chain-of-thought", "self-consistency", "thought decomposition", "verifier", "RLVR", "GRPO", "budget forcing"),
    ),
    EditionChapter(
        "ch15_multimodal_llms",
        "Multimodal and Generative Foundation Models",
        "多模态与生成式基础模型",
        ("Vision encoder", "connector", "unified understanding-generation model", "diffusion model", "VLA model", "world model"),
    ),
    EditionChapter(
        "ch16_evaluation_safety_governance",
        "Evaluation, Safety, and Governance",
        "评测、安全与治理",
        ("Construct", "evaluation harness", "benchmark contamination", "模型裁判", "red teaming", "unlearning", "content credentials"),
    ),
    EditionChapter(
        "ch17_research_frontiers_practice",
        "Research Frontiers and Practice Roadmap",
        "研究前沿与实践路线",
        ("From-scratch implementation", "resource accounting", "adaptive test-time compute", "generative foundation model", "前沿证据矩阵"),
    ),
)

CHAPTER_RE = re.compile(r"\\chapter\{([^{}]+)\}")


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


def included_english_chapters() -> list[str]:
    text = strip_tex_comments(EN_ROOT.read_text(encoding="utf-8"))
    return re.findall(r"\\include\{chapters/([^{}]+)\}", text)


def english_title(stem: str) -> str | None:
    path = CHAPTER_DIR / f"{stem}.tex"
    if not path.exists():
        return None
    text = strip_tex_comments(path.read_text(encoding="utf-8"))
    match = CHAPTER_RE.search(text)
    return match.group(1) if match else None


def chinese_chapter_blocks() -> list[tuple[str, str]]:
    text = strip_tex_comments(ZH_ROOT.read_text(encoding="utf-8"))
    chapters = list(CHAPTER_RE.finditer(text))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(chapters):
        title = match.group(1)
        if title.startswith("附录"):
            continue
        next_match = chapters[index + 1] if index + 1 < len(chapters) else None
        block = text[match.start() : next_match.start() if next_match else len(text)]
        blocks.append((title, block))
    return blocks


def contains_term(text: str, term: str) -> bool:
    return term.casefold() in text.casefold()


def check_english_order(errors: list[str]) -> None:
    expected_stems = [item.english_file for item in EXPECTED_CHAPTERS]
    included = included_english_chapters()

    if included != expected_stems:
        errors.append(
            "book/book.tex: English chapter include order changed; expected "
            + ", ".join(expected_stems)
            + " but found "
            + ", ".join(included)
        )

    for item in EXPECTED_CHAPTERS:
        title = english_title(item.english_file)
        if title is None:
            errors.append(f"book/chapters/{item.english_file}.tex: missing chapter file or title")
        elif title != item.english_title:
            errors.append(
                f"book/chapters/{item.english_file}.tex: title drifted; "
                f"expected {item.english_title!r}, found {title!r}"
            )


def check_chinese_alignment(errors: list[str]) -> tuple[int, int]:
    blocks = chinese_chapter_blocks()
    expected_titles = [item.chinese_title for item in EXPECTED_CHAPTERS]
    found_titles = [title for title, _block in blocks]

    if found_titles != expected_titles:
        errors.append(
            "book/book_zh.tex: Chinese chapter order/title alignment changed; expected "
            + ", ".join(expected_titles)
            + " but found "
            + ", ".join(found_titles)
        )

    anchor_hits = 0
    anchor_total = 0
    for number, item in enumerate(EXPECTED_CHAPTERS, start=1):
        block = blocks[number - 1][1] if number - 1 < len(blocks) else ""
        for term in item.chinese_anchor_terms:
            anchor_total += 1
            if contains_term(block, term):
                anchor_hits += 1
            else:
                errors.append(
                    f"book/book_zh.tex: chapter {number} ({item.chinese_title}) "
                    f"is missing alignment anchor {term!r}"
                )

    return anchor_hits, anchor_total


def main() -> int:
    errors: list[str] = []
    check_english_order(errors)
    anchor_hits, anchor_total = check_chinese_alignment(errors)

    print(f"edition chapter pairs checked: {len(EXPECTED_CHAPTERS)}")
    print(f"Chinese edition alignment anchors: {anchor_hits} / {anchor_total}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("edition alignment checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

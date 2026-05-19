# Frontier Gap Review

Date: 2026-05-20

## Review Basis

- Current English manuscript structure and citations.
- Stanford CS336 2026 and 2025 public course pages.
- Recent public papers and technical reports on reasoning RL, adaptive test-time compute, MoE/disaggregated inference, and multimodal frontier models.

## Findings

The manuscript already covers the core LLM lifecycle: tokenization, data, Transformer/GPT/LLaMA architecture, pretraining, distributed training, inference, SFT, PEFT, domain adaptation, RAG, tool use, preference learning, reasoning, multimodality, evaluation, safety, and governance.

The main missing layer was not another foundational chapter but a synthesis chapter connecting the book to current practice:

- CS336-style from-scratch implementation discipline.
- Resource accounting for FLOPs, memory, bandwidth, and tokens per second.
- MoE and disaggregated inference as serving-system design problems.
- Adaptive test-time compute and budgeted reasoning.
- RLVR/GRPO as part of the broader RL-for-LLMs design space.
- Native multimodal systems beyond image-text alignment.
- A reader roadmap for implementation projects and future updates.

## Changes Made

- Added Chapter 17, `Research Frontiers and Practice Roadmap`.
- Added references for CS336, Qwen3-VL, Qwen3-Omni, Kimi/WebGPT support, test-time scaling surveys, RL-for-LLMs survey, and next-generation inference simulation.
- Added `book_zh.tex`, an independent Chinese version with the same 17-chapter book structure.
- Added `.DS_Store` to `.gitignore`.

## Remaining Non-Blocking Work

- The English manuscript is now the fuller publication draft.
- The Chinese manuscript is a complete standalone Chinese edition by structure and coverage, but it is shorter than the English manuscript; future work can expand it paragraph-for-paragraph if a print-length Chinese edition is desired.
- The index remains light and should be expanded if the project moves from public draft to formal press-style release.

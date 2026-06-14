# Frontier Gap Review

Date: 2026-05-20

## Review Basis

- Current English manuscript structure and citations.
- Stanford CS336 2026 and 2025 public course pages.
- Recent public papers and technical reports on reasoning RL, adaptive test-time compute, MoE/disaggregated inference, long-context evaluation, context engineering, post-DPO preference objectives, multimodal frontier models, unified understanding-generation systems, diffusion language models, rectified-flow image generation, AR-diffusion hybrid systems, vision-language-action models, video-generation benchmarks, and synthetic-content provenance.

## Findings

The manuscript now targets large language and generative foundation models. It covers the core LLM lifecycle: tokenization, data, Transformer/GPT/LLaMA architecture, pretraining, distributed training, inference, SFT, PEFT, domain adaptation, RAG, context engineering, tool use, preference learning, reasoning, multimodality, generation, evaluation, safety, and governance.

The main missing layer was not another foundational chapter but a synthesis chapter connecting the book to current practice:

- CS336-style from-scratch implementation discipline.
- Resource accounting for FLOPs, memory, bandwidth, and tokens per second.
- MoE and disaggregated inference as serving-system design problems.
- Adaptive test-time compute and budgeted reasoning.
- RLVR/GRPO as part of the broader RL-for-LLMs design space.
- Native multimodal systems beyond image-text alignment.
- Unified understanding-generation models and any-to-any omni systems.
- Diffusion, rectified-flow, and hybrid AR-diffusion objectives as part of the broader generative-foundation-model curriculum.
- VLA/action models and world-model framing as the boundary where multimodal generation touches physical or simulated control.
- Video generation and video understanding evaluation beyond visual plausibility, including temporal consistency and physical consistency.
- Interpretability, unlearning, and watermarking as technical governance levers.
- Synthetic-content transparency and provenance standards such as NIST AI 100-4 and C2PA.
- A reader roadmap for implementation projects and future updates.

## Changes Made

- Added Chapter 17, `Research Frontiers and Practice Roadmap`.
- Broadened Chapter 15 from multimodal LLMs to multimodal and generative foundation models.
- Added coverage for context engineering and typed memory, post-DPO preference objectives, unified understanding-generation models, diffusion language models, rectified-flow and DiT-style visual generation, AR-diffusion hybrids, long-context/agentic/generative evaluation, interpretability, unlearning, and watermarking.
- Added coverage for VLA/action models, world-model framing, video-generation evaluation, embodied evaluation, and synthetic-content provenance.
- Added references for CS336, Qwen3-VL, Qwen3-Omni, Kimi/WebGPT support, test-time scaling surveys, RL-for-LLMs survey, next-generation inference simulation, Janus-Pro, MMaDA, Dream 7B, DiT, Sora, rectified-flow transformers, MammothModa2, AR-Omni, RT-2, OpenVLA, VLA surveys, VBench++, T2VPhysBench, TOC-Bench, NIST synthetic-content transparency, and C2PA.
- Updated `book_zh.tex` so the Chinese version is framed as a readable translation of the English edition, not a core-argument summary, and synchronized the new coverage.
- Added `.DS_Store` to `.gitignore`.
- Expanded the English body index across all 17 chapters so the final `\printindex` covers core concepts beyond glossary entries.
- Added `make frontier-coverage-check` so the documented frontier layer is now a release gate for both manuscripts. The latest run checks 24 required frontier bibliography keys, 24/24 English frontier citation hits, 24/24 Chinese frontier citation hits, 29/29 English frontier topic markers, and 21/21 Chinese frontier topic markers.

## Remaining Non-Blocking Work

- The English manuscript is the controlling publication draft.
- The Chinese manuscript follows the English chapter structure and has been moved toward a readable translated edition. `make bilingual-coverage-check` now quantifies substantive chapter coverage, while `make bilingual-print-plan` and `make bilingual-alignment-check` track the active paragraph-for-paragraph bilingual print objective.
- The English index now has source and rendered gates for high-value reader aliases, capitalization, component punctuation, required canonical topic paths, and required parent-subentry grouping. A publisher-requested professional indexer could still review topic wording, but the current technical draft no longer carries an open index P2.

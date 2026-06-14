# Paragraph-Level Bilingual Print Plan

Date: 2026-06-12

## Purpose

The current Chinese manuscript is a substantive readable edition, but the active publication goal is now stricter: a paragraph-level bilingual print edition. Under this goal, every publication-facing English source unit needs an explicitly paired Chinese counterpart, and the pair needs bilingual proofreading after the rendered PDF fingerprint changes.

This plan is the source-unit inventory for that work. It does not mark the bilingual print edition complete; it makes the remaining work measurable.

## Repeatable Command

From the repository root:

```bash
make bilingual-print-plan
make bilingual-print-artifact-check
make bilingual-print-proofing-check
```

`make bilingual-print-plan` reports the current English source-unit inventory for a paragraph-level bilingual print edition. It counts chapter abstracts, chapter contracts, ordinary prose paragraphs before Key Terms, figure/table captions, Key Terms entries, Exercise items, and front/back matter units. `make bilingual-print-artifact-check` writes a paragraph-level bilingual proofing draft outside the release tree, pairing each current English source unit with the Chinese counterpart from `notes/bilingual_alignment_manifest.md`, then verifies that the rendered artifact contains every aligned source-unit ID. `make bilingual-print-proofing-check` validates `notes/bilingual_print_proofing_log.md` against the current rendered text fingerprint, reviewed page ranges, and manifest `Proofed` rows. These are hard generated-artifact and proofing-log gates for the completed paragraph-level bilingual print pass.

## Current Status

- Bilingual print status: Complete; source-level alignment is complete, the rendered bilingual proofing draft builds, and BP-01 through BP-22 have proofed Chapters 1--17 plus the tracked front/back matter under the current rendered text fingerprint.
- Chapter source units requiring explicit bilingual pairing: 1105.
- Front/back matter source units requiring explicit bilingual pairing: 58.
- Total source units requiring explicit bilingual pairing: 1163.
- Explicitly recorded aligned source units: 1163.
- Proofed bilingual print source units: 1163.
- Open source units: 0.

The `1163` aligned units are recorded in `notes/bilingual_alignment_manifest.md`; all 1163 proofed units are tied to BP-01 through BP-22 in `notes/bilingual_print_proofing_log.md`, leaving 0 aligned units still needing rendered bilingual print proofing. The existing Chinese prose has now been mapped as explicit source-level pairs, and `make bilingual-print-artifact-check` renders those pairs into `/tmp/llm_book_bilingual_print/book_bilingual_print.pdf` for proofing. The current generated proofing draft builds as a 647-page PDF, contains 1163/1163 rendered source-unit IDs, and has rendered text SHA-256 `caefc5aa856c352f465ff17f991612ddac7a5e8fb29056fb4bb83cbbb84e83c1`.

The latest alignment gate reports 1163 source units, 1163 manifest rows, 1163 aligned units, 1163 proofed units, 0 open units, and 0 manifest errors.

## Chapter Unit Inventory

| Chapter | English title | Abstract | Contract | Prose | Captions | Key terms | Exercises | Units |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 01 | What Makes a Language Model Large | 1 | 1 | 22 | 2 | 5 | 5 | 36 |
| 02 | Tokens, Corpora, and Training Signals | 1 | 1 | 35 | 2 | 6 | 5 | 50 |
| 03 | Transformer Mechanics | 1 | 1 | 36 | 2 | 6 | 5 | 51 |
| 04 | From Transformer to GPT | 1 | 1 | 34 | 2 | 8 | 7 | 53 |
| 05 | LLaMA-Class Architectures | 1 | 1 | 48 | 2 | 9 | 8 | 69 |
| 06 | Optimization and Pretraining | 1 | 1 | 45 | 3 | 8 | 8 | 66 |
| 07 | Distributed Training Systems | 1 | 1 | 63 | 3 | 12 | 12 | 92 |
| 08 | Inference and Serving | 1 | 1 | 49 | 5 | 11 | 7 | 74 |
| 09 | Supervised Instruction Tuning | 1 | 1 | 41 | 2 | 7 | 7 | 59 |
| 10 | Parameter-Efficient Adaptation | 1 | 1 | 46 | 3 | 16 | 9 | 76 |
| 11 | Domain and Language Adaptation | 1 | 1 | 39 | 2 | 7 | 7 | 57 |
| 12 | Retrieval, Tools, and Agents | 1 | 1 | 41 | 3 | 11 | 9 | 66 |
| 13 | Preference Learning and Alignment | 1 | 1 | 51 | 3 | 13 | 10 | 79 |
| 14 | Reasoning and Test-Time Compute | 1 | 1 | 45 | 2 | 11 | 7 | 67 |
| 15 | Multimodal and Generative Foundation Models | 1 | 1 | 52 | 4 | 14 | 9 | 81 |
| 16 | Evaluation, Safety, and Governance | 1 | 1 | 50 | 3 | 13 | 11 | 79 |
| 17 | Research Frontiers and Practice Roadmap | 1 | 1 | 31 | 3 | 7 | 7 | 50 |

## Front And Back Matter Inventory

| Front/back matter | Units |
| --- | ---: |
| Preface | 5 |
| Responsible use | 5 |
| Appendix prose | 4 |
| Acronym entries | 20 |
| Glossary entries | 24 |

## Priority

Paragraph-level bilingual source alignment and rendered proofing are complete. Chapters 1 through 17 and the tracked front/back matter are source-level aligned in the manifest and proofed under BP-01 through BP-22.

| Priority | Chapter | Reason |
| --- | --- | --- |
| Proofed | 01 What Makes a Language Model Large | 36 explicit source units are source-level aligned and proofed in BP-01 on pages 47--66. |
| Proofed | 02 Tokens, Corpora, and Training Signals | 50 explicit source units are source-level aligned and proofed in BP-02 on pages 67--92. |
| Proofed | 03 Transformer Mechanics | 51 explicit source units are source-level aligned and proofed in BP-03 on pages 93--115. |
| Proofed | 04 From Transformer to GPT | 53 explicit source units are source-level aligned and proofed in BP-04 on pages 116--140. |
| Proofed | 05 LLaMA-Class Architectures | 69 explicit source units are source-level aligned and proofed in BP-05 on pages 142--176. |
| Proofed | 06 Optimization and Pretraining | 66 explicit source units are source-level aligned and proofed in BP-06 on pages 177--210. |
| Proofed | 07 Distributed Training Systems | 92 explicit source units are source-level aligned and proofed in BP-07 on pages 211--258. |
| Proofed | 08 Inference and Serving | 74 explicit source units are source-level aligned and proofed in BP-08 on pages 260--297. |
| Proofed | 09 Supervised Instruction Tuning | 59 explicit source units are source-level aligned and proofed in BP-09 on pages 299--329. |
| Proofed | 10 Parameter-Efficient Adaptation | 76 explicit source units are source-level aligned and proofed in BP-10 on pages 331--369. |
| Proofed | 11 Domain and Language Adaptation | 57 explicit source units are source-level aligned and proofed in BP-11 on pages 370--398. |
| Proofed | 12 Retrieval, Tools, and Agents | 66 explicit source units are source-level aligned and proofed in BP-12 on pages 399--431. |
| Proofed | 13 Preference Learning and Alignment | 79 explicit source units are source-level aligned and proofed in BP-13 on pages 432--474. |
| Proofed | 14 Reasoning and Test-Time Compute | 67 explicit source units are source-level aligned and proofed in BP-14 on pages 475--509. |
| Proofed | 15 Multimodal and Generative Foundation Models | 81 explicit source units are source-level aligned and proofed in BP-15 on pages 510--551. |
| Proofed | 16 Evaluation, Safety, and Governance | 79 explicit source units are source-level aligned and proofed in BP-16 on pages 552--592. |
| Proofed | 17 Research Frontiers and Practice Roadmap | 50 explicit source units are source-level aligned and proofed in BP-17 on pages 593--619. |
| Proofed | Front/back matter | 58 explicit source units are source-level aligned and proofed in BP-18--BP-22 on pages 620--647. |

## Chapter 1 Proofing Batch

All 36 Chapter 1 source units are now recorded as `Proofed` in `notes/bilingual_alignment_manifest.md`, including the lifecycle framing, scale-axis discussion, next-token prediction interface, scaling-law and emergence cautions, base-to-assistant transition, reasoning and test-time-compute sections, roadmap, publication-grade reading protocol, captions, Key Terms, and Exercises. BP-01 in `notes/bilingual_print_proofing_log.md` covers `ch01-abstract--ch01-exercise-005` on rendered pages 47--66 under SHA-256 `caefc5aa856c352f465ff17f991612ddac7a5e8fb29056fb4bb83cbbb84e83c1`.

## Chapter 2 Proofing Batch

All 50 Chapter 2 source units are now recorded as `Proofed` in `notes/bilingual_alignment_manifest.md`, including the data-contract framing, tokenizer and token-efficiency prose, corpus-manifest and mixture-weight sections, filtering and deduplication discussion, sequence-packing and binary-stream contracts, post-pretraining signal taxonomy, contamination and provenance material, captions, Key Terms, and Exercises. BP-02 in `notes/bilingual_print_proofing_log.md` covers `ch02-abstract--ch02-exercise-005` on rendered pages 67--92 under SHA-256 `caefc5aa856c352f465ff17f991612ddac7a5e8fb29056fb4bb83cbbb84e83c1` after tightening equation-adjacent and caption counterparts.

## Chapter 3 Proofing Batch

All 51 Chapter 3 source units are now recorded as `Proofed` in `notes/bilingual_alignment_manifest.md`, including tensor-contract prose, embeddings and position mechanisms, scaled dot-product attention, mask and causality discussion, residual/norm and feed-forward sections, debugging invariants, diagram-to-tests material, captions, Key Terms, and Exercises. BP-03 in `notes/bilingual_print_proofing_log.md` covers `ch03-abstract--ch03-exercise-005` on rendered pages 93--115 under SHA-256 `caefc5aa856c352f465ff17f991612ddac7a5e8fb29056fb4bb83cbbb84e83c1` after tightening formula-adjacent counterparts, adding the missing `masked_fill` convention sentence, and narrowing the final mask-convention exercise to match the English source unit.

## Chapter 4 Proofing Batch

All 53 Chapter 4 source units are now recorded as `Proofed` in `notes/bilingual_alignment_manifest.md`, including decoder-only contract prose, next-token loss and label-shift material, minimal GPT block-stack implementation details, batching and loss-curve sections, decoding controls, KV-cache and FlashAttention discussion, evaluation cautions, chat-interface contracts, captions, Key Terms, and Exercises. BP-04 in `notes/bilingual_print_proofing_log.md` covers `ch04-abstract--ch04-exercise-007` on rendered pages 116--140 under SHA-256 `caefc5aa856c352f465ff17f991612ddac7a5e8fb29056fb4bb83cbbb84e83c1` after tightening formula-adjacent counterparts, restoring the chat-template post-equation content to the correct source unit, clarifying the nanoGPT accumulation detail, and aligning the decoding-controls caption.

## Chapter 5 Proofing Batch

All 69 Chapter 5 source units are now recorded as `Proofed` in `notes/bilingual_alignment_manifest.md`, including LLaMA-class decoder defaults, RMSNorm and pre-normalization, SwiGLU, RoPE and YaRN scaling, cache alignment, KV-cache and attention variants, tokenizer/vocabulary contracts, long-context cautions, MoE variants, alternative sequence backbones, architectural accounting, captions, Key Terms, and Exercises. BP-05 in `notes/bilingual_print_proofing_log.md` covers `ch05-abstract--ch05-exercise-008` on rendered pages 142--176 under SHA-256 `caefc5aa856c352f465ff17f991612ddac7a5e8fb29056fb4bb83cbbb84e83c1` after tightening formula-adjacent counterparts, the KV-cache table caption, short Key Term definitions, and exercise prompts.

## Chapter 6 Proofing Batch

All 66 Chapter 6 source units are now recorded as `Proofed` in `notes/bilingual_alignment_manifest.md`, including pretraining-objective prose, data-order and validation-slice sections, auxiliary MTP objective material, AdamW and parameter-group discussion, schedules, warmup, batch-size accounting, gradient clipping, mixed precision and FP8 sections, checkpointing and recovery, compute-optimal planning, monitoring, run-card requirements, captions, Key Terms, and Exercises. BP-06 in `notes/bilingual_print_proofing_log.md` covers `ch06-abstract--ch06-exercise-008` on rendered pages 177--210 under SHA-256 `caefc5aa856c352f465ff17f991612ddac7a5e8fb29056fb4bb83cbbb84e83c1` after tightening formula-adjacent counterparts, narrowing table/caption boundary text, and restoring the max-$z$ formula summary.

## Chapter 7 Proofing Batch

All 92 Chapter 7 source units are now recorded as `Proofed` in `notes/bilingual_alignment_manifest.md`, including distributed-training systems prose, memory-accounting and parallelism sections, FSDP/ZeRO, tensor, pipeline, expert, precision, throughput, reliability, implementation-note, caption, Key Terms, and Exercises units. BP-07 in `notes/bilingual_print_proofing_log.md` covers `ch07-abstract--ch07-exercise-012` on rendered pages 211--258 under SHA-256 `caefc5aa856c352f465ff17f991612ddac7a5e8fb29056fb4bb83cbbb84e83c1` after tightening table/caption and short follow-on counterparts for `ch07-prose-009`, `ch07-prose-051`, `ch07-prose-054`, `ch07-prose-061`, `ch07-caption-002`, `ch07-caption-003`, and `ch07-key-term-012`.

## Chapter 8 Proofing Batch

All 74 Chapter 8 source units are now recorded as `Proofed` in `notes/bilingual_alignment_manifest.md`, including the prefill/decode prose, KV-cache discussion, serving-scheduler material, captions, Key Terms, and Exercises. BP-08 in `notes/bilingual_print_proofing_log.md` covers `ch08-abstract--ch08-exercise-007` on rendered pages 260--297 under SHA-256 `caefc5aa856c352f465ff17f991612ddac7a5e8fb29056fb4bb83cbbb84e83c1` after tightening figure/table intro counterparts for `ch08-prose-020` and `ch08-prose-034`, short caption counterparts for `ch08-caption-002`, `ch08-caption-003`, and `ch08-caption-004`, and exercise prompts for `ch08-exercise-001`, `ch08-exercise-002`, and `ch08-exercise-005`.

## Chapter 9 Proofing Batch

All 59 Chapter 9 source units are now recorded as `Proofed` in `notes/bilingual_alignment_manifest.md`, including supervised-instruction-tuning interface prose, chat-template and label-mask contracts, instruction-data-contract sections, synthetic Self-Instruct and distillation material, training-detail and completion-only-collator cautions, refusal/safety-data sections, evaluation and imitation-limit prose, captions, Key Terms, and Exercises. BP-09 in `notes/bilingual_print_proofing_log.md` covers `ch09-abstract--ch09-exercise-007` on rendered pages 299--329 under SHA-256 `caefc5aa856c352f465ff17f991612ddac7a5e8fb29056fb4bb83cbbb84e83c1` after tightening SFT pipeline, synthetic-data audit, template/mask boundary, padding, PEFT/full-tuning, safety-neighbor, evaluation, and regression counterparts.

## Chapter 10 Proofing Batch

All 76 Chapter 10 source units are now recorded as `Proofed` in `notes/bilingual_alignment_manifest.md`, including the PEFT efficiency prose, adapter and prompt families, LoRA/QLoRA mechanics, target-module and rank discussion, deployment/composition sections, captions, Key Terms, and Exercises. BP-10 in `notes/bilingual_print_proofing_log.md` covers `ch10-abstract--ch10-exercise-009` on rendered pages 331--369 under SHA-256 `caefc5aa856c352f465ff17f991612ddac7a5e8fb29056fb4bb83cbbb84e83c1` after tightening formula-adjacent PEFT objective, adapter-block, LoRA parameter-count, merge-weight, and QLoRA memory counterparts.

## Chapter 11 Proofing Batch

All 57 Chapter 11 source units are now recorded as `Proofed` in `notes/bilingual_alignment_manifest.md`, including domain-adaptation diagnosis prose, tokenizer and vocabulary-extension material, Chinese LLaMA/Baichuan language-adaptation discussion, continual-pretraining and replay-data sections, supervised domain tuning, NL2SQL evaluation, retrieval-versus-weight-update governance, domain-safety sections, captions, Key Terms, and Exercises. BP-11 in `notes/bilingual_print_proofing_log.md` covers `ch11-abstract--ch11-exercise-007` on rendered pages 370--398 under SHA-256 `caefc5aa856c352f465ff17f991612ddac7a5e8fb29056fb4bb83cbbb84e83c1` after tightening token-fertility, CPT mixture, NL2SQL generation, and citation-bearing language/domain adaptation counterparts.

## Chapter 12 Proofing Batch

All 66 Chapter 12 source units are now recorded as `Proofed` in `notes/bilingual_alignment_manifest.md`, including RAG control-system prose, latent-document marginalization and original RAG training-recipe discussion, indexing, hybrid retrieval, query rewriting, reranking, context construction, grounded generation, RAG evaluation, context engineering, typed memory, prompt-injection boundaries, tool-use runtime contracts, agent workflows, systems-cost sections, captions, Key Terms, and Exercises. BP-12 in `notes/bilingual_print_proofing_log.md` covers `ch12-abstract--ch12-exercise-009` on rendered pages 399--431 under SHA-256 `caefc5aa856c352f465ff17f991612ddac7a5e8fb29056fb4bb83cbbb84e83c1` after tightening formula-, citation-, and runtime-contract counterparts across the Chapter 12 RAG, tools, context-engineering, and agent sections.

## Chapter 13 Proofing Batch

All 79 Chapter 13 source units are now recorded as `Proofed` in `notes/bilingual_alignment_manifest.md`, including preference-data collection, reward-model and PPO/RLHF material, MDP framing, DPO derivation, post-DPO objectives, safety/refusal sections, reward-hacking diagnostics, captions, Key Terms, and Exercises. BP-13 in `notes/bilingual_print_proofing_log.md` covers `ch13-abstract--ch13-exercise-010` on rendered pages 432--474 under SHA-256 `caefc5aa856c352f465ff17f991612ddac7a5e8fb29056fb4bb83cbbb84e83c1` after tightening formula-, citation-, and response-mask counterparts across the Chapter 13 preference-learning and alignment sections.

## Chapter 14 Proofing Batch

All 67 Chapter 14 source units are now recorded as `Proofed` in `notes/bilingual_alignment_manifest.md`, including reasoning-as-budgeted-compute prose, CoT and self-consistency material, decomposition, verifier and process-supervision sections, tree search, RLVR and GRPO objectives, small-scale GRPO reproducibility contracts, inference-time scaling, frontier reasoning systems, pass@k cost curves, trace-faithfulness cautions, captions, Key Terms, and Exercises. BP-14 in `notes/bilingual_print_proofing_log.md` covers `ch14-abstract--ch14-exercise-007` on rendered pages 475--509 under SHA-256 `caefc5aa856c352f465ff17f991612ddac7a5e8fb29056fb4bb83cbbb84e83c1` after tightening formula-bearing self-consistency, verifier, PRM, RLVR, GRPO, router, and cost-curve counterparts.

## Chapter 15 Proofing Batch

All 81 Chapter 15 source units are now recorded as `Proofed` in `notes/bilingual_alignment_manifest.md`, including the multimodal-interface prose, CLIP/connector material, unified understanding-generation and generative-objective sections, VLA/world-model discussion, systems-cost material, evaluation and safety sections, captions, Key Terms, and Exercises. BP-15 in `notes/bilingual_print_proofing_log.md` covers `ch15-abstract--ch15-exercise-009` on rendered pages 510--551 under SHA-256 `caefc5aa856c352f465ff17f991612ddac7a5e8fb29056fb4bb83cbbb84e83c1` after tightening formula-bearing CLIP, Q-Former, diffusion/flow, VLA, chat-template, prefill-cost, and OCR-resizing exercise counterparts.

## Chapter 16 Proofing Batch

All 79 Chapter 16 source units are now recorded as `Proofed` in `notes/bilingual_alignment_manifest.md`, including evaluation-system prose, benchmark and contamination sections, long-context/agentic/multimodal evaluation, human and judge-model evaluation, factuality, robustness, safety taxonomy, red teaming, governance, interpretability, unlearning, watermarking, monitoring, captions, Key Terms, and Exercises. BP-16 in `notes/bilingual_print_proofing_log.md` covers `ch16-abstract--ch16-exercise-011` on rendered pages 552--592 under SHA-256 `caefc5aa856c352f465ff17f991612ddac7a5e8fb29056fb4bb83cbbb84e83c1` after adding the skipped LLM-as-judge source unit and tightening the LLM-as-judge, factual-precision, and uncertainty-formula counterparts.

## Chapter 17 Proofing Batch

All 50 Chapter 17 source units are now recorded as `Proofed` in `notes/bilingual_alignment_manifest.md`, including the frontier-practice roadmap, CS336-style from-scratch practice, scope and curriculum framing, frontier architecture pressure points, reasoning and adaptive test-time compute sections, data/evaluation/governance loop, frontier evidence matrix, reader roadmap, captions, Key Terms, and Exercises. BP-17 in `notes/bilingual_print_proofing_log.md` covers `ch17-abstract--ch17-exercise-007` on rendered pages 593--619 under SHA-256 `caefc5aa856c352f465ff17f991612ddac7a5e8fb29056fb4bb83cbbb84e83c1` after restoring citation anchors in Chapter 17 counterparts.

## Front And Back Matter Proofing Batch

All 58 tracked front/back matter source units are now recorded as `Proofed` in `notes/bilingual_alignment_manifest.md`, including the Preface, Declarations/Responsible Use prose, appendix reproducibility and provenance prose, acronym entries, and glossary entries. BP-18 covers the Preface on pages 620--622, BP-19 covers Responsible Use on pages 624--626, BP-20 covers Appendix prose on pages 627--628, BP-21 covers Acronyms on pages 630--637, and BP-22 covers Glossary entries on pages 638--647 under SHA-256 `caefc5aa856c352f465ff17f991612ddac7a5e8fb29056fb4bb83cbbb84e83c1`.

## Rendered Proofing Draft

`scripts/report_bilingual_print_plan.py` supports proofing-render and artifact-check modes. It extracts the real English abstract and Chapter contract text, uses balanced-brace caption extraction so citations do not truncate captions, removes source-only index/label/description commands from the proofing text, and renders each source unit next to the Chinese manifest counterpart. `make bilingual-print-artifact-check` regenerates `/tmp/llm_book_bilingual_print/book_bilingual_print.tex` and `/tmp/llm_book_bilingual_print/book_bilingual_print.pdf`; `pdfinfo` reports 647 pages, the artifact checker finds 1163/1163 rendered source-unit IDs, and the rendered text SHA-256 is `caefc5aa856c352f465ff17f991612ddac7a5e8fb29056fb4bb83cbbb84e83c1`. `make bilingual-print-proofing-check` validates the reviewed proofing batches and their matching manifest `Proofed` rows.

## Completion Evidence

The bilingual print edition is marked complete because:

- every tracked source unit above has an explicit Chinese counterpart and is marked `Proofed`;
- figure and table captions, Key Terms, Exercises, front matter, acronym entries, appendix prose, and glossary entries are covered item by item;
- equation-adjacent symbols, citations, labels, and terminology are aligned with the English source in the tracked units;
- the bilingual print PDF builds cleanly under its rendered-text fingerprint;
- `make bilingual-alignment-check`, `make bilingual-print-artifact-check`, and `make bilingual-print-proofing-check` pass for the 1163/1163 proofed source units.

# Index Audit

Date: 2026-05-25

## Purpose

The English manuscript has a real back-of-book index rather than only glossary-level entries. This audit keeps the index usable as the manuscript changes by checking coverage, makeindex health, acronym alias consistency, and press-style entry hygiene.

## Repeatable Command

From the repository root:

```bash
make index-check
```

The target rebuilds both PDFs through `make all`, then checks the English source index entries, `book/book.ilg`, and the rendered English PDF index extracted with `pdftotext`.

## Current Criteria

- At least 550 source `\index{...}` entries in English manuscript sources.
- At least 20 index entries in each of the 17 English chapters.
- `makeindex` accepts the same number of entries found in source.
- `makeindex` reports 0 rejected entries and 0 warnings.
- Important acronym and reader-vocabulary aliases use `see` entries instead of competing with canonical terms: agents, embeddings, fine-tuning, human feedback, long context, model judge, red team, tools, vector database, BPE, CoT, DPO, FFN, FSDP, GQA, GRPO, KV, LLM, MHA, MLA, MoE, MQA, PEFT, PPO, RAG, RLVR full phrase, RoPE, SFT, and VLM.
- Every `see` alias points to an existing main index term.
- Required canonical topic paths exist for high-value reader lookups such as `evaluation!benchmark contamination`, `safety!red teaming`, `governance!risk management`, `data!provenance`, `distributed training!tensor parallelism`, and `tokenization!coverage`.
- Required parent terms have enough subentry grouping for press-style navigation: `alignment`, `data`, `evaluation`, `governance`, `safety`, `tokenization`, and `Transformer`.
- Repeated source index paths are capped at 4 hits so high-value terms can appear where useful without drowning the index in mechanical duplicates.
- Index entries have no empty components, no component-leading/trailing whitespace, no terminal punctuation on components or `see` targets, no capitalization drift across repeated components, and no more than three index levels.
- The rendered English PDF index isolates to a multi-page index section with enough body lines, exposes required high-value reader terms, and renders all required acronym `see` aliases.

## Current Editorial Pass

- Expanded the glossary so canonical terms and acronym aliases live in one consistent place.
- Normalized PPO and GRPO toward full-form main entries while retaining acronym lookup through `see` entries.
- Moved KV-cache quantization under `KV cache!quantization`.
- Removed a standalone `MoE routing` main term in favor of the `mixture of experts!routing` subentry.
- Connected the front-matter acronym list to the back-of-book index with `see` aliases for common reader lookup forms, and added a gate that fails if any alias target is missing.
- Added required canonical topic paths so critical ideas remain reachable from stable parent terms rather than only as scattered standalone entries.
- Added required parent subentry groups for alignment, data, evaluation, governance, safety, tokenization, and Transformer so broad reader lookups do not collapse into single undifferentiated page lists.
- Added a repeated-entry budget so the same source index path cannot be inserted more than four times across the manuscript.
- Added a press-style hygiene gate for entry depth, component whitespace, terminal punctuation, and capitalization consistency.
- Added a focused reader-lookup pass for high-value aliases around agents/tools, embeddings/vector databases, fine-tuning, human feedback/RLHF, long context, model judges, red teams, unlearning, watermarking, content credentials, and provenance subentries.

## Latest Result

The latest `make index-check` run passed with 646 source index entries, 485 main terms, 31 `see` aliases, 17/17 required index topic paths, 7/7 required parent subentry groups, 4/4 maximum repeated source index path, 0 source index paths over repeat budget, 0 index style errors, a minimum of 21 entries in each English chapter, and a `makeindex` log with 646 accepted entries, 0 rejected entries, and 0 warnings. The rendered-index pass found 6 rendered index pages, 311 nonempty rendered index body lines, 34/34 rendered index required terms, and 31/31 rendered index see aliases.

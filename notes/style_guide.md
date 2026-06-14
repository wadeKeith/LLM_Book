# Manuscript Style Guide

Date: 2026-05-25

This note records house-style decisions that affect automated review noise.

## English Manuscript

- Use American quote punctuation in ordinary prose: commas and periods stay inside closing quotation marks.
- Use hyphenated compounds for established technical modifiers such as encoder-decoder, decoder-only, and LLaMA-class.
- Reserve en dashes for ranges or true contrasts; avoid them for routine technical compounds.
- Use roman or text subscripts for named losses and metrics when the subscript is a label rather than a variable.
- Keep raw ChkTeX output as a review aid. `notes/chktex_triage.md` records the warning disposition; `make chktex-triage-check`, `make chktex-budget-check`, and `make chktex-focused-check` keep the documented high-volume budgets and focused warning set from silently drifting.
- Keep Underfull hbox/vbox warnings as layout-review signals. `make log-quality-check` gates the current reviewed budgets so new spacing regressions are visible.
- Use booktabs-style table rules: `\toprule`, `\midrule`, and `\bottomrule` in order, with no vertical rules or `\hline` variants. `make table-quality-check` gates this for English and Chinese source tables.
- Treat executable experiments as run-card obligations. The appendix template should preserve code/data versions, tokenizer and chat-template state, model and optimization configuration, hardware/runtime, validation metrics, failure modes, and conclusions; `make reproducibility-check` gates the bilingual appendix fields.

## Chinese Readable Edition

- Keep Chinese prose readable rather than forcing paragraph-for-paragraph literal translation until a full bilingual edition is explicitly targeted.
- Keep widely used English technical terms where they improve precision, especially for code-facing concepts such as tokenizer, KV cache, LoRA, RAG, and GRPO.
- Use Chinese full stops after citations and inline code sentences in Chinese prose, and avoid spaces after Chinese punctuation before Han text. `make chinese-prose-quality-check` enforces these source-level punctuation artifacts.
- Split ordinary body prose before it becomes a monolithic reading block. `make paragraph-length-check` enforces conservative English and Chinese paragraph-length budgets while skipping lists, tables, figures, math, and verbatim-like regions.

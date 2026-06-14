# Bilingual Coverage Audit

Date: 2026-06-09

## Purpose

The English manuscript remains the controlling publication draft. The Chinese manuscript is a readable edition that follows the same 17-chapter structure, topic sequence, frontier layer, exercises, key terms, and back-matter contract. This audit keeps that framing explicit: it checks substantive Chinese coverage chapter by chapter, but it does not claim that the Chinese edition is a paragraph-for-paragraph full bilingual print counterpart.

The stricter paragraph-level bilingual print objective is tracked separately in `notes/bilingual_print_plan.md`, `notes/bilingual_alignment_manifest.md`, `notes/bilingual_print_proofing_log.md`, `make bilingual-print-plan`, `make bilingual-alignment-check`, `make bilingual-print-artifact-check`, and `make bilingual-print-proofing-check`. That plan currently records 1163 English source units, 1163 source-level aligned units, 1163 proofed units, and 0 open units, so the rendered bilingual print pass is complete under the current fingerprint. The latest alignment gate reports 1163 source units, 1163 manifest rows, 1163 aligned units, 1163 proofed units, 0 open units, and 0 manifest errors.

## Repeatable Command

From the repository root:

```bash
make bilingual-coverage-check
```

`make bilingual-coverage-check` compares English chapter body word counts before Key Terms with Chinese chapter Han-character counts. It verifies that all 17 English/Chinese chapter pairs are present, that every Chinese chapter remains at least 0.75 Chinese Han characters per English body word, and that the full Chinese readable edition remains at least 0.90 Chinese Han characters per English body word. It also reports the weakest bilingual chapter and a per-chapter coverage row so paragraph-level expansion can start from the thinnest current chapters.

## Current Criteria

- English controlling draft: 17 chapter bodies before Key Terms.
- Chinese readable edition: 17 content chapters before the appendix.
- Per-chapter floor: 0.75 Chinese Han characters per English body word.
- Whole-book floor: 0.90 Chinese Han characters per English body word.
- This audit complements `make coverage-check`, `make edition-alignment-check`, `make frontier-coverage-check`, Chinese prose checks, proofing-plan tracking, `make bilingual-print-plan`, `make bilingual-alignment-check`, `make bilingual-print-artifact-check`, and `make bilingual-print-proofing-check`; it does not replace paragraph-level bilingual review.

## Latest Result

The latest bilingual-coverage check found 17 bilingual chapter pairs, 54970 English controlling body words, 155578 Chinese readable Han characters, 2.72 minimum Chinese-to-English coverage ratio, weakest bilingual chapter: 15 ratio 2.716; Multimodal and Generative Foundation Models / 多模态与生成式基础模型, 2.83 total Chinese-to-English coverage ratio, and 0 chapters below coverage floor.

## Expansion Priority Queue

The current weakest chapters by Chinese-to-English coverage ratio are:

| Priority | Chapter | Ratio | English words | Chinese Han characters | Scope |
| --- | --- | --- | ---: | ---: | --- |
| 1 | 15 | 2.716 | 4186 | 11368 | Multimodal and Generative Foundation Models / 多模态与生成式基础模型 |
| 2 | 08 | 2.733 | 3923 | 10723 | Inference and Serving / 推理与服务 |
| 3 | 09 | 2.746 | 3308 | 9084 | Supervised Instruction Tuning / 监督指令微调 |
| 4 | 05 | 2.748 | 3183 | 8748 | LLaMA-Class Architectures / LLaMA 类架构 |
| 5 | 16 | 2.751 | 3648 | 10035 | Evaluation, Safety, and Governance / 评测、安全与治理 |

## Remaining Editorial Status

The Chinese edition is substantive enough to remain a readable companion under the current release framing. The latest visual-density and numbered-table pass added original cited diagrams and per-chapter table floats without weakening chapter coverage; Chapter 15 is now the weakest ratio at 2.716, and the total Chinese-to-English coverage ratio is 2.83. The full bilingual print follow-up has completed source-level alignment and rendered proofing for all Chapter 1 through Chapter 17 units and all tracked front/back matter units in `notes/bilingual_alignment_manifest.md`; all 1163 units are proofed under BP-01 through BP-22 in `notes/bilingual_print_proofing_log.md`.

# Visual PDF Audit

Date: 2026-06-09

## Purpose

The hard LaTeX checks catch build failures, undefined references, overfull boxes, PGF diagram warnings, and PDF destination/link warnings. They do not prove that representative pages look publication-ready. This audit defines repeatable rendered-page checks for the English controlling manuscript and the Chinese readable edition.

## Repeatable Command

From the repository root:

```bash
make visual-smoke-check
make visual-full-check
make visual-audit
```

`make visual-smoke-check` is the automated gate included in `make manuscript-audit`. It rebuilds both PDFs, renders 11 sampled pages from each PDF to temporary PPM files with `pdftoppm`, and checks for nonblank output, expected raster dimensions, unexpectedly dense output, and dark pixels touching the page edge.

`make visual-full-check` is the all-page automated gate included in `make manuscript-audit`. It rebuilds both PDFs, renders all 238 English pages and all 308 Chinese pages at 72 dpi to temporary PPM files, checks the current expected blank and low-ink visual pages, and fails if any other page is blank, unexpectedly dense, or edge-clipped. The latest run checked 546 visual pages in total: 238 English visual pages with 15 expected blank pages and 0 expected low-ink pages, plus 308 Chinese visual pages with 0 expected blank pages and 2 expected low-ink pages. Nonblank ink ratios were 0.0020--0.1185 for English and 0.0001--0.1567 for Chinese, with minimum nonblank edge margins of 89 px and 42 px respectively.

`make visual-audit` is the human review target. It rebuilds both PDFs through `make all`, renders PNG pages with `pdftoppm`, verifies the exact 360 PNG file set, checks PNG headers, dimensions, nonblank page ink ratios, expected blank visual pages, and edge margins, and writes them outside the repository by default. The latest run checked 360 PNGs at 1105x1430 px, found nonblank page ink ratios from 0.0017 to 0.1118, found a 76 px minimum nonblank edge margin, confirmed 3 expected blank visual pages, covers the existing English title/TOC/body/table/multimodal/index pages, adds the new serving, multimodal, governance, and frontier synthesis figures through those chapter ranges, and covers Chinese title/TOC/body/reference pages through the new final page 308:

```text
/tmp/llm_book_visual_audit
```

Set `VISUAL_AUDIT_DIR=/path/to/output` to override the output directory.

## Current Rendered Text Fingerprints

These fingerprints are SHA-256 digests of `pdftotext -layout` output for the current release PDFs. If either fingerprint changes, the sampled visual audit record should be treated as stale until the visual targets are rerun.

- English PDF text SHA-256: `8e41590a1c7a1158a746873f711f01c2fc32c344cc37fe35cfa02d22067fb43e`.
- Chinese PDF text SHA-256: `a4b56331f4304d70c70619a90c739fb6b268478fd047280331e21be5abb029db`.

The automatic image check expects English pages 38, 76, and 178 to be deliberate blank visual pages in the current sample. Every other rendered PNG in the sample must be nonblank, must match the expected letter-page raster size for `VISUAL_AUDIT_DPI`, and must keep dark pixels away from the page edge.

`make visual-audit-plan-check` verifies that this note, the `make visual-audit` page-rendering commands, `scripts/check_visual_audit_images.py`, and the current rendered-text fingerprints use the same sample. The latest run found 23 visual-audit page ranges, 360 visual-audit PNGs, 3 expected blank visual pages, English visual-audit text SHA-256: 8e41590a1c7a1158a746873f711f01c2fc32c344cc37fe35cfa02d22067fb43e, and Chinese visual-audit text SHA-256: a4b56331f4304d70c70619a90c739fb6b268478fd047280331e21be5abb029db.

## Human Review Page Set

English `book.pdf`:

- `1`: title page.
- `9--12`: table of contents pages with two-digit chapter and subsection numbers.
- `37--45`: LLaMA-class architecture chapter, including equations, figures, and architecture tables.
- `75--83`: inference and serving chapter pages with systems tables and long labels.
- `173--181`: multimodal/generative foundation model chapter opening and dense technical layout.
- `217--238`: appendix, glossary, references, and expanded index.

Chinese `book_zh.pdf`:

- `1`: title page.
- `3--16`: preface, ethics note, and table of contents.
- `20--42`: expanded Chapter 1 lifecycle/framing/model-card/gated-model release-evidence pages plus expanded Chapter 2 data-artifact/tokenizer/filtering/preprocessing, Hub dataset repository, Dataset Viewer, cache fingerprint, streaming-training coverage, the Chapter 2 table float, and the Part II break.
- `43--53`: updated Chapter 3 Transformer mechanics pages, including PyTorch SDPA, `MultiheadAttention` mask polarity, backend dispatch, regression-suite material, and the Chapter 3 table float.
- `54--65`: expanded Chapter 4 GPT pages, including the release-acceptance matrix for tokenizer/template, label mask, GenerationConfig, runtime overrides, cache strategy, response schema, response parsing, structured output, evaluation reproducibility, and the Chapter 4 table float.
- `66--81`: expanded Chapter 5 LLaMA-class architecture pages, including current Hugging Face Llama/Qwen3/Gemma3/Llama4 configuration fields, RoPE configuration, attention head grouping, sliding-window/chunked layers, cache-implementation evidence, and the Chapter 5 table float.
- `82--96`: expanded Chapter 6 optimization/pretraining pages, including Accelerate gradient-accumulation, Trainer configuration, FP8 backend, checkpoint-state acceptance material, and the Chapter 6 table float.
- `97--119`: expanded distributed-training chapter pages, including current Accelerate DeepSpeed/FSDP configuration evidence, FSDP2 communication grouping, tensor-parallel layout contracts, PipelineStage shape/dtype contracts, DCP async-save runbook material, strategy-selection, topology, throughput-drift, regression-suite, reliability rehearsal, export-evidence paragraphs, the system-diagnosis table, publication-acceptance matrix, and adjacent implementation contracts.
- `120--139`: expanded inference-serving pages, including continuous-batching architecture state/budget material, vLLM prefix-cache hash and isolation material, latest TGI runtime-acceptance material, current Transformers cache-implementation service evidence, the serving checklist, and the Part III break.
- `140--153`: expanded SFT pages, including current dataset format/type handling, chat templates, assistant-only loss, completion-only loss, packing, EOS, collator, tool-calling SFT, VLM SFT, MoE router-loss, and SFTTrainer configuration evidence.
- `154--170`: expanded parameter-efficient adaptation pages, including PEFT objective framing, adapters, LoRA dimensions, trainable-token handling, MoE target parameters, QLoRA memory accounting, LoftQ, Transformers PEFT adapter lifecycle, checkpoint format, hotswap, weighted merge, and mixed-adapter evidence.
- `171--183`: expanded domain/language adaptation pages, including latest tokenizer API, tokenization-pipeline, dataset fingerprint, streaming, sharding, interleaving, `load_dataset` loading-identity, and manifest evidence.
- `184--235`: Part IV break, expanded retrieval/tools/agents, preference-learning, and expanded reasoning/test-time-compute pages through current TRL v1 trainer taxonomy, DPO/RLOO/CPO/BCO/Nash-MD, dataset-format/type, Harmony/tool-calling metadata, VLM, Online DPO, and GRPO evidence, generation-configuration, and assisted-decoding acceptance material.
- `236--253`: expanded multimodal/generative foundation model pages through the multimodal processor and Chapter 15 checklist material.
- `254--268`: expanded Chapter 16 evaluation, safety, and governance pages, including Lighteval harness/task/metric/result-tracking material and NIST/EU/GPAI/frontier-risk framework mapping.
- `279--280`: appendix notation, run-card, and glossary pages.
- `269--308`: Chapter 17, appendix transition, references continuation, and final pages.

## Pass Criteria

Inspect the rendered PNGs for:

- Nonblank title, TOC, body, glossary, bibliography, and index pages.
- No clipped page headers, page numbers, equations, tables, or figure content.
- No section numbers touching titles in the TOC.
- No visibly overlapping text, figures, tables, or page furniture.
- Reference URLs and index columns remain readable enough for publication review.

The human audit is intentionally visual and sampled. It complements the automated `visual-smoke-check` and all-page low-resolution `visual-full-check`; none of these targets replaces a full proofread.

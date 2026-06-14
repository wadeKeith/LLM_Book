# Large Language Models Book

This repository contains the Overleaf-ready LaTeX manuscript for:

**Large Language and Generative Foundation Models: Foundations, Systems, Alignment, and Applications**

The controlling publication draft is the English manuscript:

```text
book/book.tex
```

The Chinese readable edition is:

```text
book/book_zh.tex
```

## Build Locally

From the repository root:

```bash
make all
```

Or run the commands manually:

```bash
cd book
latexmk -pdf -interaction=nonstopmode -halt-on-error book.tex
latexmk -xelatex -interaction=nonstopmode -halt-on-error book_zh.tex
```

The English manuscript uses the Springer `SNmono` class already included in the repository. The Chinese edition uses `ctexbook` and should be built with XeLaTeX.

## Publication Checks

Before treating a PDF as a release candidate, run:

```bash
make release-candidate
```

The `release-candidate` target wraps `make manuscript-audit`, then runs `make clean`, `make clean-check`, `git diff --check`, and a final `make release-inventory-check` after cleanup.

The `manuscript-audit` target runs toolchain checks, repository-hygiene checks, release-inventory checks, local source-inventory checks, audit-script checks, makefile-consistency checks, citation-key and bibliography-value checks, root/chapter-structure checks, front-matter quality checks, abstract-quality checks, chapter-contract checks, heading-quality checks, TOC-review checks, chapter-coverage checks, edition-alignment checks, bilingual-coverage checks, bilingual-alignment checks, bilingual-print artifact and proofing checks, documented frontier-coverage checks, cross-reference checks, table-quality checks, caption-quality checks, figure-description checks, SNmono policy checks, provenance-boundary checks, term-consistency checks, back-matter quality checks, conservative English prose-quality checks, Chinese prose-quality checks, duplicate long-prose checks, paragraph-length checks, exercise-quality checks, reproducibility-record checks, source and rendered index-quality checks with required canonical topic paths, parent subentry groups, and repeated-entry budget, reviewer-blocker checks, rendered PDF metadata checks, rendered PDF font checks, rendered PDF text-structure and source-leak checks, rendered PDF reference-locator and rendered bibliography-label checks, rendered PDF outline/bookmark checks, all-page PDF text extraction plus blank-page and low-text page set checks, sampled rendered-page visual smoke checks, all-page low-resolution rendered visual checks, visual-audit plan checks, proofing-plan checks, release-documentation consistency checks, unresolved-marker checks, ChkTeX triage, budget, and focused checks, TeX log-quality budget checks, both PDF builds, and the hard publication check. The toolchain check verifies Python 3.10+, `latexmk`, `rg`, Poppler's `pdfinfo`, `pdffonts`, `pdftotext`, and `pdftoppm`, plus `chktex`, before later gates run. The repository-hygiene check verifies that Springer template files are present, the two `SNmono.cls` copies are identical, root build configuration is stable, release artifact ignore rules are present, and README release instructions are discoverable. The release-inventory check verifies that every non-build file in the release workspace matches one documented file class and that no external figures, screenshots, datasets, model weights, model outputs, or code listings are silently present. The source-inventory check verifies that the local source-material count in `notes/source_inventory.md` matches the current surrounding source workspace, excluding the publication repository itself. The audit-script check verifies that release audit Python scripts compile, keep the expected python3 shebang and module docstring, and that every `check_*.py` script is referenced by the Makefile. The Makefile-consistency check verifies that `.PHONY`, target definitions, `manuscript-audit` dependencies, aggregate build targets, and the `release-candidate` cleanup wrapper stay synchronized. The reviewer-blocker check verifies that `notes/professor_review.md` covers all 17 English chapters, records 17 current comment-stripped chapter source fingerprints, and records no Open/Reopened P0/P1 review blockers. The citation check requires every bibliography entry to be cited, have basic metadata, use four-digit publication-year values that are not in the future, keep arXiv locators out of future months and no later than the bibliography year, avoid duplicate titles or locator URLs, use syntactically valid URL/DOI/arXiv locator fields, keep DOI values in `doi` fields rather than DOI resolver URLs, reject undocumented insecure HTTP URLs, and protect title capitalization for technical proper names. The front-matter quality check verifies that the English and Chinese preface/ethics blocks retain enough publication-facing substance, required provenance and responsibility markers, and no source-import or unresolved editorial commands. The abstract-quality check verifies that the 17 English chapter abstracts are unique, stay within the documented word budget, end with terminal punctuation, and do not contain citation/reference/label/index commands or unresolved editorial markers. The chapter-contract check verifies that every English chapter has a plain reader-facing contract after the abstract and before the first section, with a 35--70 word budget and no citation/reference/label/index commands. The heading-quality check verifies that the 17 English chapter files and the Chinese readable edition keep clean, compact, non-duplicated chapter/section/subsection headings without citation/reference/label/index/URL commands or unresolved editorial markers. The TOC-review check verifies that `notes/toc_review.md` keeps the same 17 documented TOC chapters as the English controlling manuscript. The chapter-coverage check enforces conservative floors for English body length, citations, index entries, figures, and tables, plus Chinese chapter length, citation presence, and per-chapter figure and table coverage. The edition-alignment check verifies the English chapter include order, English chapter title stability, Chinese chapter order/title alignment, and required Chinese core-topic anchors for each of the 17 chapter pairs. The bilingual-coverage check verifies that the Chinese readable edition remains a substantive companion by comparing per-chapter and whole-book Chinese Han-character coverage against English body words, without claiming paragraph-for-paragraph bilingual completeness. The bilingual-alignment check verifies that partial source-level English-to-Chinese alignment records reference current source-unit IDs and keep proofing status separate from alignment status. The bilingual-print artifact check rebuilds the outside-release-tree bilingual proofing draft and verifies that all aligned source-unit IDs appear in the rendered artifact. The bilingual-print proofing check verifies `notes/bilingual_print_proofing_log.md` against the current rendered artifact fingerprint, page ranges, unit IDs, and manifest `Proofed` rows. The frontier-coverage check verifies that the latest documented frontier layer remains cited and present in the English controlling manuscript and Chinese readable edition. The table-quality check verifies that source tables use booktabs-style rules, avoid vertical and `\hline` rules, and retain minimum data-row substance. The caption-quality check verifies that figure and table captions are unique, have enough text to be useful, stay within a compact caption budget, end with terminal punctuation, and avoid label/index commands or unresolved editorial markers. The term check verifies acronym, glossary, English chapter key-term lists, and Chinese chapter key-term paragraphs for duplicate entries, index coverage, term-label formatting, and minimum substance. The back-matter quality check verifies English appendix sections and markers, English acronym/glossary counts, Chinese appendix section order, Chinese run-card markers, and Chinese appendix glossary substance. The prose-quality check scans the English controlling manuscript for repeated words, common spelling slips, casing drift for selected technical names, and obvious source punctuation artifacts. The Chinese prose-quality check scans `book_zh.tex` for ASCII citation/code sentence periods, spacing around Chinese punctuation, repeated Chinese punctuation, and ASCII punctuation after Chinese text. The duplicate-prose check scans English and Chinese manuscript body prose for exact duplicate long paragraphs or sentences after TeX-aware normalization. The paragraph-length check scans ordinary English and Chinese prose paragraphs for conservative readability-length limits while skipping math, figures, tables, lists, and verbatim-like environments. The exercise-quality check verifies that English and Chinese exercise sections have enough items, enough prompt text, terminal punctuation, and no duplicate prompt text after normalization. The reproducibility check verifies that the English and Chinese appendices retain the required run-card fields for code/data versions, tokenizer and chat-template state, model and optimization configuration, hardware/runtime, validation metrics, failure modes, and conclusions. The cross-reference check requires labels to be unique, references to resolve, every figure/table float to have a caption and correctly prefixed label, every figure/table label to be cited in the manuscript text, and local figure/table references to appear in source order. The figure-description check requires every English SNmono figure to have a plain-text `\Description` before its caption and verifies that the generated `DescriptionTexts.txt` production side file matches those source descriptions. The rendered index check verifies that the English PDF exposes a multi-page reader index with required high-value terms and all canonical `see` aliases. The provenance check scans local readable source files for long exact English-word or CJK-character overlap with manuscript prose. The PDF metadata check verifies title, author, subject, required keywords, exact current page counts, current file-size ranges, page size, PDF version, encryption status, and JavaScript/form absence. The PDF font check rejects Type 3 fonts, unembedded fonts, non-subset fonts, and fonts without Unicode maps. The PDF text check verifies rendered structural markers and rejects leaked TeX citation/reference/manuscript commands, unresolved markers, raw BibTeX entry markers, and editorial placeholders in extracted PDF text. The PDF reference check verifies that rendered references expose the NIST synthetic-content DOI as a DOI locator, do not render DOI resolver URLs, preserve the documented Sutton/Barto HTTP exception, avoid URL bracket artifacts, and keep rendered bibliography labels contiguous with the generated `.bbl` counts. The PDF outline check verifies front-matter, part, chapter, appendix, glossary/reference, and index bookmarks in navigable order. The PDF page-integrity check verifies that `pdftotext` extracts the expected page count, that blank-page policy matches the release layout, and that the expected blank-page and low-text page sets do not drift. The all-page visual check renders every English and Chinese PDF page at low resolution and fails on unexpected blank pages, unexpectedly dense pages, or dark pixels touching the page edge. The ChkTeX triage check verifies that `notes/chktex_triage.md`, `notes/style_guide.md`, the ChkTeX budget script, and the Makefile focused-warning mutes stay synchronized. The visual-audit plan check rebuilds the PDFs as needed and verifies that `notes/visual_audit.md`, `make visual-audit`, `scripts/check_visual_audit_images.py`, and the current rendered-text fingerprints use the same sampled page ranges and expected blank pages. The documentation check verifies that release notes document the actual audit targets, current citation-count, release-inventory, source-inventory, audit-script count, Makefile-consistency count, reviewer register count, provenance-count, front-matter quality, abstract-quality, chapter-contract, bilingual heading-quality, bilingual-coverage, bilingual-alignment, bilingual-print artifact and proofing checks, caption-quality, term-list, back-matter quality, exercise-quality, reproducibility-record, TOC-review, frontier-coverage, index-quality, rendered-index, ChkTeX-triage, visual-audit-plan, proofing-plan, prose-quality, duplicate-prose, paragraph-length, and PDF-text summary notes, and current PDF metadata. The `check` target fails if the hard log scan finds undefined references, LaTeX/package errors, fatal errors, font warnings, or BibTeX warnings. It also fails on layout/linking regressions that should not ship in a release PDF: overfull hboxes, PGF diagram warnings, missing or duplicate PDF destinations, and PDF/link warnings from the TeX engines. High-volume ChkTeX style classes and current Underfull hbox/vbox log noise are triaged with budgets so they cannot silently grow.

The Makefile routes `latexmk` through `scripts/run_latexmk_locked.py`, which serializes local PDF builds across concurrent `make` processes so shared `book/` side files, logs, and PDFs are not written at the same time.

To run the source-level checks without rebuilding the release PDFs:

```bash
make toolchain-check
make citation-check
make repo-hygiene-check
make release-inventory-check
make source-inventory-check
make audit-script-check
make makefile-consistency-check
make structure-check
make frontmatter-quality-check
make abstract-quality-check
make chapter-contract-check
make heading-quality-check
make toc-review-check
make coverage-check
make edition-alignment-check
make bilingual-coverage-check
make bilingual-print-plan
make bilingual-alignment-check
make bilingual-print-artifact-check
make bilingual-print-proofing-check
make frontier-coverage-check
make crossref-check
make table-quality-check
make caption-quality-check
make snmono-policy-check
make provenance-check
make term-check
make backmatter-quality-check
make prose-quality-check
make chinese-prose-quality-check
make duplicate-prose-check
make paragraph-length-check
make exercise-quality-check
make reproducibility-check
make reviewer-check
make placeholder-check
make visual-audit-plan-check
make proofing-plan-check
make chktex-triage-check
make chktex-budget-check
make chktex-focused-check
```

For the stricter paragraph-level bilingual print objective, `make bilingual-print-plan` reports the source-unit inventory for rendered bilingual proofing. The current plan records 1163 source units, 1163 source-level aligned units, 1163 proofed units, and 0 open source units. `make bilingual-alignment-check` validates the source-level pair manifest in `notes/bilingual_alignment_manifest.md`. The latest alignment gate reports 1163 source units, 1163 manifest rows, 1163 aligned units, 1163 proofed units, 0 open units, and 0 manifest errors. `make bilingual-print-artifact-check` rebuilds `/tmp/llm_book_bilingual_print/book_bilingual_print.tex` and `.pdf`, verifies that the rendered artifact contains 1163/1163 source-unit IDs, reports 647 pages, and records rendered text SHA-256 `caefc5aa856c352f465ff17f991612ddac7a5e8fb29056fb4bb83cbbb84e83c1`. `make bilingual-print-proofing-check` verifies `notes/bilingual_print_proofing_log.md`; BP-01--BP-17 mark Chapters 1--17 as proofed on pages 47--619, and BP-18--BP-22 mark the tracked Preface, Responsible Use, Appendix, Acronyms, and Glossary units as proofed on pages 620--647.

The PDF-dependent checks rebuild PDFs as needed:

```bash
make figure-description-check
make index-check
make pdf-metadata-check
make pdf-font-check
make pdf-text-check
make pdf-reference-check
make pdf-outline-check
make pdf-page-integrity-check
make visual-smoke-check
make visual-full-check
make log-quality-check
make documentation-check
```

After cleanup, `make clean-check` verifies that ignored LaTeX side files, SNmono `DescriptionTexts.txt`, Python cache directories, and `.DS_Store` files are not left in the release workspace.

The reference, toolchain, release-inventory, source-inventory, audit-script, makefile-consistency, structure, front-matter quality, abstract-quality, chapter-contract, heading-quality, TOC-review, chapter-coverage, edition-alignment, bilingual-coverage, bilingual-alignment, bilingual-print artifact/proofing, frontier-coverage, cross-reference, table-quality, caption-quality, figure-description, SNmono policy, provenance, term-list, back-matter quality, prose-quality, duplicate-prose, paragraph-length, exercise-quality, reproducibility, index, reviewer-blocker, rendered PDF fonts, rendered PDF text and source-leak, rendered PDF reference locators and rendered bibliography labels, rendered PDF outline, all-page PDF integrity with blank-page and low-text page set checks, visual smoke, all-page visual rendering, visual-audit plan, proofing-plan, ChkTeX triage, TeX log-quality, documentation-consistency, and marker audits are documented in `notes/reference_audit.md`.

For the current English `chktex` triage summary, run:

```bash
make chktex-review
```

This optional target prints focused ChkTeX warnings after muting known noisy classes. The same focused class set is enforced by `make chktex-focused-check`, and the full warning distribution is capped by `make chktex-budget-check`; both are part of `make manuscript-audit`. The warning disposition is documented in `notes/chktex_triage.md`.

For sampled visual proofing of rendered PDFs, run:

```bash
make visual-full-check
make visual-audit
```

`make visual-full-check` renders every page at low resolution and fails on unexpected blank, dense, or edge-clipped output. `make visual-audit` rebuilds both PDFs, renders representative pages to `/tmp/llm_book_visual_audit` by default, verifies the exact 360 PNG file set, checks PNG headers, dimensions, nonblank page ink ratios, expected blank visual pages, and edge margins, then prints the generated PNG list. The sampled page set and inspection criteria are documented in `notes/visual_audit.md`.

Run `make visual-audit-plan-check` to rebuild the PDFs as needed and verify the sampled page set plus current rendered-text fingerprints without rendering PNGs. Run `make proofing-plan-check` to rebuild the PDFs as needed and verify the full human proofread record in `notes/proofing_plan.md`: it must cover all rendered pages, record the current rendered-text fingerprints, and only allow Complete proofread status when every page batch is Reviewed against those fingerprints.

## Overleaf

Create or open the Overleaf project linked to this GitHub repository and set `book/book.tex` as the main document. If Overleaf imports the `book` directory as the project root, set `book.tex` as the main document.

For the Chinese edition, create a separate Overleaf build target or project rooted at `book/book_zh.tex` and use XeLaTeX.

## Manuscript Policy

The local course repository is used as a coverage map and source of implementation exercises. Manuscript prose must be original and should cite primary papers or technical reports for research claims. Third-party slides, code, datasets, papers, model weights, and media require provenance review before publication.

The acceptance rubric and ongoing quality notes live in `notes/`. The manuscript is not publication-ready until the current acceptance gates in `notes/manuscript_acceptance_rubric.md` pass.
House-style decisions that affect manuscript review noise are recorded in `notes/style_guide.md`.

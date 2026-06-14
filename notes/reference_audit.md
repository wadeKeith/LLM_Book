# Reference and Manuscript Marker Audit

Date: 2026-05-26

## Purpose

Publication builds should fail before release if required local publication toolchain executables are missing or cannot report versions, if required Springer template files are missing or drift between root and `book/`, if release artifact ignore rules regress, if the release workspace contains uninventoried non-build files or silently includes external figures, screenshots, datasets, model weights, model outputs, or code listings, if the local source-material inventory drifts from the surrounding source workspace, if the professor-style review register does not cover all 17 English chapters, lacks current comment-stripped source fingerprints, or records an Open/Reopened P0/P1 blocker, if a manuscript citation points to a missing BibTeX key, if the BibTeX file has malformed entry structure, if the bibliography contains duplicate keys, unused entries, duplicate titles or locator URLs, malformed or future publication-year values, malformed or future-dated arXiv locators, malformed URL/DOI/arXiv locator values, DOI resolver URLs that should be stored as DOI fields, undocumented insecure HTTP URLs, entries missing basic metadata, or unprotected title capitalization for technical proper names, if root publication structure or chapter structure regresses, if bilingual front matter loses publication-facing substance, provenance markers, responsible-use markers, or source-cleanliness guarantees, if English chapter abstracts lose length, uniqueness, terminal punctuation, or source-cleanliness guarantees, if English chapter contracts lose placement, reader-facing substance, length budget, marker coverage, or source-cleanliness guarantees, if English or Chinese headings lose compactness, uniqueness, or source-cleanliness guarantees, if `notes/toc_review.md` drifts away from the current converged 17-chapter manuscript structure, if chapter coverage drops below conservative publication floors, if the Chinese readable edition loses 17-chapter order/title alignment with the English controlling manuscript or required chapter-level topic anchors, if the documented frontier coverage layer loses required references or topic markers, if cross-references point at missing or duplicate labels, if figures or tables lack captions or correctly prefixed labels, if figures or tables are not referenced in the manuscript text or are locally referenced out of source order, if source tables lose booktabs-style top/mid/bottom rules, use vertical or `\hline` rules, or become too thin to be useful, if figure or table captions lose minimum substance, terminal punctuation, uniqueness, or source-cleanliness guarantees, if English SNmono figures lack plain-text `\Description` accessibility text, if the English SNmono source violates important template portability constraints, if manuscript prose has long exact English-word or CJK-character overlap with local readable source files, if conservative English prose-quality checks find repeated words, common spelling slips, technical-name casing drift, or obvious source punctuation artifacts, if Chinese source punctuation checks find ASCII citation/code sentence periods, spacing around Chinese punctuation, repeated Chinese punctuation, or ASCII punctuation after Chinese text, if exact duplicate long prose paragraphs or sentences appear after TeX-aware normalization, if ordinary prose paragraphs exceed conservative English or Chinese readability-length budgets, if English or Chinese exercise sections lose minimum prompt count, prompt substance, terminal punctuation, or duplicate-prompt hygiene, if the bilingual reproducibility appendices lose required run-card fields for code/data versions, tokenizer and chat-template state, model and optimization configuration, hardware/runtime, validation metrics, failure modes, or conclusions, if acronym/glossary/chapter term lists lose index coverage or clean label formatting, if the appendix, acronym list, glossary, or Chinese back-matter appendix lose required section order, marker coverage, or minimum glossary substance, if the English index loses coverage, alias consistency, canonical topic paths, or required parent subentry grouping, if the rendered PDFs lose required title/author/subject/keyword metadata or document-level delivery properties, if rendered PDFs contain Type 3 fonts, unembedded fonts, fonts that are not subset embedded, or fonts without Unicode maps, if rendered PDF text loses expected publication-structure markers or leaks raw TeX commands, unresolved reference markers, raw BibTeX entry markers, or editorial placeholders, if rendered reference locators lose the NIST DOI, render a DOI resolver URL instead of a DOI locator, drop the documented Sutton/Barto HTTP exception, or show URL bracket artifacts, if rendered bibliography labels stop matching the generated `.bbl` files, if release documentation drifts away from the actual audit targets or current PDF metadata, if the PDF outline loses front-matter, part, chapter, appendix, glossary/reference, or index navigation, if all-page PDF text extraction stops matching the PDF page count, blank-page policy, expected blank-page set, or expected low-text page set, if sampled or all-page rendered PDF pages are blank, unexpectedly dense, or visibly clipped at the page edge, if TeX Underfull hbox/vbox or badness-10000 warning counts exceed the documented layout-noise budgets, or if unresolved editorial markers remain in the manuscript source.

## Repeatable Commands

From the repository root:

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
make figure-description-check
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
make index-check
make reviewer-check
make pdf-metadata-check
make pdf-font-check
make pdf-text-check
make pdf-reference-check
make pdf-outline-check
make pdf-page-integrity-check
make visual-smoke-check
make visual-full-check
make visual-audit-plan-check
make proofing-plan-check
make documentation-check
make chktex-triage-check
make chktex-budget-check
make chktex-focused-check
make log-quality-check
make placeholder-check
make manuscript-audit
make release-candidate
make clean
make clean-check
```

`make toolchain-check` verifies the local publication toolchain before later gates run. It requires Python 3.10+, `latexmk`, `rg`, `pdfinfo`, `pdffonts`, `pdftotext`, `pdftoppm`, and `chktex`, and records concise version lines.

`make citation-check` parses the English manuscript, Chinese edition, front matter, back matter, chapter files, and `book/references.bib`. It checks:

- every cited key exists in the bibliography;
- BibTeX entries have balanced braces and no unexpected non-comment text between entries;
- bibliography keys are unique;
- bibliography entries are all cited by the manuscript;
- every bibliography entry has a title and year;
- publication-year values are four digits between 1900 and the current year;
- every bibliography entry has a creator field such as author, editor, organization, or institution;
- every bibliography entry has a locator field such as DOI, URL, eprint, journal, booktitle, or howpublished;
- bibliography titles and locator URLs are not duplicated across keys;
- URL, DOI, eprint, and arXiv preprint locator values are syntactically consistent;
- arXiv locator months are not future-dated and arXiv locator years are not later than the bibliography year;
- DOI values are stored in `doi` fields instead of DOI resolver URLs;
- insecure HTTP URLs are rejected unless they are explicitly documented exceptions.
- title capitalization for technical proper names such as GPT, BERT, LoRA, Qwen, DeepSeek, NIST, and C2PA is protected against BibTeX downcasing.

`make repo-hygiene-check` verifies that required Springer release/template files exist and are nonempty, that root `SNmono.cls` and `book/SNmono.cls` are byte-identical, that the English root uses the local `SNmono` class, `spmpsci` style, and local `references.bib`, that `.gitignore` contains the expected release-artifact patterns, and that README release instructions mention the main English and Chinese entrypoints plus the audit and cleanup commands.

`make release-inventory-check` verifies that every non-build file in the release workspace matches exactly one documented file class in `notes/release_inventory.md`, that every inventory pattern has at least one release-file match, and that the inventory explicitly excludes external figures, screenshots, datasets, model weights, model outputs, and code listings unless they receive separate review.

`make source-inventory-check` verifies that `notes/source_inventory.md` matches the current surrounding source workspace after excluding `LLM_Book`, hidden directories, and Python caches. It records the total local source-root file count, major source suffix counts, provenance-readable text/code file count, and, when present, the count, paths, and byte sizes of oversize readable files that remain outside the automated provenance scan.

`make audit-script-check` verifies the release audit Python scripts themselves. It compiles every `scripts/*.py` file with `py_compile`, requires a `python3` shebang, module docstring, and `from __future__ import annotations`, requires every `check_*.py` script to be referenced by the Makefile, and verifies that `make manuscript-audit` includes the audit-script gate.

`make makefile-consistency-check` verifies the release Makefile topology. It checks that `.PHONY` targets and target definitions agree, that every non-clean `*-check` gate is included in `make manuscript-audit`, that each manuscript-audit dependency is defined and phony, and that the `all` and `check` aggregate dependencies stay stable.

`make placeholder-check` scans manuscript TeX files for unresolved editorial markers such as `TODO`, `FIXME`, `TBD`, `XXX`, `???`, `待补`, `lorem`, `dummy`, `citation needed`, and `cite needed`. It intentionally does not fail on ordinary technical uses of placeholder/image-placeholder terminology.

`make structure-check` verifies:

- the English root keeps the publication-order scaffold: title page, front matter, preface, ethics note, table of contents, acronym list, main matter, appendix, glossary, references, and index;
- the Chinese root keeps the publication-order scaffold: title page, front matter, preface, ethics note, table of contents, main matter, appendix with notation/experiment/terminology sections, and references;
- the English root includes exactly 17 chapter files;
- every English chapter file under `book/chapters/` is included and no included chapter file is missing;
- every English chapter has one `\chapter`, a `ch:` label, an abstract, at least four sections, body citations, body index entries, key terms, and exercises;
- the Chinese readable edition has 17 numbered content chapters, each with key-term and exercise paragraphs;
- manuscript sources do not import external images or code listings through `\includegraphics`, `\lstinputlisting`, `\verbatiminput`, or `\inputminted`.

`make frontmatter-quality-check` verifies that the English and Chinese front matter retain publication-facing provenance and responsible-use substance. It checks 359 English preface words, 268 English ethics words, 409 Chinese preface Han characters, 179 Chinese ethics Han characters, and 24/24 front-matter marker hits across originality, lifecycle framing, evidence-first sourcing, provenance, privacy, copyright, benchmark contamination, high-risk deployment, and no-advice disclaimers.

`make abstract-quality-check` verifies that each of the 17 English chapter files has exactly one abstract, that abstracts stay within a 40--120 word publication-facing range, end with terminal punctuation, avoid citation/reference/label/index commands and unresolved editorial markers, and remain unique after TeX-aware normalization. The latest run checked 17 English chapter abstracts, found 41 minimum abstract words, 78 maximum abstract words, and 0 duplicate abstracts.

`make chapter-contract-check` verifies that each of the 17 English chapter files has exactly one `Chapter contract` paragraph after the abstract and before the first section. It enforces a 35--70 word range, a reader-facing marker phrase, terminal punctuation, and no citation/reference/label/index commands or unresolved editorial markers. The latest run checked 17 English chapter contracts, found 37 minimum contract words, 44 maximum contract words, and 51/51 chapter contract marker hits.

`make heading-quality-check` verifies that the 17 English chapter files and the Chinese readable edition keep compact, source-clean chapter/section/subsection headings. It checks 17 English chapter heading files, 279 English headings, 1 Chinese heading file, and 392 Chinese headings. It enforces a 12-word English heading budget, a 22-unit Chinese heading budget, rejects duplicate same-level headings within chapters, rejects citation/reference/label/index/URL commands and unresolved editorial markers, and allows intentional question-form headings while rejecting sentence-like trailing punctuation. The latest run found 8 maximum heading words, 20 maximum Chinese heading text units, 0 duplicate headings within chapters, and 0 duplicate Chinese headings within chapters.

`make toc-review-check` verifies that `notes/toc_review.md` keeps the converged chapter list aligned with the English controlling manuscript. It checks 17 documented TOC chapters against the 17 manuscript chapters included by `book/book.tex`, including order and normalized chapter titles.

`make coverage-check` verifies conservative chapter-coverage floors that should not regress during editing. Each English chapter body must have at least 1,800 words before Key Terms, at least 5 citation commands, at least 20 source index entries, at least 1 figure, and at least 1 table. Each Chinese content chapter must have at least 1,800 Han characters, at least 1 citation command, at least 1 figure, and at least 1 table.

`make edition-alignment-check` verifies that the English root still includes the expected 17 chapter files in order, that English chapter titles have not drifted from the review baseline, that the Chinese readable edition keeps the corresponding 17 chapter titles in order, and that each Chinese chapter retains required core-topic anchor terms from its English counterpart. This protects chapter-level alignment but is not a paragraph-for-paragraph bilingual proofread.

`make bilingual-coverage-check` verifies that the Chinese readable edition remains a substantive companion to the English controlling draft without claiming paragraph-for-paragraph bilingual completeness. It compares English chapter body word counts before Key Terms with Chinese chapter Han-character counts, enforces per-chapter and whole-book Chinese-to-English coverage floors, and documents the result in `notes/bilingual_coverage.md`.

`make bilingual-print-plan` reports the source-unit inventory for the stricter paragraph-level bilingual print objective. The current plan in `notes/bilingual_print_plan.md` records 1163 English source units requiring explicit Chinese counterparts, 1163 explicitly aligned units, 1163 proofed units, and 0 open source units. `make bilingual-alignment-check` currently reports 1163 source units, 1163 manifest rows, 1163 aligned units, 1163 proofed units, 0 open units, and 0 manifest errors. `make bilingual-print-artifact-check` now renders those aligned pairs into a 647-page proofing draft outside the release tree, verifies 1163/1163 rendered source-unit IDs, reports rendered text SHA-256 `caefc5aa856c352f465ff17f991612ddac7a5e8fb29056fb4bb83cbbb84e83c1`, and found 0 artifact errors. `make bilingual-print-proofing-check` validates `notes/bilingual_print_proofing_log.md` against the rendered artifact; BP-01 through BP-17 cover Chapters 1--17 on pages 47--619, and BP-18 through BP-22 cover Preface, Responsible Use, Appendix prose, Acronyms, and Glossary entries on pages 620--647.

`make bilingual-alignment-check` verifies the partial source-level pair manifest in `notes/bilingual_alignment_manifest.md`. It requires every recorded alignment row to reference a current English source-unit ID, use a valid status, include substantive Chinese text, avoid unresolved markers, and keep proofing status separate from source-level alignment.

`make frontier-coverage-check` verifies that the frontier layer recorded in `notes/frontier_gap_review.md` remains present in both manuscripts. It requires the key frontier bibliography entries to exist, to be cited by the English controlling manuscript, and to be cited by the Chinese readable edition. It also checks source markers for context engineering, typed memory, post-DPO objectives, RLVR/GRPO, adaptive test-time compute, unified understanding-generation systems, diffusion and rectified-flow objectives, hybrid AR-diffusion, VLA/action models, video-generation evaluation, unlearning, watermarking, content credentials, and C2PA coverage.

`make crossref-check` verifies that every source-level `\ref`, `\eqref`, `\pageref`, `\autoref`, `\nameref`, `\cref`, `\Cref`, `\vref`, and `\Vref` target exists, that labels are unique across the manuscript sources, that every figure/table float has a caption and correctly prefixed label, that every `fig:` or `tab:` label is referenced in the manuscript text, and that local first references to figure/table labels follow the source float order.

`make table-quality-check` scans all English and Chinese `tabular` environments. It requires booktabs-style `\toprule`, `\midrule`, and `\bottomrule` rules in order, rejects vertical rules plus `\hline`/`\svhline`/`\cline`, and requires at least three data rows so tables remain substantive.

`make caption-quality-check` scans English and Chinese figure/table captions for publication-facing caption hygiene. It requires 85 current captions, a 5--70 text-unit range, terminal punctuation, no duplicate captions after TeX-aware normalization, no unresolved editorial markers, and no `\label` or `\index` commands inside caption text. The latest run checked 85 captions, found 5 minimum caption text units, 68 maximum caption text units, and 0 duplicate captions.

`make figure-description-check` rebuilds the English PDF, verifies that every English SNmono `figure` environment has exactly one plain-text `\Description` command before its caption, and verifies that the generated `DescriptionTexts.txt` production side file has the same description records in source order. This supports Springer's accessibility requirement for alternative text and catches production-side description drift.

`make snmono-policy-check` verifies Springer SNmono portability constraints for the English controlling manuscript. It fails on explicit `amsmath` loading alongside `newtxmath`, discouraged layout/font packages, `\def`, `\renewcommand`, `\pageref`, fixed page-break commands, low-level box commands, and wrapfigure/subfigure-style constructs in English manuscript sources.

`make provenance-check` scans the manuscript TeX sources against local readable source files under the surrounding source workspace, excluding `LLM_Book` itself. It fails on 18-word exact English shingles or 60-Han-character exact CJK shingles shared between manuscript prose and `.md`, `.txt`, `.py`, `.tex`, `.rst`, or `.ipynb` sources. This is a conservative hard-copying guard, not a substitute for human permissions review of PDFs, slides, media, datasets, or figures.

`make term-check` verifies that the acronym list and glossary are sorted and free of duplicate labels, that every acronym has a matching source index entry, that glossary entries contain index entries, and that English chapter Key Terms labels are unique, free of terminal label punctuation, and end their definitions cleanly. It also verifies that the Chinese readable edition has key-term paragraphs for all 17 content chapters, enough semicolon-separated entries per chapter, non-terse entry text, terminal Chinese punctuation, no duplicate entries within a chapter, and no citation/reference/index commands inside those term paragraphs.

`make backmatter-quality-check` verifies that the English appendix, acronym list, glossary, and Chinese appendix remain coherent publication back matter rather than isolated checked fragments. It checks 3/3 English appendix sections, 17/17 English appendix marker hits, 20 acronym entries, 24 glossary entries, 3/3 Chinese appendix sections, 28/28 Chinese appendix marker hits, and 17 Chinese appendix glossary entries.

`make prose-quality-check` scans the English controlling manuscript for conservative copy-editing artifacts: repeated words after TeX-aware cleanup, common spelling slips, casing drift for selected technical names such as GitHub/PyTorch/JavaScript, whitespace before punctuation in source prose, and repeated punctuation outside skipped math, table, verbatim, and TikZ regions. It is not a full human proofread.

`make chinese-prose-quality-check` scans the Chinese readable edition for conservative source punctuation artifacts: ASCII sentence periods after citations or inline code, spaces around Chinese punctuation, repeated Chinese punctuation, and ASCII punctuation after Chinese text. It is not a full bilingual proofread.

`make duplicate-prose-check` scans the English controlling manuscript and Chinese readable edition body prose for exact duplicate long paragraphs or sentences after TeX-aware normalization. It skips preamble code, math, tables, TikZ diagrams, and verbatim-like environments, so it is a conservative guard against copy-paste accidents rather than a semantic similarity detector.

`make paragraph-length-check` scans ordinary English and Chinese manuscript prose for conservative paragraph-length budgets. It skips preamble code, math, figures, tables, lists, TikZ diagrams, and verbatim-like environments, so it catches hard-to-read monolithic body paragraphs without flagging exercises, key-term lists, captions, or structural material.

`make exercise-quality-check` scans English and Chinese exercise sections for publication-facing pedagogical hygiene. It requires every English chapter to have at least five exercise prompts and every Chinese chapter to have at least four, enforces conservative prompt-length floors, requires terminal punctuation, and rejects duplicate prompts after TeX-aware normalization.

`make reproducibility-check` verifies the English and Chinese appendix experiment-record sections. It requires the English run-card template and bilingual field coverage for code and data versions, license or provenance, tokenizer and chat-template state, model configuration, random seeds, optimizer, learning rate, batch size, precision, hardware, expected runtime, checkpointing, validation, primary metrics, failure modes, and conclusions.

`make index-check` rebuilds the PDFs and verifies English index coverage, important acronym `see` aliases, required canonical topic paths, required parent subentry groups, repeated-entry budget, alias target existence, press-style entry hygiene, the `makeindex` log, and the rendered English PDF index section extracted with `pdftotext`.

`make reviewer-check` verifies `notes/professor_review.md`, requiring a review basis tied to `make manuscript-audit` and `make visual-audit`, one passing acceptance-matrix row for each of the 17 English chapters, a current comment-stripped source fingerprint for each English chapter, and 0 Open/Reopened P0/P1 reviewer blockers.

`make pdf-metadata-check` rebuilds the PDFs and verifies title, author, subject, required keyword coverage, exact current page counts, current file-size ranges, letter page size, PDF 1.7 output, no encryption, no JavaScript, and no interactive form metadata.

`make pdf-font-check` rebuilds the PDFs, reads rendered font tables with `pdffonts`, and fails on Type 3 fonts, unembedded fonts, fonts that are not subset embedded, or fonts without Unicode maps. This follows the Springer production guidance in `instructions.pdf` that Type 3 fonts can break professional output.

`make pdf-text-check` rebuilds the PDFs, extracts rendered text with `pdftotext`, and verifies that the English and Chinese PDFs contain the expected title, front-matter, contents, all 17 chapter titles, appendix, glossary/reference, and index markers in publication order. Chapter and back-matter markers must appear more than once where appropriate, so the gate checks rendered body/back-matter text rather than only the table of contents. It also fails if extracted PDF text contains raw TeX citation/reference/manuscript commands, unresolved reference markers such as `??`, raw BibTeX entry markers, or unresolved editorial placeholders.

`make pdf-reference-check` rebuilds the PDFs, extracts rendered text with `pdftotext`, and verifies selected reference locator invariants plus rendered bibliography label completeness in both release PDFs. It requires the NIST synthetic-content reference to render as a DOI locator, rejects rendered DOI resolver URLs for that entry, requires the documented Sutton/Barto HTTP URL exception to remain visible, fails if rendered URLs contain bracket artifacts, and checks that rendered bibliography labels are contiguous and match the generated `.bbl` files.

`make pdf-outline-check` rebuilds the PDFs and decodes the Hyperref outline source files (`book.out` and `book_zh.out`). It verifies front-matter, part, chapter, appendix, glossary/reference, and index bookmarks in publication order, checks that all 17 chapter bookmarks are nested under part bookmarks, and fails on malformed, duplicate, or parentless outline records.

`make pdf-page-integrity-check` rebuilds the PDFs, extracts every page with `pdftotext`, and verifies that extracted page counts match `pdfinfo`. It enforces the English SNmono layout's even-page-only blank-page policy, requires the Chinese `openany` edition to have no blank extracted pages, and pins the current expected blank-page and low-text page sets so near-blank page regressions cannot silently appear.

`make visual-smoke-check` rebuilds the PDFs, renders sampled English and Chinese pages with `pdftoppm`, and verifies that the sampled pages are nonblank, have expected raster dimensions, are not unexpectedly dense, and do not have dark pixels touching the page edge.

`make visual-full-check` rebuilds the PDFs, renders all English and Chinese pages at low resolution with `pdftoppm`, and verifies expected blank and low-ink visual pages while failing on unexpected blank, dense, or edge-clipped output. It is an automated all-page regression screen, not a substitute for human proofing.

`make visual-audit` remains the human rendered-page review target, and now also verifies the exact 360 PNG file set, PNG headers, raster dimensions, nonblank page ink ratios, expected blank visual pages, and edge margins for the larger sampled image set.

`make visual-audit-plan-check` rebuilds the PDFs as needed and verifies that `notes/visual_audit.md`, the `make visual-audit` `pdftoppm` commands, `scripts/check_visual_audit_images.py`, and the current rendered-text fingerprints use the same sampled page ranges, expected PNG count, DPI, and expected blank visual pages.

`make proofing-plan-check` rebuilds the PDFs as needed and verifies that `notes/proofing_plan.md` covers all rendered English and Chinese PDF pages exactly once for a full human proofread plan, uses valid batch statuses, records rendered-text fingerprints for the current PDFs, ties every Reviewed batch to a current rendered-text fingerprint in the proofing log, and only allows Complete status after every batch is Reviewed. The latest run found 20 proofing batches, 238/238 English proofing pages, 308/308 Chinese proofing pages, 20/20 reviewed proofing batches, Complete proofread status, English proofing text SHA-256: 8e41590a1c7a1158a746873f711f01c2fc32c344cc37fe35cfa02d22067fb43e, and Chinese proofing text SHA-256: a4b56331f4304d70c70619a90c739fb6b268478fd047280331e21be5abb029db.

`make documentation-check` rebuilds the PDFs as needed and verifies that README and this audit note document every target currently included in `make manuscript-audit`. It also checks that the acceptance rubric mentions the current release gates and `make release-candidate`, that the provenance register links to `make provenance-check`, that citation-count, release-inventory, source-inventory, audit-script-count, Makefile-consistency-count, provenance-count, front-matter quality, abstract-quality, chapter-contract, heading-quality, caption-quality, term-list, back-matter quality, exercise-quality, reproducibility-record, TOC-review, bilingual-coverage, bilingual-alignment, bilingual-print artifact and proofing notes, frontier-coverage, index-quality, ChkTeX-triage, visual-audit-plan, proofing-plan, prose-quality, duplicate-prose, paragraph-length, and PDF-text summary notes match the current scans, and that `notes/publication_quality_audit.md` records the current PDF page counts and PDF versions. Exact current page counts, current file-size ranges, and all-page visual rendering remain enforced by their dedicated gates; the release PDFs have shown byte-level rebuild variations.

`make chktex-triage-check` verifies that `notes/chktex_triage.md`, `notes/style_guide.md`, the ChkTeX budget script, and the Makefile focused-warning mutes stay synchronized. The current check covers 7 ChkTeX triaged warning classes and 719 current ChkTeX warning hits.

`make chktex-budget-check` runs full ChkTeX on the English controlling manuscript and fails if any untriaged warning class appears or if one of the documented high-volume classes exceeds its current budget. `make chktex-focused-check` verifies that the English controlling manuscript has no remaining ChkTeX warnings outside the documented high-volume house-style mutes.

`make log-quality-check` rebuilds the PDFs as needed and parses `book.log` and `book_zh.log`. It caps the current reviewed Underfull hbox/vbox warning counts and badness-10000 counts, while the hard `make check` log scan continues to fail on overfull boxes and PDF/link warnings that should remain at zero.

`make manuscript-audit` runs toolchain checks, repository-hygiene checks, release-inventory checks, source-inventory checks, audit-script checks, makefile-consistency checks, citation checks, structure checks, front-matter quality checks, abstract-quality checks, chapter-contract checks, heading-quality checks, TOC-review checks, chapter-coverage checks, edition-alignment checks, bilingual-coverage checks, bilingual-alignment checks, bilingual-print artifact checks, bilingual-print proofing checks, frontier-coverage checks, cross-reference checks, table-quality checks, caption-quality checks, figure-description checks, SNmono policy checks, provenance checks, term-list checks, back-matter quality checks, English prose-quality checks, Chinese prose-quality checks, duplicate-prose checks, paragraph-length checks, exercise-quality checks, reproducibility-record checks, ChkTeX triage, budget, and focused checks, TeX log-quality checks, index checks, reviewer-blocker checks, rendered PDF metadata checks, rendered PDF font checks, rendered PDF text and source-leak checks, rendered PDF reference-locator and bibliography-label checks, rendered PDF outline checks, rendered PDF page-integrity checks, rendered-page visual smoke checks, all-page visual rendering checks, visual-audit plan checks, proofing-plan checks, documentation-consistency checks, placeholder checks, both PDF builds, and the hard PDF/log checks.

`make release-candidate` runs the full manuscript audit, then executes `make clean`, `make clean-check`, `git diff --check`, and a final `make release-inventory-check` so the release workspace is checked again after cleanup.

`make clean-check` is intended to run after `make clean`. It verifies that ignored LaTeX side files, SNmono `DescriptionTexts.txt`, Python cache directories, and `.DS_Store` files are not left in the release workspace.

## Latest Result

The latest toolchain check found Python 3.14.5, latexmk 4.87, ripgrep 15.1.0, Poppler 26.03.0 tools (`pdfinfo`, `pdffonts`, `pdftotext`, and `pdftoppm`), and ChkTeX 1.7.9, with no missing executable or version-probe failures.

The latest citation check found 294 unique cited keys, 294 bibliography entries, 294 checked bibliography titles, 294 checked bibliography years, 2014--2026 publication-year range, 168 checked arXiv locators, 2014-12--2026-05 arXiv month range, 293 checked bibliography URLs, 1 checked DOI field, 1 documented HTTP URL exception, and 0 unused bibliography entries, with no malformed-entry, duplicate-key, missing-key, duplicate-title, duplicate-URL, publication-year, arXiv-date, locator-value, DOI-normalization, insecure-URL, basic-metadata, or title-capitalization failures.

The latest repository-hygiene check inspected 10 release/template files, 19 required `.gitignore` patterns, root build configuration, and README release instructions, with no drift or missing-file failures.

The latest release-inventory check inventoried 119 release files across 7 documented file classes, ignored build/private files, and found no uninventoried non-build files or undocumented external asset classes. The ignored-file count is intentionally not pinned because LaTeX side files and Python caches are transient release-build artifacts.

The latest source-inventory check inventoried 1,565 regular source-root files outside `LLM_Book`, including 207 MP4 files, 64 PDF files, 20 PPTX slide decks, 476 Python files, 51 notebooks, 80 Markdown files, and 96 text files. It found 703 provenance-readable text/code files under the automated suffix and size policy, plus 0 readable files over the provenance-scan size cap.

The latest audit-script check found 54 audit Python scripts, 52 audit check scripts referenced by Makefile, and 0 audit script compile/header errors.

The latest Makefile-consistency check found 63 Makefile phony targets, 63 Makefile target definitions, 52 manuscript-audit dependencies, 4 release-candidate recipe steps, and 0 Makefile consistency errors.

The latest structure check found valid English and Chinese root publication scaffolds, 17 English chapters, and 17 Chinese content chapters, with no missing key-term/exercise sections, orphan English chapter files, or external image/code imports.

The latest front-matter quality check found 359 English preface words, 268 English ethics words, 409 Chinese preface Han characters, 179 Chinese ethics Han characters, and 24/24 front-matter marker hits, with no unresolved editorial markers or source-import commands.

The latest abstract-quality check found 17 English chapter abstracts, 41 minimum abstract words, 78 maximum abstract words, and 0 duplicate abstracts, with no missing, overlong, underlength, unpunctuated, command-bearing, or editorial-marker abstracts.

The latest chapter-contract check found 17 English chapter contracts, 37 minimum contract words, 44 maximum contract words, and 51/51 chapter contract marker hits, with no misplaced, underlength, overlength, command-bearing, or editorial-marker contracts.

The latest heading-quality check found 17 English chapter heading files, 279 English headings, 8 maximum heading words, 0 duplicate headings within chapters, 1 Chinese heading file, 392 Chinese headings, 20 maximum Chinese heading text units, and 0 duplicate Chinese headings within chapters, with no overlong, empty, command-bearing, punctuation-noisy, or editorial-marker headings.

The latest TOC-review check found 17 documented TOC chapters and 17 manuscript chapters in the same order.

The latest coverage check found 17 English chapters above the coverage floors, with minimum English body coverage of 1,908 words, 6 citation commands, 21 index entries, 1 figure, and 1 table before Key Terms. It found 17 Chinese content chapters above the coverage floors, with minimum Chinese chapter coverage of 5,396 Han characters, 7 citation commands, 1 figure, and 1 table.

The latest edition-alignment check found 17 English/Chinese chapter pairs in order and 106/106 Chinese chapter alignment anchors present.

The latest bilingual-coverage check found 17 bilingual chapter pairs, 54970 English controlling body words, 155578 Chinese readable Han characters, 2.72 minimum Chinese-to-English coverage ratio, weakest bilingual chapter: 15 ratio 2.716; Multimodal and Generative Foundation Models / 多模态与生成式基础模型, 2.83 total Chinese-to-English coverage ratio, and 0 chapters below coverage floor.

The latest frontier-coverage check found 24 required frontier bibliography keys, 24/24 English frontier citation hits, 24/24 Chinese frontier citation hits, 29/29 English frontier topic markers, and 21/21 Chinese frontier topic markers.

The latest cross-reference check found 270 labels, 101 source-level references, and 85 figure/table environments, with 0 duplicate labels, 0 missing reference targets, 0 unreferenced figure/table labels, 0 files with out-of-order local figure/table references, and 0 figure/table caption-label format errors.

The latest table-quality check found 67 `tabular` environments and 41 table floats, with 0 booktabs-order, vertical-rule, old-rule, or data-row errors.

The latest caption-quality check found 85 captions, 5 minimum caption text units, 68 maximum caption text units, and 0 duplicate captions, with no missing punctuation, underlength, overlength, command-bearing, or editorial-marker captions.

The latest figure-description check found 23 English figure environments, 23 figures with plain-text `\Description` entries, and 23 generated `book/DescriptionTexts.txt` records matching the source descriptions in order.

The latest SNmono policy check inspected 23 English manuscript files and 13 English root packages, with no discouraged command, package, or `newtxmath`/`amsmath` compatibility failures.

The latest provenance check inspected 24 manuscript TeX files against 703 external readable source files, generated 74,458 manuscript 18-word shingles and 156,963 manuscript 60-Han-character shingles, and found 0 long exact source-overlap hits.

The latest term-consistency check found 20 acronym entries, 20 indexed acronym entries, 24 glossary entries, 164 chapter key-term entries, 17/17 Chinese chapter key-term chapters, 327 Chinese chapter key-term entries, 6/4 Chinese minimum key-term entries per chapter, and 10 Chinese minimum key-term text units, with 0 term consistency errors.

The latest back-matter quality check found 3/3 English appendix sections, 17/17 English appendix marker hits, 20 acronym entries, 24 glossary entries, 3/3 Chinese appendix sections, 28/28 Chinese appendix marker hits, and 17 Chinese appendix glossary entries.

The latest prose-quality check scanned 23 English manuscript files, 2,054 source prose lines, and 60,769 words after TeX-aware cleanup, with 0 copy-editing artifacts.

The latest Chinese prose-quality check scanned 1907 Chinese prose lines and 149,515 Han characters, with 0 punctuation artifacts.

The latest duplicate-prose check scanned 22 prose files, 2,616 paragraphs, and 8,671 sentences, with 0 duplicate long prose findings.

The latest paragraph-length check scanned 22 prose files and 2,066 ordinary prose paragraphs, with a maximum English ordinary paragraph length of 178 words and a maximum Chinese ordinary paragraph length of 419 Han characters, and found 0 overlength ordinary paragraphs.

The latest exercise-quality check found 17/17 English exercise chapters, 133 English exercise items, 5/5 English minimum exercise items per chapter, and 119 English minimum exercise-section words. It found 17/17 Chinese exercise chapters, 245 Chinese exercise items, 9/4 Chinese minimum exercise items per chapter, and 279 Chinese minimum exercise-section text units. No duplicate exercise prompts or terminal-punctuation failures were found.

The latest reproducibility-record check found 18/18 English reproducibility fields, 18/18 Chinese reproducibility fields, and 0 reproducibility-record errors.

The latest index check found 646 source index entries, 485 main terms, 31 `see` aliases, 17/17 required index topic paths, 7/7 required parent subentry groups, 4/4 maximum repeated source index path, 0 source index paths over repeat budget, 0 index style errors, at least 21 index entries per English chapter, and a `makeindex` log with 646 accepted entries, 0 rejected entries, and 0 warnings. The rendered-index pass found 6 rendered index pages, 311 nonempty rendered index body lines, 34/34 rendered index required terms, and 31/31 rendered index see aliases.

The latest reviewer-blocker check found 17 passing chapter review rows, 17 chapter source fingerprints, 0 Open/Reopened P0/P1 blockers, and 0 closed P0/P1 blockers recorded.

The latest PDF metadata check found the expected English and Chinese title, author, subject, keyword coverage, exact current page counts, current file-size ranges, letter page size, PDF 1.7 output, no encryption, no JavaScript, and no interactive form metadata. The current English PDF has 238 pages and 887900--888000 bytes across clean builds; the current Chinese PDF has 308 pages and 1593700--1593950 bytes across clean builds.

The latest PDF font check found 12 embedded, subset Type 1 fonts with Unicode maps in the English PDF and 28 embedded, subset fonts with Unicode maps in the Chinese PDF, covering CID TrueType, CID Type 0C, and Type 1C font types, with 0 Type 3 fonts.

The latest rendered PDF text check found the expected English and Chinese title, front-matter, contents, all 17 chapter titles, appendix, glossary/reference, and index markers in publication order. It checked 26 marker classes with 163 marker hits in the English PDF and 24 marker classes with 204 marker hits in the Chinese PDF, with 0 rendered source-leak hits in either PDF.

The latest rendered PDF reference-locator and rendered bibliography-label check confirmed that both release PDFs render the NIST synthetic-content reference as DOI `10.6028/NIST.AI.100-4`, do not render a DOI resolver URL for that entry, render the documented Sutton/Barto HTTP URL exception, contain no URL bracket artifacts, and have contiguous rendered bibliography labels matching the generated `.bbl` files: 200/200 labels in the English PDF and 270/270 labels in the Chinese PDF.

The latest rendered PDF outline check found 294 English bookmarks and 398 Chinese bookmarks. It confirmed the expected front-matter, part, chapter, appendix, glossary/reference, and index bookmarks in publication order for both PDFs, with all 17 chapter bookmarks nested under 4 part bookmarks in each outline.

The latest PDF page-integrity check verified 238 English pages with the expected 15 even blank pages, minimum nonblank page text of 16 characters, and low-text pages `[17, 105]`. It verified 308 Chinese pages with the expected 0 blank pages, minimum nonblank page text of 1 character, and low-text pages `[2, 18, 19, 42, 139, 183]`.

The latest rendered-page visual smoke check sampled 11 English pages and 11 Chinese pages. The English pages had ink ratios from 0.0058 to 0.1149 with a minimum edge margin of 60 px; the Chinese pages had ink ratios from 0.0098 to 0.1935 with a minimum edge margin of 28 px.

The latest all-page visual rendering check verified 238 English visual pages at 72 dpi with 15 expected blank pages and 0 expected low-ink pages, plus 308 Chinese visual pages with 0 expected blank pages and 2 expected low-ink pages. English nonblank ink ratios were 0.0020--0.1185 with a minimum nonblank edge margin of 89 px; Chinese nonblank ink ratios were 0.0001--0.1567 with a minimum nonblank edge margin of 42 px.

The latest visual-audit image check verified the exact 360 PNG file set at 1105x1430 px, found nonblank page ink ratios from 0.0017 to 0.1118, found a 76 px minimum nonblank edge margin, and confirmed 3 expected blank visual pages across the current title, TOC, representative body, the new serving, multimodal, governance, and frontier synthesis figures, expanded Chinese chapter sample pages, appendix transition, index, and Chinese final-reference sample through page 308. The latest visual-audit plan check confirmed 23 visual-audit page ranges, 360 visual-audit PNGs, 3 expected blank visual pages, English visual-audit text SHA-256: 8e41590a1c7a1158a746873f711f01c2fc32c344cc37fe35cfa02d22067fb43e, and Chinese visual-audit text SHA-256: a4b56331f4304d70c70619a90c739fb6b268478fd047280331e21be5abb029db.

The latest proofing-plan check found 20 proofing batches, 238/238 English proofing pages, 308/308 Chinese proofing pages, 20/20 reviewed proofing batches, Complete proofread status, English proofing text SHA-256: 8e41590a1c7a1158a746873f711f01c2fc32c344cc37fe35cfa02d22067fb43e, and Chinese proofing text SHA-256: a4b56331f4304d70c70619a90c739fb6b268478fd047280331e21be5abb029db.

The latest documentation-consistency check confirmed that 52 `make manuscript-audit` targets are documented in README and this audit note, that `make release-candidate` is documented in the release notes, that the acceptance rubric and provenance register mention the required release gates, that release-inventory, source-inventory, audit-script-count, Makefile-consistency-count, reviewer register count, provenance-count, front-matter quality, abstract-quality, chapter-contract, bilingual heading-quality, bilingual-coverage, bilingual-alignment, bilingual-print artifact/proofing notes, caption-quality, term-list, back-matter quality, exercise-quality, reproducibility-record, TOC-review, frontier-coverage, index-quality, ChkTeX-triage, visual-audit-plan, proofing-plan, prose-quality, duplicate-prose, paragraph-length, and PDF-text summary notes match the current scans, and that the publication-quality audit records the current English and Chinese PDF metadata.

The latest ChkTeX triage check confirmed 7 ChkTeX triaged warning classes and 719 current ChkTeX warning hits. The latest ChkTeX budget check found warning counts within budget: `1:45/45`, `2:278/278`, `12:4/4`, `13:17/17`, `24:366/366`, `38:9/9`, and `44:0/0`. The latest focused ChkTeX check produced no warnings after the documented house-style mutes and the zero-tolerance warning-44 check.

The latest TeX log-quality check found Underfull warning counts within budget: `book.log` Underfull hbox `84/85`, Underfull vbox `0/0`, badness-10000 hbox `36/37`, and badness-10000 vbox `0/0`; `book_zh.log` Underfull hbox `61/61`, Underfull vbox `62/71`, badness-10000 hbox `16/16`, and badness-10000 vbox `29/39`.

The latest placeholder check produced no manuscript-source hits for the unresolved editorial marker set.

After the BP-22 bilingual-print closeout, the targeted release gates rerun for the paragraph-level bilingual print objective were `make documentation-check`, `make bilingual-print-proofing-check`, `make clean`, `make clean-check`, `git diff --check`, and `make release-inventory-check`; they confirmed the current documentation, rendered bilingual-print proofing artifact, cleanup state, whitespace state, and release inventory.

The full `make manuscript-audit` and `make release-candidate` wrapper remain the repeatable broad publication-candidate gates after future non-bilingual-print content, layout, citation, or index changes.

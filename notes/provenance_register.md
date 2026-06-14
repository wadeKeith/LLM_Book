# Provenance Register

This register tracks source classes for the current manuscript. The current publication candidate does not reproduce third-party slides, video transcripts, dataset rows, model outputs, code listings, or external figures.

| Source class | Current use | Publication action |
| --- | --- | --- |
| Local course slides | Topic coverage only | No wording or figures copied |
| Local video files | Filename coverage only | No transcript-level claims or copied media |
| Local code repositories | Exercise inspiration | No code listings copied into prose |
| Local PDFs of papers | Citation and technical grounding | Primary public sources cited in bibliography |
| Local datasets/checkpoints | Coverage signal only | No dataset rows, checkpoints, or generated samples included |
| Web research papers | Primary citations | Use arXiv, ACL Anthology, NeurIPS, official technical reports |
| Generated diagrams/tables | Manuscript content | Keep source in LaTeX where possible |

## Current Rule

The book may describe concepts represented in the source repository, but final prose is original and citation-backed. Any future addition of external figures, code listings, dataset examples, screenshots, or model outputs must receive a separate license and privacy review before it is included.

## Automated Guard

`make provenance-check` compares manuscript TeX prose with local readable source files outside `LLM_Book` and fails on 18-word exact English overlap or 60-Han-character exact CJK overlap. The latest run scanned 24 manuscript TeX files against 703 external `.md`, `.txt`, `.py`, `.tex`, `.rst`, and `.ipynb` files, generated 74,458 manuscript 18-word shingles and 156,963 manuscript 60-Han-character shingles, and found 0 long exact source-overlap hits. This guard covers every current readable text/code source under the configured suffix and 5,000,000 byte size policy; PDFs, slides, media, figures, datasets, and model outputs still require human permissions review.

`make source-inventory-check` keeps `notes/source_inventory.md` aligned with the current surrounding source workspace so coverage and provenance decisions are based on a current file census rather than stale planning numbers. It also keeps any future oversize readable files that remain outside automated exact-overlap scanning listed by path and byte size for human provenance review.

`make release-inventory-check` complements the prose-overlap guard by checking the release workspace itself. It verifies that every non-build file matches a documented class in `notes/release_inventory.md` and that no external figures, screenshots, datasets, model weights, model outputs, or code listings are silently present in the release package.

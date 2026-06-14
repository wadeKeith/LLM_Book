# Release Inventory

Date: 2026-05-25

## Purpose

This inventory records the file classes intentionally present in the release workspace. It complements `notes/provenance_register.md`: provenance explains source boundaries and permissions risk, while this inventory makes unexpected files visible before a release package is prepared.

## Inventoried File Classes

| File class | Patterns | Publication role |
| --- | --- | --- |
| Release instructions and repository controls | `.gitignore`, `.nojekyll`, `Makefile`, `README.md` | Local build, audit, cleanup, Pages routing, and release instructions |
| Publication website assets | `index.html`, `assets/site.css`, `assets/*.png` | Static GitHub Pages landing page and current PDF cover previews |
| Springer template package | `SNmono.cls`, `book/SNmono.cls`, `book/*.bst`, `book/svind*.ist`, `history.txt`, `readme.txt`, `instructions.pdf` | Publisher-supplied class, bibliography/index styles, and template documentation |
| English and Chinese manuscript sources | `book/*.tex`, `book/chapters/ch*.tex`, `book/references.bib` | Editable manuscript, front/back matter, chapters, and bibliography |
| Rendered release PDFs | `book/book.pdf`, `book/book_zh.pdf` | Current English controlling draft and Chinese readable edition |
| Publication audit notes | `notes/*.md` | Human-readable audit trail, acceptance criteria, provenance, style, visual QA, and release inventory |
| Release audit scripts | `scripts/*.py` | Repeatable source, PDF, metadata, provenance, documentation, build-locking, and cleanup gates |

## Explicit Exclusions

No external figures, screenshots, datasets, model weights, model outputs, or code listings are intentionally present in the release workspace. Future additions in those classes require a separate license, privacy, and provenance review before publication.

Ignored LaTeX side files, Python caches, SNmono `DescriptionTexts.txt`, and desktop artifacts are cleanup outputs rather than release files. `make clean-check` verifies they are absent after cleanup, while `make release-inventory-check` ignores normal build side files and fails on unexpected non-build files.

## Repeatable Command

From the repository root:

```bash
make release-inventory-check
```

The check scans the release workspace outside `.git`, ignores known build/private side files, verifies every remaining file matches exactly one inventoried class, verifies every inventory pattern has at least one matching release file, and verifies this note documents the required file classes and exclusions.

# Large Language Models Book

This repository contains the Overleaf-ready LaTeX manuscript for:

**Large Language and Generative Foundation Models: Foundations, Systems, Alignment, and Applications**

The main file is:

```text
book/book.tex
```

## Build Locally

From the repository root:

```bash
cd book
latexmk -pdf book.tex
```

The project uses the Springer `SNmono` class already included in the repository.

## Overleaf

Create or open the Overleaf project linked to this GitHub repository and set `book/book.tex` as the main document. If Overleaf imports the `book` directory as the project root, set `book.tex` as the main document.

## Manuscript Policy

The local course repository is used as a coverage map and source of implementation exercises. Manuscript prose must be original and should cite primary papers or technical reports for research claims. Third-party slides, code, datasets, papers, model weights, and media require provenance review before publication.

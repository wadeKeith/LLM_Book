# Release Notes

Version: 2026.06.14
Date: 2026-06-14

## Title

Large Language and Generative Foundation Models: Foundations, Systems, Alignment, and Applications

## Creator

Cheng Yin

## Release Artifacts

- English controlling edition: `book/book.pdf`
- Chinese readable edition: `book/book_zh.pdf`
- Source package: GitHub release source archive for this repository
- Landing page: `index.html`
- Citation metadata: `CITATION.cff`

## PDF Checksums

```text
4e0204492b461f06b9c0c6bf72e0b125ac836a9acfc522fbf730399f1b71c92a  book/book.pdf
68909d699cb9ab1a31f1c5eed796294e7d0da474e26f2f563bd0752b7d0b4fff  book/book_zh.pdf
```

## Release Summary

This release contains the current English controlling draft and Chinese readable edition of a 17-chapter book on large language models and generative foundation models. The material covers foundations, data and tokenization, Transformer mechanics, GPT-style models, LLaMA-class architectures, optimization and pretraining, distributed training, inference serving, instruction tuning, parameter-efficient adaptation, domain adaptation, retrieval and agents, preference learning, reasoning and test-time compute, multimodal systems, evaluation and safety, and research practice.

The English PDF has 238 pages. The Chinese PDF has 308 pages. The bibliography currently contains 294 cited references.

## Validation

The release candidate passed:

- `make release-candidate`
- `make publication-readiness` with expected pending owner/account-side publication items
- strict local secret-pattern scan
- static GitHub Pages desktop and mobile rendering checks
- post-clean release-inventory check
- Git whitespace check

The full release-candidate target includes source, PDF, bibliography, layout, visual, bilingual-alignment, proofing, provenance, and release-inventory gates.

## Publication Path

1. Merge the release PR into `main`.
2. Choose and add a license or explicit reuse statement.
3. Make the repository public if the release should be publicly archived through GitHub Pages and Zenodo.
4. Enable GitHub Pages from the `main` branch root.
5. Enable the repository in Zenodo's GitHub integration.
6. Create the GitHub release from tag `v2026.06.14` and attach both PDFs.
7. After Zenodo mints the DOI, update `CITATION.cff`, `index.html`, and this note with the DOI.
8. Create or update the OSF project, upload or link the release artifacts, add the Zenodo DOI, and make the OSF project public when ready.

## GitHub Release Body Draft

```markdown
## Large Language and Generative Foundation Models

This release publishes the current English controlling edition and Chinese readable edition.

Artifacts:
- `book.pdf`: English controlling edition, 238 pages
- `book_zh.pdf`: Chinese readable edition, 308 pages

Checksums:
- `book/book.pdf`: `4e0204492b461f06b9c0c6bf72e0b125ac836a9acfc522fbf730399f1b71c92a`
- `book/book_zh.pdf`: `68909d699cb9ab1a31f1c5eed796294e7d0da474e26f2f563bd0752b7d0b4fff`

Validation:
- `make release-candidate`
- strict local secret-pattern scan
- post-clean release-inventory check
- Git whitespace check

Zenodo DOI and OSF mirror links will be added after archive registration.
```

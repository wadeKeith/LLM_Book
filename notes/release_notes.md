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
- Reuse statement: `RIGHTS.md`
- Publication handoff: `notes/publication_handoff.md`

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

The remaining account-side publication steps are recorded in `notes/publication_handoff.md`.

## Archive Links

- Zenodo DOI: `https://doi.org/10.5281/zenodo.20691216`
- OSF mirror: pending

## Publication Path

1. Merge the release PR into `main`. Done: `main` currently contains the release files.
2. Enable GitHub Pages from the `main` branch root. Done: GitHub reports Pages source `main` `/` at `http://yincheng429.cn/LLM_Book/`.
3. Reuse statement. Done: `RIGHTS.md` records that no open license is granted unless a later release states otherwise.
4. Repository visibility. Done: GitHub reports `wadeKeith/LLM_Book` as public, and the repository homepage points to `http://yincheng429.cn/LLM_Book/`.
5. Zenodo GitHub integration. Done: GitHub reports active Zenodo hook id `641530522` for release events.
6. GitHub release. Done: `v2026.06.14` is published at `https://github.com/wadeKeith/LLM_Book/releases/tag/v2026.06.14` with both PDF assets attached.
7. Zenodo DOI. Done: `https://doi.org/10.5281/zenodo.20691216` is recorded in `CITATION.cff`, `index.html`, and this note.
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

GitHub Pages:
- http://yincheng429.cn/LLM_Book/

Zenodo DOI: https://doi.org/10.5281/zenodo.20691216

OSF mirror: pending
```

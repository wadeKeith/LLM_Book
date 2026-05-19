# Manuscript Acceptance Rubric

The manuscript is not considered publication-ready until every chapter passes these gates.

## Chapter Gates

- Conceptual spine: the chapter has a precise problem statement, prerequisites, and relation to prior chapters.
- Mathematical rigor: notation is defined, equations are correct, tensor shapes are explicit where implementation depends on them.
- Implementation fidelity: code-oriented descriptions match equations and do not paste third-party code as prose.
- Empirical grounding: claims about performance, scaling, or behavior cite primary sources and describe evaluation limits.
- Systems realism: memory, FLOPs, bandwidth, latency, and throughput are addressed when relevant.
- Modernity: historical recipes are separated from recommended modern practice.
- Evaluation discipline: benchmark contamination, metric limits, judge-model bias, and negative examples are discussed.
- Safety and provenance: datasets, code, figures, models, and examples have citation/licensing/privacy status.
- Pedagogy: each chapter includes key terms and exercises.

## Whole-Book Gates

- `latexmk -pdf book.tex` passes without undefined references.
- Every citation key in chapter files exists in `book/references.bib`.
- No course slide wording, copied textbook prose, copied paper abstracts, or third-party code comments appear as manuscript prose.
- Every figure is original, generated, or permission-cleared.
- The final PDF has a coherent title page, table of contents, references, glossary, and appendix.
- A GPT-5.5 professor review finds no blocking P0/P1 issues.

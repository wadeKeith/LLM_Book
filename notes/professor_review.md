# Professor Review Register

Date: 2026-05-25

## Purpose

This register makes the final acceptance-rubric item operational: a release candidate should not carry open P0/P1 reviewer findings. It complements the completed full-manuscript proofing record by giving the manuscript a stable place to record blocking review issues, chapter-level acceptance status, and reviewer evidence.

## Review Basis

- Current English controlling manuscript: `book/book.tex`
- Current Chinese readable edition: `book/book_zh.tex`
- Acceptance rubric: `notes/manuscript_acceptance_rubric.md`
- Full automated release gate: `make manuscript-audit`
- Pedagogy exercise gate: `make exercise-quality-check`
- Human rendered-page spot target: `make visual-audit`
- Full-page human proofing record: `make proofing-plan-check`
- Chinese readable edition coverage: `make bilingual-coverage-check`
- Paragraph-level bilingual print plan: `make bilingual-print-plan`
- Paragraph-level bilingual alignment manifest: `make bilingual-alignment-check`
- Provenance and release-package controls: `make provenance-check` and `make release-inventory-check`

## Current Chapter Source Fingerprints

These SHA-256 digests are computed from the comment-stripped English chapter source files. If a chapter fingerprint changes, its acceptance-matrix row should be reassessed before the register is treated as current.

| Chapter file | Comment-stripped source SHA-256 |
| --- | --- |
| book/chapters/ch01_what_makes_language_models_large.tex | `b5e7863b0aba4982ad6bf16589392ff16fc4cdf58e1ec769a786c664b3ad01f4` |
| book/chapters/ch02_tokens_corpora_training_signals.tex | `783f0fc294ee2142a8838cca109e022a02fb0eaa0bf7eaccf5f7cb7897d2c672` |
| book/chapters/ch03_transformer_mechanics.tex | `a358f524539e2d48f17ce0da1151ca06d49c8d16e50e30d17fb2e15c379aefb9` |
| book/chapters/ch04_from_transformer_to_gpt.tex | `4d6f718842250f9c8589717073e87ee27d9b50d66b9353163a8943eeea0ef67f` |
| book/chapters/ch05_llama_class_architectures.tex | `b172af6a81946faed2cf90dce2c30ed448ad306397c8f5a986bfab4f6d3af1fe` |
| book/chapters/ch06_optimization_pretraining.tex | `bf248303516467d983966354d90c6aab3bb095503a0f025668c4ca5d43052f05` |
| book/chapters/ch07_distributed_training_systems.tex | `889565f0d843a2e8bed52efa58c4ac903a4b83190dc97d2264041cf47a01c58d` |
| book/chapters/ch08_inference_serving.tex | `36641e06909d80c930dd0d751d26a08aba4c97b9334e7cf099fa681c52eacdc0` |
| book/chapters/ch09_supervised_instruction_tuning.tex | `58ea3ca7e1997cdc5f86ec14afaba546a7be36e650f0a59c7fa9e7e822d4b106` |
| book/chapters/ch10_parameter_efficient_adaptation.tex | `252529aa5915276a08880ea01d0b31bfe49ccea8f9ec479a32640c8b91f32391` |
| book/chapters/ch11_domain_language_adaptation.tex | `e78741fd2f29550887a04df928e6e1fbf03639de8f22c800ce6c4c68e1eb90eb` |
| book/chapters/ch12_retrieval_tools_agents.tex | `45b318113dac79f30a3d940254f958ac64b11b522d336c14df73643da31df066` |
| book/chapters/ch13_preference_learning_alignment.tex | `2daa523f714b318eb30eacc95e533ee208965e1de27499a2b18083fcef878628` |
| book/chapters/ch14_reasoning_test_time_compute.tex | `7bd7febae7023ee2695a16dbfaf1a71d90ba2a23a6744ab03e2b9e164c458992` |
| book/chapters/ch15_multimodal_llms.tex | `cdb4e21ac51e2845964cad1952673e74958c8c66d4a3d3b42d5be881dbc77679` |
| book/chapters/ch16_evaluation_safety_governance.tex | `92ffbd45ed798385c0ac8e7391d83fa645a9fe5154721a0072874216bab77c6f` |
| book/chapters/ch17_research_frontiers_practice.tex | `ff1f4c8efb814623462333332ec6380daec2a576a6483c544e9fb055b01ca174` |

Open P0/P1 blockers: 0

## Severity Policy

| Severity | Meaning | Release disposition |
| --- | --- | --- |
| P0 | Blocks build, publication package integrity, provenance, or legal/permission posture | Must be closed before release |
| P1 | Blocks core technical correctness, chapter coherence, citation integrity, or serious rendered-PDF usability | Must be closed before release |
| P2 | Important improvement that can be scheduled if the release remains otherwise coherent | Track but does not block a candidate |
| P3 | Editorial polish, wording, or optional expansion | Track opportunistically |

## Blocking Issue Register

| ID | Severity | Status | Scope | Finding | Disposition |
| --- | --- | --- | --- | --- | --- |
| REV-001 | P2 | Closed | Chinese readable edition | The Chinese edition is structured, readable, chapter/topic aligned, covered by `notes/bilingual_coverage.md`, and now backed by a paragraph-for-paragraph bilingual print proofing record. `notes/bilingual_print_plan.md` records 1163 English source units, 1163 aligned units, 1163 proofed units, and 0 open source-alignment units. Chapters 1 through 17 and all tracked front/back matter units are recorded in `notes/bilingual_alignment_manifest.md` and tied to reviewed BP-01--BP-22 proofing batches. | Closed under the current release framing after `make bilingual-alignment-check`, `make bilingual-print-artifact-check`, and `make bilingual-print-proofing-check` validated the current aligned and proofed source-unit set. |
| REV-002 | P2 | Closed | Full-manuscript proofing | `notes/proofing_plan.md` covers every rendered English and Chinese page, but the current figure-expansion pass changed both rendered PDF fingerprints. The plan now records 20 proofing batches, 238/238 English pages, 308/308 Chinese pages, 20/20 reviewed batches, and Complete proofread status under the current fingerprints. | Closed after all 20 proofing batches were refreshed against the current rendered-text fingerprints and the proofing-plan gate passed. |
| REV-003 | P2 | Closed | Back-of-book index | A focused reader-index pass added high-value lookup aliases for agents/tools, fine-tuning, human-feedback wording, long context, embeddings/vector databases, model judges, red teams, unlearning, watermarking, content credentials, and provenance subentries; source and rendered index gates now require these entries. | Closed under the current technical draft; reopen only if a publisher requires a dedicated professional indexer or a later content batch changes the index vocabulary. |

## Chapter Acceptance Matrix

| Chapter file | Chapter title | Conceptual spine | Rigor and implementation fidelity | Evidence and evaluation discipline | Safety and provenance | Pedagogy | Blocking status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| book/chapters/ch01_what_makes_language_models_large.tex | What Makes a Language Model Large | Pass | Pass | Pass | Pass | Pass | Pass |
| book/chapters/ch02_tokens_corpora_training_signals.tex | Tokens, Corpora, and Training Signals | Pass | Pass | Pass | Pass | Pass | Pass |
| book/chapters/ch03_transformer_mechanics.tex | Transformer Mechanics | Pass | Pass | Pass | Pass | Pass | Pass |
| book/chapters/ch04_from_transformer_to_gpt.tex | From Transformer to GPT | Pass | Pass | Pass | Pass | Pass | Pass |
| book/chapters/ch05_llama_class_architectures.tex | LLaMA-Class Architectures | Pass | Pass | Pass | Pass | Pass | Pass |
| book/chapters/ch06_optimization_pretraining.tex | Optimization and Pretraining | Pass | Pass | Pass | Pass | Pass | Pass |
| book/chapters/ch07_distributed_training_systems.tex | Distributed Training Systems | Pass | Pass | Pass | Pass | Pass | Pass |
| book/chapters/ch08_inference_serving.tex | Inference and Serving | Pass | Pass | Pass | Pass | Pass | Pass |
| book/chapters/ch09_supervised_instruction_tuning.tex | Supervised Instruction Tuning | Pass | Pass | Pass | Pass | Pass | Pass |
| book/chapters/ch10_parameter_efficient_adaptation.tex | Parameter-Efficient Adaptation | Pass | Pass | Pass | Pass | Pass | Pass |
| book/chapters/ch11_domain_language_adaptation.tex | Domain and Language Adaptation | Pass | Pass | Pass | Pass | Pass | Pass |
| book/chapters/ch12_retrieval_tools_agents.tex | Retrieval, Tools, and Agents | Pass | Pass | Pass | Pass | Pass | Pass |
| book/chapters/ch13_preference_learning_alignment.tex | Preference Learning and Alignment | Pass | Pass | Pass | Pass | Pass | Pass |
| book/chapters/ch14_reasoning_test_time_compute.tex | Reasoning and Test-Time Compute | Pass | Pass | Pass | Pass | Pass | Pass |
| book/chapters/ch15_multimodal_llms.tex | Multimodal and Generative Foundation Models | Pass | Pass | Pass | Pass | Pass | Pass |
| book/chapters/ch16_evaluation_safety_governance.tex | Evaluation, Safety, and Governance | Pass | Pass | Pass | Pass | Pass | Pass |
| book/chapters/ch17_research_frontiers_practice.tex | Research Frontiers and Practice Roadmap | Pass | Pass | Pass | Pass | Pass | Pass |

## Current Disposition

The latest `make reviewer-check` run found 17 passing chapter review rows, 17 chapter source fingerprints, 0 Open/Reopened P0/P1 blockers, and 0 closed P0/P1 blockers. No open P0/P1 issues are recorded for the current candidate, and the previously open P2 review items are now closed under the current rendered fingerprints and bilingual proofing record.

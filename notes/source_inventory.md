# Source Inventory

This note records the read-only source review used to plan the book. It is intentionally high-level and does not copy course prose.

## Local Source Repository

Root: `/Users/yin/Downloads/代码与项目/手撕llm`

The current counts below exclude `LLM_Book`, hidden directories, and Python cache directories so the publication repository and its generated side files do not inflate the source-material inventory.

Observed source types:

- 1,565 regular source-root files.
- 207 MP4 files. These were treated as coverage signals from filenames only; they were not watched or transcribed.
- 64 PDF files, including neural-network foundations, Transformer, GPT, LLaMA, LoRA, QLoRA, PPO, DPO, RLHF, RAG, multimodal, and reasoning papers or slides.
- 20 PPTX slide decks. Slide text was sampled only to infer topic coverage.
- 476 Python files across Transformer, nanoGPT, LLaMA-style, LoRA/QLoRA, RAG, RLHF, MCTS, GRPO/R1-style, and serving/application examples.
- 51 notebooks, 80 Markdown files, and 96 text files, mostly implementation walkthroughs, datasets, and project documentation.
- 703 provenance-readable text/code files currently fall under the `.md`, `.txt`, `.py`, `.tex`, `.rst`, and `.ipynb` suffix and size policy used by `make provenance-check`.
- 0 readable files exceeded the 5,000,000 byte provenance-scan cap. The current automated exact-overlap scan therefore covers every readable text/code source under the configured suffix policy; any future oversize readable files must be listed here by path and byte size for human provenance review.
- Multiple compressed archives and encrypted/media package formats. These should not be treated as inspected content until explicitly unpacked and license-checked.

## Coverage Signals

The source material covers:

- Deep learning and PyTorch foundations.
- NLP and Transformer background.
- GPT and nanoGPT implementation.
- LLaMA-style architecture details.
- Alpaca, Self-Instruct, LoRA, QLoRA, and Chinese LLaMA adaptation.
- ChatLLaMA, DPO, PPO, RLHF, and preference learning.
- GPU basics, distributed training, inference acceleration, quantization, and load testing.
- RAG, LangChain-style applications, vector databases, NL2SQL, and role-play agents.
- Evaluation with OpenAI Evals, multimodal/VLM material, and O1/R1-style reasoning assets.

## Provenance Decision

The manuscript uses this inventory to decide coverage and exercises. It should not reuse course slide wording, textbook passages, code comments, or figures without explicit permission and citation.

`make source-inventory-check` recomputes these local source-root counts and fails if this note drifts from the current workspace inventory.

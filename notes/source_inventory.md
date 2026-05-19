# Source Inventory

This note records the read-only source review used to plan the book. It is intentionally high-level and does not copy course prose.

## Local Source Repository

Root: `/Users/yin/Downloads/代码与项目/手撕llm`

Observed source types:

- 1,744 total files.
- 207 MP4 files. These were treated as coverage signals from filenames only; they were not watched or transcribed.
- 56 PDF files, including neural-network foundations, Transformer, GPT, LLaMA, LoRA, QLoRA, PPO, DPO, RLHF, RAG, multimodal, and reasoning papers or slides.
- 27 PPTX slide decks. Slide text was sampled only to infer topic coverage.
- 299 Python files across Transformer, nanoGPT, LLaMA-style, LoRA/QLoRA, RAG, RLHF, MCTS, GRPO/R1-style, and serving/application examples.
- 33 notebooks and 41 Markdown files, mostly implementation walkthroughs and project documentation.
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

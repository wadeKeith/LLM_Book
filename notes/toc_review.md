# Table of Contents Review

## Main-Agent Initial Direction

The initial structure had 18 chapters, separating deployment, governance, and research frontiers into standalone chapters. That structure preserved many course topics but risked becoming a list of assets rather than a textbook argument.

## GPT-5.5 Professor Review

The reviewer argued for a tighter 16-chapter structure with five corrections:

- Put data, tokenization, contamination, and licensing before architecture.
- Teach inference and serving before post-training, because latency and KV-cache constraints shape practical adaptation choices.
- Merge production governance into the final evaluation and safety chapter.
- Add domain and language adaptation as a first-class chapter instead of burying it under LoRA.
- Treat reasoning and test-time compute as a modern continuation of alignment and inference, not as a detached final topic.

## Converged Structure

After the frontier review, the manuscript uses 17 chapters. The additional final chapter is not a topic dump; it is an audit and practice roadmap that keeps the rest of the book tied to current research without fragmenting the core pedagogy.

1. What Makes a Language Model Large
2. Tokens, Corpora, and Training Signals
3. Transformer Mechanics
4. From Transformer to GPT
5. LLaMA-Class Architectures
6. Optimization and Pretraining
7. Distributed Training Systems
8. Inference and Serving
9. Supervised Instruction Tuning
10. Parameter-Efficient Adaptation
11. Domain and Language Adaptation
12. Retrieval, Tools, and Agents
13. Preference Learning and Alignment
14. Reasoning and Test-Time Compute
15. Multimodal and Generative Foundation Models
16. Evaluation, Safety, and Governance
17. Research Frontiers and Practice Roadmap

## Latest Structure Decision

The current structure remains appropriate for a high-positioned book because it treats modern foundation-model work as one lifecycle: data, objectives, architecture, systems, adaptation, applications, evaluation, and governance. The main correction was to broaden Chapter 15 so the book is not limited to text-only LLMs. Unified understanding-generation models, diffusion/rectified-flow generation, AR-diffusion hybrids, and any-to-any omni interfaces are now covered inside the same chapter rather than split into isolated survey-style chapters.

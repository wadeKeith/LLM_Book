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

The manuscript now uses 16 chapters:

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
15. Multimodal LLMs
16. Evaluation, Safety, and Governance

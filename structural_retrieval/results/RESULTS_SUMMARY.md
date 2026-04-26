# RAPM Enhanced Prompt — Results Summary

**Method:** Task-blind cross-category RAG with ProstT5 hybrid retrieval (FAISS, α=0.7, Top-K=10)  
**Retrieval:** Cross-task only — no within-task FAISS index, no task-label conditioning  
**Few-shot:** 3 in-context input-output pairs (format reference only, within-task)  
**LLM:** Claude Sonnet 4.6 (Anthropic)  
**Tokenizer for BLEU:** `bert-base-uncased` (note: Gemini baseline used Llama-3.2-1B tokenizer)  
**Date:** April 25, 2026

---

## Main Results — Claude Sonnet 4.6, Task-Blind (Full Dataset)

| Task | N | BLEU-2 | BLEU-4 | Meta-BLEU-2 | Meta-BLEU-4 | METEOR | ROUGE-L | Exact Match |
|---|---|---|---|---|---|---|---|---|
| protein_function_OOD | 5,487 | 20.98 | 15.11 | **56.98** | **47.27** | 55.72 | 27.61 | 0.000 |
| general_function_OOD | — | 16.74 | 11.22 | **29.24** | **21.04** | 38.28 | 24.74 | 0.000 |
| catalytic_activity_OOD | — | 24.82 | 18.91 | **43.63** | **36.90** | 46.75 | 39.48 | 0.005 |
| domain_motif_OOD | 2,732 | 7.57 | 5.07 | **43.57** | **34.57** | 40.67 | 17.43 | 0.000 |

---

## Top-1 Retrieval-Only Baseline (same run)

| Task | BLEU-2 | BLEU-4 | Meta-BLEU-2 | Meta-BLEU-4 | METEOR | ROUGE-L | RAG gain (Meta-BLEU-2) |
|---|---|---|---|---|---|---|---|
| protein_function_OOD | 15.71 | 12.05 | 10.06 | 8.53 | 27.63 | 15.62 | **+46.9 pts** |
| general_function_OOD | 9.42 | 7.67 | 1.16 | 1.02 | 15.25 | 13.47 | **+28.1 pts** |
| catalytic_activity_OOD | 11.83 | 7.53 | 2.32 | 1.85 | 17.71 | 11.21 | **+41.3 pts** |
| domain_motif_OOD | 3.15 | 1.78 | 2.00 | 1.57 | 13.05 | 6.35 | **+41.6 pts** |

---

## Prediction-vs-Retrieved Overlap Score

| Task | Overlap |
|---|---|
| protein_function_OOD | 60.18% |
| general_function_OOD | 54.91% |
| catalytic_activity_OOD | 54.25% |
| domain_motif_OOD | 54.15% |

> Overlap = fraction of prediction words found in retrieved context.
> ~54–60% indicates the model uses retrieved evidence heavily but does synthesize beyond copying.

---

## Gemini 2.5 Flash Baseline (task-aware, ~256 samples, avg of 3 runs)

> ⚠️ These runs used explicit task-label conditioning and a hardcoded 256-sample subset.
> Direct comparison is not apples-to-apples but provides a rough upper-bound reference.

| Task | BLEU-2 | BLEU-4 | Meta-BLEU-2 | Meta-BLEU-4 | METEOR | ROUGE-L |
|---|---|---|---|---|---|---|
| protein_function_OOD | 23.95 | 16.76 | 56.66 | 47.15 | 55.15 | 30.05 |
| general_function_OOD | 18.61 | 11.90 | 9.21 | 6.64 | 29.88 | 21.05 |
| domain_motif_OOD | 14.45 | 9.85 | 34.43 | 27.28 | 40.41 | 23.99 |
| catalytic_activity_OOD | 22.47 | 16.47 | 43.04 | 35.80 | 45.80 | 33.45 |

---

## Key Takeaways

1. **Task-blind Claude matches task-aware Gemini on protein_function_OOD** — Meta-BLEU-2: 56.98 vs 56.66 — supporting the claim that task conditioning is unnecessary.

2. **general_function_OOD shows a large drop vs Gemini** — Meta-BLEU-2: 29.24 (Claude) vs 9.21 (Gemini). Counter-intuitively, Claude task-blind *outperforms* task-aware Gemini here, likely because general_function is the broadest/most ambiguous task and Gemini's task guidance was unhelpful.

3. **catalytic_activity_OOD is essentially tied** — Meta-BLEU-2: 43.63 (Claude) vs 43.04 (Gemini), with Claude having higher ROUGE-L (39.5 vs 33.5).

4. **domain_motif_OOD: Claude task-blind > Gemini task-aware** — Meta-BLEU-2: 43.57 vs 34.43. Strong improvement.

5. **Large RAG-vs-retrieval gap across all tasks** — Meta-BLEU-2 jumps +28 to +47 pts over Top-1 retrieval alone, confirming the LLM adds substantial generative value beyond copying annotations.

6. **Consistent overlap (~54–60%)** — The model uses retrieved context as evidence but paraphrases/synthesizes rather than copying verbatim.

7. **domain_motif_OOD has the lowest Top-1 baseline (2.0 Meta-BLEU-2)** — suggesting domain motifs are structurally diverse and cross-task retrieval starts from near zero, yet RAG still achieves 43.6 — the largest relative gain.

---

## File Locations (cluster)

| File | Path |
|---|---|
| Metrics log | `/orcd/.../SAPER/structural_retrieval/results/enhanced_prompt_alpha0.70_rapm_results.txt` |
| protein_function results | `...results/ENHANCED_PROMPT_alpha0.70_protein_function_OOD_10_results.json` |
| general_function results | `...results/ENHANCED_PROMPT_alpha0.70_general_function_OOD_10_results.json` |
| catalytic_activity results | `...results/ENHANCED_PROMPT_alpha0.70_catalytic_activity_OOD_10_results.json` |
| domain_motif results | `...results/ENHANCED_PROMPT_alpha0.70_domain_motif_OOD_10_results.json` |

---

## Configuration

```
Model:     claude-sonnet-4-6
Retrieval: ProstT5 hybrid (sequence embedding + ESM-2 feature similarity)
Alpha:     0.7 (weight toward ProstT5 vs feature similarity)
Top-K:     10 retrieved examples
Strategy:  Cross-task FAISS index (all tasks pooled, query task excluded)
Few-shot:  3 input-output pairs sampled from current task's training split (format only)
Dataset:   Full OOD test split per task
```

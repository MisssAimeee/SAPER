# LLM-as-Judge Evaluation — Claude Sonnet 4.6 Task-Blind RAPM

**Judge model:** `claude-sonnet-4-6` (with `thinking_budget=4000`)
**Predictions scored:** Claude Sonnet 4.6 task-blind RAPM outputs
(see `RESULTS_SUMMARY.md` for the underlying retrieval/generation config)
**Sample size:** 500 per task × 4 OOD tasks = 2,000 attempted
**Date:** April 25, 2026
**Total cost:** $48.56 (judge calls only)

---

## Headline Numbers (overall, macro-averaged across the 4 OOD tasks)

| Dimension     | Macro mean (0–10) |
|---------------|-------------------|
| Specificity   | **9.36**          |
| Plausibility  | 5.75              |
| Recall        | 5.09              |
| Precision     | 3.73              |
| **Final score** | **6.15**        |

> Each dimension is a 0–10 rubric score the judge assigns per (prediction, ground-truth)
> pair. `final_score` is the judge's holistic rating, not a deterministic combination
> of the four sub-dimensions.

---

## How to read each dimension

| Dimension     | What it measures                                                              | What 9.36 / 3.73 means here                                                                  |
|---------------|-------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|
| Specificity   | How concrete/technical the prediction is (avoiding vague filler).             | Very high — Claude consistently produces precise biological terminology.                     |
| Plausibility  | Whether the prediction is biologically reasonable in isolation.               | Solid mid-range — outputs are coherent biology, but not always *the right* biology.          |
| Recall        | Fraction of the ground-truth functional content the prediction covers.        | Mid — captures roughly half of the reference description's content.                          |
| Precision     | Of what the prediction says, how much is correct vs. hallucinated/extra.      | Low — the model says a lot, and a meaningful fraction isn't supported by the reference.      |
| Final score   | Judge's overall quality rating.                                               | 6.15 / 10 — useful, well-formed predictions with a real correctness gap.                     |

The **specificity ≫ precision** gap is the most informative signal in this run:
the model speaks fluent, specific protein-biology — but it pads outputs with
plausible-sounding details that aren't grounded in the reference. That pattern
is consistent with the **60% prediction-vs-retrieved overlap** seen in
`RESULTS_SUMMARY.md`: high synthesis, but the synthesized parts cost precision.

---

## Per-task run statistics

Per-task *dimension* means are written to
`/orcd/.../judge_input/SAPER-claude-taskblind/judge_scores/` on the cluster and
are not transcribed here. The visible per-task stats from the run are scoring
counts and cost:

| Task                    | Scored | Failed | Cost (USD) |
|-------------------------|-------:|-------:|-----------:|
| catalytic_activity_OOD  |    500 |      0 |     $10.92 |
| domain_motif_OOD        |    498 |      2 |     $11.58 |
| general_function_OOD    |    497 |      3 |     $13.60 |
| protein_function_OOD    |    500 |      0 |     $12.46 |
| **Total**               | **1,995** | **5** | **$48.56** |

Failure rate: 5 / 2,000 = **0.25 %** (parse errors / judge timeouts).

---

## Pipeline used

1. **Generate predictions** — `structural_retrieval/src/enhanced_prompt.py`,
   task-blind cross-task RAPM, Claude Sonnet 4.6, full OOD test split
   (4 tasks). See `RESULTS_SUMMARY.md`.

2. **Convert to benchmark schema** — `saper_to_benchmarks.py` rewrites the
   per-task JSONL into the
   `{prediction, metadata, label, test_array_index, error}` shape the judge
   expects:

   ```bash
   python saper_to_benchmarks.py \
     --in_glob "structural_retrieval/results/ENHANCED_PROMPT_alpha0.70_*_results.json" \
     --out_dir /orcd/data/jhm/001/urops/aimee_yu/saper_run/judge_input/SAPER-claude-taskblind
   ```

3. **Run the judge** — Anthropic-flavored async judge with extended thinking
   (note: this is the second attempt; see "Notes" below):

   ```bash
   python /orcd/data/jhm/001/urops/aimee_yu/saper_run/llm_judge_score_anthropic.py \
     --predictions_dir /orcd/data/jhm/001/urops/aimee_yu/saper_run/judge_input/SAPER-claude-taskblind \
     --dataset_dir     /orcd/data/jhm/001/urops/aimee_yu/saper_run/SAPER/dataset \
     --output_dir      /orcd/data/jhm/001/urops/aimee_yu/saper_run/judge_input/SAPER-claude-taskblind/judge_scores \
     --judge_model     claude-sonnet-4-6 \
     --num_samples     500 \
     --max_concurrent  10 \
     --thinking_budget 4000
   ```

---

## Notes & caveats

1. **Judge = generator.** Both the predictions and the judge are
   `claude-sonnet-4-6`. This is a known source of self-preference bias —
   absolute scores should be read as *Claude's opinion of Claude*. For
   cross-method comparisons we still need a neutral judge (e.g. GPT-5.5) or
   per-task human spot-checks.

2. **First judge attempt failed.** Running the synchronous `llm_judge_score.py`
   produced a 30 % failure rate on `catalytic_activity_OOD` (150/500) before
   we ctrl-C'd at `domain_motif_OOD` 58 %. Switching to
   `llm_judge_score_anthropic.py` with `thinking_budget=4000` and
   `max_concurrent=10` cut failures to 0–3 per task. The first run's partial
   `judge_scores/` directory was deleted before the rerun.

3. **Sample = 500/task, not full split.** The judge run is on a fixed 500-sample
   subset per task (the full split sizes are in `RESULTS_SUMMARY.md`,
   e.g. 5,487 for `protein_function_OOD`). Final scores are macro-averaged
   across tasks, not weighted by split size.

4. **Per-task dimension breakdowns live on the cluster.** Pull them with:

   ```bash
   scp -r aimeeyu@orcd-login.mit.edu:/orcd/data/jhm/001/urops/aimee_yu/saper_run/judge_input/SAPER-claude-taskblind/judge_scores \
     ~/Desktop/SP26/saper/SAPER/structural_retrieval/results/judge_scores
   ```

   Once they're local, this README should be updated with a per-task
   (recall / precision / specificity / plausibility / final) table to match
   the structure of `RESULTS_SUMMARY.md`.

---

## Open follow-ups

- [ ] Pull per-task judge scores and add a per-task table here.
- [ ] Re-run with a non-Claude judge (GPT-5.5 or Gemini 2.5 Pro) to remove
      the self-preference confound on absolute numbers.
- [ ] Run the same judge over the **Top-1 retrieval-only** baseline outputs
      so the LLM-judge gain (RAPM vs. retrieval) is comparable to the
      Meta-BLEU gain reported in `RESULTS_SUMMARY.md`.
- [ ] Investigate why **precision (3.73)** is so much lower than
      **specificity (9.36)** — sample 20 low-precision predictions and check
      whether the model is hallucinating extra clauses or whether the judge
      is penalizing correct-but-not-in-reference content.

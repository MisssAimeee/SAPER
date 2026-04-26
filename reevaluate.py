"""Re-evaluate saved RAPM predictions without re-running inference.

Reads the per-task JSONL files written by
``structural_retrieval/src/enhanced_prompt.py`` (one record per line, keys:
``instruction``, ``sequence``, ``answer``, ``top1_retrieved``,
``retrieval_overlap``, ``label``, ``meta_label``) and re-computes
BLEU-2/4, Meta-BLEU-2/4, METEOR, ROUGE, Exact Match, and the
prediction-vs-retrieved overlap score for both the LLM RAPM output and the
Top-1 retrieval-only baseline.

Use this after changing the tokenizer in ``enhanced_prompt.evaluation``
(e.g. bert-base-uncased -> meta-llama/Llama-3.2-1B-Instruct) to re-score
the existing inference outputs without paying for another LLM run.

Usage (from SAPER repo root):

    python reevaluate.py \\
        --results_dir structural_retrieval/results \\
        --pattern    "ENHANCED_PROMPT_alpha0.70_*_results.json" \\
        --out_file   structural_retrieval/results/enhanced_prompt_alpha0.70_LLAMA_rapm_results.txt
"""

import argparse
import glob
import json
import os
import sys


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(THIS_DIR, "structural_retrieval", "src"))

from enhanced_prompt import evaluation  # noqa: E402  (uses current tokenizer)


def load_jsonl(path):
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results_dir", required=True,
                    help="Directory containing ENHANCED_PROMPT_*.json result files")
    ap.add_argument("--pattern", default="ENHANCED_PROMPT_alpha0.70_*_results.json",
                    help="Glob pattern relative to --results_dir")
    ap.add_argument("--out_file", required=True,
                    help="Output metrics text file (appended; not overwritten)")
    args = ap.parse_args()

    paths = sorted(glob.glob(os.path.join(args.results_dir, args.pattern)))
    if not paths:
        raise SystemExit(f"No files matched {args.pattern} in {args.results_dir}")

    out_f = open(args.out_file, "a+")
    print(f"=== Re-evaluation run ===", file=out_f)
    print(f"Re-scoring {len(paths)} task file(s) using tokenizer currently "
          f"configured in enhanced_prompt.evaluation", file=out_f)

    for p in paths:
        records = load_jsonl(p)
        task = os.path.basename(p)
        print("=" * 80)
        print(f"Re-evaluating: {task}  (n={len(records)})")

        print("\n" + "=" * 80, file=out_f)
        print(f"Task file: {task}  (n={len(records)})", file=out_f)

        answers     = [r.get("answer", "") or "" for r in records]
        top1        = [r.get("top1_retrieved", "") or "" for r in records]
        labels      = [r.get("label", "") or "" for r in records]
        meta_labels = [r.get("meta_label", "") or "" for r in records]

        print("\n--- LLM RAPM (cross-task retrieval) ---", file=out_f)
        evaluation(answers, labels, meta_labels, out_f)

        print("\n--- Top-1 Retrieval-Only Baseline ---", file=out_f)
        evaluation(top1, labels, meta_labels, out_f)

        # retrieval_overlap is per-record word-level overlap; tokenizer-independent.
        # Reuse the saved per-record value for fidelity to the original run.
        per_overlap = [float(r.get("retrieval_overlap", 0.0) or 0.0) for r in records]
        if per_overlap:
            mean_overlap = (sum(per_overlap) / len(per_overlap)) * 100
            print(f"\nPrediction-vs-Retrieved Overlap Score: {mean_overlap:.2f}%", file=out_f)
            print(f"Prediction-vs-Retrieved Overlap Score: {mean_overlap:.2f}%")
            print("(reused from saved JSONL; word-level, tokenizer-independent)", file=out_f)

    out_f.close()
    print(f"\nMetrics appended to: {args.out_file}")


if __name__ == "__main__":
    main()

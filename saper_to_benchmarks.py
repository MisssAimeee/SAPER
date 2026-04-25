"""Convert SAPER's per-task results JSONL to the schema expected by
saper-clip-benchmarks (rapm_rescore.py + fix_entity_bleu.py).

SAPER writes JSONL (one record per line) with keys:
    instruction, sequence, answer, label, meta_label

The benchmark scripts expect a JSON LIST with at minimum:
    {"prediction": "...", "metadata": "..."}

Usage:
    python saper_to_benchmarks.py \
        --in_glob  "structural_retrieval/results/ENHANCED_PROMPT_alpha0.70_*_results.json" \
        --out_dir  benchmarks_predictions/SAPER-claude
"""

import argparse
import glob
import json
import os
import re


TASKS = [
    "catalytic_activity_OOD",
    "domain_motif_OOD",
    "general_function_OOD",
    "protein_function_OOD",
]


def detect_task(filename: str) -> str:
    base = os.path.basename(filename)
    for t in TASKS:
        if t in base:
            return t
    raise ValueError(f"Could not detect task name in {filename}")


def load_jsonl(path):
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def convert_one(in_path: str, out_dir: str) -> str:
    task = detect_task(in_path)
    records = load_jsonl(in_path)

    converted = []
    for i, r in enumerate(records):
        converted.append({
            "test_array_index": i,
            "prediction": r.get("answer", "") or "",
            "metadata": r.get("meta_label", "") or "",
            "label": r.get("label", "") or "",
            "error": "" if r.get("answer") else "empty answer",
        })

    out_path = os.path.join(out_dir, f"{task}_predictions.json")
    with open(out_path, "w") as f:
        json.dump(converted, f, indent=2)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--in_glob",
        required=True,
        help="Glob matching SAPER per-task result files "
             "(e.g. structural_retrieval/results/ENHANCED_PROMPT_*.json)",
    )
    ap.add_argument(
        "--out_dir",
        required=True,
        help="Where to write {task}_predictions.json files",
    )
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    matches = sorted(glob.glob(args.in_glob))
    if not matches:
        raise SystemExit(f"No files matched: {args.in_glob}")

    for m in matches:
        out = convert_one(m, args.out_dir)
        print(f"  {m}\n     -> {out}")


if __name__ == "__main__":
    main()

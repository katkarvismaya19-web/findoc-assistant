"""Retrieval evaluation.

Measures how often the correct passage is actually retrieved, which is the
part of a RAG system that most often fails silently. A fluent answer built on
the wrong passage looks fine and is wrong.

Metrics:
  Recall@k - fraction of questions where a correct chunk appears in the top k
  MRR      - mean of 1/rank of the first correct chunk (0 if none in top k)

A retrieved chunk counts as correct when it comes from the expected source
file and its page is within PAGE_TOLERANCE of the expected page, since chunk
boundaries do not align with page boundaries.

Run:
    python -m eval.evaluate
    python -m eval.evaluate --collections findoc_1000 findoc_500 --k 3
"""
import argparse
import json
from pathlib import Path

from app import retrieval

PAGE_TOLERANCE = 1
QUESTIONS = Path(__file__).parent / "questions.json"


def is_hit(chunk, expected):
    if chunk["source"] != expected["expected_source"]:
        return False
    return abs(int(chunk["page"]) - int(expected["expected_page"])) <= PAGE_TOLERANCE


def score_strategy(questions, strategy, k, collection):
    hits = 0
    reciprocal_ranks = []
    misses = []

    for item in questions:
        chunks = retrieval.search(
            item["question"], strategy=strategy, k=k, collection_name=collection
        )
        rank = next(
            (i for i, c in enumerate(chunks, start=1) if is_hit(c, item)), None
        )
        if rank:
            hits += 1
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)
            misses.append(item["question"])

    n = len(questions)
    return {
        "recall": hits / n,
        "mrr": sum(reciprocal_ranks) / n,
        "misses": misses,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--collections", nargs="+", default=["findoc_1000"])
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--show-misses", action="store_true")
    args = ap.parse_args()

    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    print(f"{len(questions)} questions, k={args.k}, page tolerance={PAGE_TOLERANCE}\n")

    results = {}
    for collection in args.collections:
        print(f"=== collection: {collection} ===")
        print(f"{'strategy':<10} {'Recall@' + str(args.k):>10} {'MRR':>8}")
        print("-" * 30)
        for strategy in ("dense", "bm25", "hybrid"):
            res = score_strategy(questions, strategy, args.k, collection)
            results[(collection, strategy)] = res
            print(f"{strategy:<10} {res['recall']:>10.3f} {res['mrr']:>8.3f}")
        print()

    # The headline number for the resume bullet.
    for collection in args.collections:
        dense = results[(collection, "dense")]["recall"]
        hybrid = results[(collection, "hybrid")]["recall"]
        if dense > 0:
            lift = (hybrid - dense) / dense * 100
            print(
                f"[{collection}] hybrid vs dense-only on Recall@{args.k}: "
                f"{lift:+.1f}%"
            )

    if args.show_misses:
        print("\nQuestions hybrid still misses (look for a pattern):")
        for collection in args.collections:
            for q in results[(collection, "hybrid")]["misses"]:
                print(f"  - [{collection}] {q}")


if __name__ == "__main__":
    main()


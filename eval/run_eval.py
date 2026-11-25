"""
Retrieval evaluation.

For each question in questions.json we retrieve the top-5 chunks and check
whether the expected source document appears among the top-3 (hit-rate@3) and
top-5 (hit-rate@5). This measures the retriever alone — no LLM is involved, so
the numbers are deterministic and cheap to reproduce.

Hit-rate@k = (questions whose correct document is in the top-k results) / (total questions)

Run:  python -m eval.run_eval
Out:  eval/results.json
"""
from __future__ import annotations

import json
import os

from app.config import get_settings
from app.embeddings import embed_one
from app.vectorstore import VectorStore

HERE = os.path.dirname(__file__)
QUESTIONS_PATH = os.path.join(HERE, "questions.json")
RESULTS_PATH = os.path.join(HERE, "results.json")


def _sources_for(store: VectorStore, question: str, k: int) -> list[str]:
    """Return the ordered, de-duplicated source files for the top-k chunks."""
    hits = store.search(embed_one(question), k)
    seen: list[str] = []
    for meta, _ in hits:
        if meta["file"] not in seen:
            seen.append(meta["file"])
    return seen


def run() -> dict:
    with open(QUESTIONS_PATH, encoding="utf-8") as fh:
        questions = json.load(fh)

    store = VectorStore.load(get_settings().index_dir)

    per_question = []
    hits3 = hits5 = 0
    for q in questions:
        top5 = _sources_for(store, q["question"], 5)
        hit3 = q["expected_source"] in top5[:3]
        hit5 = q["expected_source"] in top5[:5]
        hits3 += hit3
        hits5 += hit5
        per_question.append({
            "id": q["id"],
            "question": q["question"],
            "expected_source": q["expected_source"],
            "retrieved_top5": top5,
            "hit@3": hit3,
            "hit@5": hit5,
        })

    n = len(questions)
    results = {
        "total_questions": n,
        "hit_rate_at_3": round(hits3 / n, 4),
        "hit_rate_at_5": round(hits5 / n, 4),
        "per_question": per_question,
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)

    print(f"Questions: {n}")
    print(f"Hit-rate@3: {results['hit_rate_at_3']:.1%}")
    print(f"Hit-rate@5: {results['hit_rate_at_5']:.1%}")
    print(f"Wrote {RESULTS_PATH}")
    return results


if __name__ == "__main__":
    run()

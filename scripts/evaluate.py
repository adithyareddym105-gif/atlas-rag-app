from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import json
from datetime import datetime

from rag.hybrid_retrieval import hybrid_search
from rag.indexing import index_directory

EVAL_DIR = ROOT / "eval"
RESULTS_DIR = ROOT / "results"

CONFIGS = [
    {"name": "baseline-800-80", "chunk_size": 800, "overlap": 80},
    {"name": "smaller-400-40", "chunk_size": 400, "overlap": 40},
]

K_VALUES = [1, 3, 5, 10]


def load_questions(corpus):
    filename = EVAL_DIR / f"{corpus}.questions.jsonl"
    with filename.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def evaluate_question(question, corpus, top_k):
    expected = question.get("evidence", [])
    answerable = question.get("answerable", True)

    retrieved = hybrid_search(
        question["question"],
        top_k=top_k,
        corpus_name=corpus,
    )

    recall_at_k = {}

    for k in K_VALUES:
        if not answerable or not expected:
            recall_at_k[k] = None
            continue

        found = 0
        for evidence in expected:
            matched = any(
                evidence["source"] == chunk["source"]
                and evidence["quote"].lower() in chunk["text"].lower()
                for chunk in retrieved[:k]
            )
            if matched:
                found += 1

        recall_at_k[k] = round(found / len(expected), 4)

    return {
        "id": question["id"],
        "type": question.get("type", "other"),
        "question": question["question"],
        "answerable": answerable,
        "expected_answer": question.get("expected_answer", ""),
        "evidence": expected,
        "retrieved": [
            {
                "chunk_id": chunk["chunk_id"],
                "source": chunk["source"],
                "score": chunk["hybrid_score"],
                "text": chunk["text"],
            }
            for chunk in retrieved
        ],
        "recallAtK": recall_at_k,
        "grade": None,
        "noContextCorrect": None,
    }


def average_recall(results, k):
    valid = [r for r in results if r["answerable"] and r["evidence"]]
    if not valid:
        return None
    return round(
        sum(r["recallAtK"][k] for r in valid) / len(valid), 4
    )


def calculate_metrics(results):
    summary = {}
    for k in K_VALUES:
        summary[f"Recall@{k}"] = average_recall(results, k)

    by_type = {}
    for question_type in sorted({r["type"] for r in results}):
        typed = [r for r in results if r["type"] == question_type]
        by_type[question_type] = {}
        for k in K_VALUES:
            valid = [
                r for r in typed
                if r["answerable"] and r["evidence"]
            ]
            by_type[question_type][f"Recall@{k}"] = (
                round(
                    sum(r["recallAtK"][k] for r in valid) / len(valid), 4
                )
                if valid else None
            )

    return summary, by_type


def run():
    RESULTS_DIR.mkdir(exist_ok=True)
    runs = []

    for corpus in ["kestrel", "custom"]:
        questions = load_questions(corpus)
        document_dir = ROOT / "corpora" / corpus / "docs"

        for config in CONFIGS:
            print(f"\nEvaluating {corpus} - {config['name']}")

            count = index_directory(
                str(document_dir),
                corpus_name=corpus,
                chunk_size=config["chunk_size"],
                overlap=config["overlap"],
            )
            print(f"Indexed {count} chunks.")

            results = [
                evaluate_question(question, corpus, top_k=10)
                for question in questions
            ]

            summary, by_type = calculate_metrics(results)

            run_data = {
                "corpus": corpus,
                "config": config,
                "generatedAt": datetime.now().isoformat(),
                "total": len(results),
                "summary": summary,
                "byType": by_type,
                "results": results,
            }
            runs.append(run_data)

            print("Evidence Recall results:")
            for metric, value in summary.items():
                print(f"  {metric}: {value}")

    output = {
        "generatedAt": datetime.now().isoformat(),
        "runs": runs,
    }

    filename = RESULTS_DIR / (
        f"python-evaluation-{datetime.now():%Y%m%d-%H%M%S}.json"
    )
    filename.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nSaved results to: {filename}")


if __name__ == "__main__":
    run()

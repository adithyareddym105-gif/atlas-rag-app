
from pathlib import Path
import os
import json
import time
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL") or None,
)

MODEL = os.getenv("LLM_MODEL")
if not MODEL:
    raise RuntimeError("LLM_MODEL is missing from .env")

results = []

for corpus in ["kestrel", "custom"]:
    path = ROOT / "eval" / f"{corpus}.questions.jsonl"

    with path.open(encoding="utf-8") as file:
        questions = [json.loads(line) for line in file if line.strip()]

    for q in questions:
        print(f"Running {corpus}: {q['id']}")

        prompt = (
            "Answer this question WITHOUT access to company documents "
            "or retrieved context. Use only your existing model knowledge. "
            "Do not invent company-specific policies or facts. "
            "If you cannot reliably know the answer, clearly say so.\n\n"
            f"Question: {q['question']}"
        )

        try:
            response = client.chat.completions.create(
                model=MODEL,
                temperature=0.1,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a careful question-answering assistant."
                    },
                    {"role": "user", "content": prompt}
                ],
            )

            answer = response.choices[0].message.content or ""
            error = None

        except Exception as e:
            answer = ""
            error = str(e)
            print(f"ERROR: {error}")

        results.append({
            "corpus": corpus,
            "id": q["id"],
            "question": q["question"],
            "answerable": q.get("answerable", True),
            "expected_answer": q.get("expected_answer", ""),
            "no_context_answer": answer,
            "error": error,
            "manual_grade": None
        })

        time.sleep(0.3)

output = {
    "generatedAt": datetime.now().isoformat(),
    "model": MODEL,
    "method": "LLM generation without retrieved document context",
    "total": len(results),
    "results": results
}

results_dir = ROOT / "results"
results_dir.mkdir(exist_ok=True)

filename = results_dir / (
    f"no-context-evaluation-{datetime.now():%Y%m%d-%H%M%S}.json"
)

filename.write_text(
    json.dumps(output, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print(f"\nCompleted: {len(results)} questions")
print(f"Saved to: {filename}")

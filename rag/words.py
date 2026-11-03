import re
from collections import Counter
from pathlib import Path

from rag.vector_store import get_collection


def get_word_analytics(corpus="kestrel"):
    folder = Path("corpora") / corpus / "docs"
    words = Counter()
    word_chunks = {}

    for path in folder.glob("*"):
        if path.suffix.lower() not in {".md", ".txt"}:
            continue

        text = path.read_text(encoding="utf-8").lower()
        for word in re.findall(r"\b[a-z][a-z0-9-]{2,}\b", text):
            words[word] += 1

    collection = get_collection()
    chunks = collection.get(
        where={"corpus": corpus},
        include=["documents", "metadatas"],
    )

    for document, metadata in zip(chunks["documents"], chunks["metadatas"]):
        for word in set(re.findall(r"\b[a-z][a-z0-9-]{2,}\b", document.lower())):
            word_chunks.setdefault(word, []).append(metadata["chunk_id"])

    return {
        "corpus": corpus,
        "totalWords": sum(words.values()),
        "uniqueWords": len(words),
        "topWords": [
            {"word": word, "count": count}
            for word, count in words.most_common(30)
        ],
        "wordChunks": word_chunks,
    }


def analyze_question(question, corpus="kestrel"):
    analytics = get_word_analytics(corpus)
    present = []
    absent = []

    for word in set(re.findall(r"\b[a-z][a-z0-9-]{2,}\b", question.lower())):
        if word in analytics["wordChunks"]:
            present.append({
                "word": word,
                "chunks": analytics["wordChunks"][word],
            })
        else:
            absent.append(word)

    return {"present": present, "absent": sorted(absent)}

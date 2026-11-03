import re

from rag.retrieval import search_documents
from rag.keyword_search import keyword_search


def hybrid_search(query: str, top_k: int = 5, corpus_name: str = "kestrel") -> list[dict]:
    """Combine semantic and keyword retrieval using reciprocal rank fusion."""
    if not query.strip():
        raise ValueError("Query cannot be empty")

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    semantic_results = search_documents(query, top_k=top_k, corpus_name=corpus_name)
    keyword_results = keyword_search(query, top_k=top_k, corpus_name=corpus_name)

    combined = {}

    for rank, result in enumerate(semantic_results, start=1):
        chunk_id = result["chunk_id"]
        combined[chunk_id] = {
            **result,
            "semantic_rank": rank,
            "keyword_rank": None,
            "hybrid_score": 1 / (60 + rank),
        }

    for rank, result in enumerate(keyword_results, start=1):
        chunk_id = result["chunk_id"]

        if chunk_id not in combined:
            combined[chunk_id] = {
                **result,
                "semantic_rank": None,
                "keyword_rank": rank,
                "hybrid_score": 0,
            }

        combined[chunk_id]["keyword_rank"] = rank
        combined[chunk_id]["hybrid_score"] += 1 / (60 + rank)

        identifiers = re.findall(r"\b[a-z]+-\d+\b", query.lower())
        matched_terms = result.get("matched_terms", [])

        if any(identifier in matched_terms for identifier in identifiers):
            combined[chunk_id]["hybrid_score"] += 1.0

    ranked = sorted(
        combined.values(),
        key=lambda item: item["hybrid_score"],
        reverse=True,
    )

    return ranked[:top_k]

import re

from rag.vector_store import get_collection

STOPWORDS = {
    "what", "does", "how", "and", "the", "is", "it",
    "a", "an", "to", "for", "of", "in", "on", "do",
    "i", "my", "me", "can", "you", "fix", "mean"
}


def keyword_search(query: str, top_k: int = 5, corpus_name: str = "kestrel") -> list[dict]:
    """Find document chunks using exact keywords and identifiers."""
    if not query.strip():
        raise ValueError("Query cannot be empty")

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    collection = get_collection()

    results = collection.get(
        where={"corpus": corpus_name},
        include=["documents", "metadatas"],
    )

    query_terms = set(re.findall(r"[a-zA-Z0-9-]+", query.lower()))
    query_terms -= STOPWORDS

    identifiers = {
        term for term in query_terms
        if re.fullmatch(r"[a-z]+-\d+", term)
    }

    matches = []

    for document, metadata in zip(results["documents"], results["metadatas"]):
        text = document.lower()
        document_terms = set(re.findall(r"[a-zA-Z0-9-]+", text))
        matched_terms = query_terms.intersection(document_terms)

        if matched_terms:
            score = len(matched_terms)

            for identifier in identifiers.intersection(document_terms):
                score += 10

            matches.append({
                "chunk_id": metadata["chunk_id"],
                "source": metadata["source"],
                "chunk_number": metadata["chunk_number"],
                "text": document,
                "keyword_score": score,
                "matched_terms": sorted(matched_terms),
            })

    matches.sort(key=lambda item: item["keyword_score"], reverse=True)

    return matches[:top_k]

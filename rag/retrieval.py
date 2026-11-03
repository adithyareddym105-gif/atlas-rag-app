from rag.embeddings import embed_query
from rag.vector_store import get_collection


def search_documents(query: str, top_k: int = 5, corpus_name: str = "kestrel") -> list[dict]:
    """Find the most semantically relevant document chunks."""
    if not query.strip():
        raise ValueError("Query cannot be empty")

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    collection = get_collection()

    if collection.count() == 0:
        return []

    query_embedding = embed_query(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        where={"corpus": corpus_name},
        include=["documents", "metadatas", "distances"],
    )

    matches = []

    for document, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        matches.append({
            "chunk_id": metadata["chunk_id"],
            "source": metadata["source"],
            "chunk_number": metadata["chunk_number"],
            "text": document,
            "distance": distance,
            "similarity": 1 - distance,
        })

    return matches

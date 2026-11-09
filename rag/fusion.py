"""Reciprocal Rank Fusion over whichever retrievers are switched on.

Each retriever returns its own ranked list of chunks (up to `candidates` of them).
RRF gives a chunk weight / (rrf_k + rank) for every list it appears in, and adds them up.
Every fused result says which retriever found it and at which rank (found_by).
"""
import time

from rag.bm25 import bm25_search
from rag.retrieval import search_documents

RRF_K = 60
DEFAULT_RETRIEVERS = ("dense", "bm25")


def _graph_search(query: str, top_k: int, corpus_name: str) -> list[dict]:
    try:
        from rag.graph_retrieval import graph_search  # added later in V3
    except ModuleNotFoundError as error:
        raise ValueError("The graph retriever is not available yet") from error
    return graph_search(query, top_k=top_k, corpus_name=corpus_name)


# Every retriever has the same signature: (query, top_k, corpus_name) -> list[dict]
REGISTRY = {
    "dense": search_documents,
    "bm25": bm25_search,
    "graph": _graph_search,
}


def fuse(
    ranked_lists: dict[str, list[dict]],
    weights: dict[str, float] | None = None,
    rrf_k: int = RRF_K,
) -> list[dict]:
    """Pure RRF: no I/O, easy to test."""
    weights = weights or {}
    fused: dict[str, dict] = {}

    for name, results in ranked_lists.items():
        weight = weights.get(name, 1.0)
        for rank, item in enumerate(results, start=1):
            entry = fused.setdefault(item["chunk_id"], {"found_by": {}, "rrf_score": 0.0})
            for key, value in item.items():
                entry.setdefault(key, value)  # keep text, source, per-retriever scores
            entry["found_by"][name] = rank
            entry["rrf_score"] += weight / (rrf_k + rank)

    ranked = sorted(
        fused.values(),
        key=lambda e: (-e["rrf_score"], min(e["found_by"].values()), e["chunk_id"]),
    )
    for entry in ranked:
        entry["hybrid_score"] = entry["rrf_score"]  # name used by V2 code (main.py, evaluate.py)
    return ranked


def retrieve_detailed(
    query: str,
    corpus_name: str = "kestrel",
    top_k: int = 5,
    retrievers: tuple[str, ...] | list[str] = DEFAULT_RETRIEVERS,
    candidates: int = 50,
    weights: dict[str, float] | None = None,
    rrf_k: int = RRF_K,
) -> dict:
    """Run the retrievers that are on, fuse, and keep what is needed to analyse the fusion."""
    names = list(dict.fromkeys(retrievers))
    if not names:
        raise ValueError("Switch on at least one retriever")
    unknown = set(names) - set(REGISTRY)
    if unknown:
        raise ValueError(f"Unknown retriever(s): {sorted(unknown)}")
    if not query.strip():
        raise ValueError("Query cannot be empty")
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    per_retriever: dict[str, list[dict]] = {}
    latency_ms: dict[str, float] = {}
    for name in names:
        start = time.perf_counter()
        per_retriever[name] = REGISTRY[name](
            query, top_k=max(candidates, top_k), corpus_name=corpus_name
        )
        latency_ms[name] = round((time.perf_counter() - start) * 1000, 1)

    fused = fuse(per_retriever, weights=weights, rrf_k=rrf_k)
    return {
        "results": fused[:top_k],
        "per_retriever": per_retriever,  # full candidate lists, for "did the graph's chunks reach the top k?"
        "latency_ms": latency_ms,
    }


def retrieve(*args, **kwargs) -> list[dict]:
    """Fused top_k chunks, each with found_by = {retriever: rank}."""
    return retrieve_detailed(*args, **kwargs)["results"]

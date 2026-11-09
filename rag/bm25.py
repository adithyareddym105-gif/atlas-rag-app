"""BM25 retriever on SQLite FTS5.

- Index lives in data/bm25.sqlite (a file, so it survives restarts).
- One FTS5 table per corpus, so IDF statistics are not mixed across corpora.
- Built from the same chunks as the dense index (read from Chroma), keyed by chunk_id.
- Rebuilt automatically when the set of chunk ids in Chroma changes, and explicitly
  by build_index(corpus) (call it at the end of index_directory).
"""
import hashlib
import re
import sqlite3
from contextlib import closing
from pathlib import Path

from rag.vector_store import get_collection

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "bm25.sqlite"

# Applied to the QUERY only. The index keeps every word and lets IDF down-weight them.
QUERY_STOPWORDS = {
    "a", "an", "the", "of", "to", "in", "on", "at", "for", "and", "or",
    "is", "are", "was", "were", "be", "it", "its", "this", "that",
    "what", "which", "how", "does", "do", "did", "i", "my", "me", "we",
}

# "KST-2044", "LLM_API_KEY", "203.0.113.10" are matched as one compound token.
_TOKEN = re.compile(r"[^\W_]+(?:[-_.][^\W_]+)+|[^\W_]+")
_SPLIT = re.compile(r"[-_.]")


def analyze(text: str) -> list[str]:
    """Lowercase and tokenize. Compound identifiers are indexed in two ways:
    joined ("kst2044") and split ("kst", "2044"). So "E47" and "E-47" both give "e47",
    and "api key" still matches LLM_API_KEY."""
    terms = []
    for token in _TOKEN.findall(text.lower()):
        parts = _SPLIT.split(token)
        if len(parts) > 1:
            terms.append("".join(parts))
        terms.extend(parts)
    return terms


def _table(corpus: str) -> str:
    if not re.fullmatch(r"[a-z0-9_]+", corpus):
        raise ValueError(f"Invalid corpus name: {corpus}")
    return f"bm25_{corpus}"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "CREATE TABLE IF NOT EXISTS bm25_meta "
        "(corpus TEXT PRIMARY KEY, n INTEGER, signature TEXT)"
    )
    return con


def _signature(ids: list[str]) -> str:
    return hashlib.md5("\n".join(sorted(ids)).encode("utf-8")).hexdigest()


def build_index(corpus: str) -> int:
    """(Re)build the BM25 index of one corpus from the chunks currently in Chroma."""
    table = _table(corpus)
    data = get_collection().get(
        where={"corpus": corpus}, include=["documents", "metadatas"]
    )
    rows = [
        (m["chunk_id"], m["source"], m["chunk_number"], doc, " ".join(analyze(doc)))
        for doc, m in zip(data["documents"], data["metadatas"])
    ]

    with closing(_connect()) as con, con:
        con.execute(f"DROP TABLE IF EXISTS {table}")
        con.execute(
            f"CREATE VIRTUAL TABLE {table} USING fts5("
            "chunk_id UNINDEXED, source UNINDEXED, chunk_number UNINDEXED, "
            "text UNINDEXED, terms, tokenize='unicode61 remove_diacritics 2')"
        )
        con.executemany(
            f"INSERT INTO {table}(chunk_id, source, chunk_number, text, terms) "
            "VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        con.execute(
            "INSERT OR REPLACE INTO bm25_meta VALUES (?, ?, ?)",
            (corpus, len(rows), _signature(data["ids"])),
        )
    return len(rows)


def ensure_index(corpus: str) -> None:
    """Rebuild the index if Chroma now holds a different set of chunks."""
    ids = get_collection().get(where={"corpus": corpus}, include=["metadatas"])["ids"]
    with closing(_connect()) as con:
        row = con.execute(
            "SELECT signature FROM bm25_meta WHERE corpus = ?", (corpus,)
        ).fetchone()
    if row is None or row[0] != _signature(ids):
        build_index(corpus)


def bm25_search(query: str, top_k: int = 5, corpus_name: str = "kestrel") -> list[dict]:
    """Rank the chunks of a corpus with BM25. Same output shape as the other retrievers."""
    if not query.strip():
        raise ValueError("Query cannot be empty")
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    table = _table(corpus_name)
    query_terms = [
        t for t in dict.fromkeys(analyze(query)) if t not in QUERY_STOPWORDS
    ]
    if not query_terms:
        return []

    ensure_index(corpus_name)
    match = " OR ".join(f'"{t}"' for t in query_terms)

    with closing(_connect()) as con:
        rows = con.execute(
            f"SELECT chunk_id, source, chunk_number, text, terms, -bm25({table}) AS score "
            f"FROM {table} WHERE {table} MATCH ? "
            "ORDER BY score DESC, source, chunk_number LIMIT ?",
            (match, top_k),
        ).fetchall()

    wanted = set(query_terms)
    return [
        {
            "chunk_id": chunk_id,
            "source": source,
            "chunk_number": chunk_number,
            "text": text,
            "bm25_score": round(score, 4),
            "matched_terms": sorted(wanted & set(terms.split())),
        }
        for chunk_id, source, chunk_number, text, terms, score in rows
    ]

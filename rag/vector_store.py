import chromadb

from pathlib import Path

DB_PATH = Path("data/chroma")


def get_collection():
    """Return the persistent ChromaDB collection."""
    client = chromadb.PersistentClient(path=str(DB_PATH))

    return client.get_or_create_collection(
        name="kestrel_documents",
        metadata={"hnsw:space": "cosine"},
    )

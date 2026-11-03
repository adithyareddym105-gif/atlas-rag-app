from pathlib import Path
from rag.chunking import chunk_text
from rag.embeddings import embed_texts
from rag.vector_store import get_collection


def index_directory(
    directory: str,
    corpus_name: str = "kestrel",
    chunk_size: int = 800,
    overlap: int = 80,
) -> int:
    root = Path(directory)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")

    collection = get_collection()

    # Remove the previous index for this corpus before rebuilding it.
    collection.delete(where={"corpus": corpus_name})

    documents = []
    ids = []
    metadatas = []

    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file() or file_path.suffix.lower() not in {".md", ".txt"}:
            continue

        content = file_path.read_text(encoding="utf-8")
        chunks = chunk_text(content, chunk_size, overlap)

        for chunk_number, chunk in enumerate(chunks):
            chunk_id = f"{corpus_name}:{file_path.stem}:{chunk_number}"
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({
                "corpus": corpus_name,
                "source": file_path.name,
                "chunk_number": chunk_number,
                "chunk_id": chunk_id,
            })

    if not documents:
        return 0

    embeddings = embed_texts(documents)

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )

    return len(documents)

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from rag.hybrid_retrieval import hybrid_search
from rag.generation import generate_answer

app = FastAPI(
    title="EPITA RAG Application",
    description="Retrieval-Augmented Generation API",
    version="1.0.0",
)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    corpus: str = "kestrel"
    top_k: int = Field(default=5, ge=1, le=20)


class ChunkResult(BaseModel):
    chunk_id: str
    source: str
    text: str
    hybrid_score: float


class SearchResponse(BaseModel):
    query: str
    corpus: str
    results: list[ChunkResult]


@app.get("/")
def home():
    return {"message": "EPITA RAG API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/api/search", response_model=SearchResponse)
def search(request: SearchRequest):
    if request.corpus not in {"kestrel", "custom"}:
        raise HTTPException(status_code=400, detail="Unknown corpus")

    try:
        results = hybrid_search(
            request.query,
            top_k=request.top_k,
            corpus_name=request.corpus,
        )

        return {
            "query": request.query,
            "corpus": request.corpus,
            "results": [
                {
                    "chunk_id": item["chunk_id"],
                    "source": item["source"],
                    "text": item["text"],
                    "hybrid_score": item["hybrid_score"],
                }
                for item in results
            ],
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


class AnswerResponse(BaseModel):
    query: str
    corpus: str
    answer: str
    citations: list[str]
    not_found: bool
    results: list[ChunkResult]


@app.post("/api/answer", response_model=AnswerResponse)
def answer(request: SearchRequest):
    if request.corpus not in {"kestrel", "custom"}:
        raise HTTPException(status_code=400, detail="Unknown corpus")
    try:
        results = hybrid_search(
            request.query,
            top_k=request.top_k,
            corpus_name=request.corpus,
        )
        generated = generate_answer(request.query, results)
        return {
            "query": request.query,
            "corpus": request.corpus,
            "answer": generated.answer,
            "citations": generated.citations,
            "not_found": generated.not_found,
            "results": [
                {
                    "chunk_id": item["chunk_id"],
                    "source": item["source"],
                    "text": item["text"],
                    "hybrid_score": item["hybrid_score"],
                }
                for item in results
            ],
        }
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))




@app.get("/api/health")
def api_health():
    import os
    return {
        "status": "healthy",
        "llmConfigured": bool(os.getenv("LLM_API_KEY")),
        "model": os.getenv("LLM_MODEL", "Gemini")
    }


@app.get("/api/documents")
def list_documents(corpus: str = "kestrel"):
    from pathlib import Path

    if corpus not in {"kestrel", "custom"}:
        raise HTTPException(status_code=400, detail="Unknown corpus")

    folder = Path("corpora") / corpus / "docs"
    documents = []

    if folder.exists():
        for file in sorted(folder.iterdir()):
            if file.is_file() and file.suffix.lower() in {".md", ".txt"}:
                content = file.read_text(encoding="utf-8")
                documents.append({
                    "id": file.name,
                    "name": file.name,
                    "type": file.suffix.lstrip("."),
                    "chars": len(content),
                    "builtin": True
                })

    return documents


@app.get("/app")
def frontend():
    return FileResponse("public/index.html")




@app.get("/api/words")
def words_analytics(corpus: str = "kestrel"):
    from rag.words import get_word_analytics

    if corpus not in {"kestrel", "custom"}:
        raise HTTPException(status_code=400, detail="Unknown corpus")

    return get_word_analytics(corpus)


@app.post("/api/words/question")
def words_question(request: SearchRequest):
    from rag.words import analyze_question

    if request.corpus not in {"kestrel", "custom"}:
        raise HTTPException(status_code=400, detail="Unknown corpus")

    return analyze_question(request.query, request.corpus)


app.mount("/", StaticFiles(directory="public"), name="public")

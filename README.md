# Atlas – RAG Application

## Overview

Atlas is a Retrieval-Augmented Generation application built with Python, FastAPI, ChromaDB and Gemini. It supports the provided Kestrel knowledge base and a custom document corpus.

## Architecture

- Document chunking with configurable size and overlap.
- Local embeddings using `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions).
- Persistent vector storage using ChromaDB.
- Hybrid semantic and keyword retrieval.
- Reciprocal Rank Fusion and exact-identifier matching.
- Grounded answer generation using Gemini.
- Pydantic response validation and source citations.
- Words Analytics frontend.

## Requirements

- Python 3.11 or newer.
- Gemini API key.

## Setup (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install fastapi uvicorn sentence-transformers chromadb pydantic python-multipart python-dotenv openai pytest httpx
```

Create `.env` using `.env.example` as a template and add your Gemini API key.

## Run the application

```powershell
uvicorn main:app --reload
```

Open http://127.0.0.1:8000.

## Run tests

```powershell
python -m pytest -q
```

## Run retrieval evaluation

```powershell
python scripts/evaluate.py
```

The evaluation compares 800/80 and 400/40 chunk configurations on the Kestrel and custom corpora. Unanswerable questions are excluded from evidence recall. Results are saved under `results/`.

The measured evaluation JSON is included in this repository.

## Project structure

- `main.py` – FastAPI application and API endpoints.
- `rag/` – chunking, embeddings, indexing, retrieval and generation.
- `corpora/` – Kestrel and custom documents.
- `eval/` – evaluation question sets.
- `scripts/` – evaluation script.
- `public/` – frontend.
- `tests/` – automated tests.
- `REPORT.md` – evaluation report.

## Security

Never commit `.env` or expose API keys. `.env.example` contains placeholders only.

## Limitations

No-context evaluation, manual answer grading, question-level retrieval-miss diagnosis, and full upload/delete integration remain incomplete. See `REPORT.md` for details.
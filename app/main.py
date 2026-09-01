"""FastAPI service.

    uvicorn app.main:app --reload
    open http://localhost:8000/docs
"""
import json
from typing import List, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from pathlib import Path

from app import config, llm, retrieval

STATIC = Path(__file__).parent / "static"

app = FastAPI(
    title="FinDoc Assistant",
    description="Hybrid RAG over financial regulatory documents.",
    version="1.0.0",
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, examples=["What is the KYC periodic update requirement?"])
    strategy: Literal["dense", "bm25", "hybrid"] = "hybrid"
    k: int = Field(default=config.DEFAULT_K, ge=1, le=10)
    collection: str | None = None


class Source(BaseModel):
    source: str
    page: int
    score: float
    excerpt: str


class AskResponse(BaseModel):
    question: str
    strategy: str
    answer: str
    sources: List[Source]


def _to_sources(chunks):
    return [
        Source(
            source=c["source"],
            page=c["page"],
            score=round(float(c["score"]), 4),
            excerpt=c["text"][:300] + ("..." if len(c["text"]) > 300 else ""),
        )
        for c in chunks
    ]


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/health")
def health():
    """Reports whether an index is actually loaded, not just that the process is up."""
    chunk_file = config.CHUNKS_DIR / f"{config.COLLECTION}.json"
    chunks = None
    if chunk_file.exists():
        try:
            chunks = len(json.loads(chunk_file.read_text(encoding="utf-8")))
        except (ValueError, OSError):
            chunks = None
    return {
        "status": "ok" if chunks else "no_index",
        "collection": config.COLLECTION,
        "chunks": chunks,
    }


@app.post("/search", response_model=List[Source])
def search(req: AskRequest):
    """Retrieval only, no LLM. Useful for inspecting what the index returns."""
    try:
        chunks = retrieval.search(req.question, req.strategy, req.k, req.collection)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return _to_sources(chunks)


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    try:
        chunks = retrieval.search(req.question, req.strategy, req.k, req.collection)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if not chunks:
        raise HTTPException(status_code=404, detail="No matching passages found.")

    return AskResponse(
        question=req.question,
        strategy=req.strategy,
        answer=llm.answer(req.question, chunks),
        sources=_to_sources(chunks),
    )


app.mount("/static", StaticFiles(directory=STATIC), name="static")


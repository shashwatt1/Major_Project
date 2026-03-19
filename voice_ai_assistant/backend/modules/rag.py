from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from modules import llm_client


BASE_DIR = Path(__file__).resolve().parents[2]
DOCS_DIR = BASE_DIR / "data" / "docs"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def _split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + chunk_size)
        chunks.append(cleaned[start:end])
        if end == len(cleaned):
            break
        start = max(end - overlap, 0)
    return chunks


def _load_documents() -> list[tuple[str, str]]:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    documents: list[tuple[str, str]] = []
    for path in sorted(DOCS_DIR.rglob("*.txt")):
        try:
            documents.append((path.name, path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return documents


def _build_chunks() -> tuple[list[str], list[str]]:
    chunk_texts: list[str] = []
    sources: list[str] = []
    for source_name, content in _load_documents():
        for chunk in _split_text(content):
            chunk_texts.append(chunk)
            sources.append(source_name)
    return chunk_texts, sources


@lru_cache(maxsize=1)
def _get_embedder() -> SentenceTransformer:
    return SentenceTransformer("all-MiniLM-L6-v2")


@lru_cache(maxsize=1)
def _get_index() -> tuple[faiss.IndexFlatL2 | None, list[str], list[str]]:
    chunks, sources = _build_chunks()
    if not chunks:
        return None, [], []

    embedder = _get_embedder()
    embeddings = embedder.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)
    embeddings = np.asarray(embeddings, dtype="float32")

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index, chunks, sources


def retrieve(query: str, top_k: int = 3) -> list[dict[str, str]]:
    index, chunks, sources = _get_index()
    if index is None or not chunks:
        return []

    embedder = _get_embedder()
    query_embedding = embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    query_embedding = np.asarray(query_embedding, dtype="float32")

    limit = min(max(top_k, 1), len(chunks))
    _distances, indices = index.search(query_embedding, limit)

    results: list[dict[str, str]] = []
    for idx in indices[0]:
        if 0 <= idx < len(chunks):
            results.append({"source": sources[idx], "content": chunks[idx]})
    return results


def build_prompt(query: str, top_k: int = 3) -> tuple[str, list[dict[str, str]]]:
    matches = retrieve(query, top_k=top_k)
    if not matches:
        return query, []

    context = "\n\n".join(f"[{item['source']}]\n{item['content']}" for item in matches)
    prompt = (
        "Answer the user's question using the retrieved context when relevant.\n\n"
        f"Retrieved Context:\n{context}\n\n"
        f"User Question:\n{query}"
    )
    return prompt, matches


def rag_answer(query: str, top_k: int = 3, user_id: str | None = None) -> tuple[str, list[dict[str, str]]]:
    prompt, matches = build_prompt(query, top_k=top_k)
    answer = llm_client.get_response(prompt, user_id=user_id)
    return answer, matches

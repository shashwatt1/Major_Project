from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_RAG_DIR = BASE_DIR / "data" / "rag_docs"

def _tokenize(text: str) -> list[str]:
    return [t for t in "".join(ch if ch.isalnum() else " " for ch in text.lower()).split() if t]

def _term_freq(tokens: Iterable[str]) -> dict[str, float]:
    counts: dict[str, int] = {}
    for tok in tokens:
        counts[tok] = counts.get(tok, 0) + 1
    total = float(sum(counts.values())) or 1.0
    return {k: v / total for k, v in counts.items()}

def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    dot = 0.0
    for k, v in a.items():
        if k in b:
            dot += v * b[k]
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)

def _load_docs(rag_dir: Path) -> list[tuple[str, str]]:
    docs: list[tuple[str, str]] = []
    for path in sorted(rag_dir.glob("*.txt")):
        try:
            docs.append((path.name, path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return docs

def retrieve(query: str, rag_dir: Path | None = None, top_k: int = 3) -> list[tuple[str, str]]:
    rag_dir = rag_dir or DEFAULT_RAG_DIR
    rag_dir.mkdir(parents=True, exist_ok=True)

    docs = _load_docs(rag_dir)
    if not docs:
        return []

    q_vec = _term_freq(_tokenize(query))
    scored: list[tuple[float, str, str]] = []
    for name, content in docs:
        d_vec = _term_freq(_tokenize(content))
        scored.append((_cosine(q_vec, d_vec), name, content))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [(name, content) for score, name, content in scored[: max(top_k, 1)] if score > 0.0]

def build_prompt(query: str, rag_dir: Path | None = None, top_k: int = 3) -> tuple[str, list[str]]:
    retrieved = retrieve(query, rag_dir=rag_dir, top_k=top_k)
    if not retrieved:
        return query, []

    context_blocks = []
    sources = []
    for name, content in retrieved:
        sources.append(name)
        context_blocks.append(f"[{name}]\n{content.strip()}")

    context = "\n\n".join(context_blocks)
    prompt = (
        "You are a helpful assistant. Use the context below if relevant.\n\n"
        f"Context:\n{context}\n\n"
        f"User Query:\n{query}\n"
    )
    return prompt, sources

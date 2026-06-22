"""
Vector store — stores and retrieves embeddings for semantic search.
Uses a simple in-memory store with cosine similarity.
In production, replace with pgvector on Supabase.
"""

import math
import json
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class VectorDocument:
    id: str
    content: str
    embedding: list[float]
    metadata: dict = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


class VectorStore:
    """In-memory vector store with cosine similarity search."""

    def __init__(self):
        self._documents: dict[str, VectorDocument] = {}

    def add(self, doc: VectorDocument):
        self._documents[doc.id] = doc

    def add_batch(self, docs: list[VectorDocument]):
        for doc in docs:
            self._documents[doc.id] = doc

    def search(self, query_embedding: list[float], top_k: int = 5, threshold: float = 0.0) -> list[dict]:
        results = []
        for doc in self._documents.values():
            similarity = _cosine_similarity(query_embedding, doc.embedding)
            if similarity >= threshold:
                results.append({
                    "id": doc.id,
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "similarity": round(similarity, 4),
                    "created_at": doc.created_at,
                })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def delete(self, doc_id: str):
        self._documents.pop(doc_id, None)

    def count(self) -> int:
        return len(self._documents)

    def clear(self):
        self._documents.clear()


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# Global singleton
store = VectorStore()

"""
RAG Retriever — ingests articles into the vector store and retrieves relevant context.
"""

from embeddings import generate_embedding, generate_embeddings_batch, chunk_text
from vector_store import VectorStore, VectorDocument, store
from config import get_settings


async def ingest_article(article_id: str, headline: str, content: str, category: str = "general"):
    """Chunk an article, generate embeddings, and store in the vector store."""
    settings = get_settings()
    chunks = chunk_text(content, settings.chunk_size, settings.chunk_overlap)

    if not chunks:
        return

    embeddings = await generate_embeddings_batch(chunks)

    docs = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        docs.append(VectorDocument(
            id=f"{article_id}_chunk_{i}",
            content=chunk,
            embedding=embedding,
            metadata={
                "article_id": article_id,
                "headline": headline,
                "category": category,
                "chunk_index": i,
                "total_chunks": len(chunks),
            },
        ))

    store.add_batch(docs)


async def retrieve_context(query: str, top_k: int = 5, category: str | None = None) -> list[dict]:
    """
    Retrieve relevant context for a query using semantic search.

    Args:
        query: Search query text
        top_k: Number of results to return
        category: Optional category filter

    Returns:
        List of relevant document chunks with similarity scores
    """
    settings = get_settings()
    query_embedding = await generate_embedding(query)
    results = store.search(query_embedding, top_k=top_k, threshold=settings.similarity_threshold)

    if category:
        results = [r for r in results if r["metadata"].get("category") == category]

    return results


async def check_duplicate(headline: str, threshold: float = 0.85) -> tuple[bool, float, str]:
    """
    Check if a headline is semantically similar to existing articles.

    Returns:
        (is_duplicate, similarity_score, matching_headline)
    """
    query_embedding = await generate_embedding(headline)
    results = store.search(query_embedding, top_k=1, threshold=threshold)

    if results:
        match = results[0]
        return True, match["similarity"], match["metadata"].get("headline", "")

    return False, 0.0, ""


async def get_fact_context(facts: str, top_k: int = 3) -> str:
    """
    Retrieve relevant prior articles to help verify facts.
    Used by the Fact Extraction agent for cross-referencing.
    """
    results = await retrieve_context(facts, top_k=top_k)
    if not results:
        return ""

    context_parts = []
    for r in results:
        context_parts.append(
            f"[Prior article: {r['metadata'].get('headline', 'Unknown')} | "
            f"Similarity: {r['similarity']}]\n{r['content'][:300]}"
        )

    return "\n\n---\n\n".join(context_parts)

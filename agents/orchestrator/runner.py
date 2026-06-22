"""
Pipeline runner — executes the LangGraph agent pipeline on articles.
"""

import asyncio
import time
from state import PipelineState
from graph import compile_pipeline


async def process_article(
    raw_text: str,
    source_url: str = "",
    source_name: str = "unknown",
    category: str = "general",
) -> PipelineState:
    """
    Run a single article through the full agent pipeline.

    Returns:
        Final PipelineState with all agent outputs.
    """
    pipeline = compile_pipeline()

    initial_state = PipelineState(
        raw_text=raw_text,
        source_url=source_url,
        source_name=source_name,
        category=category,
    )

    result = await pipeline.ainvoke(initial_state)
    return result


async def process_batch(
    articles: list[dict],
    concurrency: int = 3,
) -> list[PipelineState]:
    """
    Process a batch of articles with controlled concurrency.

    Args:
        articles: List of dicts with raw_text, source_url, source_name, category.
        concurrency: Max parallel pipeline runs.
    """
    semaphore = asyncio.Semaphore(concurrency)
    results = []

    async def run_one(article: dict) -> PipelineState:
        async with semaphore:
            return await process_article(
                raw_text=article.get("raw_text", ""),
                source_url=article.get("source_url", ""),
                source_name=article.get("source_name", "unknown"),
                category=article.get("category", "general"),
            )

    tasks = [run_one(a) for a in articles]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return [r if isinstance(r, PipelineState) else PipelineState(errors=[str(r)]) for r in results]


if __name__ == "__main__":
    import json

    test_article = """
    Apple announced today that it will invest $500 billion in US infrastructure over the next five years.
    CEO Tim Cook made the announcement at Apple Park in Cupertino, California.
    The investment will create over 20,000 new jobs across data centers, manufacturing, and R&D facilities.
    Apple shares rose 3.2% in after-hours trading following the announcement.
    """

    async def main():
        result = await process_article(
            raw_text=test_article,
            source_name="Reuters",
            category="technology",
        )
        print(json.dumps({
            "headline": result.headline,
            "relevance": result.relevance_score,
            "facts": result.fact_count,
            "word_count": result.word_count_en,
            "legal_approved": result.legal_approved,
            "critic_approved": result.critic_approved,
            "seo_keywords": result.keywords,
            "translations": list(result.translations.keys()),
            "errors": result.errors,
            "timings": result.agent_timings,
        }, indent=2))

    asyncio.run(main())

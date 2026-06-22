# Orchestrator Agent

Master coordinator that manages the multi-agent pipeline. Receives raw news events and delegates to specialized agents in sequence.

## Pipeline Flow
1. Receive raw article/event from ingestion
2. Dispatch to Discovery Agent (deduplication + relevance)
3. Route to Fact Agent (verification)
4. Legal Agent (compliance check)
5. Rewrite Agent (article generation)
6. SEO Agent (optimization)
7. Translation Agent (multi-language)
8. Avatar Agent (video production)
9. Publishing Agent (distribution)

## Tech
- Python, LangGraph / custom DAG
- Redis for inter-agent messaging
- Celery for async orchestration

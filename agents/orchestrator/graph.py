"""
A.N.N. Agent Pipeline — LangGraph DAG definition.

Pipeline flow:
  discovery → fact_extraction → scriptwriter → critic
      ↕ (rewrite loop)          → legal
  headline ──┐
  seo ───────┤ (parallel after critic pass)
  translation┘
      → publishing
"""

from langgraph.graph import StateGraph, END

from state import PipelineState
from config import get_settings
from nodes import (
    discovery_node,
    fact_extraction_node,
    legal_node,
    scriptwriter_node,
    critic_node,
    headline_node,
    seo_node,
    translation_node,
    publishing_node,
)


def should_skip_low_relevance(state: PipelineState) -> str:
    settings = get_settings()
    if state.relevance_score < settings.relevance_threshold:
        return "end"
    return "fact_extraction"


def should_rewrite(state: PipelineState) -> str:
    settings = get_settings()
    if not state.critic_approved and state.draft_count <= settings.max_critic_retries:
        return "scriptwriter"
    return "legal"


def should_block_legal(state: PipelineState) -> str:
    if not state.legal_approved:
        return "end"
    return "parallel_post_process"


def build_pipeline() -> StateGraph:
    """Build the LangGraph agent pipeline DAG."""

    graph = StateGraph(PipelineState)

    # Add nodes
    graph.add_node("discovery", discovery_node)
    graph.add_node("fact_extraction", fact_extraction_node)
    graph.add_node("scriptwriter", scriptwriter_node)
    graph.add_node("critic", critic_node)
    graph.add_node("legal", legal_node)
    graph.add_node("headline", headline_node)
    graph.add_node("seo", seo_node)
    graph.add_node("translation", translation_node)
    graph.add_node("publishing", publishing_node)

    # Set entry point
    graph.set_entry_point("discovery")

    # Discovery → relevance gate
    graph.add_conditional_edges("discovery", should_skip_low_relevance, {
        "fact_extraction": "fact_extraction",
        "end": END,
    })

    # Fact extraction → scriptwriter
    graph.add_edge("fact_extraction", "scriptwriter")

    # Scriptwriter → critic
    graph.add_edge("scriptwriter", "critic")

    # Critic → rewrite loop OR legal
    graph.add_conditional_edges("critic", should_rewrite, {
        "scriptwriter": "scriptwriter",
        "legal": "legal",
    })

    # Legal → block OR continue
    graph.add_conditional_edges("legal", should_block_legal, {
        "end": END,
        "parallel_post_process": "headline",
    })

    # Headline → SEO → Translation → Publishing (sequential for simplicity)
    graph.add_edge("headline", "seo")
    graph.add_edge("seo", "translation")
    graph.add_edge("translation", "publishing")

    # Publishing → END
    graph.add_edge("publishing", END)

    return graph


def compile_pipeline():
    """Compile the pipeline into a runnable graph."""
    graph = build_pipeline()
    return graph.compile()

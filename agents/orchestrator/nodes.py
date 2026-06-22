"""
Agent nodes — each function is a node in the LangGraph pipeline DAG.
Every node receives PipelineState, performs work, and returns updated state.
"""

import time
import asyncio
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from state import PipelineState
from config import get_settings


def _get_client():
    s = get_settings()
    return AsyncOpenAI(api_key=s.llm_api_key, base_url=s.llm_base_url), s.llm_model


async def _llm_call(system: str, user: str, temperature: float = 0.3, max_tokens: int = 2000) -> str:
    client, model = _get_client()
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


# ── Discovery Node ────────────────────────────────────────

async def discovery_node(state: PipelineState) -> PipelineState:
    t0 = time.time()
    score = await _llm_call(
        system="Rate this news article's relevance and newsworthiness on a scale of 1-10. Reply with ONLY the number.",
        user=f"Category: {state.category}\n\nArticle:\n{state.raw_text[:2000]}",
        temperature=0.0,
        max_tokens=5,
    )
    try:
        state.relevance_score = float(score.strip())
    except ValueError:
        state.relevance_score = 5.0

    state.agent_timings["discovery"] = round(time.time() - t0, 2)
    return state


# ── Fact Extraction Node ──────────────────────────────────

FACT_PROMPT = """You are a Legal Compliance AI. Extract ONLY verified facts from this article.
Rules: 1) Extract names, dates, numbers, locations, official statements. 2) Strip all prose/opinions.
3) Present as bulleted list (• Fact). 4) Add "Source: [name]" at end."""

async def fact_extraction_node(state: PipelineState) -> PipelineState:
    t0 = time.time()
    facts = await _llm_call(
        system=FACT_PROMPT,
        user=f"Source: {state.source_name}\n\nArticle:\n{state.raw_text}",
        temperature=0.0,
    )
    state.facts = facts
    state.fact_count = len([l for l in facts.split("\n") if l.strip().startswith("•")])
    state.agent_timings["fact_extraction"] = round(time.time() - t0, 2)
    return state


# ── Legal Compliance Node ─────────────────────────────────

LEGAL_PROMPT = """You are a media Legal Compliance Officer. Review this script for:
1) Copyright infringement (>30% overlap with source)
2) Defamation risk
3) Privacy violations (unnecessary PII exposure)
4) Content policy violations

Reply: First line "APPROVED" or "BLOCKED". If blocked, list specific risks."""

async def legal_node(state: PipelineState) -> PipelineState:
    t0 = time.time()
    review = await _llm_call(
        system=LEGAL_PROMPT,
        user=f"SOURCE FACTS:\n{state.facts}\n\nDRAFT SCRIPT:\n{state.english_script}",
        temperature=0.0,
        max_tokens=500,
    )
    state.legal_approved = review.strip().upper().startswith("APPROVED")
    if not state.legal_approved:
        state.legal_risks = [line.strip() for line in review.split("\n")[1:] if line.strip()]
    state.agent_timings["legal"] = round(time.time() - t0, 2)
    return state


# ── Scriptwriter Node ─────────────────────────────────────

SCRIPT_PROMPT = """You are an elite news anchor scriptwriter.
Write a 30-60 second broadcast script from these facts.
Style: BBC World Service meets Vice News. Short punchy sentences.
Include [PAUSE] markers. No bullet points — flowing broadcast prose.
Output ONLY the script text."""

async def scriptwriter_node(state: PipelineState) -> PipelineState:
    t0 = time.time()
    user_content = f"Category: {state.category.upper()}\n\nFacts:\n{state.facts}"

    if state.draft_count > 0 and state.critic_feedback:
        user_content += f"\n\nPREVIOUS DRAFT:\n{state.english_script}\n\nFEEDBACK TO FIX:\n{state.critic_feedback}"

    script = await _llm_call(system=SCRIPT_PROMPT, user=user_content, temperature=0.7, max_tokens=1000)
    state.english_script = script
    state.draft_count += 1
    state.word_count_en = len(script.split())
    state.estimated_duration_seconds = int((state.word_count_en / 150) * 60)
    state.agent_timings["scriptwriter"] = round(time.time() - t0, 2)
    return state


# ── Critic Node ───────────────────────────────────────────

CRITIC_PROMPT = """You are a Senior Executive Producer reviewing a broadcast script.
Check: 1) Hallucinations (details NOT in facts = FAIL). 2) Pacing/hooks. 3) Objectivity. 4) Clarity.
First line: "PASS" or "REJECT". If reject, explain what to fix (1-3 sentences)."""

async def critic_node(state: PipelineState) -> PipelineState:
    t0 = time.time()
    review = await _llm_call(
        system=CRITIC_PROMPT,
        user=f"SOURCE FACTS:\n{state.facts}\n\nDRAFT SCRIPT:\n{state.english_script}",
        temperature=0.1,
        max_tokens=300,
    )
    state.critic_approved = review.strip().upper().startswith("PASS")
    state.critic_feedback = review
    state.agent_timings["critic"] = round(time.time() - t0, 2)
    return state


# ── Headline Node ─────────────────────────────────────────

HEADLINE_PROMPT = """Create ONE compelling headline. Max 12 words, active voice, AP Title Case.
No clickbait. Output ONLY the headline."""

async def headline_node(state: PipelineState) -> PipelineState:
    t0 = time.time()
    headline = await _llm_call(
        system=HEADLINE_PROMPT,
        user=f"Script:\n{state.english_script}",
        temperature=0.8,
        max_tokens=50,
    )
    state.headline = headline.strip().strip('"')
    state.agent_timings["headline"] = round(time.time() - t0, 2)
    return state


# ── SEO Node ──────────────────────────────────────────────

SEO_PROMPT = """You are an SEO specialist. For this news article, generate:
1. meta_title (60 chars max)
2. meta_description (160 chars max)
3. keywords (5-8 comma-separated)

Format:
META_TITLE: ...
META_DESC: ...
KEYWORDS: ..."""

async def seo_node(state: PipelineState) -> PipelineState:
    t0 = time.time()
    result = await _llm_call(
        system=SEO_PROMPT,
        user=f"Headline: {state.headline}\n\nScript:\n{state.english_script}",
        temperature=0.3,
        max_tokens=300,
    )
    for line in result.strip().split("\n"):
        line = line.strip()
        if line.startswith("META_TITLE:"):
            state.meta_title = line.split(":", 1)[1].strip()
        elif line.startswith("META_DESC:"):
            state.meta_description = line.split(":", 1)[1].strip()
        elif line.startswith("KEYWORDS:"):
            state.keywords = [k.strip() for k in line.split(":", 1)[1].split(",")]

    state.schema_json = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": state.headline,
        "description": state.meta_description,
        "keywords": ", ".join(state.keywords),
        "articleSection": state.category,
    }
    state.agent_timings["seo"] = round(time.time() - t0, 2)
    return state


# ── Translation Node ──────────────────────────────────────

TRANSLATE_PROMPT = """Translate this English broadcast script into natural, conversational {language}.
Keep [PAUSE] markers. Maintain tone and pacing. Use native script. Output ONLY the translation."""

async def translation_node(state: PipelineState) -> PipelineState:
    t0 = time.time()
    languages = ["Hindi", "Spanish", "French", "Arabic"]

    async def translate_one(lang: str) -> tuple[str, str]:
        prompt = TRANSLATE_PROMPT.replace("{language}", lang)
        result = await _llm_call(system=prompt, user=state.english_script, temperature=0.3, max_tokens=1500)
        return lang, result

    results = await asyncio.gather(*[translate_one(lang) for lang in languages], return_exceptions=True)

    for r in results:
        if isinstance(r, tuple):
            lang, text = r
            state.translations[lang] = text
            if lang == "Hindi":
                state.hindi_script = text
        elif isinstance(r, Exception):
            state.errors.append(f"Translation error: {str(r)}")

    state.agent_timings["translation"] = round(time.time() - t0, 2)
    return state


# ── Publishing Node ───────────────────────────────────────

async def publishing_node(state: PipelineState) -> PipelineState:
    """Calls article-service to persist, then notification-service to distribute."""
    import httpx
    from config import get_settings
    s = get_settings()
    t0 = time.time()

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Save to article service
            r = await client.post(f"{s.article_service_url}/api/v1/scripts", json={
                "headline": state.headline,
                "english_script": state.english_script,
                "hindi_script": state.hindi_script,
                "translations": state.translations,
                "category": state.category,
                "source_url": state.source_url,
            })
            if r.status_code == 200:
                data = r.json()
                state.script_id = data.get("id", "")

            # Index in search service
            await client.post(f"{s.search_service_url}/api/v1/search/index", json={
                "id": state.script_id,
                "headline": state.headline,
                "content": state.english_script,
                "category": state.category,
                "word_count": state.word_count_en,
            })

            # Trigger social broadcast
            await client.post(f"{s.notification_service_url}/api/v1/social/broadcast", json={
                "headline": state.headline,
                "excerpt": state.english_script.replace("[PAUSE]", "")[:400],
                "category": state.category,
                "script_id": state.script_id,
            })

    except Exception as e:
        state.errors.append(f"Publishing error: {str(e)}")

    state.agent_timings["publishing"] = round(time.time() - t0, 2)
    return state

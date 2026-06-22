# A.N.N. — Agent System Reference

> **Version:** 1.0
> **Last Updated:** 2026-06-22

---

## Overview

A.N.N. uses a multi-agent pipeline where each agent is a specialized AI module performing one step of the news production process. Agents are chained in a directed acyclic graph (DAG) — the output of one becomes the input of the next.

```
Raw Article ──► Fact Extractor ──► Scriptwriter ◄──► Critic (review loop)
                                        │
                              ┌─────────┴─────────┐
                              ▼                   ▼
                        Headline Gen        Translator
                              │                   │
                              └─────────┬─────────┘
                                        ▼
                                  BroadcastScript
                                        │
                              ┌─────────┴─────────┐
                              ▼                   ▼
                         ElevenLabs TTS     HeyGen Video
                              │                   │
                              └─────────┬─────────┘
                                        ▼
                                   Distribution
```

**Current agents (built):** 5 operational + 2 media producers
**Planned agents:** 4 additional (Discovery, Legal, SEO, Publishing)

---

## Agent Definitions

### 1. Fact Extractor Agent

> *The legal compliance firewall. Strips copyrighted prose, extracts only verifiable facts.*

**File:** `backend/agents/fact_extractor.py`
**Class:** `FactExtractorAgent`
**Role in pipeline:** First agent — receives raw copyrighted text, outputs clean facts

#### Responsibilities

- Extract verifiable facts (names, dates, numbers, locations, official statements) from copyrighted news articles
- Strip all original journalistic prose, opinions, analysis, and creative formatting
- Ensure zero sentence structure is copied from the original (copyright compliance)
- Produce a clean bulleted list of atomic facts with source attribution

#### Inputs

| Field | Type | Description |
|---|---|---|
| `raw_text` | string | Full copyrighted article text (min 50 chars) |
| `source_name` | string | Publication name for attribution |

#### Outputs

| Field | Type | Description |
|---|---|---|
| `facts` | string | Bulleted list of atomic facts (`• Fact 1\n• Fact 2\n...`) |
| `fact_count` | int | Number of facts extracted (derived from `•` count) |

#### LLM Configuration

| Parameter | Value | Rationale |
|---|---|---|
| `temperature` | 0.0 | Zero creativity — pure factual extraction |
| `max_tokens` | 2000 | Accommodates long-form articles |
| System prompt | Legal compliance persona | Strict rules against copying prose |

#### Failure Handling

- **Retry:** 5 attempts with exponential backoff (15s–60s)
- **Rate limit:** Acquires `llm` rate limiter token before each call
- **On total failure:** Exception propagates to pipeline orchestrator, article skipped, error logged

---

### 2. Scriptwriter Agent

> *The newsroom anchor writer. Transforms dry facts into compelling broadcast scripts.*

**File:** `backend/agents/scriptwriter.py`
**Class:** `ScriptwriterAgent`
**Role in pipeline:** Second agent — receives facts, outputs broadcast-ready English script

#### Responsibilities

- Write original, engaging broadcast scripts from extracted facts
- Target 30–60 second read time (~75–150 words)
- Use spoken-delivery style (short sentences, active voice)
- Insert `[PAUSE]` markers for dramatic pacing
- Accept and implement critic feedback for rewrites

#### Inputs

| Field | Type | Description |
|---|---|---|
| `facts` | string | Bulleted fact list from Fact Extractor |
| `category` | string | News category (affects tone) |
| `previous_draft` | string? | Prior script if rewriting after critic rejection |
| `feedback` | string? | Critic's specific feedback to implement |

#### Outputs

| Field | Type | Description |
|---|---|---|
| `script` | string | Broadcast-ready English script with `[PAUSE]` markers |

#### LLM Configuration

| Parameter | Value | Rationale |
|---|---|---|
| `temperature` | 0.7 | Creative enough for engaging prose, controlled enough for accuracy |
| `max_tokens` | 1000 | ~150 words target, buffer for longer stories |
| System prompt | Elite news anchor persona | BBC World Service × Vice News tone |

#### Failure Handling

- **Retry:** 5 attempts with exponential backoff
- **On critic rejection:** Receives feedback and rewrites (single retry — no infinite loops)
- **On total failure:** Exception propagates, article skipped

---

### 3. Critic Agent

> *The executive editor. Reviews every script for accuracy, bias, and quality — forces rewrites when standards aren't met.*

**File:** `backend/agents/critic.py`
**Class:** `CriticAgent`
**Role in pipeline:** Quality gate between Scriptwriter and downstream agents

#### Responsibilities

- Review drafted scripts against source facts for hallucinations
- Evaluate pacing, hooks, objectivity, clarity, and conciseness
- Issue `PASS` or `REJECT` verdicts
- Provide specific, actionable feedback when rejecting

#### Inputs

| Field | Type | Description |
|---|---|---|
| `facts` | string | Original extracted facts (ground truth) |
| `draft_script` | string | Scriptwriter's draft to review |

#### Outputs

| Field | Type | Description |
|---|---|---|
| `is_approved` | bool | `True` if script passes quality standards |
| `feedback` | string | `"PASS: [compliment]"` or `"REJECT: [specific fixes]"` |

#### LLM Configuration

| Parameter | Value | Rationale |
|---|---|---|
| `temperature` | 0.1 | Strict, analytical — minimal variance in judgment |
| `max_tokens` | 300 | Concise verdicts only |
| System prompt | Senior executive producer persona | Merciless quality standards |

#### Review Criteria

1. **Hallucination check** — Does the script contain any detail NOT present in the source facts? → Automatic `REJECT`
2. **Pacing & hooks** — Does the opening grab attention?
3. **Objectivity** — Any hidden bias or sensationalism?
4. **Clarity** — Would an anchor stumble reading this aloud?
5. **Conciseness** — Can it be said with fewer, more powerful words?

#### Failure Handling

- **Retry:** 5 attempts with exponential backoff
- **On ambiguous verdict:** If response doesn't start with `PASS`, treated as rejection
- **On total failure:** Script passes through unreviewed (fail-open to avoid blocking pipeline)

---

### 4. Headline Generator Agent

> *The hook master. Creates maximum-impact headlines in 12 words or fewer.*

**File:** `backend/agents/headline_generator.py`
**Class:** `HeadlineGeneratorAgent`
**Role in pipeline:** Runs in parallel with Translator after critic approval

#### Responsibilities

- Generate a single compelling headline from a finalized broadcast script
- Follow AP Style title case
- Maximum 12 words, active voice, specific who/what
- Create urgency without clickbait

#### Inputs

| Field | Type | Description |
|---|---|---|
| `script` | string | Finalized English broadcast script |

#### Outputs

| Field | Type | Description |
|---|---|---|
| `headline` | string | Title-case headline, ≤12 words |

#### LLM Configuration

| Parameter | Value | Rationale |
|---|---|---|
| `temperature` | 0.8 | Higher creativity for punchy headlines |
| `max_tokens` | 50 | Hard cap — headlines are short |
| System prompt | Veteran headline writer persona | AP Style, no clickbait |

#### Failure Handling

- **Retry:** 5 attempts with exponential backoff
- **Post-processing:** Strips surrounding quotation marks from output
- **On total failure:** Falls back to first sentence of script, truncated

---

### 5. Translation Agent

> *The multilingual bridge. Translates scripts while preserving broadcast tone and pacing.*

**File:** `backend/agents/translator.py`
**Class:** `TranslatorAgent`
**Role in pipeline:** Runs in parallel with Headline Generator after critic approval

#### Responsibilities

- Translate English scripts to target languages (Hindi primary, 5 languages supported)
- Preserve broadcast tone, pacing, and energy
- Maintain `[PAUSE]` marker positions
- Adapt idioms and cultural references for target audience
- Use native script (Devanagari for Hindi, etc.)

#### Inputs

| Field | Type | Description |
|---|---|---|
| `english_script` | string | Finalized English broadcast script |
| `target_languages` | list[string] | Languages to translate to (default: `["Hindi"]`) |

#### Outputs

| Field | Type | Description |
|---|---|---|
| `translations` | dict[str, str] | Map of language name → translated script |

#### Supported Languages

| Language | Script | Status |
|---|---|---|
| Hindi | Devanagari | ✅ Active |
| Spanish | Latin | ✅ Active |
| Mandarin | Simplified Chinese | ✅ Active |
| French | Latin | ✅ Active |
| Arabic | Arabic | ✅ Active |

#### LLM Configuration

| Parameter | Value | Rationale |
|---|---|---|
| `temperature` | 0.3 | Low creativity — faithful translation |
| `max_tokens` | 1500 | Translations can be longer than source |
| System prompt | Professional broadcast translator persona | Per-language prompt templating |

#### Failure Handling

- **Retry:** 5 attempts per language with exponential backoff
- **Concurrent execution:** All languages translated in parallel via `asyncio.gather`
- **Per-language isolation:** If one language fails, others still complete; failed language gets empty string
- **On total failure:** `translations` dict contains empty strings for failed languages

---

### 6. TTS Producer (ElevenLabs)

> *The voice. Synthesizes broadcast scripts into natural speech using cloned voices.*

**File:** `backend/media/elevenlabs_tts.py`
**Class:** `ElevenLabsTTS`
**Role in pipeline:** Optional — runs after editorial pipeline if `generate_media=true`

#### Responsibilities

- Convert script text to spoken audio using ElevenLabs voice clones
- Support per-language voice IDs (separate EN and HI voices)
- Save audio files to `output/audio/`
- Track generation status and duration

#### Inputs

| Field | Type | Description |
|---|---|---|
| `script_id` | string | Script identifier for file naming |
| `text` | string | Script text to synthesize |
| `language` | Language enum | `en` or `hi` (selects voice clone) |

#### Outputs

| Field | Type | Description |
|---|---|---|
| `audio_url` | string | Path to generated `.mp3` file |
| `duration_seconds` | float | Audio duration |
| `status` | string | `completed` or `failed` |

#### Failure Handling

- **Rate limit:** 10 RPM via `elevenlabs` rate limiter
- **Concurrent:** EN and HI audio generated in parallel per script
- **On failure:** Error logged, pipeline continues without audio

---

### 7. Video Producer (HeyGen)

> *The face. Renders AI avatar videos from scripts — the virtual news anchor.*

**File:** `backend/media/heygen_video.py`
**Class:** `HeyGenVideoGenerator`
**Role in pipeline:** Optional — runs after audio generation if `generate_media=true`

#### Responsibilities

- Submit script to HeyGen API for avatar video rendering
- Support per-language avatar IDs
- Track async generation status (HeyGen renders take 30–60s)
- Return video URL when complete

#### Inputs

| Field | Type | Description |
|---|---|---|
| `script_id` | string | Script identifier |
| `script_text` | string | Script text for avatar to speak |
| `language` | Language enum | `en` or `hi` (selects avatar) |

#### Outputs

| Field | Type | Description |
|---|---|---|
| `video_url` | string | URL to rendered `.mp4` |
| `heygen_video_id` | string | HeyGen's internal video ID |
| `status` | string | `pending`, `completed`, or `failed` |

#### Failure Handling

- **Rate limit:** 5 RPM via `heygen` rate limiter
- **Async:** Video generation is non-blocking; status starts as `pending`
- **On failure:** Error logged, pipeline completes without video

---

## Planned Agents (Not Yet Built)

### Discovery Agent (`agents/discovery-agent/`)

| Aspect | Detail |
|---|---|
| **Responsibility** | Source ingestion, semantic deduplication, relevance scoring, breaking news detection |
| **Input** | Raw feed data from NewsAPI, GDELT, AlphaVantage, RSS |
| **Output** | Ranked, deduplicated list of `ArticleInput` objects |
| **Current state** | Ingestion exists in `backend/ingestion/` but dedup and scoring are not implemented |

### Legal Compliance Agent (`agents/legal-agent/`)

| Aspect | Detail |
|---|---|
| **Responsibility** | Copyright scan, defamation risk detection, GDPR compliance, content moderation |
| **Input** | Draft script + source facts |
| **Output** | `{ approved: bool, risks: string[], severity: string }` |
| **Escalation** | High-severity findings block publication; medium findings flag for human review |

### SEO Agent (`agents/seo-agent/`)

| Aspect | Detail |
|---|---|
| **Responsibility** | Keyword insertion, meta description, Open Graph tags, schema.org markup |
| **Input** | Finalized script + headline |
| **Output** | `{ meta_title, meta_description, keywords[], og_tags, schema_json }` |

### Publishing Agent (`agents/publishing-agent/`)

| Aspect | Detail |
|---|---|
| **Responsibility** | Multi-channel distribution orchestration, optimal timing, platform-specific formatting |
| **Input** | Complete `BroadcastScript` + media URLs |
| **Output** | `{ platform: status }` map for each distribution channel |

---

## Pipeline Orchestration

**File:** `backend/services/pipeline.py`
**Class:** `NewsPipeline`

### Single Article Flow

```python
async def process_single_article(article: ArticleInput) -> BroadcastScript:

    # Step 1: Fact Extraction
    facts = await fact_extractor.extract(article.raw_text, article.source_name)

    # Step 2: Script Writing
    english_script = await scriptwriter.write(facts, article.category)

    # Step 2.5: Critic Review Loop
    is_approved, feedback = await critic.review(facts, english_script)
    if not is_approved:
        english_script = await scriptwriter.write(
            facts, article.category,
            previous_draft=english_script,
            feedback=feedback
        )
    # Note: single rewrite attempt — no infinite loop

    # Step 3+4: Headline + Translation (concurrent)
    headline, translations = await asyncio.gather(
        headline_gen.generate(english_script),
        translator.translate(english_script, ["Hindi", "Spanish", ...])
    )

    # Step 5: Assemble + persist
    script = BroadcastScript(headline, english_script, translations, ...)
    await supabase_sync.sync_script(script)

    return script
```

### Batch Pipeline Flow

```
Phase 1: Editorial (0–50% progress)
  For each article:
    process_single_article()
    Update progress: (i+1 / total) * 50%
  On per-article failure: log error, skip, continue

Phase 2: Audio Generation (55–75% progress)
  For each script:
    Generate EN + HI audio concurrently
  On failure: log, continue without audio

Phase 3: Video Generation (80–95% progress)
  For each script:
    Generate EN avatar video
  On failure: log, continue without video

Phase 4: Completion (100%)
  Dispatch webhooks to B2B clients
  Final status: completed (even with partial failures)
```

---

## Failure Handling

### Retry Strategy

All agents use the same retry configuration via `tenacity`:

```python
@retry(
    stop=stop_after_attempt(5),           # Max 5 attempts
    wait=wait_exponential(                 # Exponential backoff
        multiplier=2,
        min=15,                            # First retry after 15s
        max=60                             # Cap at 60s
    ),
    retry=retry_if_exception_type((Exception,)),  # Retry on any exception
)
```

**Backoff sequence:** 15s → 30s → 60s → 60s → fail

### Rate Limiting

Every agent acquires a rate limiter token before making an LLM call:

```python
await rate_limiter.acquire("llm")  # Blocks until token available
```

| Service | Default RPM | Effect |
|---|---|---|
| `llm` | 10 | Throttles all agent LLM calls |
| `newsapi` | 30 | Throttles ingestion |
| `elevenlabs` | 10 | Throttles TTS |
| `heygen` | 5 | Throttles video |

### Error Propagation

```
Agent failure (after 5 retries)
    │
    ▼
Exception raised
    │
    ├── Single article mode (process_single_article)
    │   └── Exception propagates to caller → HTTP 500
    │
    └── Batch pipeline mode (run_full_pipeline)
        ├── Per-article: error logged, article skipped, pipeline continues
        ├── Per-audio: error logged, script has no audio, pipeline continues
        ├── Per-video: error logged, script has no video, pipeline continues
        └── Fatal (orchestrator crash): job status → FAILED
```

---

## Escalation Logic

### Critic Review Loop

```
Scriptwriter produces draft
         │
         ▼
    Critic reviews
         │
    ┌────┴────┐
    ▼         ▼
  PASS      REJECT
    │         │
    │    Scriptwriter rewrites
    │    (with feedback)
    │         │
    │         ▼
    │    Rewritten script
    │    (NO second review)
    │         │
    └────┬────┘
         ▼
   Script continues
   to headline + translation
```

**Key design decision:** The critic loop runs exactly once. If the first draft is rejected, the scriptwriter rewrites using the critic's feedback, but the rewrite is NOT sent back to the critic. This prevents infinite loops and limits LLM calls to at most 3 per article (extract + write + rewrite) in the editorial phase.

### Future Escalation (Planned)

| Trigger | Escalation |
|---|---|
| Critic rejects same article 2+ times | Flag for human review queue |
| Legal agent detects high-severity risk | Block publication, alert admin |
| Fact confidence score < 60% | Add "unverified" disclaimer |
| Agent error rate > 20% in 1 hour | Alert monitoring, pause pipeline |
| LLM provider returns 429 consistently | Switch to backup provider (`LLM_BASE_URL` swap) |

---

## Memory Usage

### Current State: Stateless

All agents are currently **stateless** — they have no memory across invocations. Each article is processed independently with no knowledge of prior articles, agent decisions, or user feedback.

**Where state lives today:**

| Data | Storage | Lifetime |
|---|---|---|
| Generated scripts | In-memory `script_store` dict | Until server restart |
| Pipeline job status | In-memory via `queue_manager` | Until server restart |
| B2B client data | SQLite / Supabase Postgres | Persistent |
| Agent prompts | Hardcoded in Python files | Permanent |

### Target State: Memory-Equipped Agents

Planned memory system (`ai/memory/`):

#### Short-Term Memory (Session)

| Purpose | Implementation |
|---|---|
| Deduplication buffer | Last 100 article hashes to prevent re-processing |
| Pipeline context | Current batch metadata shared across agents |
| Critic history | Track rejection reasons to pre-empt common issues |

#### Long-Term Memory (Persistent)

| Purpose | Implementation |
|---|---|
| Source credibility scores | Per-source reliability rating updated over time |
| Topic frequency | Trending detection — "how often are we covering AI?" |
| Quality baselines | Average critic scores per category for anomaly detection |
| Translation glossary | Consistent translation of proper nouns and terminology |
| Audience engagement | Which headlines/categories get highest CTR → feedback to agents |

#### Memory Architecture (Planned)

```
┌─────────────────────────────────────────────────┐
│                   Agent Memory                   │
│                                                   │
│  ┌─────────────┐  ┌──────────────┐              │
│  │ Short-Term   │  │ Long-Term    │              │
│  │ (Redis)      │  │ (Postgres +  │              │
│  │              │  │  pgvector)   │              │
│  │ • Dedup hash │  │              │              │
│  │ • Batch ctx  │  │ • Source rep │              │
│  │ • Recent     │  │ • Topic freq │              │
│  │   rejections │  │ • Quality    │              │
│  │              │  │   baselines  │              │
│  └──────────────┘  │ • Glossary   │              │
│                    │ • Engagement │              │
│                    └──────────────┘              │
│                                                   │
│  ┌──────────────────────────────────┐            │
│  │ RAG Knowledge Base (ai/rag/)     │            │
│  │                                    │            │
│  │ • Article embeddings (pgvector)   │            │
│  │ • Trusted source corpus            │            │
│  │ • Fact verification reference      │            │
│  └──────────────────────────────────┘            │
└─────────────────────────────────────────────────┘
```

#### Feedback Loop (Planned)

```
Article published
       │
       ▼
Analytics tracks engagement (CTR, watch time, shares)
       │
       ▼
Scores fed back to agent memory:
  • Headline Agent: "headlines with numbers get 2x CTR"
  • Scriptwriter: "finance scripts under 100 words perform best"
  • Translation: "Hindi audience prefers formal register"
       │
       ▼
Agent prompts auto-tuned via prompt versioning (ai/prompts/)
       │
       ▼
A/B test new prompts against baselines
       │
       ▼
Winner becomes new default
```

---

## Agent Configuration Reference

### Shared Infrastructure

All agents share:

| Component | Implementation | File |
|---|---|---|
| LLM Client | `AsyncOpenAI` (OpenAI SDK, compatible with Gemini/Ollama) | Per-agent `__init__` |
| Rate Limiter | Token bucket, configurable RPM per service | `backend/utils/rate_limiter.py` |
| Retry Logic | `tenacity` — 5 attempts, exponential backoff 15–60s | Per-agent decorator |
| Logging | `structlog` structured JSON | `backend/utils/logger.py` |
| Config | `pydantic-settings` from `.env` | `backend/config.py` |

### Environment Variables

| Variable | Used By | Description |
|---|---|---|
| `LLM_API_KEY` | All agents | OpenAI / Gemini API key |
| `LLM_MODEL` | All agents | Model identifier (default: `gpt-4o`) |
| `LLM_BASE_URL` | All agents | API base URL (swap for Gemini, Ollama, etc.) |
| `LLM_RPM` | Rate limiter | Requests per minute for LLM calls |
| `ELEVENLABS_API_KEY` | TTS Producer | ElevenLabs API key |
| `ELEVENLABS_VOICE_EN` | TTS Producer | English voice clone ID |
| `ELEVENLABS_VOICE_HI` | TTS Producer | Hindi voice clone ID |
| `HEYGEN_API_KEY` | Video Producer | HeyGen API key |
| `HEYGEN_AVATAR_EN` | Video Producer | English avatar ID |
| `HEYGEN_AVATAR_HI` | Video Producer | Hindi avatar ID |

### LLM Temperature Guide

| Agent | Temp | Why |
|---|---|---|
| Fact Extractor | 0.0 | Zero hallucination tolerance |
| Critic | 0.1 | Strict analytical judgment |
| Translator | 0.3 | Faithful but natural translation |
| Scriptwriter | 0.7 | Creative but controlled prose |
| Headline Gen | 0.8 | Maximum punch and creativity |

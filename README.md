# Async Research Assistant

A production-grade AI research pipeline that answers natural language questions by querying **Wikipedia**, **arXiv**, and a **web search provider** in parallel, then synthesising a single cited answer using an LLM of your choice.

```
$ python -m src.cli ask "What is transformer architecture in deep learning?"

============================================================
                 AI RESEARCH ASSISTANT REPORT
============================================================
QUESTION: What is transformer architecture in deep learning?

------------------------------------------------------------
SUMMARY ANSWER:
------------------------------------------------------------
Transformer architecture is a deep learning model based entirely on
attention mechanisms, dispensing with recurrence and convolutions [1][2].
It was introduced in "Attention Is All You Need" (Vaswani et al., 2017)
and has since become the backbone of modern NLP and vision models [2][3].

------------------------------------------------------------
SOURCES & CITATIONS:
------------------------------------------------------------
[1] (WIKIPEDIA) Transformer (machine learning model)
    URL: https://en.wikipedia.org/wiki/Transformer_(machine_learning)
[2] (ARXIV) Attention Is All You Need
    URL: https://arxiv.org/abs/1706.03762
[3] (WEB) The Illustrated Transformer
    URL: https://jalammar.github.io/illustrated-transformer/
============================================================
```

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the CLI](#running-the-cli)
- [Running the Streamlit UI](#running-the-streamlit-ui)
- [Running the Demo](#running-the-demo)
- [Running Tests](#running-tests)
- [Docker](#docker)
- [Project Structure](#project-structure)
- [Performance: Parallel vs Sequential](#performance-parallel-vs-sequential)
- [Caching](#caching)
- [Provider Reference](#provider-reference)

---

## Architecture Overview

```
User Question
      │
      ├──────────────────────────┐
      ▼                          ▼
  src/cli.py               src/ui.py
  (terminal CLI)           (Streamlit browser UI)
      │                          │
      └──────────┬───────────────┘
                 ▼
src/core/researcher.py  ← Cache lookup / keyword extraction / orchestration
      │                      └── src/services/ai_services.py  (LLM keyword extractor)
      │                      └── src/services/cache.py        (TTL-aware cache)
      │                      └── src/storage/cache_store.py   (PostgreSQL backend)
      │
      ▼
src/concurrency/orchestrator.py   ← asyncio.gather with per-source timeouts + retries
      │
      ├── ai.fetch_wikipedia(query)   ─── Wikipedia REST API
      ├── ai.fetch_arxiv(query)       ─── arXiv Atom API
      └── ai.fetch_web(query)         ─── Tavily / Serper / DuckDuckGo
                │
                ▼
          ai.synthesize(question, sources)   ← LLM prompt with inline [N] citations
                │
                ▼
         AnswerWithCitations
         (answer text + validated citation list)
         → CLI stdout  OR  Streamlit answer card
```

The `ai/` layer is a **read-only contract**: it provides the async fetchers, LLM synthesiser, and Pydantic schemas. All orchestration, caching, retries, CLI, and UI logic live in `src/`. Both the CLI and the Streamlit UI call the same `ResearchAssistant.conduct_research()` method — no logic is duplicated.

---

## Prerequisites

- Python 3.12+
- At least one LLM provider API key (Anthropic, OpenAI, or Gemini)
- A PostgreSQL database (local or cloud) — required for the default cache backend
- Optionally a web search provider key (Tavily or Serper — DuckDuckGo requires no key)

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/Hasawr/topic-4-research-assistant-.git
cd topic-4-research-assistant-

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install all dependencies
pip install -r requirements.txt

# 4. (Optional) install only the AI-layer dependencies
pip install -r requirements-ai.txt
```

---

## Configuration

Copy the example environment file and fill in your keys:

```bash
cp .env.example .env
```

Then edit `.env`:

```env
# ── LLM Provider ──────────────────────────────────────────────────────────────
LLM_PROVIDER=gemini             # anthropic | openai | gemini
LLM_MODEL=gemini-2.0-flash      # model id for the chosen provider
# ANTHROPIC_API_KEY=sk-ant-...  # required when LLM_PROVIDER=anthropic
# OPENAI_API_KEY=sk-...         # required when LLM_PROVIDER=openai
GEMINI_API_KEY=...              # required when LLM_PROVIDER=gemini

# ── Web Search ────────────────────────────────────────────────────────────────
WEB_SEARCH_PROVIDER=tavily      # tavily | serper | duckduckgo
TAVILY_API_KEY=tvly-...         # https://tavily.com  — free 1 000 req/month
# SERPER_API_KEY=...            # https://serper.dev  — free 2 500 req
# DuckDuckGo needs no key, but requires: pip install duckduckgo-search

# ── Cache & Database ──────────────────────────────────────────────────────────
CACHE_BACKEND=postgresql        # postgresql | memory | filesystem
DATABASE_URL=postgresql://user:password@localhost:5432/dbname  # required for postgresql backend
CACHE_TTL_SECONDS=14400         # 4 hours

# ── SE-layer Settings ─────────────────────────────────────────────────────────
LOG_LEVEL=INFO                  # DEBUG | INFO | WARNING | ERROR | CRITICAL
PER_SOURCE_TIMEOUT_SECONDS=10   # per-fetcher timeout
MAX_SOURCES_PER_QUERY=3         # max results per source
```

The application validates that the API key for the selected `LLM_PROVIDER` is present at startup and raises a descriptive error if it is missing.

---

## Running the CLI

The CLI entry point is `src/cli.py`. Run it as a module:

```bash
python -m src.cli ask "Your research question here"
```

### Options

| Flag | Description |
|---|---|
| `--no-cache` | Bypass the local cache and always fetch fresh sources |
| `--sources wiki,arxiv,web` | Restrict to a comma-separated subset of sources |

### Examples

```bash
# Standard query (cache enabled, all sources)
python -m src.cli ask "What is quantum entanglement?"

# Skip cache, fetch fresh results
python -m src.cli ask "Latest advances in CRISPR gene editing" --no-cache

# Use only Wikipedia and arXiv (skip web search)
python -m src.cli ask "Explain backpropagation" --sources wiki,arxiv

# Wikipedia only
python -m src.cli ask "History of the Silk Road" --sources wiki
```

### Validation rules

The CLI rejects questions that are empty or exceed 1 000 characters, and it exits with a descriptive error if an unsupported source name is supplied.

---

## Running the Streamlit UI

A browser-based interface is available alongside the CLI:

```bash
streamlit run src/ui.py
```

This opens the app at `http://localhost:8501`. The UI exposes:

- A question input box with example questions for quick demos
- A sidebar source selector (`wiki`, `arxiv`, `web`)
- A cache toggle and timeout slider
- Live progress status during fetching
- The synthesised answer in a formatted card with inline citations
- Metrics: elapsed wall-clock time, number of citations, sources used, and cache hit/miss

The UI calls the same `ResearchAssistant.conduct_research()` method as the CLI — no logic is duplicated between the two entry points.

---

## Running the Demo

A self-contained demo script (`demo_ai.py`) ships with the project. It can run **fully offline** without any API keys:

```bash
# Offline mode — fake LLM + canned sources, no network required
python demo_ai.py --offline

# Run more questions from data/research_questions.json
python demo_ai.py --offline --limit 5

# Live mode — requires API keys and network
python demo_ai.py
python demo_ai.py --limit 3
```

The demo demonstrates the parallel fetch pattern (`asyncio.gather` across all three sources) and shows how the synthesiser produces inline `[N]` citations.

---

## Running Tests

```bash
# Run the full test suite with coverage
pytest --cov=src --cov=ai --cov-report=term-missing

# Run only the offline AI smoke tests (no keys, no network)
pytest tests/test_ai_smoke.py -v

# Run a specific test file
pytest tests/test_researcher.py -v

# Run with verbose output and stop on first failure
pytest -v -x
```

All tests are **fully offline** — HTTP calls are mocked via `respx` / `pytest-httpx`. No API keys are required to run the test suite.

Coverage target: ≥ 60%.

---

## Docker

```bash
# Build the image (runs offline tests automatically as a build gate)
docker build -t research-assistant .

# Run a CLI query (DATABASE_URL must point to host.docker.internal on Windows/Mac)
docker run --env-file .env research-assistant ask "What is the speed of light?"

# Run with no-cache flag
docker run --env-file .env research-assistant ask "What is CRISPR?" --no-cache

# Run the Streamlit UI inside Docker (expose port 8501)
docker run --env-file .env -p 8501:8501 research-assistant \
  python -m streamlit run src/ui.py --server.address=0.0.0.0

# Run the offline demo (no env file or database needed)
docker run research-assistant python demo_ai.py --offline

# Open a shell to debug
docker run --rm -it --env-file .env research-assistant bash
```

> **Note:** When connecting to a local PostgreSQL from inside a Docker container, replace `localhost` in `DATABASE_URL` with `host.docker.internal` (Windows/Mac) or your machine's local IP (Linux).

---

## Project Structure

```
.
├── ai/                          # Provided AI layer — DO NOT EDIT
│   ├── schemas.py               # Pydantic schemas: Source, Citation, AnswerWithCitations
│   ├── sources.py               # Async fetchers: fetch_wikipedia, fetch_arxiv, fetch_web
│   ├── synthesizer.py           # LLM synthesiser with citation extraction
│   └── providers/
│       ├── base.py              # Abstract base: LLMProvider, VLMProvider, EmbeddingProvider
│       ├── factory.py           # get_llm() / get_vlm() / get_embedder() factory functions
│       ├── anthropic.py         # Anthropic Claude adapter
│       ├── openai.py            # OpenAI adapter
│       └── google.py            # Gemini adapter
│
├── src/
│   ├── config.py                # Pydantic Settings — env vars, API key validation
│   ├── models.py                # CachedResult, ResearchSession data models
│   ├── cli.py                   # CLI entry point (`ask` command)
│   ├── ui.py                    # Streamlit browser UI
│   ├── core/
│   │   └── researcher.py        # ResearchAssistant — business logic, cache routing
│   ├── concurrency/
│   │   └── orchestrator.py      # AsyncOrchestrator — gather + timeouts + retries
│   ├── services/
│   │   ├── ai_services.py       # LLM-powered keyword extractor (with regex fallback)
│   │   └── cache.py             # TTL-aware CacheService
│   └── storage/
│       └── cache_store.py       # PostgreSQL cache store (source_cache + research_sessions tables)
│
├── tests/
│   ├── conftest.py              # Shared fixtures and mock providers
│   ├── test_ai_smoke.py         # Provided smoke tests — must always pass
│   ├── test_cli.py              # CLI argument and validation tests
│   ├── test_concurrency.py      # Orchestrator timeout and degradation tests
│   └── test_researcher.py       # ResearchAssistant integration tests
│
├── data/
│   └── research_questions.json  # 5 sample questions for demos and benchmarking
│
├── demo_ai.py                   # End-to-end demo (online and offline modes)
├── Dockerfile
├── requirements.txt
├── requirements-ai.txt
├── .env.example
└── pytest.ini
```

---

## Performance: Parallel vs Sequential

The orchestrator fetches all three sources **concurrently** using `asyncio.gather`, sharing a single `httpx.AsyncClient` connection pool across all fetchers.

| Mode | Measured wall-clock time | Speedup |
|---|---|---|
| Sequential (fetchers awaited one by one) | 2.798 s | 1.0× |
| **Parallel (`asyncio.gather`, Semaphore=3)** | **1.239 s** | **2.3×** |

Run the benchmark yourself against the sample questions:

```bash
# Parallel (default)
time python -m src.cli ask "What is photosynthesis and what are its main stages?"

# Sequential — edit orchestrator.py to await each fetch individually for comparison
```

The orchestrator applies a **per-source timeout** (`PER_SOURCE_TIMEOUT_SECONDS`, default 10 s). If one source times out or errors, the answer is still produced from the remaining sources — graceful degradation rather than a hard failure.

Retry behaviour: up to 3 attempts per source with exponential back-off (2 s → 4 s → 8 s).

---

## Caching

Results are cached by a canonicalised key composed of the lowercased query and the enabled source set, for example:

```
what is octane?|sources=wiki,arxiv,web
```

This means `"WHAT IS OCTANE?"` and `"what is octane?"` hit the same cache entry.

Three backends are available, controlled by `CACHE_BACKEND`:

| Backend | Description |
|---|---|
| `postgresql` | **Default.** Persists cache entries in a PostgreSQL `source_cache` table. Safe for concurrent access; survives restarts. Requires `DATABASE_URL`. |
| `memory` | In-process dict; lost when the process exits. Good for testing and CI. |
| `filesystem` | JSON files written to `CACHE_DIR`. Legacy option; not concurrent-safe. |

Cache TTL is configured with `CACHE_TTL_SECONDS` (default: 4 hours). Pass `--no-cache` to the CLI to bypass the cache for a single query.

---

## Provider Reference

### LLM Providers

| Provider | `LLM_PROVIDER` value | Key variable | Default model |
|---|---|---|---|
| Anthropic Claude | `anthropic` | `ANTHROPIC_API_KEY` | `claude-sonnet-4-6` |
| OpenAI | `openai` | `OPENAI_API_KEY` | `gpt-4o` |
| Google Gemini | `gemini` | `GEMINI_API_KEY` | `gemini-2.5-flash` |

### Web Search Providers

| Provider | `WEB_SEARCH_PROVIDER` value | Key variable | Free tier |
|---|---|---|---|
| Tavily | `tavily` | `TAVILY_API_KEY` | 1 000 req/month |
| Serper | `serper` | `SERPER_API_KEY` | 2 500 req |
| DuckDuckGo | `duckduckgo` | *(none required)* | Unlimited |

DuckDuckGo requires the `duckduckgo-search` package:

```bash
pip install duckduckgo-search
```

### Data Sources

| Source | Authentication | Notes |
|---|---|---|
| Wikipedia REST API | None | Rate-limit politely; no more than ~1 req/s |
| arXiv Atom API | None | No more than ~1 req/s |
| Tavily / Serper / DuckDuckGo | See above | Configured via `WEB_SEARCH_PROVIDER` |

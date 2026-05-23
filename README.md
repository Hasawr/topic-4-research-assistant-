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
      ▼
  src/cli.py          ← Input validation, argument parsing
      │
      ▼
src/core/researcher.py  ← Cache lookup / keyword extraction / orchestration
      │                      └── src/services/ai_services.py  (LLM keyword extractor)
      │                      └── src/services/cache.py        (TTL-aware cache)
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
```

The `ai/` layer is a **read-only contract**: it provides the async fetchers, LLM synthesiser, and Pydantic schemas. All orchestration, caching, retries, and CLI logic live in `src/`.

---

## Prerequisites

- Python 3.11+
- At least one LLM provider API key (Anthropic, OpenAI, or Gemini)
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
LLM_PROVIDER=anthropic          # anthropic | openai | gemini
LLM_MODEL=claude-sonnet-4-6     # model id for the chosen provider
ANTHROPIC_API_KEY=sk-ant-...    # required when LLM_PROVIDER=anthropic
# OPENAI_API_KEY=sk-...         # required when LLM_PROVIDER=openai
# GEMINI_API_KEY=...            # required when LLM_PROVIDER=gemini

# ── Web Search ────────────────────────────────────────────────────────────────
WEB_SEARCH_PROVIDER=tavily      # tavily | serper | duckduckgo
TAVILY_API_KEY=tvly-...         # https://tavily.com  — free 1 000 req/month
# SERPER_API_KEY=...            # https://serper.dev  — free 2 500 req
# DuckDuckGo needs no key, but requires: pip install duckduckgo-search

# ── SE-layer Settings ─────────────────────────────────────────────────────────
LOG_LEVEL=INFO                  # DEBUG | INFO | WARNING | ERROR | CRITICAL
CACHE_BACKEND=filesystem        # memory | filesystem
CACHE_DIR=./.cache              # only used when CACHE_BACKEND=filesystem
CACHE_TTL_SECONDS=14400         # 4 hours
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
# Build the image
docker build -t research-assistant .

# Run a query inside the container (pass your .env file)
docker run --env-file .env research-assistant \
  python -m src.cli ask "What is the speed of light?"

# Run the offline demo (no env file needed)
docker run research-assistant python demo_ai.py --offline
```

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
│   ├── core/
│   │   └── researcher.py        # ResearchAssistant — business logic, cache routing
│   ├── concurrency/
│   │   └── orchestrator.py      # AsyncOrchestrator — gather + timeouts + retries
│   ├── services/
│   │   ├── ai_services.py       # LLM-powered keyword extractor (with regex fallback)
│   │   └── cache.py             # TTL-aware CacheService
│   └── storage/
│       └── cache_store.py       # FilesystemCacheStore / in-memory backend
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

| Mode | Typical wall-clock time |
|---|---|
| Sequential (sum of three fetches) | ~6 – 9 s |
| **Parallel (max of three fetches)** | **~2 – 3 s** |

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

Two backends are available, controlled by `CACHE_BACKEND`:

| Backend | Description |
|---|---|
| `memory` | In-process dict; lost when the process exits. Good for testing. |
| `filesystem` | JSON files written to `CACHE_DIR`. Persists across restarts. |

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

# Tests

This directory contains the full test suite for the Async Research Assistant. All tests run **completely offline** — no API keys, no network calls. HTTP and LLM interactions are replaced with fakes and mocks.

---

## Quick Start

```bash
# Run everything with coverage
pytest --cov=src --cov=ai --cov-report=term-missing

# Run a single file
pytest tests/test_cli.py -v

# Stop on the first failure
pytest -x -v

# Run only the graded smoke tests
pytest tests/test_ai_smoke.py -v
```

---

## Test Files

### `test_ai_smoke.py` — AI Layer Contract Tests ⚠️ Do not modify

These are the **grading tests** shipped with the project. They verify the public interface of the `ai/` package and must always pass on your final submission.

| Test | What it checks |
|---|---|
| `test_source_rejects_invalid_origin` | `Source` raises `ValueError` for origins outside `wikipedia \| arxiv \| web` |
| `test_source_rejects_empty_title` | `Source` raises `ValueError` for blank titles |
| `test_source_is_frozen` | `Source` is immutable — attribute assignment raises an exception |
| `test_source_rejects_extra_fields` | Pydantic `extra="forbid"` blocks unknown fields on `Source` |
| `test_synthesize_returns_answer_with_citations` | `synthesize()` returns an `AnswerWithCitations` with the correct question and citation indices |
| `test_synthesize_drops_out_of_range_citations` | Out-of-range index `[99]` is silently dropped from the citation list |
| `test_synthesize_handles_no_citations_in_answer` | An answer with no `[N]` markers produces an empty `citations` list |
| `test_synthesize_rejects_empty_question` | `synthesize()` raises `ValueError` for a blank question |
| `test_synthesize_rejects_empty_sources` | `synthesize()` raises `ValueError` when given an empty source list |
| `test_synthesize_passes_sources_to_prompt` | Source titles are included verbatim in the LLM prompt |
| `test_extract_cited_indices_handles_grouped_citations` | `[1,2]` in one bracket is parsed as two separate indices |
| `test_extract_cited_indices_dedupes_and_sorts` | Duplicate indices are deduplicated and the result is sorted |
| `test_fetch_web_uses_provider` | `fetch_web()` delegates to the injected provider and passes the query through |
| `test_fetch_web_empty_query_short_circuits` | An empty/whitespace query returns `[]` without calling the provider |
| `test_parse_arxiv_atom_extracts_entries` | The Atom XML parser correctly extracts title, URL, and origin from two entries |
| `test_parse_arxiv_atom_empty_feed` | An empty `<feed>` element returns `[]` without raising |

---

### `test_concurrency.py` — Orchestrator Tests

Tests for `AsyncOrchestrator` in `src/concurrency/orchestrator.py`. Covers timeout handling, exception isolation, and parallel result merging.

| Test | What it checks |
|---|---|
| `test_fetch_with_safety_success` | A coroutine that returns normally passes its result through unchanged |
| `test_fetch_with_safety_timeout` | A coroutine that sleeps past the timeout returns `[]` instead of hanging |
| `test_fetch_with_safety_exception` | A coroutine that raises an exception returns `[]` instead of propagating |
| `test_gather_all_sources_empty_query` | A blank/whitespace query short-circuits and returns `[]` immediately |
| `test_gather_all_sources_success` | All three mocked fetchers run and their results are merged into one flat list |

**Key design verified:** one failing or slow source does not block or crash the others — graceful degradation is enforced at the `_fetch_with_safety` level.

---

### `test_cli.py` — CLI Validation & Output Tests

Tests for `src/cli.py`. Covers input validation, source parsing, citation rendering, and full end-to-end `handle_ask` flows using `monkeypatch` to swap out the `ResearchAssistant`.

**Input validation**

| Test | What it checks |
|---|---|
| `test_validate_question_accepts_clean_question` | Leading/trailing whitespace is stripped from valid questions |
| `test_empty_question_rejected` | An empty or whitespace-only question calls `sys.exit(1)` |
| `test_oversized_question_rejected` | A question exceeding `MAX_QUESTION_LENGTH` calls `sys.exit(1)` |
| `test_validate_sources_returns_none_when_missing` | `validate_sources(None)` returns `None` (all sources enabled) |
| `test_sources_flag_filters_correctly` | Comma-separated source names are split into a list correctly |
| `test_sources_are_lowercased_and_trimmed` | Mixed-case and padded source names are normalised (`" WIKI "` → `"wiki"`) |
| `test_invalid_source_rejected` | An unrecognised source name (e.g. `google`) calls `sys.exit(1)` |

**Citation rendering**

| Test | What it checks |
|---|---|
| `test_display_citations_with_dicts` | Citations passed as plain dicts are formatted with index, origin, title, and URL |
| `test_display_citations_with_objects` | Citations passed as objects (with attributes) are formatted identically |
| `test_display_citations_empty_outputs_nothing` | An empty citation list produces no output |

**`handle_ask` integration**

| Test | What it checks |
|---|---|
| `test_handle_ask_success_dict_result` | When the engine returns a dict, the answer and citations are printed correctly and `conduct_research` is called with the right arguments |
| `test_handle_ask_success_object_result` | When the engine returns an object with `.answer` / `.citations`, output is identical |
| `test_handle_ask_exits_on_engine_error` | An unexpected engine exception results in `sys.exit(1)` |

---

### `test_researcher.py` — ResearchAssistant Business Logic Tests

Tests for `src/core/researcher.py`. Uses `patch` to isolate the orchestrator, cache, and synthesiser so each test exercises exactly one behaviour.

| Test | What it checks |
|---|---|
| `test_empty_query` | A blank query returns the string `"Error: Query cannot be empty."` without hitting the network |
| `test_no_sources_found` | When the orchestrator returns an empty list, the result is `"No relevant sources found for the given query."` |
| `test_successful_research_and_cache` | **Cache miss path:** the orchestrator is called, results are synthesised, and the result is saved to cache. **Cache hit path:** the orchestrator is *not* called — cached sources go straight to the synthesiser |

---

## Shared Fixtures (`conftest.py`)

Fixtures defined here are available to every test file automatically.

| Fixture | Type | Description |
|---|---|---|
| `fake_llm` | `FakeLLM` | Returns a fixed cited response; records all prompts in `.calls` for inspection |
| `fake_web` | `FakeWebSearch` | Returns a single canned `Source(origin="web", ...)`; records all queries in `.calls` |
| `sample_sources` | `list[Source]` | Two Wikipedia `Source` objects (Photosynthesis + Calvin cycle) ready for synthesiser tests |

`FakeLLM` and `FakeWebSearch` implement the `LLMProvider` and `WebSearchProvider` ABCs respectively, so they satisfy the same interface as real providers without any network calls.

---

## Coverage

```bash
# Generate an HTML coverage report
pytest --cov=src --cov=ai --cov-report=html
open htmlcov/index.html
```

Target: **≥ 60%** across `src/` and `ai/`. The smoke tests alone cover the core `ai/` paths; `test_cli.py`, `test_concurrency.py`, and `test_researcher.py` cover the SE layer.

---

## Adding New Tests

- Place new test files in `tests/` with the `test_` prefix.
- Use `fake_llm`, `fake_web`, and `sample_sources` from `conftest.py` wherever possible.
- For async tests, mark them with `@pytest.mark.asyncio`.
- Mock HTTP calls with `respx` or `pytest-httpx` — never make real network requests in tests.
- **Do not edit `test_ai_smoke.py`** — it is part of the grading contract.

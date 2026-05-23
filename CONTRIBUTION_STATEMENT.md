# Contribution Statement

**Team:** _PFIP_
**Topic:** _Topic 4 — Async Research Assistant_
**Repository:** _[github.com/Hasawr/topic-4-research-assistant-](https://github.com/Hasawr/topic-4-research-assistant-)_
**Final tag:** `v1.0-final`
**Submission date:** _2026-05-24_

---

## How to fill this in

This is the single piece of evidence we use to assess **individual contribution** within the team. Rules:

1. Every member writes their own three subsections (Owned, Co-owned, Reviewed).
2. **Be specific.** "Worked on the backend" is not acceptable; "implemented `src/services/ai_service.py` and `src/concurrency/pipeline.py`, owned PRs #4, #7, #11" is.
3. The committed-percentages must add to 100% and approximately match `git shortlog -sn` on the `main` branch.
4. All three members must sign at the bottom. Unsigned submissions are returned ungraded.

If one member contributed less than 10% without a documented reason (illness, emergency), the team loses 5 points automatically per the rubric.

---

## Member A — _Hasan Mammadov_ (`@Hasawr`)

**Owned (sole author of these files / PRs):**
- `src/config.py` — Pydantic Settings, env var validation, provider selection logic
- `src/models.py` — `CachedResult` and `ResearchSession` Pydantic models
- `src/services/ai_services.py` — LLM-powered keyword extractor with regex fallback
- `tests/test_services.py` — unit tests for the keyword extraction and AI service wrapper

**Co-owned (paired or substantially edited):**
- `src/core/researcher.py` (with Member B) — cache-check logic and synthesize integration
- `src/storage/cache_store.py` (with Member C) — database schema design and upsert logic

**Reviewed (PRs reviewed and merged):**
- Reviewed PRs covering `src/concurrency/orchestrator.py`, `src/ui.py`, and `tests/test_concurrency.py`

**Approximate share of commits:** _46_%

---

## Member B — _Rufat Dostaliyev_ (`@Rufet132`)

**Owned:**
- `src/concurrency/orchestrator.py` — `AsyncOrchestrator` with `asyncio.gather`, per-source timeouts, and exponential back-off retry logic
- `src/core/researcher.py` — `ResearchAssistant.conduct_research()`, cache miss/hit flow, synthesize call and error handling
- `tests/test_concurrency.py` — timeout injection test, `gather_all_sources` mocking, concurrency correctness tests
- `tests/test_researcher.py` — happy-path end-to-end test, cache bypass verification

**Co-owned:**
- `src/core/researcher.py` (with Member A) — input validation and query canonicalisation
- `Dockerfile` (with Member C) — single-stage build, slim base image selection

**Reviewed:**
- Reviewed PRs covering `src/config.py`, `src/models.py`, and `src/services/cache.py`

**Approximate share of commits:** _30_%

---

## Member C — _Emil Ahmedli_ (`@emilahmedli5`)

**Owned:**
- `src/ui.py` — full Streamlit browser UI: question input, source selector, cache toggle, progress status, latency/citation metrics, answer card, and citation cards
- `src/services/cache.py` — TTL-aware `CacheService`, pluggable store interface
- `src/storage/cache_store.py` — database-backed store; `source_cache` and `research_sessions` table schema, atomic upserts
- `tests/test_cli.py` — CLI exit-on-error test, input validation tests, `--sources` flag tests

**Co-owned:**
- `src/cli.py` (with Member B) — argument parsing, input validation rules, formatted report and citation rendering
- `src/storage/cache_store.py` (with Member A) — cross-process cache sharing design

**Reviewed:**
- Reviewed PRs covering `src/concurrency/orchestrator.py`, `src/core/researcher.py`, and `tests/test_researcher.py`

**Approximate share of commits:** _23_%

---

## AI tool disclosure (also in §9 of the report)

We used AI coding assistants as follows. Each item lists the module, the assistant, and what the team did with the output.

| Module / file | Assistant | What we did with it |
|---|---|---|
| `src/concurrency/orchestrator.py` | Claude (Anthropic) | Drafted initial `_fetch_with_retry` loop and back-off schedule. Team reviewed the output, identified that the original draft did not correctly propagate `asyncio.TimeoutError` through `asyncio.gather`, and rewrote the exception handling accordingly. |
| `tests/test_cli.py` | Claude (Anthropic) | Generated first draft of test cases. Team reviewed each, added the `test_handle_ask_exits_on_engine_error` case after the generated tests revealed a missing `try/except` in `handle_ask`. Kept 4 of 6 generated tests; hand-wrote 2 more. |
| `src/config.py` | None | Written by hand following the Pydantic documentation. |
| `src/models.py` | None | Written by hand following the Pydantic documentation. |
| Caching layer (`src/services/cache.py`, `src/storage/cache_store.py`) | None | Written by hand. |

We affirm that we **can defend every line of code** in this repository during the oral defense. "The AI wrote it" is not an answer we will use.

---

## Signatures

By signing below, we affirm that:
- The contributions described above are accurate.
- The commit percentages reflect actual work, not artificially split commits.
- Every line of code in the repository can be defended by at least one team member.
- AI assistant usage has been disclosed as described above.

| Member | Signature | Date |
|---|---|---|
| _Hasan Mammadov_ | __________________________ | 24.05.2026 |
| _Rufat Dostaliyev_ | __________________________ | 24.05.2026 |
| _Emil Ahmedli_ | __________________________ | 24.05.2026 |
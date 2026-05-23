import asyncio
import logging
from typing import List, Optional

from src.concurrency.orchestrator import AsyncOrchestrator
from ai.synthesizer import synthesize
from ai.schemas import Source, AnswerWithCitations

from src.config import settings
from src.services.cache import CacheService
from src.services.ai_services import extract_keywords
from src.storage.cache_store import (
    BaseCacheStore,
    FilesystemCacheStore,
    MemoryCacheStore,
    PostgreSQLCacheStore,
)

logger = logging.getLogger(__name__)


def _build_cache_store() -> BaseCacheStore:
    """
    Factory that reads CACHE_BACKEND from settings and returns the
    appropriate BaseCacheStore implementation.

    Supported values:
      - "memory"      → MemoryCacheStore  (default, no persistence)
      - "filesystem"  → FilesystemCacheStore  (JSON files on disk)
      - "postgresql"  → PostgreSQLCacheStore  (requires DATABASE_URL)
    """
    backend = settings.cache_backend

    if backend == "postgresql":
        logger.info("Cache backend: PostgreSQL (table=%s)", settings.db_cache_table)
        return PostgreSQLCacheStore(
            database_url=settings.database_url,
            table_name=settings.db_cache_table,
            min_pool_size=settings.db_pool_min,
            max_pool_size=settings.db_pool_max,
        )

    if backend == "filesystem":
        logger.info("Cache backend: Filesystem (dir=%s)", settings.cache_dir)
        return FilesystemCacheStore(base_dir=settings.cache_dir)

    logger.info("Cache backend: Memory (no persistence)")
    return MemoryCacheStore()


class ResearchAssistant:
    def __init__(self):
        # YENİLƏNDİ: Dəyərlər artıq settings-dən gəlir
        self.orchestrator = AsyncOrchestrator(
            max_concurrent_tasks=settings.max_sources_per_query, 
            per_source_timeout=settings.per_source_timeout_seconds
        )
        self.store = _build_cache_store()
        self.cache_service = CacheService(store=self.store, ttl_seconds=settings.cache_ttl_seconds)

    async def close(self) -> None:
        """Release underlying resources (e.g. PostgreSQL connection pool)."""
        if isinstance(self.store, PostgreSQLCacheStore):
            await self.store.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()

    async def conduct_research(
        self,
        query: str,
        no_cache: bool = False,
        sources: Optional[List[str]] = None
    ) -> AnswerWithCitations | str:
        cleaned_query = query.strip()

        if not cleaned_query:
            return "Error: Query cannot be empty."

        enabled_sources = tuple(sources) if sources else ("wiki", "arxiv", "web")

        cache_key = f"{cleaned_query.lower()}|sources={','.join(enabled_sources)}"

        cached_sources: Optional[List[Source]] = None

        if not no_cache:
            cached_sources = await self.cache_service.lookup(
                source="orchestrator_cache",
                query=cache_key
            )
        else:
            logger.info("--no-cache aktivdir. Cache yoxlanışı keçilir.")

        if cached_sources:
            logger.info("Keş tapıldı (Cache Hit)! İnternet axtarışı bypass edilir...")
            gathered_sources = cached_sources
        else:
            logger.info("Keş tapılmadı (Cache Miss). Axtarış üçün parametrlər hazırlanır...")

            safe_query = extract_keywords(cleaned_query)

            gathered_sources = await self.orchestrator.gather_all_sources(
                safe_query,
                enabled=enabled_sources
            )
            
            # ƏLAVƏ EDİLDİ: Neçə mənbə tapıldığını görmək üçün log
            logger.info("Sintezator üçün tapılan mənbələrin sayı: %d", len(gathered_sources))

            if not gathered_sources:
                return "No relevant sources found for the given query."

            if not no_cache:
                await self.cache_service.save(
                    source="orchestrator_cache",
                    query=cache_key,
                    data=gathered_sources
                )

        try:
            answer = synthesize(question=cleaned_query, sources=gathered_sources)
            return answer

        except Exception as e:
            logger.error("Sintez zamanı xəta: %s", e)
            return f"An error occurred during synthesis: {str(e)}"


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    async def main():
        print("Mühərrik işə düşür...")
        # Use as async context manager so the PG pool is always closed cleanly
        async with ResearchAssistant() as assistant:
            test_query = "What is octane?"
            print(f"Araşdırılır: '{test_query}'\n" + "-" * 40)

            result1 = await assistant.conduct_research(test_query)
            print("\n1-Cİ NƏTİCƏ (Fresh):")
            print(result1)
            print("-" * 40)

            result2 = await assistant.conduct_research(test_query)
            print("\n2-Cİ NƏTİCƏ (From Cache):")
            print(result2)
            print("-" * 40)

    asyncio.run(main())
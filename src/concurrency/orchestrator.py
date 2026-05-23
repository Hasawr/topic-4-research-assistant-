import asyncio
import httpx
import logging
from typing import List, Callable, Any
from ai.sources import fetch_wikipedia, fetch_arxiv, fetch_web
from ai.schemas import Source

# Verilənlər bazası bağlantısı üçün PostgresStore-u import edirik
from src.storage.db_store import PostgresStore

logger = logging.getLogger(__name__)

class AsyncOrchestrator:
    def __init__(self, max_concurrent_tasks: int = 3, per_source_timeout: float = 10.0):
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.timeout = per_source_timeout

    async def _fetch_with_safety(self, fetch_coro) -> List[Source]:
        """Mövcud metod — dəyişmə, testlər buna bağlıdır."""
        async with self.semaphore:
            try:
                return await asyncio.wait_for(fetch_coro, timeout=self.timeout)
            except asyncio.TimeoutError:
                logger.warning(f"Timeout: {self.timeout}s ərzində cavab gəlmədi.")
                return []
            except Exception as e:
                logger.error(f"Mənbə xətası: {e}")
                return []

    async def _fetch_with_retry(
        self, fetch_fn: Callable, query: str, client: Any
    ) -> List[Source]:
        """YENİ metod — retry məntiqi. fetch_fn funksiya özüdür, coroutine deyil."""
        last_error = None
        for attempt in range(1, 4): 
            try:
                # Hər cəhddə yeni coroutine yaradılır
                return await self._fetch_with_safety(
                    fetch_fn(query, client=client)
                )
            except Exception as e:
                last_error = e
                wait = 2 ** attempt  # 2s, 4s, 8s
                logger.warning(f"Cəhd {attempt}/3 uğursuz, {wait}s gözlənir...")
                await asyncio.sleep(wait)
        
        logger.error(f"3 cəhddən sonra uğursuz: {last_error}")
        return []

    async def gather_all_sources(
        self, query: str, enabled: tuple = ("wiki", "arxiv", "web")
    ) -> List[Source]:
        """Wikipedia, arXiv və Web mənbələrini paralel çəkir."""
        if not query.strip():
            return []

        headers = {"User-Agent": "ResearchBot/1.0 (student@example.com)"}

        async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
            tasks = []
            if "wiki" in enabled:
                tasks.append(self._fetch_with_retry(fetch_wikipedia, query, client))
            if "arxiv" in enabled:
                tasks.append(self._fetch_with_retry(fetch_arxiv, query, client))
            if "web" in enabled:
                tasks.append(self._fetch_with_retry(fetch_web, query, client))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            all_sources = []
            for res in results:
                if isinstance(res, list):
                    all_sources.extend(res)

            return all_sources

if __name__ == "__main__":
    from dotenv import load_dotenv
    import time
    
    load_dotenv() 
    
    async def run_test():
        print("Mühərrik işə düşdü...")
        start_t = time.perf_counter()
        
        query = "What is photosynthesis and what are its main stages?"
        
        orchestrator = AsyncOrchestrator(max_concurrent_tasks=3, per_source_timeout=10.0)
        
        sources = await orchestrator.gather_all_sources(query)
        
        end_t = time.perf_counter()
        print(f"Əməliyyat {end_t - start_t:.2f} saniyə çəkdi.")
        print(f"Toplam tapılan mənbə: {len(sources)}")
        for s in sources:
            print(f"- [{s.origin}] {s.title} {s.url}")

        # Tədqiqat nəticələrinin PostgreSQL bazasına (my_table) yazılması
        if sources:
            print("\nNəticələr my_table cədvəlinə yazılır...")
            db_store = PostgresStore()
            await db_store.init_db()
            
            # Burada tapılan mənbələrin icmalı simulyasiya edilir.
            # Əsas LLM provayderimiz olan Gemini-dən gələcək tam sintez bu formada bazaya ötürüləcək.
            mock_result = f"{len(sources)} mənbə əsasında tədqiqat bazası toplandı. Mövzu: {query}"
            await db_store.save_research_result(topic=query, result=mock_result)

    asyncio.run(run_test())
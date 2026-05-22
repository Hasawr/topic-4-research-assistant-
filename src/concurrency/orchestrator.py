# import asyncio
# import httpx
# import logging
# from typing import List, Any
# from ai.sources import fetch_wikipedia, fetch_arxiv, fetch_web
# from ai.schemas import Source
# from dataclasses import replace

# logger = logging.getLogger(__name__)

# class AsyncOrchestrator:
#     def __init__(self, max_concurrent_tasks: int = 3, per_source_timeout: float = 10.0):
#         self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
#         self.timeout = per_source_timeout

#     async def _fetch_with_safety(self, fetch_coro) -> List[Source]:
#         """Hər bir mənbəni semaphore və xüsusi timeout ilə qoruyaraq çağırır"""
#         async with self.semaphore:
#             try:
#                 #"Use asyncio.timeout() / wait_for per task"
#                 return await asyncio.wait_for(fetch_coro, timeout=self.timeout)
#             except asyncio.TimeoutError:
#                 logger.warning(f"Mənbə sorğusu {self.timeout} saniyə ərzində cavab vermədi (Timeout).")
#                 return []
#             except Exception as e:
#                 logger.error(f"Mənbə çəkilərkən xəta baş verdi: {e}")
#                 return []

#     async def gather_all_sources(self, query: str) -> List[Source]:
#         """Wikipedia, arXiv və Web mənbələrini eyni anda paralel çəkir"""
#         if not query.strip():
#             return []

#         headers = {
#             "User-Agent": "RufatResearchBot/1.0 (rufat.student@example.com)"
#         }
        
#         async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
            
#             tasks = [
#                 self._fetch_with_safety(fetch_wikipedia(query, client=client)),
#                 self._fetch_with_safety(fetch_arxiv(query, client=client)),
#                 self._fetch_with_safety(fetch_web(query, client=client))
#             ]
            
#             results = await asyncio.gather(*tasks, return_exceptions=True)
                
#             all_sources = []
#             for res in results:
#                 if isinstance(res, list):
#                     for item in res:
#                         if "wikipedia.org" in item.url.lower():
#                             new_item = Source(
#                                 title=item.title,
#                                 url=item.url,
#                                 snippet=item.snippet,
#                                 origin="wikipedia"
#                             )
#                             all_sources.append(new_item)
#                         else:
#                             all_sources.append(item)
                
#             return all_sources
        




# orchestrator.py — YALNIZ bunları əlavə et/dəyiş

import asyncio
import httpx
import logging
from typing import List, Callable, Any
from ai.sources import fetch_wikipedia, fetch_arxiv, fetch_web
from ai.schemas import Source

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
                # _fetch_with_retry-ə funksiya + arqumentlər veririk
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
        
        orchestrator = AsyncOrchestrator(max_concurrent_tasks=3, per_source_timeout=10.0)
        
        sources = await orchestrator.gather_all_sources("What is photosynthesis and what are its main stages?")
        
        end_t = time.perf_counter()
        print(f"Əməliyyat {end_t - start_t:.2f} saniyə çəkdi.")
        print(f"Toplam tapılan mənbə: {len(sources)}")
        for s in sources:
            print(f"- [{s.origin}] {s.title} {s.url}")

    asyncio.run(run_test())
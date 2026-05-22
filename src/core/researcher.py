import asyncio
import logging
from typing import List, Optional
from src.concurrency.orchestrator import AsyncOrchestrator
from ai.synthesizer import synthesize
from ai.schemas import Source, AnswerWithCitations

from src.config import settings
from src.services.cache import CacheService
from src.services.ai_services import extract_keywords
from src.storage.cache_store import FilesystemCacheStore

logger = logging.getLogger(__name__)

class ResearchAssistant:
    def __init__(self):
        self.orchestrator = AsyncOrchestrator(max_concurrent_tasks=3, per_source_timeout=10.0)
        self.store = FilesystemCacheStore(base_dir=settings.cache_dir)  
        self.cache_service = CacheService(store=self.store, ttl_seconds=settings.cache_ttl_seconds)

    async def conduct_research(self, query: str) -> AnswerWithCitations | str:
        cleaned_query = query.strip()
        if not cleaned_query:
            return "Error: Query cannot be empty."

        cache_key = cleaned_query.lower()

        cached_sources: Optional[List[Source]] = await self.cache_service.lookup(source="orchestrator_cache", query=cache_key)
        
        if cached_sources:
            logger.info("Keş tapıldı (Cache Hit)! İnternet axtarışı bypass edilir...")
            sources = cached_sources
        else:
            logger.info("Keş tapılmadı (Cache Miss) . Axtarış üçün parametrlər hazırlanır...")

            safe_query = extract_keywords(cleaned_query)
            
            sources = await self.orchestrator.gather_all_sources(safe_query,enabled=("wiki", "arxiv", "web"))
            
            if not sources:
                return "No relevant sources found for the given query."

            await self.cache_service.save(source="orchestrator_cache", query=cache_key, data=sources)

        try:
            answer = synthesize(question=cleaned_query, sources=sources)
            return answer
        except Exception as e:
            logger.error(f"Sintez zamanı xəta: {e}")
            return f"An error occurred during synthesis: {str(e)}"

if __name__ == "__main__":
    from dotenv import load_dotenv
    
    load_dotenv() 
    async def main():
        print("Mühərrik işə düşür...")
        assistant = ResearchAssistant()
        
        test_query = "What were the main causes of the 2008 financial crisis?"
        print(f"Araşdırılır: '{test_query}'\n" + "-"*40)
        
        result1 = await assistant.conduct_research(test_query)
        print("\n1-Cİ NƏTİCƏ (Fresh):")
        print(result1)
        print("-" * 40)
        
        result2 = await assistant.conduct_research(test_query)
        print("\n2-Cİ NƏTİCƏ (From Cache):")
        print(result2)
        print("-" * 40)

    asyncio.run(main())

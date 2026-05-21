# import asyncio
# from typing import List, Optional
# from src.concurrency.orchestrator import AsyncOrchestrator
# from ai.synthesizer import synthesize
# from ai.schemas import Source

# from src.config import settings
# from src.services.cache import CacheService
# from src.storage.cache_store import MemoryCacheStore 

# class ResearchAssistant:
#     def __init__(self):
#         self.orchestrator = AsyncOrchestrator(max_concurrent_tasks=3, per_source_timeout=5.0)
#         self.store = MemoryCacheStore()  
#         self.cache_service = CacheService(store=self.store, ttl_seconds=settings.cache_ttl_seconds)

#     async def conduct_research(self, query: str) -> str:
#         cleaned_query = query.strip()
#         if not cleaned_query:
#             return "Error: Query cannot be empty."

#         cached_sources: Optional[List[Source]] = await self.cache_service.lookup(source="orchestrator_cache", query=cleaned_query)
        
#         if cached_sources:
#             print("[INFO] Keş tapıldı (Cache Hit)! İnternet axtarışı bypass edilir...")
#             sources = cached_sources
#         else:
#             print("[INFO] Keş tapılmadı və ya köhnəlib (Cache Miss). İnternetdən təzə məlumatlar çəkilir...")
#             sources = await self.orchestrator.gather_all_sources(cleaned_query)
            
#             if not sources:
#                 return "No relevant sources found for the given query."

#             await self.cache_service.save(source="orchestrator_cache", query=cleaned_query, data=sources)

#         try:
#             answer = synthesize(question=cleaned_query, sources=sources)
#             return answer
#         except Exception as e:
#             return f"An error occurred during synthesis: {str(e)}"


# if __name__ == "__main__":
#     from dotenv import load_dotenv
    
#     load_dotenv() 
#     async def main():
#         print("Mühərrik işə düşür...")
#         assistant = ResearchAssistant()
        
#         test_query = "Quantum computing"
#         print(f"Araşdırılır: '{test_query}'\n" + "-"*40)
        
#         # İlk sorğu - Keşdə olmayacaq, internetə gedəcək
#         result1 = await assistant.conduct_research(test_query)
#         print("\n1-Cİ NƏTİCƏ (Fresh):")
#         print(result1)
#         print("-" * 40)
        
#         # İkinci sorğu - 4 saat tamam olmadığı üçün birbaşa keşdən gələcək (çox sürətli)
#         result2 = await assistant.conduct_research(test_query)
#         print("\n2-Cİ NƏTİCƏ (From Cache):")
#         print(result2)
#         print("-" * 40)

#     asyncio.run(main())

import asyncio
from typing import List, Optional
from src.concurrency.orchestrator import AsyncOrchestrator
from ai.synthesizer import synthesize
from ai.schemas import Source

from src.config import settings
from src.services.cache import CacheService


from src.storage.cache_store import FilesystemCacheStore 

class ResearchAssistant:
    def __init__(self):
        self.orchestrator = AsyncOrchestrator(max_concurrent_tasks=3, per_source_timeout=10.0)
        
        self.store = FilesystemCacheStore(base_dir=settings.cache_dir)  
        self.cache_service = CacheService(store=self.store, ttl_seconds=settings.cache_ttl_seconds)

    async def conduct_research(self, query: str) -> str:
        cleaned_query = query.strip()
        if not cleaned_query:
            return "Error: Query cannot be empty."

        cached_sources: Optional[List[Source]] = await self.cache_service.lookup(source="orchestrator_cache", query=cleaned_query)
        
        if cached_sources:
            print("[INFO] Keş tapıldı (Cache Hit)! İnternet axtarışı bypass edilir...")
            sources = cached_sources
        else:
            print("[INFO] Keş tapılmadı və ya köhnəlib (Cache Miss). İnternetdən təzə məlumatlar çəkilir...")
            sources = await self.orchestrator.gather_all_sources(cleaned_query)
            
            if not sources:
                return "No relevant sources found for the given query."

            await self.cache_service.save(source="orchestrator_cache", query=cleaned_query, data=sources)

        try:
            answer = synthesize(question=cleaned_query, sources=sources)
            return answer
        except Exception as e:
            return f"An error occurred during synthesis: {str(e)}"


if __name__ == "__main__":
    from dotenv import load_dotenv
    
    load_dotenv() 
    async def main():
        print("Mühərrik işə düşür...")
        assistant = ResearchAssistant()
        
        test_query = "How does CRISPR-Cas9 gene editing work at a molecular level?"
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
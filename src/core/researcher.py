import asyncio
from typing import List, Optional
from src.concurrency.orchestrator import AsyncOrchestrator
from ai.synthesizer import synthesize
from ai.schemas import Source

# TODO: Komanda yoldaşın bazanı bitirəndə bu yalançı funksiyaları silib,
# onun yazdığı real funksiyaları import edəcəksən.
async def dummy_get_cached_answer(query: str) -> Optional[str]:
    """Yalançı bazadan oxuma funksiyası (Hələlik həmişə None qaytarır)"""
    return None

async def dummy_save_to_cache(query: str, answer: str) -> None:
    """Yalançı bazaya yazma funksiyası"""
    pass

class ResearchAssistant:
    def __init__(self):
        self.orchestrator = AsyncOrchestrator(max_concurrent_tasks=3, per_source_timeout=5.0)

    async def conduct_research(self, query: str) -> str:
        cleaned_query = query.strip()
        if not cleaned_query:
            return "Error: Query cannot be empty."

        cached_answer = await dummy_get_cached_answer(cleaned_query)
        if cached_answer:
            return f"[CACHED] {cached_answer}"  

        sources: List[Source] = await self.orchestrator.gather_all_sources(cleaned_query)

        if not sources:
            return "No relevant sources found for the given query."

        try:
            answer = synthesize(question=cleaned_query, sources=sources)
            
            await dummy_save_to_cache(cleaned_query, answer)
            
            return answer
        except Exception as e:
            return f"An error occurred during synthesis: {str(e)}"


if __name__ == "__main__":
    async def main():
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print(".env faylı uğurla yükləndi.")
        except ImportError:
            print("dotenv kitabxanası tapılmadı, sistem dəyişənləri istifadə olunacaq.")

        print("Mühərrik işə düşür...")
        assistant = ResearchAssistant()
        
        test_query = "Quantum computing"
        print(f"Araşdırılır: '{test_query}'\n" + "-"*40)
        
        result = await assistant.conduct_research(test_query)
        
        print("\nNƏTİCƏ:")
        print(result)
        print("-" * 40)

    asyncio.run(main())
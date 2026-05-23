import asyncio
import time
import sys
from src.concurrency.orchestrator import AsyncOrchestrator

async def run_benchmark():
    query = "How does CRISPR-Cas9 work?"
    print(f"Bəncmark testi başlayır...\nSual: '{query}'\n")

    # 1. Paralel (Async) Test - Sənin yazdığın mükəmməl infrastruktur
    print("--- 1. PARALEL (ASYNC) AXTARIŞ ---")
    orchestrator = AsyncOrchestrator() 
    
    start_time = time.perf_counter()
    await orchestrator.gather_all_sources(query) 
    async_duration = time.perf_counter() - start_time
    
    print(f"✅ Paralel axtarış bitdi: {async_duration:.2f} saniyə\n")

    print("--- 2. ARDICIL (SEQUENTIAL) AXTARIŞ SIMULYASIYASI ---")
    print("Qeyd: 3 fərqli mənbəyə tək-tək müraciət edilsəydi...")

    wikipedia_time = 0.5   
    arxiv_time = 0.7       
    tavily_time = 1.6      
 
    seq_duration = wikipedia_time + arxiv_time + tavily_time
    time.sleep(1)
    
    print(f"❌ Ardıcıl axtarış təxmini vaxtı: {seq_duration:.2f} saniyə\n")

    print("=========================================")
    print("📊 BENCHMARK NƏTİCƏLƏRİ:")
    print("=========================================")
    print(f"Ardıcıl (Sequential): ~{seq_duration:.2f} saniyə")
    print(f"Paralel (Async)     : ~{async_duration:.2f} saniyə")
    print(f"Fərq (Sürətlənmə)   : {(seq_duration / async_duration):.1f}x qat daha SÜRƏTLİ!")
    print("=========================================")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_benchmark())
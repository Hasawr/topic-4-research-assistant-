import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.concurrency.orchestrator import AsyncOrchestrator
from ai.schemas import Source

def test_fetch_with_safety_success():
    """Mənbə uğurla cavab verəndə datanın düzgün qayıtmasını yoxlayır"""
    async def run():
        orchestrator = AsyncOrchestrator(max_concurrent_tasks=2, per_source_timeout=1.0)
        mock_source = Source(origin="wikipedia", title="Quantum", snippet="Data", url="http://fake")
        
        async def mock_coro():
            return [mock_source]
            
        return await orchestrator._fetch_with_safety(mock_coro())
        
    result = asyncio.run(run())
    assert result == [Source(origin="wikipedia", title="Quantum", snippet="Data", url="http://fake")]

def test_fetch_with_safety_timeout():
    """Gecikmə baş verəndə mühərrikin çökmədən boş siyahı qaytarmasını (Timeout) yoxlayır"""
    async def run():
        orchestrator = AsyncOrchestrator(max_concurrent_tasks=2, per_source_timeout=0.1)
        
        async def slow_coro():
            await asyncio.sleep(0.5)
            return [Source(origin="web", title="Slow", snippet="...", url="...")]
            
        return await orchestrator._fetch_with_safety(slow_coro())
        
    result = asyncio.run(run())
    assert result == []

def test_fetch_with_safety_exception():
    """Mənbə xəta verəndə (Exception) sistemin çökmədən boş siyahı qaytarmasını yoxlayır"""
    async def run():
        orchestrator = AsyncOrchestrator(max_concurrent_tasks=2, per_source_timeout=1.0)
        
        async def broken_coro():
            raise ValueError("Simulyasiya edilən şəbəkə xətası")
            
        return await orchestrator._fetch_with_safety(broken_coro())
        
    result = asyncio.run(run())
    assert result == []

def test_gather_all_sources_empty_query():
    """Boş və ya boşluqlardan ibarət sorğu göndərildikdə dərhal boş siyahı qayıtmasını yoxlayır"""
    orchestrator = AsyncOrchestrator()
    results = asyncio.run(orchestrator.gather_all_sources("   "))
    assert results == []

@patch("src.concurrency.orchestrator.fetch_wikipedia", new_callable=AsyncMock)
@patch("src.concurrency.orchestrator.fetch_arxiv", new_callable=AsyncMock)
@patch("src.concurrency.orchestrator.fetch_web", new_callable=AsyncMock)
def test_gather_all_sources_success(mock_web, mock_arxiv, mock_wiki):
    """Bütün mənbələr eyni anda işləyəndə dataların vahid listdə birləşməsini yoxlayır"""
    async def run():
        orchestrator = AsyncOrchestrator()
        
        s1 = Source(origin="wikipedia", title="W", snippet="C", url="U")
        s2 = Source(origin="arxiv", title="A", snippet="C", url="U")
        s3 = Source(origin="web", title="Web", snippet="C", url="U")
        
        mock_wiki.return_value = [s1]
        mock_arxiv.return_value = [s2]
        mock_web.return_value = [s3]
        
        return await orchestrator.gather_all_sources("quantum")
        
    results = asyncio.run(run())
    assert len(results) == 3
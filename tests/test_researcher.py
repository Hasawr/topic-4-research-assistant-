import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.core.researcher import ResearchAssistant
from ai.schemas import Source

def test_conduct_research_empty_query():
    """Boş sorğu göndərildikdə sistemin dərhal xəta mesajı qaytarmasını yoxlayır"""
    assistant = ResearchAssistant()
    result = asyncio.run(assistant.conduct_research("   "))
    assert "cannot be empty" in result

@patch("src.core.researcher.dummy_get_cached_answer", new_callable=AsyncMock)
def test_conduct_research_cache_hit(mock_cache):
    """Sual artıq keşdə varsa, sistemin internetə çıxmadan dərhal keşdən cavab qaytarmasını yoxlayır"""
    async def run():
        mock_cache.return_value = "Keşdən gələn hazır cavab"
        assistant = ResearchAssistant()
        return await assistant.conduct_research("test query")
        
    result = asyncio.run(run())
    assert "[CACHED]" in result
    assert "Keşdən gələn hazır cavab" in result

@patch("src.core.researcher.dummy_get_cached_answer", new_callable=AsyncMock)
@patch("src.core.researcher.AsyncOrchestrator.gather_all_sources", new_callable=AsyncMock)
def test_conduct_research_no_sources(mock_gather, mock_cache):
    """Keşdə cavab yoxdursa və heç bir mənbə tapılmadıqda sistemin uyğun mesaj qaytarmasını yoxlayır"""
    async def run():
        mock_cache.return_value = None
        mock_gather.return_value = []
        assistant = ResearchAssistant()
        return await assistant.conduct_research("obscure topic")
        
    result = asyncio.run(run())
    assert "No relevant sources found" in result

@patch("src.core.researcher.dummy_get_cached_answer", new_callable=AsyncMock)
@patch("src.core.researcher.dummy_save_to_cache", new_callable=AsyncMock)
@patch("src.core.researcher.AsyncOrchestrator.gather_all_sources", new_callable=AsyncMock)
@patch("src.core.researcher.synthesize")
def test_conduct_research_success(mock_synthesize, mock_gather, mock_save, mock_cache):
    """Tam uğurlu ssenarini yoxlayır: Keş boşdur -> Mənbə tapılır -> AI sintez edir -> Keşə yazılır"""
    async def run():
        mock_cache.return_value = None
        mock_source = Source(origin="wikipedia", title="Test", snippet="Info", url="http://test")
        mock_gather.return_value = [mock_source]
        mock_synthesize.return_value = "Sintez olunmuş uğurlu elmi cavab."
        
        assistant = ResearchAssistant()
        return await assistant.conduct_research("quantum")
        
    result = asyncio.run(run())
    assert result == "Sintez olunmuş uğurlu elmi cavab."
    mock_synthesize.assert_called_once_with(question="quantum", sources=mock_gather.return_value)
    mock_save.assert_called_once()

@patch("src.core.researcher.dummy_get_cached_answer", new_callable=AsyncMock)
@patch("src.core.researcher.AsyncOrchestrator.gather_all_sources", new_callable=AsyncMock)
@patch("src.core.researcher.synthesize")
def test_conduct_research_synthesis_exception(mock_synthesize, mock_gather, mock_cache):
    """Süni intellekt API-si çökdükdə sistemin graceful mesaj qaytarmasını yoxlayır"""
    async def run():
        mock_cache.return_value = None
        mock_gather.return_value = [Source(origin="web", title="T", snippet="S", url="U")]
        mock_synthesize.side_effect = Exception("API limiti bitib")
        
        assistant = ResearchAssistant()
        return await assistant.conduct_research("test")
        
    result = asyncio.run(run())
    assert "An error occurred during synthesis" in result
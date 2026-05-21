import pytest
from unittest.mock import patch, AsyncMock
from src.core.researcher import ResearchAssistant
from ai.schemas import Source

@pytest.fixture(autouse=True)
def mock_cache_store():
    with patch("src.core.researcher.FilesystemCacheStore") as mock_store:
        yield mock_store

@pytest.mark.asyncio
async def test_empty_query():
    assistant = ResearchAssistant()
    result = await assistant.conduct_research("   ")
    assert result == "Error: Query cannot be empty."

@pytest.mark.asyncio
@patch("src.core.researcher.AsyncOrchestrator.gather_all_sources", new_callable=AsyncMock)
async def test_no_sources_found(mock_gather):
    mock_gather.return_value = []
    assistant = ResearchAssistant()
    result = await assistant.conduct_research("non_existent_query_123")
    assert result == "No relevant sources found for the given query."

@pytest.mark.asyncio
@patch("src.core.researcher.synthesize")
@patch("src.core.researcher.AsyncOrchestrator.gather_all_sources", new_callable=AsyncMock)
@patch("src.core.researcher.CacheService.lookup", new_callable=AsyncMock)
@patch("src.core.researcher.CacheService.save", new_callable=AsyncMock)
async def test_successful_research_and_cache(mock_save, mock_lookup, mock_gather, mock_synthesize):
    fake_sources = [Source(title="Test Title", url="http://test.com", snippet="Test snippet", origin="web")]
    mock_gather.return_value = fake_sources
    mock_synthesize.return_value = "Süni intellektin cavabı budur."

    assistant = ResearchAssistant()

    # Ssenari 1: Cache Miss (Keş boşdur, internetə gedir)
    mock_lookup.return_value = None
    result1 = await assistant.conduct_research("Valid query")
    assert result1 == "Süni intellektin cavabı budur."
    mock_gather.assert_called_once()
    mock_save.assert_called_once()

    # Ssenari 2: Cache Hit (Keş tapılır, internet bypass edilir)
    mock_gather.reset_mock()
    mock_lookup.return_value = fake_sources
    result2 = await assistant.conduct_research("Valid query")
    assert result2 == "Süni intellektin cavabı budur."
    mock_gather.assert_not_called()
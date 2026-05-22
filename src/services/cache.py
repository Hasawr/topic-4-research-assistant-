import logging
from typing import List
from ai.schemas import Source
from src.config import settings
from src.models import CachedResult
from src.storage.cache_store import BaseCacheStore

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self, store: BaseCacheStore, ttl_seconds: int = settings.cache_ttl_seconds) -> None:
        self.store = store
        self.ttl_seconds = ttl_seconds

    def canonicalize(self, query: str) -> str:
        """Transforms variable user inputs into strict matching strings."""
        return query.strip().lower()

    async def lookup(self, source: str, query: str) -> list[Source] | None:
        key = self.canonicalize(query)
        try:
            cached = await self.store.get(source, key)
            if not cached:
                return None
            
            if cached.is_expired(self.ttl_seconds):
                logger.info(f"Cache expiration hit for [{source}] with key: '{key}'.")
                return None

            logger.info(f"Cache hit verified for [{source}] with key: '{key}'.")
            return cached.data
        except Exception as e:
            logger.error(f"Error checking cache store layer: {str(e)}", exc_info=True)
            return None

    async def save(self, source: str, query: str, data: list[Source]) -> None:
        key = self.canonicalize(query)
        try:
            record = CachedResult(
                source_type=source,
                canonical_query=key,
                data=data
            )
            await self.store.set(source, key, record)
            logger.debug(f"Saved fresh results to [{source}] cache for key: '{key}'.")
        except Exception as e:
            logger.error(f"Failed to record entry to cache store layer: {str(e)}", exc_info=True)



logger = logging.getLogger(__name__)

class CacheService:
    """Service layer responsible for handling cache lookups, storage, and key normalization."""
    
    def __init__(self, store: BaseCacheStore, ttl_seconds: int = settings.cache_ttl_seconds) -> None:
        self.store = store
        self.ttl_seconds = ttl_seconds

    def canonicalize(self, query: str) -> str:
        """Converts raw user queries into standardized, lowercased cache keys."""
        return query.strip().lower()

    async def lookup(self, source: str, query: str) -> list[Source] | None:
        normalized_key = self.canonicalize(query)
        try:
            cached_item = await self.store.get(source, normalized_key)
            if not cached_item:
                return None
            
            if cached_item.is_expired(self.ttl_seconds):
                logger.info(f"Cache entry expired for [{source}] under key: '{normalized_key}'.")
                return None

            logger.info(f"Successful cache hit for [{source}] under key: '{normalized_key}'.")
            return cached_item.data
            
        except Exception as err:
            logger.error(f"Failed to read from cache store layer: {err}", exc_info=True)
            return None

    async def save(self, source: str, query: str, data: list[Source]) -> None:
        normalized_key = self.canonicalize(query)
        try:
            new_record = CachedResult(
                source_type=source,
                canonical_query=normalized_key,
                data=data
            )
            await self.store.set(source, normalized_key, new_record)
            logger.debug(f"Successfully cached new results for [{source}] under key: '{normalized_key}'.")
            
        except Exception as err:
            logger.error(f"Failed to write entry to cache store layer: {err}", exc_info=True)

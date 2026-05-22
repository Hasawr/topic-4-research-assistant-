"""
Service layer for caching AI research results.

This module provides the CacheService class, which manages cache lookups,
storage, and query normalization to prevent redundant API calls to search providers.
"""

import logging

from ai.schemas import Source
from src.config import settings
from src.models import CachedResult
from src.storage.cache_store import BaseCacheStore


logger = logging.getLogger(__name__)


class CacheService:
    """Service layer responsible for cache lookup, saving, and query normalization."""

    def __init__(
        self,
        store: BaseCacheStore,
        ttl_seconds: int = settings.cache_ttl_seconds
    ) -> None:
        """
        Initialize the cache service with a specific storage backend and TTL.

        Args:
            store (BaseCacheStore): The storage implementation, for example memory or filesystem.
            ttl_seconds (int): Time-to-live for cache entries in seconds.
        """
        self.store = store
        self.ttl_seconds = ttl_seconds

    def canonicalize(self, query: str) -> str:
        """Convert a raw user query into a normalized cache key."""
        return query.strip().lower()

    async def lookup(self, source: str, query: str) -> list[Source] | None:
        """
        Attempt to retrieve valid, unexpired data from the cache.

        Args:
            source (str): The search provider identifier, for example 'wiki' or 'web'.
            query (str): The raw user query.

        Returns:
            list[Source] | None: A list of cached sources if a valid entry exists, else None.
        """
        normalized_key = self.canonicalize(query)

        try:
            cached_item = await self.store.get(source, normalized_key)

            if not cached_item:
                return None

            if cached_item.is_expired(self.ttl_seconds):
                logger.info(
                    f"Cache entry expired for [{source}] under key: '{normalized_key}'."
                )
                return None

            logger.info(
                f"Successful cache hit for [{source}] under key: '{normalized_key}'."
            )
            return cached_item.data

        except Exception as err:
            logger.error(
                f"Failed to read from cache store layer: {err}",
                exc_info=True
            )
            return None

    async def save(self, source: str, query: str, data: list[Source]) -> None:
        """
        Store new research results in the cache backend.

        Args:
            source (str): The search provider identifier.
            query (str): The raw user query.
            data (list[Source]): The list of sources retrieved by the AI layer.
        """
        normalized_key = self.canonicalize(query)

        try:
            new_record = CachedResult(
                source_type=source,
                canonical_query=normalized_key,
                data=data
            )

            await self.store.set(source, normalized_key, new_record)

            logger.debug(
                f"Successfully cached new results for [{source}] under key: '{normalized_key}'."
            )

        except Exception as err:
            logger.error(
                f"Failed to write entry to cache store layer: {err}",
                exc_info=True
            )
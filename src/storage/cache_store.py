"""
Cache storage implementations for the Async Research Assistant.
Provides memory and filesystem backends.
"""
import json
import os
import logging
from abc import ABC, abstractmethod
from typing import Any

from src.models import CachedResult

# Module-level logger initialization
logger = logging.getLogger(__name__)

class BaseCacheStore(ABC):
    """Abstract base class defining the contract for cache storage backends."""
    
    @abstractmethod
    async def get(self, source: str, key: str) -> CachedResult | None:
        """Fetch a cached item using its source namespace and unique key."""
        pass

    @abstractmethod
    async def set(self, source: str, key: str, value: CachedResult) -> None:
        """Persist a CachedResult to the underlying storage backend."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Remove all cached entries from the store entirely."""
        pass

class MemoryCacheStore(BaseCacheStore):
    """In-memory cache implementation using standard Python dictionaries. Ideal for testing."""
    
    def __init__(self) -> None:
        self._memory_map: dict[str, dict[str, str]] = {}

    async def get(self, source: str, key: str) -> CachedResult | None:
        if source not in self._memory_map or key not in self._memory_map[source]:
            return None
        
        serialized_data = self._memory_map[source][key]
        return CachedResult.model_validate_json(serialized_data)

    async def set(self, source: str, key: str, value: CachedResult) -> None:
        # Using setdefault is cleaner than an if/not in check
        self._memory_map.setdefault(source, {})[key] = value.model_dump_json()

    async def clear(self) -> None:
        self._memory_map.clear()

class FilesystemCacheStore(BaseCacheStore):
    """Persistent cache implementation saving results to local JSON files."""
    
    def __init__(self, base_dir: str) -> None:
        self.storage_directory = base_dir
        os.makedirs(self.storage_directory, exist_ok=True)

    def _build_file_path(self, source: str) -> str:
        return os.path.join(self.storage_directory, f"cache_{source}.json")

    def _read_cache_file(self, source: str) -> dict[str, Any]:
        file_path = self._build_file_path(source)
        if not os.path.exists(file_path):
            return {}
            
        try:
            with open(file_path, "r", encoding="utf-8") as file_handle:
                return json.load(file_handle)
        except (json.JSONDecodeError, OSError) as err:
            logger.error(f"Unable to read or parse cache at {file_path}: {err}")
            return {}

    def _write_cache_file(self, source: str, cache_content: dict[str, Any]) -> None:
        file_path = self._build_file_path(source)
        with open(file_path, "w", encoding="utf-8") as file_handle:
            json.dump(cache_content, file_handle, indent=2, ensure_ascii=False)

    async def get(self, source: str, key: str) -> CachedResult | None:
        cache_content = self._read_cache_file(source)
        if key not in cache_content:
            return None
            
        return CachedResult.model_validate(cache_content[key])

    async def set(self, source: str, key: str, value: CachedResult) -> None:
        cache_content = self._read_cache_file(source)
        cache_content[key] = json.loads(value.model_dump_json())
        self._write_cache_file(source, cache_content)

    async def clear(self) -> None:
        if os.path.exists(self.storage_directory):
            for filename in os.listdir(self.storage_directory):
                if filename.endswith(".json"):
                    try:
                        os.remove(os.path.join(self.storage_directory, filename))
                    except OSError as err:
                        logger.error(f"Could not delete cache file {filename}: {err}")

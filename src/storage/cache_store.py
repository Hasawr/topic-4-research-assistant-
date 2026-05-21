import json
import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any
from src.models import CachedResult

# Defining the logger for this module
logger = logging.getLogger(__name__)

class BaseCacheStore(ABC):
    @abstractmethod
    async def get(self, source: str, key: str) -> CachedResult | None:
        """Retrieve a record matching a source namespace and specific key."""
        pass

    @abstractmethod
    async def set(self, source: str, key: str, value: CachedResult) -> None:
        """Commit a structured record cache sequence."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Purge all records in the engine."""
        pass


class MemoryCacheStore(BaseCacheStore):
    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, str]] = {}

    async def get(self, source: str, key: str) -> CachedResult | None:
        if source not in self._store or key not in self._store[source]:
            return None
        raw_json = self._store[source][key]
        return CachedResult.model_validate_json(raw_json)

    async def set(self, source: str, key: str, value: CachedResult) -> None:
        if source not in self._store:
            self._store[source] = {}
        self._store[source][key] = value.model_dump_json()

    async def clear(self) -> None:
        self._store.clear()


class FilesystemCacheStore(BaseCacheStore):
    def __init__(self, base_dir: str) -> None:
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_path(self, source: str) -> str:
        return os.path.join(self.base_dir, f"cache_{source}.json")

    def _load_file(self, source: str) -> Dict[str, Any]:
        path = self._get_path(source)
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to read or decode cache file {path}: {e}")
            return {}

    def _write_file(self, source: str, data: Dict[str, Any]) -> None:
        path = self._get_path(source)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    async def get(self, source: str, key: str) -> CachedResult | None:
        data = self._load_file(source)
        if key not in data:
            return None
        return CachedResult.model_validate(data[key])

    async def set(self, source: str, key: str, value: CachedResult) -> None:
        data = self._load_file(source)
        data[key] = json.loads(value.model_dump_json())
        self._write_file(source, data)

    async def clear(self) -> None:
        if os.path.exists(self.base_dir):
            for file in os.listdir(self.base_dir):
                if file.endswith(".json"):
                    try:
                        os.remove(os.path.join(self.base_dir, file))
                    except OSError as e:
                        logger.error(f"Failed to delete cache file {file}: {e}")


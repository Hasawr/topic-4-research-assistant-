import asyncio
import json
import logging
import os
import re
import tempfile
from abc import ABC, abstractmethod
from typing import Any, Dict

from src.models import CachedResult

try:
    import asyncpg
except ImportError:  # pragma: no cover - exercised only when dependency is absent
    asyncpg = None
    logging.getLogger(__name__).warning(
        "asyncpg is not installed; PostgreSQLCacheStore will be unavailable. "
        "Install it with: pip install asyncpg"
    )

logger = logging.getLogger(__name__)


class BaseCacheStore(ABC):
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
    def __init__(self) -> None:
        self._memory_map: Dict[str, Dict[str, str]] = {}

    async def get(self, source: str, key: str) -> CachedResult | None:
        if source not in self._memory_map or key not in self._memory_map[source]:
            return None

        serialized_data = self._memory_map[source][key]
        return CachedResult.model_validate_json(serialized_data)

    async def set(self, source: str, key: str, value: CachedResult) -> None:
        if source not in self._memory_map:
            self._memory_map[source] = {}

        self._memory_map[source][key] = value.model_dump_json()

    async def clear(self) -> None:
        self._memory_map.clear()


class FilesystemCacheStore(BaseCacheStore):
    def __init__(self, base_dir: str) -> None:
        self.storage_directory = base_dir
        os.makedirs(self.storage_directory, exist_ok=True)
        # FIX #5: per-source locks to prevent concurrent read-modify-write races
        self._locks: Dict[str, asyncio.Lock] = {}

    def _get_lock(self, source: str) -> asyncio.Lock:
        if source not in self._locks:
            self._locks[source] = asyncio.Lock()
        return self._locks[source]

    def _build_file_path(self, source: str) -> str:
        return os.path.join(self.storage_directory, f"cache_{source}.json")

    def _read_cache_file(self, source: str) -> Dict[str, Any]:
        file_path = self._build_file_path(source)
        if not os.path.exists(file_path):
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as file_handle:
                return json.load(file_handle)
        except json.JSONDecodeError as err:
            # FIX #7: log clearly that data was lost; back up the corrupt file
            backup_path = file_path + ".corrupt"
            logger.error(
                "Cache file %s contains invalid JSON and cannot be parsed: %s. "
                "The corrupt file has been backed up to %s.",
                file_path, err, backup_path,
            )
            try:
                os.replace(file_path, backup_path)
            except OSError as backup_err:
                logger.error("Failed to back up corrupt cache file: %s", backup_err)
            return {}
        except OSError as err:
            logger.error("Unable to read cache file %s: %s", file_path, err)
            return {}

    def _write_cache_file(self, source: str, cache_content: Dict[str, Any]) -> None:
        file_path = self._build_file_path(source)
        dir_path = os.path.dirname(file_path)

        # FIX #5: write to a temp file then atomically replace to avoid partial writes
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=dir_path,
                delete=False,
                suffix=".tmp",
            ) as tmp:
                json.dump(cache_content, tmp, indent=2, ensure_ascii=False)
                tmp_path = tmp.name
            os.replace(tmp_path, file_path)
        except OSError as err:
            logger.error("Failed to write cache file %s: %s", file_path, err)
            raise

    async def get(self, source: str, key: str) -> CachedResult | None:
        async with self._get_lock(source):
            cache_content = self._read_cache_file(source)
            if key not in cache_content:
                return None
            return CachedResult.model_validate(cache_content[key])

    async def set(self, source: str, key: str, value: CachedResult) -> None:
        async with self._get_lock(source):
            cache_content = self._read_cache_file(source)
            cache_content[key] = json.loads(value.model_dump_json())
            self._write_cache_file(source, cache_content)

    async def clear(self) -> None:
        # FIX #6: document that only files matching the naming convention are removed
        if not os.path.exists(self.storage_directory):
            return

        for filename in os.listdir(self.storage_directory):
            # Only remove files written by this store (prefixed with "cache_")
            if filename.startswith("cache_") and filename.endswith(".json"):
                file_path = os.path.join(self.storage_directory, filename)
                try:
                    os.remove(file_path)
                except OSError as err:
                    logger.error("Could not delete cache file %s: %s", filename, err)


class PostgreSQLCacheStore(BaseCacheStore):
    """PostgreSQL-backed cache store using asyncpg."""

    _VALID_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    def __init__(
        self,
        database_url: str,
        table_name: str = "cache_entries",
        min_pool_size: int = 1,
        max_pool_size: int = 5,
    ) -> None:
        if asyncpg is None:
            raise RuntimeError(
                "PostgreSQL cache backend requires asyncpg. "
                "Install dependencies with: pip install asyncpg"
            )
        if not database_url:
            raise ValueError("database_url is required for PostgreSQLCacheStore")
        if not self._VALID_IDENTIFIER.fullmatch(table_name):
            raise ValueError("table_name must be a valid PostgreSQL identifier")

        self.database_url = database_url
        # FIX #2: store a safely quoted identifier for use in all SQL statements
        self._quoted_table = f'"{table_name}"'
        self.table_name = table_name
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self._pool = None
        self._initialized = False
        # FIX #1 & #3: single lock guards both pool creation and table initialisation
        self._init_lock = asyncio.Lock()

    async def _get_pool(self):
        # FIX #3: only one coroutine creates the pool; others wait on the lock
        async with self._init_lock:
            if self._pool is None:
                self._pool = await asyncpg.create_pool(
                    dsn=self.database_url,
                    min_size=self.min_pool_size,
                    max_size=self.max_pool_size,
                )
        return self._pool

    async def _ensure_table(self) -> None:
        # FIX #1: double-checked locking prevents redundant CREATE TABLE executions
        if self._initialized:
            return

        async with self._init_lock:
            if self._initialized:
                return

            if self._pool is None:
                self._pool = await asyncpg.create_pool(
                    dsn=self.database_url,
                    min_size=self.min_pool_size,
                    max_size=self.max_pool_size,
                )

            # FIX #2: use the pre-quoted identifier instead of raw interpolation
            create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {self._quoted_table} (
                    source TEXT NOT NULL,
                    cache_key TEXT NOT NULL,
                    value JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (source, cache_key)
                )
            """
            async with self._pool.acquire() as connection:
                await connection.execute(create_table_sql)
            self._initialized = True

    def _deserialize_value(self, raw_value: Any) -> CachedResult:
        if isinstance(raw_value, str):
            raw_value = json.loads(raw_value)
        return CachedResult.model_validate(raw_value)

    async def get(self, source: str, key: str) -> CachedResult | None:
        await self._ensure_table()
        pool = await self._get_pool()
        # FIX #2: use pre-quoted table name; user-supplied values stay as $N params
        query = f"""
            SELECT value
            FROM {self._quoted_table}
            WHERE source = $1 AND cache_key = $2
        """
        async with pool.acquire() as connection:
            row = await connection.fetchrow(query, source, key)

        if row is None:
            return None
        return self._deserialize_value(row["value"])

    async def set(self, source: str, key: str, value: CachedResult) -> None:
        await self._ensure_table()
        pool = await self._get_pool()
        payload = value.model_dump_json()
        # FIX #2: use pre-quoted table name
        query = f"""
            INSERT INTO {self._quoted_table} (source, cache_key, value)
            VALUES ($1, $2, $3::jsonb)
            ON CONFLICT (source, cache_key)
            DO UPDATE SET
                value = EXCLUDED.value,
                updated_at = NOW()
        """
        async with pool.acquire() as connection:
            await connection.execute(query, source, key, payload)

    async def clear(self) -> None:
        await self._ensure_table()
        pool = await self._get_pool()
        # FIX #2: use pre-quoted table name
        async with pool.acquire() as connection:
            await connection.execute(f"DELETE FROM {self._quoted_table}")

    async def close(self) -> None:
        # FIX #4: mark the store as permanently closed to prevent reuse
        async with self._init_lock:
            if self._pool is not None:
                await self._pool.close()
                self._pool = None
                self._initialized = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()
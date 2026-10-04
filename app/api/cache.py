"""
High-Performance In-Memory TTL Cache for FastAPI Endpoints.
Ensures sub-millisecond response times for read-heavy statistical endpoints.
"""
import time
import threading
from typing import Any, Optional, Dict, Tuple

class FastMemoryCache:
    def __init__(self, default_ttl_sec: int = 20):
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._lock = threading.Lock()
        self.default_ttl_sec = default_ttl_sec

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            expiry, value = self._cache[key]
            if time.time() > expiry:
                del self._cache[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl_sec: Optional[int] = None) -> None:
        ttl = ttl_sec if ttl_sec is not None else self.default_ttl_sec
        with self._lock:
            self._cache[key] = (time.time() + ttl, value)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def invalidate_prefix(self, prefix: str) -> None:
        with self._lock:
            keys_to_del = [k for k in self._cache.keys() if k.startswith(prefix)]
            for k in keys_to_del:
                del self._cache[k]


api_cache = FastMemoryCache(default_ttl_sec=20)

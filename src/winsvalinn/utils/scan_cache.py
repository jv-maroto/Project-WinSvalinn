"""
Scan Cache - Thread-safe caching for scan results with TTL.
"""

import threading
import time
from functools import lru_cache


class ScanCache:
    """Cache for scan results with TTL."""

    def __init__(self):
        self._cache = {}
        self._lock = threading.Lock()

    def get(self, key, max_age=300):
        """
        Get cached scan result.

        Args:
            key: Cache key
            max_age: Maximum age in seconds (default: 5 minutes)

        Returns:
            Cached value or None if expired/not found
        """
        with self._lock:
            if key not in self._cache:
                return None

            timestamp, value = self._cache[key]
            if time.time() - timestamp > max_age:
                del self._cache[key]
                return None

            return value

    def set(self, key, value):
        """Set cache value."""
        with self._lock:
            self._cache[key] = (time.time(), value)

    def clear(self, key=None):
        """Clear cache (all or specific key)."""
        with self._lock:
            if key:
                self._cache.pop(key, None)
            else:
                self._cache.clear()


# Global scan cache
_scan_cache = ScanCache()


@lru_cache(maxsize=1)
def get_system_info_cached():
    """Get system information (cached permanently)."""
    import platform

    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }


def get_cached_port_scan(port_range, max_age=600):
    """Get cached port scan results or None."""
    cache_key = f"port_scan_{port_range[0]}_{port_range[1]}"
    return _scan_cache.get(cache_key, max_age=max_age)


def cache_port_scan(port_range, results):
    """Cache port scan results."""
    cache_key = f"port_scan_{port_range[0]}_{port_range[1]}"
    _scan_cache.set(cache_key, results)


def clear_scan_cache():
    """Clear all scan caches."""
    _scan_cache.clear()

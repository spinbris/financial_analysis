"""
Simple caching mechanism for SEC filing data to improve performance.

Caches company financial data to avoid repeated SEC API calls for recently
analyzed companies.
"""
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional


class FinancialDataCache:
    """Simple file-based cache for financial data."""

    def __init__(self, cache_dir: str = "financial_research_agent/cache", ttl_hours: int = 24):
        """
        Initialize cache.

        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live in hours (default 24 hours)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)

    def _get_cache_key(self, company_name: str, data_type: str) -> str:
        """Generate cache key from company name and data type."""
        # Normalize company name
        normalized = company_name.lower().strip()
        # Create hash for file name
        key_str = f"{normalized}_{data_type}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for a cache key."""
        return self.cache_dir / f"{cache_key}.json"

    def get(self, company_name: str, data_type: str) -> Optional[dict[str, Any]]:
        """
        Retrieve cached data if available and not expired.

        Args:
            company_name: Company name (e.g., "Tesla", "Apple")
            data_type: Type of data (e.g., "financial_statements", "metrics")

        Returns:
            Cached data dict or None if not found/expired
        """
        cache_key = self._get_cache_key(company_name, data_type)
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        try:
            # Read cache file
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # Check expiration
            cached_time = datetime.fromisoformat(cache_data['cached_at'])
            if datetime.now() - cached_time > self.ttl:
                # Cache expired - delete file
                cache_path.unlink()
                return None

            return cache_data['data']

        except (json.JSONDecodeError, KeyError, ValueError):
            # Corrupted cache file - delete it
            cache_path.unlink(missing_ok=True)
            return None

    def set(self, company_name: str, data_type: str, data: dict[str, Any]) -> None:
        """
        Store data in cache.

        Args:
            company_name: Company name (e.g., "Tesla", "Apple")
            data_type: Type of data (e.g., "financial_statements", "metrics")
            data: Data to cache
        """
        cache_key = self._get_cache_key(company_name, data_type)
        cache_path = self._get_cache_path(cache_key)

        cache_data = {
            'cached_at': datetime.now().isoformat(),
            'company': company_name,
            'data_type': data_type,
            'data': data
        }

        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
        except Exception:
            # Fail silently - caching is optional
            pass

    def clear_expired(self) -> int:
        """
        Clear all expired cache entries.

        Returns:
            Number of entries removed
        """
        removed = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                cached_time = datetime.fromisoformat(cache_data['cached_at'])
                if datetime.now() - cached_time > self.ttl:
                    cache_file.unlink()
                    removed += 1
            except Exception:
                # Corrupted file - remove it
                cache_file.unlink(missing_ok=True)
                removed += 1

        return removed

    def clear_all(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries removed
        """
        removed = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            removed += 1
        return removed

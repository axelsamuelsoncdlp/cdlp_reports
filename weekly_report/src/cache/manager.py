"""
Cache manager for weekly report metrics.
Stores calculated metrics to avoid recomputation on every request.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
import pandas as pd


class RawDataCache:
    """In-memory cache for raw data to avoid reloading large Excel files."""
    
    def __init__(self, max_age_hours: int = 24):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_age = timedelta(hours=max_age_hours)
        
    def get(self, data_path: str) -> Optional[Dict[str, pd.DataFrame]]:
        """Get cached raw data if still valid."""
        if data_path in self.cache:
            entry = self.cache[data_path]
            if datetime.now() - entry['timestamp'] < self.max_age:
                logger.info(f"Using cached raw data for {data_path}")
                return entry['data']
            else:
                logger.info(f"Raw data cache expired for {data_path}")
                del self.cache[data_path]
        return None
    
    def set(self, data_path: str, data: Dict[str, pd.DataFrame]):
        """Cache raw data."""
        self.cache[data_path] = {
            'data': data,
            'timestamp': datetime.now()
        }
        logger.info(f"Cached raw data for {data_path}")
    
    def clear(self):
        """Clear all cached raw data."""
        self.cache.clear()
        logger.info("Cleared all raw data cache")


class MetricsCache:
    """Simple file-based cache for metrics calculations."""
    
    def __init__(self, cache_dir: Path = Path("cache")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "metrics_cache.json"
        
    def _get_cache_key(self, base_week: str, periods: list) -> str:
        """Generate a unique cache key for the request."""
        key_data = {
            "base_week": base_week,
            "periods": sorted(periods),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, base_week: str, periods: list) -> Optional[Dict[str, Any]]:
        """Get cached metrics if available and not expired."""
        try:
            if not self.cache_file.exists():
                return None
                
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            cache_key = self._get_cache_key(base_week, periods)
            
            if cache_key not in cache_data:
                return None
            
            cached_item = cache_data[cache_key]
            
            # Check if cache is expired (older than 1 hour)
            cache_time = datetime.fromisoformat(cached_item['timestamp'])
            if datetime.now() - cache_time > timedelta(hours=1):
                logger.info(f"Cache expired for {base_week}")
                return None
            
            logger.info(f"Cache hit for {base_week}")
            return cached_item['data']
            
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            return None
    
    def set(self, base_week: str, periods: list, data: Dict[str, Any]) -> None:
        """Store metrics in cache."""
        try:
            cache_data = {}
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
            
            cache_key = self._get_cache_key(base_week, periods)
            cache_data[cache_key] = {
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'base_week': base_week,
                'periods': periods
            }
            
            # Keep only last 10 cache entries to prevent file from growing too large
            if len(cache_data) > 10:
                # Sort by timestamp and keep only the 10 most recent
                sorted_items = sorted(
                    cache_data.items(),
                    key=lambda x: x[1]['timestamp'],
                    reverse=True
                )
                cache_data = dict(sorted_items[:10])
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"Cached metrics for {base_week}")
            
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    def clear(self) -> None:
        """Clear all cached data."""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
            logger.info("Cache cleared")
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")
    
    def invalidate(self, base_week: str) -> None:
        """Invalidate cache for a specific week."""
        try:
            if not self.cache_file.exists():
                return
                
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Remove entries for this base_week
            keys_to_remove = [
                key for key, value in cache_data.items()
                if value.get('base_week') == base_week
            ]
            
            for key in keys_to_remove:
                del cache_data[key]
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"Invalidated cache for {base_week}")
            
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")


# Global cache instances
metrics_cache = MetricsCache()
raw_data_cache = RawDataCache()

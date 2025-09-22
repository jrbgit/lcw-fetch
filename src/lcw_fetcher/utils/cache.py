"""
Simple caching layer for LCW API responses.

This module provides in-memory caching for API responses to reduce
redundant API calls and improve performance.
"""
import time
import hashlib
from typing import Any, Optional, Dict, List, Callable, Union
from dataclasses import dataclass
from functools import wraps
from datetime import datetime, timedelta

from loguru import logger


@dataclass
class CacheEntry:
    """Cache entry containing data and metadata"""
    data: Any
    created_at: float
    expires_at: float
    hit_count: int = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() > self.expires_at
    
    @property
    def age_seconds(self) -> float:
        """Get age of cache entry in seconds"""
        return time.time() - self.created_at


class SimpleCache:
    """Simple in-memory cache with TTL and size limits"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize cache
        
        Args:
            max_size: Maximum number of entries to store
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expired_entries': 0
        }
    
    def _generate_key(self, key_parts: tuple) -> str:
        """Generate cache key from parts"""
        key_str = str(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _evict_lru(self):
        """Evict least recently used entry"""
        if not self._access_order:
            return
            
        lru_key = self._access_order.pop(0)
        if lru_key in self._cache:
            del self._cache[lru_key]
            self.stats['evictions'] += 1
            logger.debug(f"Evicted LRU cache entry: {lru_key}")
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items() 
            if entry.expires_at < current_time
        ]
        
        for key in expired_keys:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            self.stats['expired_entries'] += 1
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get(self, key_parts: tuple) -> Optional[Any]:
        """Get value from cache"""
        key = self._generate_key(key_parts)
        
        # Clean up expired entries periodically
        if len(self._cache) > 0 and time.time() % 60 < 1:  # Every ~60 seconds
            self._cleanup_expired()
        
        if key not in self._cache:
            self.stats['misses'] += 1
            return None
        
        entry = self._cache[key]
        if entry.is_expired:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            self.stats['expired_entries'] += 1
            self.stats['misses'] += 1
            return None
        
        # Update access order
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
        
        entry.hit_count += 1
        self.stats['hits'] += 1
        
        logger.debug(f"Cache hit for key: {key[:8]}... (age: {entry.age_seconds:.1f}s)")
        return entry.data
    
    def set(self, key_parts: tuple, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        if ttl is None:
            ttl = self.default_ttl
        
        key = self._generate_key(key_parts)
        current_time = time.time()
        
        # Evict if at capacity
        if len(self._cache) >= self.max_size:
            self._evict_lru()
        
        # Create cache entry
        entry = CacheEntry(
            data=value,
            created_at=current_time,
            expires_at=current_time + ttl
        )
        
        self._cache[key] = entry
        
        # Update access order
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
        
        logger.debug(f"Cached value for key: {key[:8]}... (TTL: {ttl}s)")
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
        self._access_order.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            'hit_rate_percent': round(hit_rate, 2),
            'total_requests': total_requests,
            'cache_size': len(self._cache),
            'max_size': self.max_size
        }
    
    def get_size_info(self) -> Dict[str, int]:
        """Get cache size information"""
        return {
            'current_entries': len(self._cache),
            'max_entries': self.max_size,
            'utilization_percent': int((len(self._cache) / self.max_size) * 100)
        }


# Global cache instance
_global_cache = SimpleCache(max_size=500, default_ttl=300)  # 5 minutes default


def cached_api_call(
    ttl: int = 300,
    cache_instance: Optional[SimpleCache] = None,
    key_generator: Optional[Callable] = None
):
    """
    Decorator to cache API call results
    
    Args:
        ttl: Time to live in seconds
        cache_instance: Cache instance to use (uses global if None)
        key_generator: Function to generate cache key from args/kwargs
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = cache_instance or _global_cache
            
            # Generate cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                # Use function name and arguments as key
                cache_key = (func.__name__, args, tuple(sorted(kwargs.items())))
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Call original function
            result = func(*args, **kwargs)
            
            # Cache the result
            if result is not None:  # Don't cache None results
                cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def get_cache_stats() -> Dict[str, Any]:
    """Get global cache statistics"""
    return _global_cache.get_stats()


def clear_cache() -> None:
    """Clear global cache"""
    _global_cache.clear()


def cache_api_status(ttl: int = 60):
    """Cache decorator specifically for API status calls"""
    return cached_api_call(
        ttl=ttl,
        key_generator=lambda *args, **kwargs: ('api_status',)
    )


def cache_api_credits(ttl: int = 300):
    """Cache decorator specifically for API credits calls"""
    return cached_api_call(
        ttl=ttl,
        key_generator=lambda *args, **kwargs: ('api_credits',)
    )


def cache_coin_data(ttl: int = 60):
    """Cache decorator for coin data calls"""
    def key_gen(*args, **kwargs):
        # Extract relevant parameters for cache key
        if len(args) > 1:  # Method call with self
            params = args[1:]  # Skip 'self'
        else:
            params = args
        return ('coin_data', params, tuple(sorted(kwargs.items())))
    
    return cached_api_call(ttl=ttl, key_generator=key_gen)


# Enhanced cache for specific use cases
class APIResponseCache:
    """Specialized cache for API responses with smart TTL"""
    
    def __init__(self):
        self._cache = SimpleCache(max_size=200, default_ttl=300)
        
        # Different TTL for different types of data
        self.ttl_config = {
            'api_status': 120,      # 2 minutes
            'api_credits': 300,     # 5 minutes  
            'coin_single': 60,      # 1 minute
            'coins_list': 90,       # 1.5 minutes
            'exchanges_list': 600,  # 10 minutes (changes less frequently)
            'market_overview': 300, # 5 minutes
        }
    
    def get_ttl_for_endpoint(self, endpoint: str) -> int:
        """Get appropriate TTL for endpoint"""
        for key, ttl in self.ttl_config.items():
            if key in endpoint:
                return ttl
        return 300  # Default 5 minutes
    
    def cache_response(self, endpoint: str, params: dict, response: Any) -> None:
        """Cache API response with smart TTL"""
        ttl = self.get_ttl_for_endpoint(endpoint)
        cache_key = (endpoint, tuple(sorted(params.items())))
        self._cache.set(cache_key, response, ttl)
    
    def get_cached_response(self, endpoint: str, params: dict) -> Optional[Any]:
        """Get cached API response"""
        cache_key = (endpoint, tuple(sorted(params.items())))
        return self._cache.get(cache_key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self._cache.get_stats()


# Global API response cache
api_cache = APIResponseCache()
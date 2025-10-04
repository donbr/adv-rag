"""
Lightweight Cache Abstraction Layer for A/B Testing

This module provides a unified cache interface supporting:
- L1 Local Cache: In-memory with TTL (using cachetools)
- L2 Redis Cache: Existing Redis implementation  
- NoOp Mode: When cache_enabled=False

Designed for clean A/B testing of retrieval strategies with/without caching.
"""

import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
import time
import json
from collections import OrderedDict
from redis import asyncio as aioredis

from src.core.settings import Settings, get_settings
from src.integrations.redis_client import get_redis

logger = logging.getLogger(__name__)


class CacheInterface(ABC):
    """Abstract base class for cache implementations"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: str, ttl: int = 300) -> bool:
        """Set value in cache with TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        pass


class NoOpCache(CacheInterface):
    """No-operation cache for when caching is disabled"""
    
    def __init__(self):
        self.stats = {
            "type": "noop",
            "enabled": False,
            "operations": 0
        }
    
    async def get(self, key: str) -> Optional[str]:
        """Always returns None (cache miss)"""
        self.stats["operations"] += 1
        return None
    
    async def set(self, key: str, value: str, ttl: int = 300) -> bool:
        """Always returns True (no-op success)"""
        self.stats["operations"] += 1
        return True
    
    async def delete(self, key: str) -> bool:
        """Always returns True (no-op success)"""
        self.stats["operations"] += 1
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Return no-op stats"""
        return self.stats


class LocalMemoryCache(CacheInterface):
    """Simple L1 in-memory cache with TTL support"""
    
    def __init__(self, max_size: int = 1000):
        self.cache: OrderedDict[str, tuple[str, float]] = OrderedDict()
        self.max_size = max_size
        self.stats = {
            "type": "local_memory",
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0
        }
    
    async def get(self, key: str) -> Optional[str]:
        """Get from local cache with TTL check"""
        if key in self.cache:
            value, expiry = self.cache[key]
            if time.time() < expiry:
                self.stats["hits"] += 1
                # Move to end (LRU)
                self.cache.move_to_end(key)
                return value
            else:
                # Expired
                del self.cache[key]
        
        self.stats["misses"] += 1
        return None
    
    async def set(self, key: str, value: str, ttl: int = 300) -> bool:
        """Set in local cache with TTL"""
        try:
            expiry = time.time() + ttl
            
            # Evict oldest if at capacity
            if len(self.cache) >= self.max_size and key not in self.cache:
                self.cache.popitem(last=False)
                self.stats["evictions"] += 1
            
            self.cache[key] = (value, expiry)
            self.stats["sets"] += 1
            return True
        except Exception as e:
            logger.error(f"Local cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete from local cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Return cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0
        
        return {
            **self.stats,
            "size": len(self.cache),
            "hit_rate": hit_rate,
            "max_size": self.max_size
        }


class RedisCache(CacheInterface):
    """L2 Redis cache wrapper"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.stats = {
            "type": "redis",
            "operations": 0,
            "errors": 0
        }
    
    async def get(self, key: str) -> Optional[str]:
        """Get from Redis"""
        try:
            self.stats["operations"] += 1
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            self.stats["errors"] += 1
            return None
    
    async def set(self, key: str, value: str, ttl: int = 300) -> bool:
        """Set in Redis with TTL"""
        try:
            self.stats["operations"] += 1
            return await self.redis.set(key, value, ex=ttl)
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            self.stats["errors"] += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete from Redis"""
        try:
            self.stats["operations"] += 1
            return bool(await self.redis.delete(key))
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            self.stats["errors"] += 1
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Return Redis stats"""
        return self.stats


class MultiLevelCache(CacheInterface):
    """Multi-level cache combining L1 (local) and L2 (Redis)"""
    
    def __init__(self, l1_cache: CacheInterface, l2_cache: CacheInterface):
        self.l1 = l1_cache
        self.l2 = l2_cache
        self.stats = {
            "type": "multi_level",
            "l1_hits": 0,
            "l2_hits": 0,
            "misses": 0,
            "sets": 0
        }
    
    async def get(self, key: str) -> Optional[str]:
        """Get from L1 first, then L2 if miss"""
        # Try L1
        value = await self.l1.get(key)
        if value is not None:
            self.stats["l1_hits"] += 1
            return value
        
        # Try L2
        value = await self.l2.get(key)
        if value is not None:
            self.stats["l2_hits"] += 1
            # Populate L1 for next time
            await self.l1.set(key, value, ttl=60)  # Shorter TTL for L1
            return value
        
        self.stats["misses"] += 1
        return None
    
    async def set(self, key: str, value: str, ttl: int = 300) -> bool:
        """Set in both L1 and L2"""
        self.stats["sets"] += 1
        # Set in both levels
        l1_result = await self.l1.set(key, value, ttl=min(ttl, 60))  # L1 has shorter TTL
        l2_result = await self.l2.set(key, value, ttl=ttl)
        return l1_result and l2_result
    
    async def delete(self, key: str) -> bool:
        """Delete from both L1 and L2"""
        l1_result = await self.l1.delete(key)
        l2_result = await self.l2.delete(key)
        return l1_result or l2_result
    
    def get_stats(self) -> Dict[str, Any]:
        """Return combined stats"""
        total_hits = self.stats["l1_hits"] + self.stats["l2_hits"]
        total_requests = total_hits + self.stats["misses"]
        hit_rate = total_hits / total_requests if total_requests > 0 else 0
        
        return {
            **self.stats,
            "hit_rate": hit_rate,
            "l1_stats": self.l1.get_stats(),
            "l2_stats": self.l2.get_stats()
        }


async def get_cache(settings: Optional[Settings] = None) -> CacheInterface:
    """
    Factory function to get appropriate cache implementation based on settings.
    
    Returns:
        - NoOpCache if cache_enabled=False
        - MultiLevelCache (L1+L2) if cache_enabled=True and Redis available
        - LocalMemoryCache if cache_enabled=True but Redis unavailable
    """
    if settings is None:
        settings = get_settings()
    
    if not settings.cache_enabled:
        logger.info("🚫 Cache disabled - using NoOpCache")
        return NoOpCache()
    
    # Try to get Redis for L2
    try:
        redis_client = await get_redis()
        l2_cache = RedisCache(redis_client)
        l1_cache = LocalMemoryCache(max_size=100)  # Small L1 cache
        
        logger.info("✅ Multi-level cache enabled (L1: Local, L2: Redis)")
        return MultiLevelCache(l1_cache, l2_cache)
        
    except Exception as e:
        logger.warning(f"⚠️ Redis unavailable, falling back to local cache only: {e}")
        return LocalMemoryCache(max_size=500)  # Larger size when Redis unavailable


# Cache wrapper functions for backward compatibility
async def cache_get(key: str) -> Optional[str]:
    """Get from cache using default cache instance"""
    cache = await get_cache()
    return await cache.get(key)


async def cache_set(key: str, value: str, ttl: int = 300) -> bool:
    """Set in cache using default cache instance"""
    cache = await get_cache()
    return await cache.set(key, value, ttl)


async def cache_delete(key: str) -> bool:
    """Delete from cache using default cache instance"""
    cache = await get_cache()
    return await cache.delete(key)
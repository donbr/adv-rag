"""
Modern Redis Client for FastAPI with MCP Integration
Following 2024-2025 best practices for async Redis with dependency injection
"""

import logging
from typing import Optional
from contextlib import asynccontextmanager
from redis import asyncio as aioredis
from redis.exceptions import ConnectionError, TimeoutError
from src.settings import get_settings

logger = logging.getLogger(__name__)

class RedisClient:
    """Modern Redis client with connection pooling and error handling"""
    
    def __init__(self):
        self._client: Optional[aioredis.Redis] = None
        self._pool: Optional[aioredis.ConnectionPool] = None
    
    async def connect(self) -> None:
        """Initialize Redis connection with connection pooling"""
        settings = get_settings()
        
        try:
            # Create connection pool for better performance
            self._pool = aioredis.ConnectionPool.from_url(
                settings.redis_url,
                max_connections=settings.redis_max_connections,
                decode_responses=True,  # Auto-decode to strings
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30,  # Health check every 30 seconds
            )
            
            # Create Redis client with pool
            self._client = aioredis.Redis(connection_pool=self._pool)
            
            # Test connection
            await self._client.ping()
            logger.info("✅ Redis connection established successfully")
            
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Clean up Redis connections"""
        if self._client:
            await self._client.aclose()
        if self._pool:
            await self._pool.aclose()
        logger.info("🔌 Redis connection closed")
    
    @property
    def client(self) -> aioredis.Redis:
        """Get Redis client instance"""
        if not self._client:
            raise RuntimeError("Redis client not initialized. Call connect() first.")
        return self._client

# Global Redis client instance
redis_client = RedisClient()

async def get_redis() -> aioredis.Redis:
    """Dependency injection for Redis client with auto-connect"""
    try:
        # Try to get the client - this will raise RuntimeError if not connected
        client = redis_client.client
        # Test the connection
        await client.ping()
        return client
    except (RuntimeError, ConnectionError, TimeoutError):
        # Auto-connect if not connected
        logger.info("🔄 Redis not connected, attempting to connect...")
        await redis_client.connect()
        return redis_client.client

@asynccontextmanager
async def redis_lifespan():
    """Context manager for Redis lifecycle management"""
    await redis_client.connect()
    try:
        yield redis_client.client
    finally:
        await redis_client.disconnect()

# Cache utilities
async def cache_set(key: str, value: str, ttl: int = 300) -> bool:
    """Set cache with TTL"""
    try:
        client = await get_redis()
        return await client.set(key, value, ex=ttl)
    except Exception as e:
        logger.error(f"Cache set error for key {key}: {e}")
        return False

async def cache_get(key: str) -> Optional[str]:
    """Get from cache"""
    try:
        client = await get_redis()
        return await client.get(key)
    except Exception as e:
        logger.error(f"Cache get error for key {key}: {e}")
        return None

async def cache_delete(key: str) -> bool:
    """Delete from cache"""
    try:
        client = await get_redis()
        return bool(await client.delete(key))
    except Exception as e:
        logger.error(f"Cache delete error for key {key}: {e}")
        return False 
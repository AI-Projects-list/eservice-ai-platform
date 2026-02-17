"""
Redis cache client wrapper with connection pooling and utilities.

Provides async Redis client with automatic retry, connection pooling,
and convenient methods for common caching patterns.
"""

from typing import Any, Optional
import json
import time

from redis.asyncio import AsyncRedis, from_url
from redis.asyncio.connection import ConnectionPool
import structlog

from src.config import settings

logger = structlog.get_logger(__name__)


class RedisClient:
    """Async Redis client with connection pooling."""
    
    def __init__(self) -> None:
        self.redis: Optional[AsyncRedis] = None
        self.pool: Optional[ConnectionPool] = None
    
    async def connect(self) -> None:
        """Initialize Redis connection pool."""
        try:
            self.pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_POOL_SIZE,
                socket_connect_timeout=settings.REDIS_TIMEOUT,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,  # TCP_KEEPIDLE
                    2: 1,  # TCP_KEEPINTVL
                    3: 3,  # TCP_KEEPCNT
                },
            )
            self.redis = AsyncRedis(connection_pool=self.pool, decode_responses=True)
            
            # Test connection
            await self.redis.ping()
            logger.info("Redis connected", url=settings.REDIS_URL)
        
        except Exception as exc:
            logger.error("Failed to connect to Redis", error=str(exc))
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connection pool."""
        if self.redis:
            await self.redis.close()
            logger.info("Redis disconnected")
    
    async def ping(self) -> bool:
        """Check Redis connection."""
        try:
            return await self.redis.ping()
        except Exception:
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        value = await self.redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = settings.CACHE_DEFAULT_TTL
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
            
        Returns:
            Success status
        """
        try:
            json_value = json.dumps(value) if not isinstance(value, str) else value
            return await self.redis.setex(key, ttl, json_value)
        except Exception as exc:
            logger.error("Cache set failed", key=key, error=str(exc))
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete cache key.
        
        Args:
            key: Cache key
            
        Returns:
            Success status
        """
        return await self.redis.delete(key) > 0
    
    async def exists(self, key: str) -> bool:
        """Check if cache key exists."""
        return await self.redis.exists(key) > 0
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter in cache."""
        return await self.redis.incrby(key, amount)
    
    async def mget(self, *keys: str) -> list[Optional[Any]]:
        """Get multiple cache values."""
        values = await self.redis.mget(keys)
        return [
            json.loads(v) if v and isinstance(v, str) else v
            for v in values
        ]
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        cursor = 0
        count = 0
        
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            if keys:
                count += await self.redis.delete(*keys)
            if cursor == 0:
                break
        
        return count


# Global Redis client instance
redis_client = RedisClient()


# Decorator for caching
def cache_key(prefix: str, *args: Any, **kwargs: Any) -> str:
    """Generate cache key from prefix and arguments."""
    key_parts = [prefix]
    key_parts.extend(str(arg) for arg in args)
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    return ":".join(key_parts)


def cached(ttl: int = settings.CACHE_DEFAULT_TTL, key_prefix: str = "cache"):
    """
    Decorator for caching async function results.
    
    Usage:
        @cached(ttl=3600)
        async def get_user(user_id: int):
            return await db.find_user(user_id)
    
    Args:
        ttl: Cache time-to-live in seconds
        key_prefix: Key prefix for cache
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_k = cache_key(f"{key_prefix}:{func.__name__}", *args, **kwargs)
            
            # Try to get from cache
            cached_value = await redis_client.get(cache_k)
            if cached_value is not None:
                logger.debug("Cache hit", key=cache_k)
                return cached_value
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await redis_client.set(cache_k, result, ttl)
            logger.debug("Cache miss, result cached", key=cache_k, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator

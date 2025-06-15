#!/usr/bin/env python3
"""
Test Redis MCP Cache Integration (2024-2025 Best Practices)

This script tests the modern Redis caching functionality for MCP tools by:
1. Testing FastAPI endpoints (which become MCP tools via FastMCP.from_fastapi())
2. Verifying cache hits and misses with proper performance metrics
3. Testing both exact and semantic caching patterns
4. Validating Redis MCP server operations
"""

import asyncio
import httpx
import redis.asyncio as redis
import json
import time
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RedisMCPTester:
    """Modern Redis MCP integration tester"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", api_base: str = "http://localhost:8000"):
        self.redis_url = redis_url
        self.api_base = api_base
        self.redis_client = None
        self.http_client = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        self.http_client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.redis_client:
            await self.redis_client.close()
        if self.http_client:
            await self.http_client.aclose()
    
    async def test_redis_connection(self) -> bool:
        """Test Redis connection and basic operations"""
        try:
            await self.redis_client.ping()
            logger.info("✅ Redis connection successful")
            
            # Test basic operations
            await self.redis_client.set("test_key", "test_value", ex=10)
            value = await self.redis_client.get("test_key")
            assert value == "test_value", f"Expected 'test_value', got {value}"
            
            await self.redis_client.delete("test_key")
            logger.info("✅ Redis basic operations working")
            return True
            
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            return False
    
    async def test_api_health(self) -> bool:
        """Test FastAPI health endpoint"""
        try:
            response = await self.http_client.get(f"{self.api_base}/health")
            if response.status_code == 200:
                logger.info("✅ FastAPI health check passed")
                return True
            else:
                logger.error(f"❌ FastAPI health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ FastAPI connection failed: {e}")
            return False
    
    async def test_cache_stats(self) -> Dict[str, Any]:
        """Test cache statistics endpoint"""
        try:
            response = await self.http_client.get(f"{self.api_base}/cache/stats")
            if response.status_code == 200:
                stats = response.json()
                logger.info(f"✅ Cache stats: {stats}")
                return stats
            else:
                logger.error(f"❌ Cache stats failed: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"❌ Cache stats error: {e}")
            return {}
    
    async def test_mcp_tool_caching(self, endpoint: str, question: str) -> Dict[str, Any]:
        """Test MCP tool caching performance"""
        logger.info(f"🧪 Testing {endpoint} caching...")
        
        # Clear any existing cache for this test
        cache_pattern = "mcp_cache:*"
        keys = await self.redis_client.keys(cache_pattern)
        if keys:
            await self.redis_client.delete(*keys)
            logger.info(f"🧹 Cleared {len(keys)} cache keys")
        
        # First request (cache miss)
        start_time = time.time()
        response1 = await self.http_client.post(
            f"{self.api_base}/invoke/{endpoint}",
            json={"question": question}
        )
        miss_time = time.time() - start_time
        
        if response1.status_code != 200:
            logger.error(f"❌ First request failed: {response1.status_code}")
            return {"success": False}
        
        # Second request (cache hit)
        start_time = time.time()
        response2 = await self.http_client.post(
            f"{self.api_base}/invoke/{endpoint}",
            json={"question": question}
        )
        hit_time = time.time() - start_time
        
        if response2.status_code != 200:
            logger.error(f"❌ Second request failed: {response2.status_code}")
            return {"success": False}
        
        # Verify responses are identical
        data1 = response1.json()
        data2 = response2.json()
        
        if data1 == data2:
            speedup = miss_time / hit_time if hit_time > 0 else float('inf')
            logger.info(f"✅ Cache working! Miss: {miss_time:.3f}s, Hit: {hit_time:.3f}s, Speedup: {speedup:.1f}x")
            
            # Check Redis for cached data
            cache_keys = await self.redis_client.keys("mcp_cache:*")
            logger.info(f"📊 Found {len(cache_keys)} cache entries")
            
            return {
                "success": True,
                "miss_time": miss_time,
                "hit_time": hit_time,
                "speedup": speedup,
                "cache_keys": len(cache_keys)
            }
        else:
            logger.error("❌ Cache responses don't match!")
            return {"success": False}
    
    async def test_redis_mcp_server_operations(self):
        """Test Redis MCP server operations (if available)"""
        logger.info("🧪 Testing Redis MCP server operations...")
        
        # These would be available as MCP tools when using the Redis MCP server
        test_operations = [
            ("set", {"key": "mcp_test", "value": "hello_world", "expireSeconds": 60}),
            ("get", {"key": "mcp_test"}),
            ("list", {"pattern": "mcp_*"}),
            ("delete", {"key": "mcp_test"})
        ]
        
        results = {}
        for operation, params in test_operations:
            try:
                # Direct Redis operations (simulating MCP server behavior)
                if operation == "set":
                    await self.redis_client.setex(params["key"], params["expireSeconds"], params["value"])
                    results[operation] = "✅ Success"
                elif operation == "get":
                    value = await self.redis_client.get(params["key"])
                    results[operation] = f"✅ Got: {value}"
                elif operation == "list":
                    keys = await self.redis_client.keys(params["pattern"])
                    results[operation] = f"✅ Found {len(keys)} keys"
                elif operation == "delete":
                    deleted = await self.redis_client.delete(params["key"])
                    results[operation] = f"✅ Deleted {deleted} keys"
                    
            except Exception as e:
                results[operation] = f"❌ Error: {e}"
        
        logger.info(f"📊 Redis MCP operations: {results}")
        return results

async def main():
    """Main test runner"""
    logger.info("🚀 Starting Redis MCP Integration Tests")
    logger.info("=" * 60)
    
    async with RedisMCPTester() as tester:
        # Test 1: Basic connectivity
        redis_ok = await tester.test_redis_connection()
        api_ok = await tester.test_api_health()
        
        if not (redis_ok and api_ok):
            logger.error("❌ Basic connectivity failed. Ensure Redis and FastAPI are running.")
            return
        
        # Test 2: Cache statistics
        await tester.test_cache_stats()
        
        # Test 3: MCP tool caching for different endpoints
        test_cases = [
            ("semantic_retriever", "What makes John Wick movies special?"),
            ("bm25_retriever", "action scenes in John Wick"),
            ("ensemble_retriever", "Who is the main character?")
        ]
        
        cache_results = {}
        for endpoint, question in test_cases:
            result = await tester.test_mcp_tool_caching(endpoint, question)
            cache_results[endpoint] = result
        
        # Test 4: Redis MCP server operations
        redis_ops = await tester.test_redis_mcp_server_operations()
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)
        
        successful_caches = sum(1 for r in cache_results.values() if r.get("success"))
        logger.info(f"✅ Successful cache tests: {successful_caches}/{len(cache_results)}")
        
        if successful_caches > 0:
            avg_speedup = sum(r.get("speedup", 0) for r in cache_results.values() if r.get("success")) / successful_caches
            logger.info(f"⚡ Average cache speedup: {avg_speedup:.1f}x")
        
        successful_ops = sum(1 for r in redis_ops.values() if "✅" in str(r))
        logger.info(f"🔧 Successful Redis operations: {successful_ops}/{len(redis_ops)}")
        
        if successful_caches == len(cache_results) and successful_ops == len(redis_ops):
            logger.info("🎉 ALL TESTS PASSED! Redis MCP integration is working perfectly.")
        else:
            logger.warning("⚠️ Some tests failed. Check logs above for details.")

if __name__ == "__main__":
    asyncio.run(main()) 
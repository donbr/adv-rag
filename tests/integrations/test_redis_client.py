import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from redis.exceptions import ConnectionError
from src.core.settings import Settings

@pytest.fixture
def mock_redis_dependencies():
    """Mock aioredis and settings for RedisClient tests."""
    with patch('src.integrations.redis_client.aioredis', autospec=True) as mock_aioredis, \
         patch('src.integrations.redis_client.get_settings') as mock_get_settings:
        
        # Configure the Redis client and pool mocks to be async
        mock_redis_instance = AsyncMock()
        mock_pool_instance = AsyncMock()
        mock_aioredis.Redis.return_value = mock_redis_instance
        mock_aioredis.ConnectionPool.from_url.return_value = mock_pool_instance

        # Configure settings mock
        mock_get_settings.return_value = Settings(redis_url="redis://localhost", redis_max_connections=10)
        
        yield {
            "aioredis": mock_aioredis,
            "settings": mock_get_settings,
            "redis_instance": mock_redis_instance,
            "pool_instance": mock_pool_instance
        }

@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_client_connection(mock_redis_dependencies):
    """Test RedisClient connect and disconnect."""
    from src.integrations.redis_client import RedisClient
    client = RedisClient()

    await client.connect()
    
    mock_redis_dependencies["redis_instance"].ping.assert_awaited_once()
    
    await client.disconnect()
    mock_redis_dependencies["redis_instance"].aclose.assert_awaited_once()
    mock_redis_dependencies["pool_instance"].aclose.assert_awaited_once()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_redis_dependency(mock_redis_dependencies):
    """Test get_redis dependency injection and auto-reconnect."""
    from src.integrations.redis_client import get_redis, redis_client
    
    # Reset client state for clean test
    redis_client._client = None
    redis_client._pool = None

    # Mock the connect method to simulate setting the client
    async def mock_connect():
        redis_client._client = mock_redis_dependencies["redis_instance"]
        redis_client._pool = mock_redis_dependencies["pool_instance"]

    with patch.object(redis_client, 'connect', side_effect=mock_connect, new_callable=AsyncMock) as patched_connect:
        # The first call to get_redis should trigger a connect
        client = await get_redis()
        patched_connect.assert_awaited_once()
        assert client == mock_redis_dependencies["redis_instance"]

        # The second call should not trigger connect again
        await get_redis()
        patched_connect.assert_awaited_once() # Still 1 
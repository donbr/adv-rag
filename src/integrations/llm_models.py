# llm_models.py
from langchain_openai import ChatOpenAI
import logging
from langchain.globals import set_llm_cache
from langchain_redis import RedisCache, RedisSemanticCache
from langchain_openai import OpenAIEmbeddings
from src.core.settings import get_settings

logger = logging.getLogger(__name__)

def get_chat_openai():
    """
    Get ChatOpenAI instance with Redis caching (2024-2025 best practices)
    
    Uses langchain-redis 0.2.2 for both exact and semantic caching
    """
    settings = get_settings()
    
    # Initialize Redis caching for LLM responses
    try:
        # Option 1: Exact match caching (faster, less storage)
        redis_cache = RedisCache(redis_url=settings.redis_url)
        
        # Option 2: Semantic caching (more intelligent, finds similar queries)
        # embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        # redis_cache = RedisSemanticCache(
        #     redis_url=settings.redis_url,
        #     embeddings=embeddings,
        #     distance_threshold=0.2  # Adjust for similarity sensitivity
        # )
        
        # Set global LLM cache
        set_llm_cache(redis_cache)
        logger.info("✅ LangChain Redis cache initialized successfully")
        
    except Exception as e:
        logger.warning(f"⚠️ Failed to initialize Redis cache: {e}. LLM caching disabled.")
    
    return ChatOpenAI(
        model=settings.openai_model_name,
        temperature=settings.openai_temperature,
        openai_api_key=settings.openai_api_key,
        # Additional performance settings from configuration
        max_retries=settings.openai_max_retries,
        request_timeout=settings.openai_request_timeout,
    )

# Backward compatibility alias
def get_chat_model():
    """Backward compatibility alias for get_chat_openai()"""
    return get_chat_openai()

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        from src.core.logging_config import setup_logging
        setup_logging()

    logger.info("--- Running llm_models.py standalone test ---")
    try:
        chat_model = get_chat_openai()
        if chat_model:
            logger.info(f"Chat model type: {type(chat_model)}")
        else:
            logger.error("Chat model could not be initialized in standalone test.")
    except Exception as e:
        logger.error(f"Error during llm_models.py standalone test: {e}", exc_info=True)
    logger.info("--- Finished llm_models.py standalone test ---") 
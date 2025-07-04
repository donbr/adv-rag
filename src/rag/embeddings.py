# embeddings.py
from langchain_openai import OpenAIEmbeddings
from src.core.settings import get_settings
import logging

logger = logging.getLogger(__name__)

def get_openai_embeddings():
    settings = get_settings()
    logger.info(f"Initializing OpenAIEmbeddings model: {settings.embedding_model_name}")
    try:
        model = OpenAIEmbeddings(model=settings.embedding_model_name)
        logger.info("OpenAIEmbeddings model initialized successfully.")
        return model
    except Exception as e:
        logger.error(f"Failed to initialize OpenAIEmbeddings model: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        from src.core.logging_config import setup_logging
        setup_logging()

    logger.info("--- Running embeddings.py standalone test ---")
    try:
        embedding_model = get_openai_embeddings()
        if embedding_model:
            logger.info(f"Embedding model type: {type(embedding_model)}")
            test_query = "This is a test sentence for embedding."
            logger.info(f"Embedding test query: '{test_query}'")
            test_embedding = embedding_model.embed_query(test_query)
            logger.info(f"Test embedding dimension: {len(test_embedding)}")
            logger.info(f"Test embedding (first 5 dimensions): {test_embedding[:5]}")
        else:
            logger.error("Embedding model could not be initialized in standalone test.")
    except Exception as e:
        logger.error(f"Error during embeddings.py standalone test: {e}", exc_info=True)
    logger.info("--- Finished embeddings.py standalone test ---") 
# vectorstore.py
from langchain_qdrant import QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient, models as qdrant_models
from langchain_experimental.text_splitter import SemanticChunker
import logging

from src.core.settings import get_settings

from .data_loader import load_documents
from .embeddings import get_openai_embeddings

logger = logging.getLogger(__name__)

# Initialize once
settings = get_settings()
QDRANT_API_URL = settings.qdrant_url
BASELINE_COLLECTION_NAME = "johnwick_baseline"
SEMANTIC_COLLECTION_NAME = "johnwick_semantic"
logger.debug("Loading documents for vector store setup...")
DOCUMENTS = load_documents()
logger.debug("Initializing embeddings for vector store setup...")
EMBEDDINGS = get_openai_embeddings()


def get_main_vectorstore():
    logger.info("Attempting to create main vector store 'johnwick_baseline'...")

    try:
        # Initialize Qdrant client
        qdrant_client = QdrantClient(
            url=QDRANT_API_URL,
            prefer_grpc=True
        )

        # Construct the VectorStore using cloud client
        vs = QdrantVectorStore(
            embedding=EMBEDDINGS,
            client=qdrant_client,
            collection_name=BASELINE_COLLECTION_NAME,
            retrieval_mode=RetrievalMode.DENSE,
        )

        logger.info("Main vector store 'johnwick_baseline' created successfully.")
        return vs
    except Exception as e:
        logger.error(f"Failed to create main vector store 'johnwick_baseline': {e}", exc_info=True)
        raise

def get_semantic_vectorstore():
    logger.info("Attempting to create semantic vector store 'johnwick_semantic'...")

    try:
        # Initialize Qdrant client
        qdrant_client = QdrantClient(
            url=QDRANT_API_URL,
            prefer_grpc=True
        )

        # Construct the VectorStore using cloud client
        vs = QdrantVectorStore(
            embedding=EMBEDDINGS,
            client=qdrant_client,
            collection_name=SEMANTIC_COLLECTION_NAME,
            retrieval_mode=RetrievalMode.DENSE,
        )

        logger.info("Semantic vector store 'johnwick_semantic' created successfully.")
        return vs
    except Exception as e:
        logger.error(f"Failed to create semantic vector store 'johnwick_semantic': {e}", exc_info=True)
        raise

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        from src.core.logging_config import setup_logging
        setup_logging()

    logger.info("--- Running vectorstore_setup.py standalone test ---")
    if not DOCUMENTS:
        logger.warning("No documents were loaded by data_loader. Cannot proceed with vector store creation tests.")
    else:
        logger.info("Documents loaded, proceeding with vector store creation tests...")
        try:
            main_vs = get_main_vectorstore()
            if main_vs:
                logger.info(f"Baseline vector store '{main_vs.collection_name}' test instance created.")
                client = QdrantClient(url=QDRANT_API_URL, prefer_grpc=True)
                count = client.count(collection_name=main_vs.collection_name).count
                logger.info(f"-> Points in '{main_vs.collection_name}': {count}")
        except Exception as e:
            logger.error(f"Error during Main vector store test: {e}", exc_info=True)

        try:
            semantic_vs = get_semantic_vectorstore()
            if semantic_vs:
                logger.info(f"Semantic vector store '{semantic_vs.collection_name}' test instance created.")
                client = QdrantClient(url=QDRANT_API_URL, prefer_grpc=True)
                count = client.count(collection_name=semantic_vs.collection_name).count
                logger.info(f"-> Points in '{semantic_vs.collection_name}': {count}")
        except Exception as e:
            logger.error(f"Error during Semantic vector store test: {e}", exc_info=True)

    logger.info("--- Finished vectorstore_setup.py standalone test ---") 
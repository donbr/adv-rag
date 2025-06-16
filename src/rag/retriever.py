# retriever.py
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_cohere import CohereRerank
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers import ParentDocumentRetriever, EnsembleRetriever
from langchain.storage import InMemoryStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging
import os

from src.core.settings import get_settings
# settings.setup_env_vars() # Called by settings import

from .data_loader import load_documents # For BM25 and ParentDocumentRetriever original docs
from src.integrations.llm_models import get_chat_model
from .embeddings import get_openai_embeddings # For SemanticChunker if used directly here
from .vectorstore import (
    get_main_vectorstore,
    get_semantic_vectorstore
)
# For SemanticChunker if ParentDocumentRetriever needs to re-chunk (it uses child_splitter)
# from langchain_experimental.text_splitter import SemanticChunker 

logger = logging.getLogger(__name__)

# Initialize base components that might be shared or needed early
logger.debug("Loading documents for retriever factory...")
DOCUMENTS = load_documents()
logger.debug("Initializing chat model for retriever factory...")
CHAT_MODEL = get_chat_model()
# EMBEDDINGS = get_openai_embeddings() # Already initialized in vectorstore_setup

logger.debug("Initializing vector stores for retriever factory...")
BASELINE_VECTORSTORE = None
SEMANTIC_VECTORSTORE = None

if DOCUMENTS: # Only attempt to create stores if documents were loaded
    try:
        BASELINE_VECTORSTORE = get_main_vectorstore()
    except Exception as e:
        logger.error(f"Failed to initialize BASELINE_VECTORSTORE in retriever_factory: {e}", exc_info=True)
    try:
        SEMANTIC_VECTORSTORE = get_semantic_vectorstore()
    except Exception as e:
        logger.error(f"Failed to initialize SEMANTIC_VECTORSTORE in retriever_factory: {e}", exc_info=True)
else:
    logger.warning("No documents loaded; vector stores will not be initialized in retriever_factory.")


def get_naive_retriever():
    if not BASELINE_VECTORSTORE:
        logger.warning("Main vectorstore not available for naive_retriever. Returning None.")
        return None
    logger.info("Creating naive_retriever (BASELINE_VECTORSTORE.as_retriever).")
    return BASELINE_VECTORSTORE.as_retriever(search_kwargs={"k": 10})

def get_bm25_retriever():
    if not DOCUMENTS:
        logger.warning("Documents not available for bm25_retriever. Returning None.")
        return None
    logger.info("Creating bm25_retriever...")
    try:
        retriever = BM25Retriever.from_documents(DOCUMENTS)
        logger.info("BM25Retriever created successfully.")
        return retriever
    except Exception as e:
        logger.error(f"Failed to create BM25Retriever: {e}", exc_info=True)
        return None

def get_contextual_compression_retriever():
    logger.info("Attempting to create contextual_compression_retriever...")
    naive_ret = get_naive_retriever()
    if not naive_ret:
        logger.warning("Naive retriever not available, cannot create contextual_compression_retriever. Returning None.")
        return None
    if not os.getenv("COHERE_API_KEY"): # Check for Cohere key
        logger.warning("COHERE_API_KEY not set. Cannot create CohereRerank for contextual_compression_retriever. Returning None.")
        return None
    try:
        settings = get_settings()
        compressor = CohereRerank(model=settings.cohere_rerank_model) 
        retriever = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=naive_ret
        )
        logger.info("ContextualCompressionRetriever created successfully.")
        return retriever
    except Exception as e:
        logger.error(f"Failed to create ContextualCompressionRetriever: {e}", exc_info=True)
        return None

def get_multi_query_retriever():
    logger.info("Attempting to create multi_query_retriever...")
    naive_ret = get_naive_retriever()
    if not naive_ret:
        logger.warning("Naive retriever not available, cannot create multi_query_retriever. Returning None.")
        return None
    try:
        retriever = MultiQueryRetriever.from_llm(
            retriever=naive_ret, llm=CHAT_MODEL
        )
        logger.info("MultiQueryRetriever created successfully.")
        return retriever
    except Exception as e:
        logger.error(f"Failed to create MultiQueryRetriever: {e}", exc_info=True)
        return None

def get_semantic_retriever():
    if not SEMANTIC_VECTORSTORE:
        logger.warning("Semantic vectorstore not available for semantic_retriever. Returning None.")
        return None
    logger.info("Creating semantic_retriever (SEMANTIC_VECTORSTORE.as_retriever).")
    return SEMANTIC_VECTORSTORE.as_retriever(search_kwargs={"k": 10})

def get_ensemble_retriever():
    logger.info("Attempting to create ensemble_retriever...")
    retrievers_to_ensemble_map = {
        "bm25": get_bm25_retriever(),
        "naive": get_naive_retriever(),
        "contextual_compression": get_contextual_compression_retriever(), # Can be slow for ensemble
        "multi_query": get_multi_query_retriever() # Can be slow for ensemble
        # "semantic": get_semantic_retriever()
    }

    active_retrievers = [r for r_name, r in retrievers_to_ensemble_map.items() if r is not None]
    active_retriever_names = [r_name for r_name, r in retrievers_to_ensemble_map.items() if r is not None]

    if not active_retrievers:
        logger.warning("No retrievers available for ensemble_retriever. Returning None.")
        return None
    if len(active_retrievers) < 2:
         logger.warning(f"Ensemble retriever requires at least 2 active retrievers, got {len(active_retrievers)} ({active_retriever_names}). Returning the first one or None.")
         return active_retrievers[0] if active_retrievers else None

    logger.info(f"Creating EnsembleRetriever with retrievers: {active_retriever_names}")
    try:
        equal_weighting = [1.0 / len(active_retrievers)] * len(active_retrievers)
        retriever = EnsembleRetriever(
            retrievers=active_retrievers, weights=equal_weighting
        )
        logger.info("EnsembleRetriever created successfully.")
        return retriever
    except Exception as e:
        logger.error(f"Failed to create EnsembleRetriever: {e}", exc_info=True)
        return None


def create_retriever(retrieval_type: str, vectorstore=None, **kwargs):
    """
    Factory function to create retrievers based on type.
    
    Args:
        retrieval_type: Type of retriever ("naive", "bm25", "hybrid", "ensemble", etc.)
        vectorstore: Vector store instance (may not be used by all retrievers)
        **kwargs: Additional arguments (currently unused)
    
    Returns:
        Configured retriever instance or None if creation fails
    """
    logger.info(f"Creating retriever of type: {retrieval_type}")
    
    retriever_map = {
        "naive": get_naive_retriever,
        "bm25": get_bm25_retriever,
        "hybrid": get_ensemble_retriever,  # Use ensemble for hybrid search
        "ensemble": get_ensemble_retriever,
        "contextual": get_contextual_compression_retriever,
        "contextual_compression": get_contextual_compression_retriever,
        "multi_query": get_multi_query_retriever,
        "semantic": get_semantic_retriever,
    }
    
    retriever_func = retriever_map.get(retrieval_type.lower())
    if not retriever_func:
        logger.warning(f"Unknown retriever type: {retrieval_type}. Falling back to naive retriever.")
        retriever_func = get_naive_retriever
    
    try:
        retriever = retriever_func()
        if retriever:
            logger.info(f"Successfully created {retrieval_type} retriever")
        else:
            logger.warning(f"Failed to create {retrieval_type} retriever - function returned None")
        return retriever
    except Exception as e:
        logger.error(f"Error creating {retrieval_type} retriever: {e}")
        return None


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        from src.core.logging_config import setup_logging
        setup_logging()
    
    logger.info("--- Running retriever_factory.py standalone test ---")
    if not DOCUMENTS:
        logger.warning("No documents were loaded by data_loader. Retriever initialization will be limited.")
    else:
        logger.info(f"{len(DOCUMENTS)} documents loaded. Proceeding with retriever initialization tests...")

    retrievers_status = {}
    retrievers_status["Naive"] = get_naive_retriever()
    retrievers_status["BM25"] = get_bm25_retriever()
    retrievers_status["Contextual Compression"] = get_contextual_compression_retriever()
    retrievers_status["Multi-Query"] = get_multi_query_retriever()
    retrievers_status["Semantic"] = get_semantic_retriever()
    retrievers_status["Ensemble"] = get_ensemble_retriever()

    logger.info("\n--- Retriever Initialization Status ---")
    for name, r_instance in retrievers_status.items():
        logger.info(f"{name} Retriever: {'Ready' if r_instance else 'Failed/Not Available'}")

    logger.info("--- Finished retriever_factory.py standalone test ---") 
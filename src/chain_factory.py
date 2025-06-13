# chain_factory.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter
import logging

from src import settings

from src.llm_models import get_chat_model
from src.retriever_factory import (
    get_naive_retriever,
    get_bm25_retriever,
    get_contextual_compression_retriever,
    get_multi_query_retriever,
    get_ensemble_retriever,
    get_semantic_retriever
)

logger = logging.getLogger(__name__)

# Lazy initialization - don't initialize chat model at import time
_CHAT_MODEL = None

def get_chat_model_lazy():
    """Get chat model with lazy initialization"""
    global _CHAT_MODEL
    if _CHAT_MODEL is None:
        logger.debug("Initializing chat model for chain_factory...")
        _CHAT_MODEL = get_chat_model()
    return _CHAT_MODEL

RAG_TEMPLATE_STR = """\
You are a helpful and kind assistant. Use the context provided below to answer the question.

If you do not know the answer, or are unsure, say you don't know.

Query:
{question}

Context:
{context}
"""

logger.debug("Creating RAG_PROMPT from template...")
RAG_PROMPT = ChatPromptTemplate.from_template(RAG_TEMPLATE_STR)

def create_rag_chain(retriever):
    if retriever is None:
        # The calling code in this module will log which specific chain failed based on this None.
        return None
    logger.info(f"Creating RAG chain for retriever: {type(retriever).__name__}") # Can be verbose
    try:
        chain = (
            {"context": itemgetter("question") | retriever, "question": itemgetter("question")}
            | RunnablePassthrough.assign(context=itemgetter("context")) 
            | {"response": RAG_PROMPT | get_chat_model_lazy(), "context": itemgetter("context")}
        )
        logger.info(f"RAG chain created successfully for {type(retriever).__name__}.")
        return chain
    except Exception as e:
        logger.error(f"Failed to create RAG chain for {type(retriever).__name__ if retriever else 'UnknownRetriever'}: {e}", exc_info=True)
        return None

# Create all chains
logger.info("Creating all RAG chains...")
NAIVE_RETRIEVAL_CHAIN = create_rag_chain(get_naive_retriever())
BM25_RETRIEVAL_CHAIN = create_rag_chain(get_bm25_retriever())
CONTEXTUAL_COMPRESSION_CHAIN = create_rag_chain(get_contextual_compression_retriever())
MULTI_QUERY_CHAIN = create_rag_chain(get_multi_query_retriever())
ENSEMBLE_CHAIN = create_rag_chain(get_ensemble_retriever())
SEMANTIC_CHAIN = create_rag_chain(get_semantic_retriever())
logger.info("Finished creating RAG chains.")

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        if 'logging_config' not in globals():
            from src import logging_config
        logging_config.setup_logging()

    logger.info("--- Running chain_factory.py standalone test ---")
    chains = {
        "Naive": NAIVE_RETRIEVAL_CHAIN,
        "BM25": BM25_RETRIEVAL_CHAIN,
        "Contextual Compression": CONTEXTUAL_COMPRESSION_CHAIN,
        "Multi-Query": MULTI_QUERY_CHAIN,
        "Ensemble": ENSEMBLE_CHAIN,
        "Semantic": SEMANTIC_CHAIN,
    }

    test_question = "Did people generally like John Wick?"
    logger.info(f"Test question for all chains: '{test_question}'")
    
    for name, chain_instance in chains.items():
        logger.info(f"--- Testing {name} Chain ---           [Status: {'Ready' if chain_instance else 'Not Available'}]")
        if chain_instance:
            try:
                response = chain_instance.invoke({"question": test_question})
                answer_content = response.get("response", {}).content if hasattr(response.get("response"), "content") else "N/A"
                context_len = len(response.get('context', []))
                logger.info(f"  Question: {test_question}")
                logger.info(f"  Answer: {answer_content}")
                logger.info(f"  Context Docs: {context_len}")
            except Exception as e:
                logger.error(f"  Error invoking {name} chain: {e}", exc_info=True)
        # else: (already logged status above)
        # logger.warning(f"--- {name} Chain is not available for testing ---")
    logger.info("--- Finished chain_factory.py standalone test ---") 
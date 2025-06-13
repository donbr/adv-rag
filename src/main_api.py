# main_api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import logging

from src import settings

from src.chain_factory import (
    NAIVE_RETRIEVAL_CHAIN,
    BM25_RETRIEVAL_CHAIN,
    CONTEXTUAL_COMPRESSION_CHAIN,
    MULTI_QUERY_CHAIN,
    ENSEMBLE_CHAIN,
    SEMANTIC_CHAIN
)

from contextlib import asynccontextmanager

# Get a logger for this module
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    logger.info("FastAPI application startup...")
    logger.info("Initializing components and chains...")

    available_chains = {
        "Naive Retriever Chain": NAIVE_RETRIEVAL_CHAIN,
        "BM25 Retriever Chain": BM25_RETRIEVAL_CHAIN,
        "Contextual Compression Chain": CONTEXTUAL_COMPRESSION_CHAIN,
        "Multi-Query Chain": MULTI_QUERY_CHAIN,
        "Ensemble Chain": ENSEMBLE_CHAIN,
        "Semantic Chain": SEMANTIC_CHAIN
    }

    logger.info("\n--- Chain Initialization Status ---")
    all_chains_ready = True
    for name, chain_instance in available_chains.items():
        if chain_instance is not None:
            logger.info(f"[+] {name}: Ready")
        else:
            logger.warning(f"[-] {name}: Not available. Check logs for retriever/vectorstore initialization issues.")
            all_chains_ready = False
    
    if all_chains_ready:
        logger.info("All chains initialized successfully.")
    else:
        logger.warning("One or more chains failed to initialize. API functionality may be limited.")
    logger.info("------------------------------------------------------")
    yield
    # Code to run on shutdown
    logger.info("FastAPI application shutdown.")

app = FastAPI(
    title="Advanced RAG Retriever API",
    description="API for invoking various LangChain retrieval chains for John Wick movie reviews.",
    version="1.0.0",
    lifespan=lifespan # Use the lifespan context manager
)

class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str
    # context: list # You might want to define a Pydantic model for Document if returning context
    context_document_count: int

async def invoke_chain_logic(chain, question: str, chain_name: str):
    if chain is None:
        logger.error(f"Chain '{chain_name}' is not available (None). Cannot process request for question: '{question}'")
        raise HTTPException(status_code=503, detail=f"The '{chain_name}' is currently unavailable. Please check server logs.")
    try:
        logger.info(f"Invoking '{chain_name}' with question: '{question[:50]}...'")
        result = await chain.ainvoke({"question": question})
        answer = result.get("response", {}).content if hasattr(result.get("response"), "content") else "No answer content found."
        context_docs_count = len(result.get("context", []))
        logger.info(f"'{chain_name}' invocation successful. Answer: '{answer[:50]}...', Context docs: {context_docs_count}")
        return AnswerResponse(answer=answer, context_document_count=context_docs_count)
    except Exception as e:
        logger.error(f"Error invoking '{chain_name}' for question '{question[:50]}...': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred while processing your request with {chain_name}.")

@app.post("/invoke/naive_retriever", response_model=AnswerResponse, operation_id="naive_retriever")
async def invoke_naive_endpoint(request: QuestionRequest):
    """Invokes the Naive Retriever chain for basic similarity search."""
    return await invoke_chain_logic(NAIVE_RETRIEVAL_CHAIN, request.question, "Naive Retriever Chain")

@app.post("/invoke/bm25_retriever", response_model=AnswerResponse, operation_id="bm25_retriever")
async def invoke_bm25_endpoint(request: QuestionRequest):
    """Invokes the BM25 Retriever chain for keyword-based search."""
    return await invoke_chain_logic(BM25_RETRIEVAL_CHAIN, request.question, "BM25 Retriever Chain")

@app.post("/invoke/contextual_compression_retriever", response_model=AnswerResponse, operation_id="contextual_compression_retriever")
async def invoke_contextual_compression_endpoint(request: QuestionRequest):
    """Invokes the Contextual Compression Retriever chain for compressed context."""
    return await invoke_chain_logic(CONTEXTUAL_COMPRESSION_CHAIN, request.question, "Contextual Compression Chain")

@app.post("/invoke/multi_query_retriever", response_model=AnswerResponse, operation_id="multi_query_retriever")
async def invoke_multi_query_endpoint(request: QuestionRequest):
    """Invokes the Multi-Query Retriever chain for enhanced query expansion."""
    return await invoke_chain_logic(MULTI_QUERY_CHAIN, request.question, "Multi-Query Chain")

@app.post("/invoke/ensemble_retriever", response_model=AnswerResponse, operation_id="ensemble_retriever")
async def invoke_ensemble_endpoint(request: QuestionRequest):
    """Invokes the Ensemble Retriever chain combining multiple retrieval strategies."""
    return await invoke_chain_logic(ENSEMBLE_CHAIN, request.question, "Ensemble Chain")

@app.post("/invoke/semantic_retriever", response_model=AnswerResponse, operation_id="semantic_retriever")
async def invoke_semantic_endpoint(request: QuestionRequest):
    """Invokes the Semantic Retriever chain for advanced semantic search."""
    return await invoke_chain_logic(SEMANTIC_CHAIN, request.question, "Semantic Chain")

if __name__ == "__main__":
    logger.info("Starting FastAPI server using uvicorn.run() from __main__...")

    uvicorn.run(app, host="0.0.0.0", port=8000) 
"""
📈 Telemetry-Driven Retrieval Strategy Evaluation - Complete Bootstrap Walkthrough

This script demonstrates sophisticated evaluation of 6 retrieval strategies using Phoenix telemetry 
rather than manual code-centric evaluation. Perfect for comparing MCP vs FastAPI performance and 
optimizing RAG pipeline performance through observability.
"""

import os
import asyncio
import logging
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Any

import requests
from dotenv import load_dotenv

# Phoenix setup - using latest 2025 best practices with arize-phoenix-otel
from phoenix.otel import register
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient, models
from langchain_core.prompts import ChatPromptTemplate
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_cohere import CohereRerank
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers import EnsembleRetriever

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress verbose HTTP request logs since we have Phoenix tracing
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai._base_client").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

# Centralized prompt template
RAG_PROMPT = ChatPromptTemplate.from_template("""You are a helpful assistant. Use the context below to answer the question.
If you don't know the answer, say you don't know.

Question: {question}
Context: {context}""")

@dataclass
class Config:
    """Centralized configuration management"""
    # API Keys
    openai_api_key: str
    cohere_api_key: str
    
    # Phoenix settings
    phoenix_endpoint: str = "http://localhost:6006"
    project_name: str = f"retrieval-evaluation-{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Qdrant settings
    qdrant_api_url: str = "http://localhost:6333"
    baseline: str = "johnwick_baseline"
    semantic: str = "johnwick_semantic"

    # Model settings
    model_name: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"
    
    # Cache configuration for A/B testing
    cache_enabled: bool = True
    cache_mode: str = "default"  # "enabled", "disabled", or "default"
    
    # Data settings
    data_urls: List[tuple] = None
    
    def __post_init__(self):
        if self.data_urls is None:
            self.data_urls = [
                ("https://raw.githubusercontent.com/AI-Maker-Space/DataRepository/main/jw1.csv", "john_wick_1.csv"),
                ("https://raw.githubusercontent.com/AI-Maker-Space/DataRepository/main/jw2.csv", "john_wick_2.csv"),
                ("https://raw.githubusercontent.com/AI-Maker-Space/DataRepository/main/jw3.csv", "john_wick_3.csv"),
                ("https://raw.githubusercontent.com/AI-Maker-Space/DataRepository/main/jw4.csv", "john_wick_4.csv"),
            ]

def setup_environment() -> Config:
    """Setup environment and return configuration"""
    load_dotenv()
    
    config = Config(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        cohere_api_key=os.getenv("COHERE_API_KEY", "")
    )
    
    # Set environment variables
    os.environ["OPENAI_API_KEY"] = config.openai_api_key
    os.environ["COHERE_API_KEY"] = config.cohere_api_key
    os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = config.phoenix_endpoint
    
    return config


def setup_phoenix_tracing(config: Config):
    """Setup Phoenix tracing with auto-instrumentation (best practice)"""
    return register(
        project_name=config.project_name,
        auto_instrument=True,
        batch=True
    )

# initialize vectorstore
def setup_vectorstore_client(config: Config, collection_name: str, embeddings) -> QdrantVectorStore:
    """Reusable function to setup vector stores"""
    
    # Initialize Qdrant client
    qdrant_client = QdrantClient(
        url=config.qdrant_api_url,
        prefer_grpc=True
    )

    # Construct the VectorStore using cloud client
    vector_store = QdrantVectorStore(
        embedding=embeddings,
        client=qdrant_client,
        collection_name=collection_name,
        retrieval_mode=RetrievalMode.DENSE,
    )

    return vector_store


def create_retrievers(baseline_vectorstore, semantic_vectorstore, all_docs, llm) -> Dict[str, Any]:
    """Create all retrieval strategies"""
    retrievers = {}
    
    # Basic retrievers
    retrievers["naive"] = baseline_vectorstore.as_retriever(search_kwargs={"k": 10})
    retrievers["semantic"] = semantic_vectorstore.as_retriever(search_kwargs={"k": 10})
    retrievers["bm25"] = BM25Retriever.from_documents(all_docs)
    
    # Advanced retrievers
    cohere_rerank = CohereRerank(model="rerank-english-v3.0")
    retrievers["compression"] = ContextualCompressionRetriever(
        base_compressor=cohere_rerank,
        base_retriever=retrievers["naive"]
    )
    
    retrievers["multiquery"] = MultiQueryRetriever.from_llm(
        retriever=retrievers["naive"],
        llm=llm
    )
    
    retrievers["ensemble"] = EnsembleRetriever(
        retrievers=[
            retrievers["bm25"], 
            retrievers["naive"], 
            retrievers["compression"], 
            retrievers["multiquery"]
        ],
        weights=[0.25, 0.25, 0.25, 0.25]
    )
    
    return retrievers

async def load_and_process_data(config: "Config") -> List:
    """Load and process John Wick movie review data"""
    data_dir = Path.cwd() / "data"
    data_dir.mkdir(exist_ok=True)
    
    all_docs = []
    
    for idx, (url, filename) in enumerate(config.data_urls, start=1):
        file_path = data_dir / filename
        
        # Download if not exists
        if not file_path.exists():
            try:
                response = requests.get(url)
                response.raise_for_status()
                file_path.write_bytes(response.content)
            except requests.RequestException as e:
                logger.error(f"Error downloading {filename}: {e}")
                continue
        
        # Load documents
        try:
            loader = CSVLoader(
                file_path=file_path,
                metadata_columns=["Review_Date", "Review_Title", "Review_Url", "Author", "Rating"]
            )
            docs = loader.load()
            
            # Add metadata
            for doc in docs:
                doc.metadata.update({
                    "Movie_Title": f"John Wick {idx}",
                    "Rating": int(doc.metadata.get("Rating", 0) or 0),
                    "last_accessed_at": (datetime.now() - timedelta(days=4 - idx)).isoformat()
                })
            
            all_docs.extend(docs)
            
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            continue
    
    return all_docs

def create_rag_chain(retriever, llm, method_name: str):
    """Create a simple RAG chain with method identification - Phoenix auto-traces this"""
    chain = (
        {"context": itemgetter("question") | retriever, "question": itemgetter("question")}
        | RunnablePassthrough.assign(context=itemgetter("context"))
        | {"response": RAG_PROMPT | llm, "context": itemgetter("context")}
    )
    
    # Use uniform span name with retriever tag for easier Phoenix filtering
    return chain.with_config({
        "run_name": f"rag_chain_{method_name}",
        "span_attributes": {"retriever": method_name}
    })

async def run_evaluation(question: str, chains: Dict[str, Any], cache_mode: str = "default") -> Dict[str, Any]:
    """Run evaluation across all retrieval strategies with cache mode tracking"""
    results = {}
    
    for method_name, chain in chains.items():
        start_time = time.time()
        try:
            result = await chain.ainvoke({"question": question})
            response_content = result["response"].content
            context_count = len(result.get("context", []))
            
            end_time = time.time()
            latency = (end_time - start_time) * 1000  # ms
            
            results[method_name] = {
                "response": response_content,
                "latency_ms": latency,
                "context_count": context_count,
                "cache_mode": cache_mode,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error with {method_name}: {e}")
            results[method_name] = {
                "error": str(e),
                "cache_mode": cache_mode,
                "timestamp": datetime.now().isoformat()
            }
    
    return results

async def run_cache_comparison(question: str, chains: Dict[str, Any], config: Config) -> Dict[str, Any]:
    """Run evaluation with different cache modes for A/B testing"""
    comparison_results = {
        "question": question,
        "experiment_id": f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "cache_enabled_results": {},
        "cache_disabled_results": {},
        "comparison_metrics": {}
    }
    
    # Run with cache enabled
    if config.cache_mode in ["default", "both"]:
        os.environ["CACHE_ENABLED"] = "true"
        logger.info("🟢 Running evaluation with cache ENABLED")
        comparison_results["cache_enabled_results"] = await run_evaluation(question, chains, "enabled")
    
    # Run with cache disabled
    if config.cache_mode in ["disabled", "both"]:
        os.environ["CACHE_ENABLED"] = "false"
        logger.info("🔴 Running evaluation with cache DISABLED")
        comparison_results["cache_disabled_results"] = await run_evaluation(question, chains, "disabled")
    
    # Calculate comparison metrics
    if config.cache_mode == "both":
        for method in chains.keys():
            enabled = comparison_results["cache_enabled_results"].get(method, {})
            disabled = comparison_results["cache_disabled_results"].get(method, {})
            
            if "latency_ms" in enabled and "latency_ms" in disabled:
                comparison_results["comparison_metrics"][method] = {
                    "cache_speedup": disabled["latency_ms"] - enabled["latency_ms"],
                    "cache_speedup_percentage": ((disabled["latency_ms"] - enabled["latency_ms"]) / disabled["latency_ms"] * 100) if disabled["latency_ms"] > 0 else 0
                }
    
    return comparison_results

async def main():
    """Main execution function"""
    try:
        # Setup
        config = setup_environment()
        tracer_provider = setup_phoenix_tracing(config)

        logger.info(f"✅ Phoenix tracing configured for project: {config.project_name}")
        
        # Initialize models
        llm = ChatOpenAI(model=config.model_name)
        embeddings = OpenAIEmbeddings(model=config.embedding_model)

                # Load data
        logger.info("📥 Loading and processing data...")
        all_docs = await load_and_process_data(config)
        
        if not all_docs:
            raise ValueError("No documents loaded successfully")

        # Setup vector stores
        logger.info("🔧 Setting up vector stores...")
        baseline_vectorstore = setup_vectorstore_client(config, config.baseline, embeddings)
        semantic_vectorstore = setup_vectorstore_client(config, config.semantic, embeddings)
        
        # Create retrievers and chains
        logger.info("⚙️ Creating retrieval strategies...")
        retrievers = create_retrievers(baseline_vectorstore, semantic_vectorstore, all_docs, llm)
        
        # Create RAG chains
        chains = {
            name: create_rag_chain(retriever, llm, name)
            for name, retriever in retrievers.items()
        }

        # Run evaluation
        logger.info("🔍 Running evaluation...")
        question = "Did people generally like John Wick?"
        
        # Check if we're doing cache comparison
        cache_mode = os.getenv("CACHE_MODE", "both")  # default to both for A/B testing
        config.cache_mode = cache_mode
        
        if cache_mode == "both":
            # Run cache comparison
            comparison_results = await run_cache_comparison(question, chains, config)
            
            # Log comparison results
            logger.info("\n📊 Cache A/B Testing Results:")
            logger.info("=" * 70)
            
            # Save structured results
            output_file = Path("processed") / f"cache_comparison_{comparison_results['experiment_id']}.json"
            output_file.parent.mkdir(exist_ok=True)
            with open(output_file, "w") as f:
                json.dump(comparison_results, f, indent=2, default=str)
            
            logger.info(f"💾 Detailed results saved to: {output_file}")
            
            # Display summary
            if comparison_results.get("comparison_metrics"):
                logger.info("\n⚡ Cache Performance Impact:")
                for method, metrics in comparison_results["comparison_metrics"].items():
                    logger.info(f"{method}: {metrics['cache_speedup_percentage']:.1f}% speedup with cache")
        else:
            # Run single mode evaluation
            results = await run_evaluation(question, chains, cache_mode)
            
            # Log results
            logger.info(f"\n📊 Retrieval Strategy Results (Cache {cache_mode.upper()}):")
            logger.info("=" * 50)
            for method, data in results.items():
                if "response" in data:
                    logger.info(f"\n{method:15} Latency: {data['latency_ms']:.0f}ms")
                    logger.info(f"{'':15} Response: {data['response'][:100]}...")
                else:
                    logger.info(f"\n{method:15} Error: {data.get('error', 'Unknown')}")
        
        logger.info(f"\n✅ Evaluation complete! View traces at: {config.phoenix_endpoint}")
        
    except Exception as e:
        logger.error(f"❌ Error during execution: {e}")
        raise
    finally:
        logger.info("🔄 Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())
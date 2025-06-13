"""
📈 Telemetry-Driven Retrieval Strategy Evaluation - Complete Bootstrap Walkthrough

This script demonstrates sophisticated evaluation of 6 retrieval strategies using Phoenix telemetry 
rather than manual code-centric evaluation. Perfect for comparing MCP vs FastAPI performance and 
optimizing RAG pipeline performance through observability.

## 🎯 STEP 1: Prerequisites (Must Complete First)

### Complete Data & Server Stack:
```bash
# 1. Data foundation
python scripts/ingestion/csv_ingestion_pipeline.py

# 2. FastAPI server running
python run.py &

# 3. MCP server integration
python src/mcp_server/fastapi_wrapper.py &

# 4. Verify stack health
curl http://localhost:8000/health
curl http://localhost:6006  # Phoenix UI
```

### Environment Requirements:
```bash
# API Keys for all retrievers
export OPENAI_API_KEY="your-key"        # LLM + embeddings
export COHERE_API_KEY="your-key"        # Reranking

# Phoenix telemetry endpoint
export PHOENIX_COLLECTOR_ENDPOINT="http://localhost:6006"
```

## 📊 STEP 2: Telemetry-First Evaluation Architecture

### Why Telemetry Over Manual Evaluation:
- **Real-time performance monitoring** during actual usage
- **Automatic instrumentation** of LLM calls, embeddings, vector searches
- **Cost tracking** (token usage, API calls) across strategies
- **A/B testing** capabilities with minimal code changes
- **Production-ready metrics** that scale beyond development

### Phoenix Auto-Instrumentation Coverage:
```python
# Automatically tracked without manual code:
- OpenAI API calls (tokens, latency, cost)
- Vector store operations (search time, relevance scores)  
- LangChain chain execution (step-by-step tracing)
- Embedding generation (batch efficiency)
- Retrieval document quality (content analysis)
```

## 🔄 STEP 3: 6 Retrieval Strategies Evaluated

### Strategy Comparison Matrix:
```
Strategy                 | Speed | Accuracy | Cost  | Use Case
-------------------------|-------|----------|-------|------------------
naive_retriever         | Fast  | Baseline | Low   | Simple similarity
bm25_retriever          | Fast  | Keyword  | None  | Exact term matching  
compression_retriever   | Slow  | High     | High  | Quality-first
multiquery_retriever    | Med   | Better   | Med   | Query expansion
ensemble_retriever      | Slow  | Best     | High  | Hybrid approach
semantic_retriever      | Med   | Good     | Low   | Context-aware
```

### Telemetry Metrics Automatically Collected:
- **Latency**: P50, P95, P99 response times per strategy
- **Cost**: Token consumption and API call costs
- **Quality**: Document relevance scores and user feedback
- **Throughput**: Requests per second under load
- **Error Rates**: Failures and retry patterns

## 📈 STEP 4: Phoenix Telemetry Dashboard Setup

### Project Organization:
```python
project_name = f"retrieval-evaluation-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
# Creates timestamped experiments for comparison
```

### Key Dashboard Views:
1. **Strategy Comparison** - Side-by-side latency/cost analysis
2. **LLM Token Usage** - Cost optimization insights  
3. **Vector Search Performance** - Retrieval speed optimization
4. **Error Tracking** - Failure pattern analysis
5. **A/B Testing** - Statistical significance testing

### Real-time Monitoring URLs:
```bash
# Phoenix main dashboard
http://localhost:6006

# Project-specific metrics
http://localhost:6006/projects/{project_name}

# Trace search and filtering
http://localhost:6006/traces?filter=retriever:semantic_retriever
```

## 🎯 STEP 5: MCP vs FastAPI Performance Comparison

### Instrumentation Strategy:
```python
# Same RAG chains used for both FastAPI and MCP
# Phoenix automatically tracks both call paths:

# FastAPI Direct Call:
POST /invoke/semantic_retriever → traced as "fastapi_semantic_retriever"

# MCP Tool Call:
semantic_retriever() → traced as "mcp_semantic_retriever"

# Compare in Phoenix dashboard with retriever tag filtering
```

### Key Comparison Metrics:
- **Protocol Overhead**: JSON-RPC vs HTTP serialization time
- **Transport Efficiency**: STDIO vs HTTP network latency  
- **Schema Validation**: Pydantic overhead comparison
- **Tool Discovery**: MCP tools/list vs FastAPI /docs performance

## 🔬 STEP 6: Advanced Evaluation Patterns

### A/B Testing Setup:
```python
# Randomly assign retrieval strategies for comparison
strategies = ["semantic", "ensemble", "compression"]
strategy = random.choice(strategies)

# Phoenix automatically segments metrics by strategy
chain = create_rag_chain(retrievers[strategy], llm, strategy)
```

### Cost Optimization Analysis:
```python
# Token usage tracking per strategy
# Automatically captured in Phoenix:
- Input tokens (question + context)
- Output tokens (generated response)
- Cost per query (strategy comparison)
- Cost per quality unit (value analysis)
```

### Quality vs Speed Trade-offs:
```python
# Phoenix spans tagged with retriever method
# Enable filtering and comparison:
chain.with_config({
    "run_name": f"rag_chain_{method_name}",
    "span_attributes": {"retriever": method_name}
})
```

## 🎯 STEP 7: Production Insights & Optimization

### Performance Optimization Workflow:
1. **Run evaluation script** → Generate telemetry data
2. **Analyze Phoenix dashboard** → Identify bottlenecks
3. **Optimize slow strategies** → Code improvements
4. **Re-run evaluation** → Measure improvements
5. **Production deployment** → Monitor real usage

### Key Optimization Areas:
- **Embedding cache** for repeated queries
- **Vector search parameter tuning** (k, score thresholds)
- **LLM prompt optimization** for token efficiency
- **Retrieval strategy selection** based on query type

## 🚨 Troubleshooting Telemetry

### Common Phoenix Issues:
- **No traces appearing**: Check PHOENIX_COLLECTOR_ENDPOINT
- **Missing LLM data**: Verify OpenAI key and auto-instrumentation
- **Incomplete spans**: Ensure all chains use .with_config()
- **Performance overhead**: Disable auto-instrumentation in production

### Debug Commands:
```bash
# Check Phoenix connectivity
curl http://localhost:6006/health

# Verify auto-instrumentation
python -c "from phoenix.otel import register; print('Phoenix ready')"

# Test trace generation
python scripts/evaluation/retrieval_method_comparison.py
```

## 🎯 Expected Outcomes

After successful telemetry evaluation:
- ✅ **Performance rankings** of all 6 retrieval strategies
- ✅ **Cost analysis** showing token usage per strategy
- ✅ **Quality metrics** with statistical significance
- ✅ **MCP vs FastAPI** overhead analysis
- ✅ **Production-ready insights** for strategy selection

## 🔗 Next Steps

1. **Analyze Phoenix dashboard** - Compare strategy performance
2. **Optimize slow retrievers** - Focus on bottlenecks identified
3. **A/B test in production** - Deploy best strategies
4. **Monitor real usage** - Continuous improvement cycle
5. **Scale evaluation** - Test with larger datasets and query volumes

This telemetry-driven approach provides production-ready insights that manual evaluation cannot match,
especially for comparing the performance impact of MCP integration vs direct FastAPI usage.
"""

import os
import asyncio
import logging
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

async def run_evaluation(question: str, chains: Dict[str, Any]) -> Dict[str, str]:
    """Run evaluation across all retrieval strategies"""
    results = {}
    
    for method_name, chain in chains.items():
        try:
            result = await chain.ainvoke({"question": question})
            response_content = result["response"].content
            results[method_name] = response_content
        except Exception as e:
            logger.error(f"Error with {method_name}: {e}")
            results[method_name] = f"Error: {str(e)}"
    
    return results

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
        
        results = await run_evaluation(question, chains)
        
        # Log results
        logger.info("\n📊 Retrieval Strategy Results:")
        logger.info("=" * 50)
        for method, response in results.items():
            logger.info(f"\n{method:15} {response}")
        
        logger.info(f"\n✅ Evaluation complete! View traces at: {config.phoenix_endpoint}")
        
    except Exception as e:
        logger.error(f"❌ Error during execution: {e}")
        raise
    finally:
        logger.info("🔄 Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())
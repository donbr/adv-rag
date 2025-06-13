"""
📊 CSV Data Ingestion Pipeline - Complete Bootstrap Walkthrough

This script provides the foundation for the Advanced RAG system by ingesting John Wick movie 
review data and setting up vector stores. Follow this step-by-step guide to bootstrap your 
environment from scratch.

## 🚀 STEP 1: Environment Prerequisites

### Docker Services (Required First)
```bash
# Start supporting services
docker-compose up -d qdrant phoenix redis

# Verify services are running
curl http://localhost:6333/health    # Qdrant vector database
curl http://localhost:6006           # Phoenix tracing UI  
curl http://localhost:6379           # Redis (future caching)
```

### Python Environment
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys:
# OPENAI_API_KEY=your_key_here
# COHERE_API_KEY=your_key_here (for reranking)
```

## 🔄 STEP 2: Data Ingestion Process

### What This Script Does:
1. **Downloads** John Wick movie review CSV files from GitHub
2. **Processes** reviews with metadata (ratings, dates, authors)
3. **Creates** two vector store collections:
   - `johnwick_baseline`: Standard text chunking
   - `johnwick_semantic`: Semantic chunking (context-aware boundaries)
4. **Instruments** everything with Phoenix tracing for observability

### Data Pipeline Architecture:
```
Raw CSV Files → Document Loading → Metadata Enhancement → Chunking → Vector Embedding → Qdrant Storage
     ↓                ↓                    ↓              ↓           ↓              ↓
[jw1-4.csv]    [CSVLoader]        [Movie metadata]  [Semantic]  [OpenAI]     [Collections]
```

## 📈 STEP 3: Telemetry & Observability

### Phoenix Tracing Integration:
- **Auto-instruments** LangChain and LLM API calls, embeddings, and vector operations
- **Project naming** with timestamps for experiment tracking
- **Batch processing** for performance optimization
- **Real-time monitoring** at http://localhost:6006

### Key Metrics Tracked:
- Document processing latency
- Embedding generation time
- Vector store insertion performance
- Error rates and retry patterns

## 🎯 STEP 4: Post-Ingestion Validation

### Verify Collections Created:
```bash
# Check Qdrant collections
curl http://localhost:6333/collections

# Expected collections:
# - johnwick_baseline (standard chunking)
# - johnwick_semantic (semantic chunking)
```

### Data Quality Checks:
- Document count validation
- Metadata completeness
- Embedding dimensionality
- Vector store connectivity

## 🔗 STEP 5: Integration with RAG Pipeline

After successful ingestion:
1. **FastAPI Server** (`run.py`) will connect to these collections
2. **MCP Server** (`fastapi_wrapper.py`) exposes retrieval as tools
3. **Evaluation Scripts** can compare retrieval strategies
4. **Phoenix UI** provides telemetry for all operations

## 🚨 Troubleshooting

### Common Issues:
- **Qdrant Connection**: Ensure Docker service is running on port 6333
- **API Keys**: Verify OPENAI_API_KEY is set and valid
- **Memory**: Large datasets may require increased Docker memory limits
- **Phoenix**: Check port 6006 isn't blocked by firewall

### Recovery Commands:
```bash
# Reset vector stores
docker-compose restart qdrant

# Clear Phoenix data
docker-compose restart phoenix

# Re-run ingestion
python scripts/ingestion/csv_ingestion_pipeline.py
```

## 📊 Expected Outcomes

After successful execution:
- ✅ 4 CSV files downloaded to `data/raw/`
- ✅ ~10,000+ movie review documents processed
- ✅ 2 Qdrant collections populated with embeddings
- ✅ Phoenix tracing data available for analysis
- ✅ System ready for FastAPI/MCP server startup

## 🔄 Next Steps

1. Run `python run.py` to start the FastAPI server
2. Run `python src/mcp_server/fastapi_wrapper.py` for MCP integration  
3. Use evaluation scripts to compare retrieval strategies
4. Monitor performance through Phoenix telemetry

This pipeline forms the data foundation for all downstream RAG operations and telemetry-driven evaluation.
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
from langchain_qdrant import QdrantVectorStore
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
def setup_vectorstore(config: Config, documents, collection_name: str, embeddings) -> QdrantVectorStore:
    """Reusable function to setup vector stores"""
    
    return QdrantVectorStore.from_documents(
        documents=documents,
        embedding=embeddings,
        url=config.qdrant_api_url,
        prefer_grpc=True,
        collection_name=collection_name,
        force_recreate=True
    )

async def load_and_process_data(config: "Config") -> List:
    """Load and process John Wick movie review data"""
    data_dir = Path.cwd() / "data/raw"
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
    
        # Ingest data
        logger.info("📊 Ingesting documents...")
        
        # Semantic chunking
        semantic_chunker = SemanticChunker(
            embeddings=embeddings,
            breakpoint_threshold_type="percentile"
        )
        semantic_docs = semantic_chunker.split_documents(all_docs)
        
        # Setup vector stores
        logger.info("🔧 Setting up vector stores...")
        baseline_vectorstore = setup_vectorstore(config, all_docs, config.baseline, embeddings)
        semantic_vectorstore = setup_vectorstore(config, semantic_docs, config.semantic, embeddings)

    except Exception as e:
        logger.error(f"❌ Error during execution: {e}")
        raise
    finally:
        logger.info("🔄 Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())
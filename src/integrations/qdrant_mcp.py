"""
Enhanced Qdrant MCP Server with Validation Framework

Task 2.1: Extend existing Qdrant MCP servers with validation metadata support.

This module provides enhanced Qdrant MCP functionality including:
- Validation metadata support for Phoenix experiments
- Confidence scoring and filtering
- Pattern storage with experiment provenance
- Hybrid search with metadata filtering
- Cross-MCP pattern sharing capabilities

The server extends basic vector storage with intelligence from Phoenix experiments.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from contextlib import asynccontextmanager

import numpy as np
from qdrant_client import QdrantClient, models as qdrant_models
from qdrant_client.http.models import Distance, VectorParams, CreateCollection
from langchain_qdrant import QdrantVectorStore
from pydantic import BaseModel, Field

from mcp.server import Server
from mcp.types import Resource, Tool, TextResourceContents, EmbeddedResource

from src.core.settings import get_settings
from src.rag.embeddings import get_openai_embeddings
from src.integrations.phoenix_mcp import ExtractedPattern, PhoenixMCPClient

logger = logging.getLogger(__name__)

# Enhanced collection names for validated patterns
ENHANCED_CODE_SNIPPETS_COLLECTION = "enhanced_code_snippets"
ENHANCED_SEMANTIC_MEMORY_COLLECTION = "enhanced_semantic_memory"
PATTERN_VALIDATION_COLLECTION = "pattern_validation"

@dataclass
class ValidationMetadata:
    """Validation metadata structure for enhanced Qdrant patterns."""
    confidence_score: float
    qa_correctness_score: float
    rag_relevance_score: float
    experiment_id: str
    dataset_id: str
    validation_timestamp: str
    pattern_type: str
    validation_status: str
    expiration_date: Optional[str] = None


class EnhancedQdrantPattern(BaseModel):
    """Enhanced pattern with validation metadata for Qdrant storage."""
    pattern_id: str = Field(description="Unique pattern identifier")
    content: str = Field(description="Pattern content (code, semantic text)")
    pattern_type: str = Field(description="Type: code_snippet, semantic_memory, or phoenix_validated")
    validation_metadata: ValidationMetadata = Field(description="Phoenix validation information")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    category: str = Field(default="general", description="Pattern category")


class EnhancedQdrantMCPServer:
    """
    Enhanced Qdrant MCP Server with validation framework support.
    
    Task 2.1: Core implementation extending existing Qdrant MCP with:
    - Validation metadata indexing
    - Confidence-based filtering
    - Phoenix experiment integration
    - Pattern expiration and refresh
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.embeddings = get_openai_embeddings()
        self.phoenix_client = PhoenixMCPClient()
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            url=self.settings.qdrant_url,
            prefer_grpc=True
        )
        
        # Collection configurations
        self.collections_config = {
            ENHANCED_CODE_SNIPPETS_COLLECTION: {
                "description": "Enhanced code snippets with validation metadata",
                "vector_size": 1536,  # text-embedding-3-small dimension
                "distance": Distance.COSINE
            },
            ENHANCED_SEMANTIC_MEMORY_COLLECTION: {
                "description": "Enhanced semantic memory with validation metadata", 
                "vector_size": 1536,
                "distance": Distance.COSINE
            },
            PATTERN_VALIDATION_COLLECTION: {
                "description": "Validation patterns from Phoenix experiments",
                "vector_size": 1536,
                "distance": Distance.COSINE
            }
        }
        
        self.logger = logging.getLogger(__name__)
    
    async def initialize_collections(self):
        """Initialize enhanced Qdrant collections with validation metadata support."""
        for collection_name, config in self.collections_config.items():
            try:
                # Check if collection exists
                collections = await asyncio.to_thread(self.qdrant_client.get_collections)
                existing_collections = [c.name for c in collections.collections]
                
                if collection_name not in existing_collections:
                    self.logger.info(f"Creating enhanced collection: {collection_name}")
                    
                    # Create collection with validation metadata payload schema
                    await asyncio.to_thread(
                        self.qdrant_client.create_collection,
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=config["vector_size"],
                            distance=config["distance"]
                        )
                    )
                    
                    # Create indexes for validation metadata
                    await self._create_validation_indexes(collection_name)
                    
                    self.logger.info(f"Enhanced collection {collection_name} created successfully")
                else:
                    self.logger.info(f"Enhanced collection {collection_name} already exists")
                    
            except Exception as e:
                self.logger.error(f"Failed to initialize collection {collection_name}: {e}")
                raise
    
    async def _create_validation_indexes(self, collection_name: str):
        """Create indexes for validation metadata fields."""
        try:
            # Index for confidence scores (range queries)
            await asyncio.to_thread(
                self.qdrant_client.create_payload_index,
                collection_name=collection_name,
                field_name="validation_metadata.confidence_score",
                field_schema=qdrant_models.PayloadSchemaType.FLOAT
            )
            
            # Index for experiment IDs (exact match)
            await asyncio.to_thread(
                self.qdrant_client.create_payload_index,
                collection_name=collection_name,
                field_name="validation_metadata.experiment_id",
                field_schema=qdrant_models.PayloadSchemaType.KEYWORD
            )
            
            # Index for pattern types
            await asyncio.to_thread(
                self.qdrant_client.create_payload_index,
                collection_name=collection_name,
                field_name="pattern_type",
                field_schema=qdrant_models.PayloadSchemaType.KEYWORD
            )
            
            # Index for validation status
            await asyncio.to_thread(
                self.qdrant_client.create_payload_index,
                collection_name=collection_name,
                field_name="validation_metadata.validation_status",
                field_schema=qdrant_models.PayloadSchemaType.KEYWORD
            )
            
            self.logger.info(f"Created validation indexes for collection {collection_name}")
            
        except Exception as e:
            self.logger.warning(f"Failed to create some indexes for {collection_name}: {e}")
    
    async def store_validated_pattern(
        self,
        pattern: EnhancedQdrantPattern,
        collection_name: str = PATTERN_VALIDATION_COLLECTION
    ) -> str:
        """
        Store a validated pattern with metadata.
        
        Args:
            pattern: Enhanced pattern with validation metadata
            collection_name: Target collection for storage
            
        Returns:
            Pattern ID of stored pattern
        """
        try:
            # Generate embedding for the pattern content
            embedding = await asyncio.to_thread(
                self.embeddings.embed_query,
                pattern.content
            )
            
            # Create point with validation metadata
            point = qdrant_models.PointStruct(
                id=pattern.pattern_id,
                vector=embedding,
                payload={
                    "content": pattern.content,
                    "pattern_type": pattern.pattern_type,
                    "tags": pattern.tags,
                    "category": pattern.category,
                    "validation_metadata": {
                        "confidence_score": pattern.validation_metadata.confidence_score,
                        "qa_correctness_score": pattern.validation_metadata.qa_correctness_score,
                        "rag_relevance_score": pattern.validation_metadata.rag_relevance_score,
                        "experiment_id": pattern.validation_metadata.experiment_id,
                        "dataset_id": pattern.validation_metadata.dataset_id,
                        "validation_timestamp": pattern.validation_metadata.validation_timestamp,
                        "pattern_type": pattern.validation_metadata.pattern_type,
                        "validation_status": pattern.validation_metadata.validation_status,
                        "expiration_date": pattern.validation_metadata.expiration_date
                    },
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
            )
            
            # Store in Qdrant
            await asyncio.to_thread(
                self.qdrant_client.upsert,
                collection_name=collection_name,
                points=[point]
            )
            
            self.logger.info(f"Stored validated pattern {pattern.pattern_id} in {collection_name}")
            return pattern.pattern_id
            
        except Exception as e:
            self.logger.error(f"Failed to store pattern {pattern.pattern_id}: {e}")
            raise
    
    async def find_patterns_with_confidence(
        self,
        query: str,
        min_confidence: float = 0.7,
        collection_name: str = PATTERN_VALIDATION_COLLECTION,
        limit: int = 5,
        pattern_type: Optional[str] = None,
        experiment_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find patterns with confidence filtering and metadata.
        
        Task 2.1: Enhanced search with validation metadata support.
        
        Args:
            query: Search query text
            min_confidence: Minimum confidence score threshold
            collection_name: Collection to search
            limit: Maximum number of results
            pattern_type: Filter by pattern type
            experiment_id: Filter by specific experiment
            
        Returns:
            List of patterns with validation metadata
        """
        try:
            # Generate query embedding
            query_embedding = await asyncio.to_thread(
                self.embeddings.embed_query,
                query
            )
            
            # Build filter conditions
            filter_conditions = [
                qdrant_models.FieldCondition(
                    key="validation_metadata.confidence_score",
                    range=qdrant_models.Range(gte=min_confidence)
                )
            ]
            
            if pattern_type:
                filter_conditions.append(
                    qdrant_models.FieldCondition(
                        key="pattern_type",
                        match=qdrant_models.MatchValue(value=pattern_type)
                    )
                )
            
            if experiment_id:
                filter_conditions.append(
                    qdrant_models.FieldCondition(
                        key="validation_metadata.experiment_id",
                        match=qdrant_models.MatchValue(value=experiment_id)
                    )
                )
            
            # Create filter
            search_filter = qdrant_models.Filter(
                must=filter_conditions
            ) if filter_conditions else None
            
            # Perform search
            search_results = await asyncio.to_thread(
                self.qdrant_client.search,
                collection_name=collection_name,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            # Format results with validation metadata
            results = []
            for hit in search_results:
                result = {
                    "pattern_id": hit.id,
                    "content": hit.payload.get("content", ""),
                    "similarity_score": hit.score,
                    "validation_metadata": hit.payload.get("validation_metadata", {}),
                    "pattern_type": hit.payload.get("pattern_type", ""),
                    "tags": hit.payload.get("tags", []),
                    "category": hit.payload.get("category", "general"),
                    "created_at": hit.payload.get("created_at", ""),
                    "updated_at": hit.payload.get("updated_at", "")
                }
                results.append(result)
            
            self.logger.info(f"Found {len(results)} patterns with confidence >= {min_confidence}")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to search patterns: {e}")
            raise
    
    async def sync_phoenix_patterns(
        self,
        dataset_id: str,
        qa_threshold: float = 0.8,
        min_confidence: float = 0.7,
        max_patterns: int = 100
    ) -> Dict[str, Any]:
        """
        Synchronize patterns from Phoenix experiments.
        
        Task 2.1: Integration with Phoenix pattern extraction.
        
        Args:
            dataset_id: Phoenix dataset to sync from
            qa_threshold: Minimum QA correctness threshold
            min_confidence: Minimum confidence threshold
            max_patterns: Maximum patterns to sync
            
        Returns:
            Sync summary with statistics
        """
        try:
            self.logger.info(f"Starting Phoenix pattern sync for dataset {dataset_id}")
            
            # Get patterns from Phoenix
            dataset_analysis = await self.phoenix_client.analyze_dataset_for_golden_patterns(
                dataset_id=dataset_id,
                qa_threshold=qa_threshold,
                min_confidence=min_confidence,
                max_experiments=max_patterns // 10  # Assume ~10 patterns per experiment
            )
            
            patterns_stored = 0
            failed_storage = 0
            
            # Store each pattern in enhanced collection
            for pattern in dataset_analysis.successful_patterns[:max_patterns]:
                try:
                    # Convert Phoenix pattern to enhanced format
                    enhanced_pattern = EnhancedQdrantPattern(
                        pattern_id=pattern.pattern_id,
                        content=f"Query: {pattern.query}\nResponse: {pattern.response}",
                        pattern_type="phoenix_validated",
                        validation_metadata=ValidationMetadata(
                            confidence_score=pattern.confidence_score,
                            qa_correctness_score=pattern.qa_correctness_score,
                            rag_relevance_score=pattern.rag_relevance_score,
                            experiment_id=pattern.experiment_id,
                            dataset_id=pattern.dataset_id,
                            validation_timestamp=datetime.utcnow().isoformat(),
                            pattern_type="phoenix_validated",
                            validation_status="validated",
                            expiration_date=(datetime.utcnow() + timedelta(days=30)).isoformat()
                        ),
                        tags=["phoenix", "validated", "golden_testset"],
                        category="qa_pattern"
                    )
                    
                    await self.store_validated_pattern(enhanced_pattern)
                    patterns_stored += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to store pattern {pattern.pattern_id}: {e}")
                    failed_storage += 1
            
            sync_summary = {
                "dataset_id": dataset_id,
                "sync_timestamp": datetime.utcnow().isoformat(),
                "total_phoenix_patterns": len(dataset_analysis.successful_patterns),
                "patterns_stored": patterns_stored,
                "failed_storage": failed_storage,
                "success_rate": patterns_stored / len(dataset_analysis.successful_patterns) if dataset_analysis.successful_patterns else 0.0,
                "thresholds_used": {
                    "qa_threshold": qa_threshold,
                    "min_confidence": min_confidence
                }
            }
            
            self.logger.info(f"Phoenix sync completed: {patterns_stored} patterns stored")
            return sync_summary
            
        except Exception as e:
            self.logger.error(f"Failed to sync Phoenix patterns: {e}")
            raise
    
    async def cleanup_expired_patterns(self) -> Dict[str, int]:
        """Clean up expired patterns from collections."""
        try:
            cleanup_stats = {}
            current_time = datetime.utcnow()
            
            for collection_name in self.collections_config.keys():
                try:
                    # Find expired patterns
                    expired_filter = qdrant_models.Filter(
                        must=[
                            qdrant_models.FieldCondition(
                                key="validation_metadata.expiration_date",
                                range=qdrant_models.Range(lt=current_time.isoformat())
                            )
                        ]
                    )
                    
                    # Get expired pattern IDs
                    expired_results = await asyncio.to_thread(
                        self.qdrant_client.scroll,
                        collection_name=collection_name,
                        scroll_filter=expired_filter,
                        with_payload=False,
                        with_vectors=False
                    )
                    
                    expired_ids = [point.id for point in expired_results[0]]
                    
                    if expired_ids:
                        # Delete expired patterns
                        await asyncio.to_thread(
                            self.qdrant_client.delete,
                            collection_name=collection_name,
                            points_selector=qdrant_models.PointIdsList(points=expired_ids)
                        )
                        
                        cleanup_stats[collection_name] = len(expired_ids)
                        self.logger.info(f"Cleaned up {len(expired_ids)} expired patterns from {collection_name}")
                    else:
                        cleanup_stats[collection_name] = 0
                        
                except Exception as e:
                    self.logger.error(f"Failed to cleanup {collection_name}: {e}")
                    cleanup_stats[collection_name] = -1
            
            return cleanup_stats
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired patterns: {e}")
            raise


# MCP Server Implementation
async def create_enhanced_qdrant_mcp_server() -> Server:
    """Create enhanced Qdrant MCP server with validation framework."""
    server = Server("enhanced-qdrant")
    enhanced_qdrant = EnhancedQdrantMCPServer()
    
    # Initialize collections on startup
    await enhanced_qdrant.initialize_collections()
    
    # Tool: Store validated pattern
    @server.tool("store-validated-pattern")
    async def store_validated_pattern_tool(
        content: str,
        pattern_type: str = "phoenix_validated",
        confidence_score: float = 0.8,
        qa_correctness_score: float = 0.0,
        rag_relevance_score: float = 0.0,
        experiment_id: str = "",
        dataset_id: str = "",
        tags: List[str] = None,
        category: str = "general",
        collection: str = PATTERN_VALIDATION_COLLECTION
    ) -> str:
        """Store a validated pattern with metadata."""
        if tags is None:
            tags = []
            
        pattern = EnhancedQdrantPattern(
            pattern_id=f"pattern_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(content) % 10000}",
            content=content,
            pattern_type=pattern_type,
            validation_metadata=ValidationMetadata(
                confidence_score=confidence_score,
                qa_correctness_score=qa_correctness_score,
                rag_relevance_score=rag_relevance_score,
                experiment_id=experiment_id,
                dataset_id=dataset_id,
                validation_timestamp=datetime.utcnow().isoformat(),
                pattern_type=pattern_type,
                validation_status="validated",
                expiration_date=(datetime.utcnow() + timedelta(days=30)).isoformat()
            ),
            tags=tags,
            category=category
        )
        
        pattern_id = await enhanced_qdrant.store_validated_pattern(pattern, collection)
        return f"Stored pattern {pattern_id} with confidence {confidence_score}"
    
    # Tool: Enhanced find with confidence filtering
    @server.tool("qdrant-find-validated")
    async def find_validated_patterns_tool(
        query: str,
        min_confidence: float = 0.7,
        collection: str = PATTERN_VALIDATION_COLLECTION,
        limit: int = 5,
        pattern_type: str = None,
        experiment_id: str = None
    ) -> str:
        """Find patterns with confidence filtering and validation metadata."""
        results = await enhanced_qdrant.find_patterns_with_confidence(
            query=query,
            min_confidence=min_confidence,
            collection_name=collection,
            limit=limit,
            pattern_type=pattern_type,
            experiment_id=experiment_id
        )
        
        if not results:
            return f"No patterns found with confidence >= {min_confidence}"
        
        formatted_results = []
        for result in results:
            validation = result["validation_metadata"]
            formatted_results.append(
                f"Pattern: {result['content'][:200]}...\n"
                f"Confidence: {validation.get('confidence_score', 0.0):.3f}\n"
                f"QA Score: {validation.get('qa_correctness_score', 0.0):.3f}\n"
                f"RAG Score: {validation.get('rag_relevance_score', 0.0):.3f}\n"
                f"Experiment: {validation.get('experiment_id', 'N/A')}\n"
                f"Similarity: {result['similarity_score']:.3f}\n"
                "---"
            )
        
        return f"Found {len(results)} validated patterns:\n\n" + "\n".join(formatted_results)
    
    # Tool: Sync patterns from Phoenix
    @server.tool("sync-phoenix-patterns")
    async def sync_phoenix_patterns_tool(
        dataset_id: str,
        qa_threshold: float = 0.8,
        min_confidence: float = 0.7,
        max_patterns: int = 100
    ) -> str:
        """Synchronize patterns from Phoenix experiments."""
        sync_result = await enhanced_qdrant.sync_phoenix_patterns(
            dataset_id=dataset_id,
            qa_threshold=qa_threshold,
            min_confidence=min_confidence,
            max_patterns=max_patterns
        )
        
        return (
            f"Phoenix sync completed for dataset {dataset_id}:\n"
            f"- Patterns stored: {sync_result['patterns_stored']}\n"
            f"- Failed storage: {sync_result['failed_storage']}\n"
            f"- Success rate: {sync_result['success_rate']:.1%}\n"
            f"- QA threshold: {sync_result['thresholds_used']['qa_threshold']}\n"
            f"- Confidence threshold: {sync_result['thresholds_used']['min_confidence']}"
        )
    
    # Tool: Cleanup expired patterns
    @server.tool("cleanup-expired-patterns")
    async def cleanup_expired_patterns_tool() -> str:
        """Clean up expired patterns from all collections."""
        cleanup_stats = await enhanced_qdrant.cleanup_expired_patterns()
        
        results = []
        for collection, count in cleanup_stats.items():
            if count >= 0:
                results.append(f"- {collection}: {count} patterns cleaned")
            else:
                results.append(f"- {collection}: cleanup failed")
        
        return "Expired pattern cleanup completed:\n" + "\n".join(results)
    
    # Resource: Collection information
    @server.resource("enhanced-qdrant://collections/{collection_name}")
    async def get_collection_info(collection_name: str) -> str:
        """Get information about enhanced Qdrant collections."""
        try:
            collection_info = await asyncio.to_thread(
                enhanced_qdrant.qdrant_client.get_collection,
                collection_name=collection_name
            )
            
            points_count = await asyncio.to_thread(
                enhanced_qdrant.qdrant_client.count,
                collection_name=collection_name
            )
            
            return (
                f"Enhanced Collection: {collection_name}\n"
                f"Vector Size: {collection_info.config.params.vectors.size}\n"
                f"Distance: {collection_info.config.params.vectors.distance}\n"
                f"Points Count: {points_count.count}\n"
                f"Status: {collection_info.status}\n"
                f"Enhanced Features: Validation metadata, confidence filtering, Phoenix integration"
            )
        except Exception as e:
            return f"Error getting collection info: {e}"
    
    return server


# Standalone server runner
if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server
    
    async def main():
        server = await create_enhanced_qdrant_mcp_server()
        async with stdio_server(server) as streams:
            await server.run(*streams)
    
    asyncio.run(main()) 
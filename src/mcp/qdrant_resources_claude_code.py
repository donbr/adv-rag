# qdrant_resources.py - CQRS-Compliant MCP Resources for Read-Only Qdrant Access

"""
CQRS-Compliant MCP Resources Implementation

This module implements true CQRS pattern separation:
- Resources: Read-only access to Qdrant collections (queries)
- Tools: Command operations that modify data (handled elsewhere)

Following the claude_code_instructions.md guidance:
- Resources for queries: @server:qdrant://collections/johnwick_baseline
- Tools for commands: Use existing MCP tools for data modification
- Zero duplication: Leverage existing vectorstore infrastructure
"""

import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
import numpy as np

# Setup project path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.core.settings import get_settings
from src.rag.embeddings import get_openai_embeddings

logger = logging.getLogger(__name__)

class QdrantResourceProvider:
    """
    CQRS-compliant resource provider for read-only Qdrant access.
    
    This class provides Resources (not Tools) for query operations:
    - Collection metadata access
    - Document retrieval by ID
    - Raw vector similarity search
    - Collection statistics
    
    Command operations (insert, update, delete) are handled by Tools elsewhere.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.embeddings = get_openai_embeddings()
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            url=self.settings.qdrant_url,
            prefer_grpc=True
        )
        
        # Known collections in the system
        self.known_collections = [
            "johnwick_baseline",
            "johnwick_semantic"
        ]
        
        logger.info("QdrantResourceProvider initialized for CQRS read operations")
    
    async def get_collection_info(self, collection_name: str) -> str:
        """
        Get collection metadata and statistics (READ-ONLY).
        
        Resource URI: qdrant://collections/{collection_name}
        """
        try:
            # Get collection information
            collection_info = await asyncio.to_thread(
                self.qdrant_client.get_collection,
                collection_name=collection_name
            )
            
            # Get collection count
            count_result = await asyncio.to_thread(
                self.qdrant_client.count,
                collection_name=collection_name
            )
            
            # Extract vector configuration (handle both dict and object formats)
            vectors_config = collection_info.config.params.vectors
            if isinstance(vectors_config, dict):
                # Qdrant often uses empty string as default vector name
                vector_params = vectors_config.get('', vectors_config.get(list(vectors_config.keys())[0] if vectors_config else None))
                if vector_params:
                    vector_size = getattr(vector_params, 'size', 'Unknown')
                    distance_metric = getattr(vector_params, 'distance', 'Unknown')
                    on_disk = getattr(vector_params, 'on_disk', 'Unknown')
                else:
                    vector_size = distance_metric = on_disk = 'Unknown'
            else:
                vector_size = getattr(vectors_config, 'size', 'Unknown')
                distance_metric = getattr(vectors_config, 'distance', 'Unknown')
                on_disk = getattr(vectors_config, 'on_disk', 'Unknown')
            
            # Format as structured data for LLM consumption
            return f"""# Qdrant Collection: {collection_name}

## Collection Metadata
- **Name**: {collection_name}
- **Status**: {collection_info.status}
- **Vector Size**: {vector_size}
- **Distance Metric**: {distance_metric}
- **Total Documents**: {count_result.count}

## Configuration Details
- **Optimizer Status**: {collection_info.optimizer_status}
- **Indexed Only**: {on_disk}

## CQRS Information
- **Operation Type**: READ-ONLY Resource
- **Access Pattern**: Query/Retrieval Operations
- **Last Updated**: {datetime.utcnow().isoformat()}

## Available Operations
Use these Resource URIs for read-only access:
- Collection info: `qdrant://collections/{collection_name}`
- Document by ID: `qdrant://collections/{collection_name}/documents/{{point_id}}`
- Search: `qdrant://collections/{collection_name}/search?query={{text}}&limit={{n}}`
- Statistics: `qdrant://collections/{collection_name}/stats`

---
*Read-only access via CQRS Resources pattern*
"""
            
        except Exception as e:
            logger.error(f"Failed to get collection info for {collection_name}: {e}")
            return f"""# Error: Collection {collection_name}

## Error Details
- **Type**: {type(e).__name__}
- **Message**: {str(e)}
- **Timestamp**: {datetime.utcnow().isoformat()}

## Troubleshooting
1. Verify collection exists: Check available collections first
2. Check Qdrant service: Ensure Qdrant is running on {self.settings.qdrant_url}
3. Network connectivity: Verify service accessibility

## Available Collections
{', '.join(self.known_collections)}

---
*Error from CQRS Resources*
"""
    
    async def get_document_by_id(self, collection_name: str, point_id: str) -> str:
        """
        Retrieve a specific document by ID (READ-ONLY).
        
        Resource URI: qdrant://collections/{collection_name}/documents/{point_id}
        """
        try:
            # Retrieve specific point
            points = await asyncio.to_thread(
                self.qdrant_client.retrieve,
                collection_name=collection_name,
                ids=[point_id],
                with_payload=True,
                with_vectors=False
            )
            
            if not points:
                return f"""# Document Not Found: {point_id}

## Search Details
- **Collection**: {collection_name}
- **Point ID**: {point_id}
- **Result**: No document found with this ID

## Suggestions
1. Verify the point ID exists in the collection
2. Use search operation to find relevant documents
3. Check collection statistics for available point count

---
*CQRS Resource: Read-Only Access*
"""
            
            point = points[0]
            payload = point.payload or {}
            
            # Extract content safely
            content = payload.get('page_content', payload.get('content', 'No content available'))
            metadata = payload.get('metadata', {})
            
            return f"""# Document: {point_id}

## Content
{content[:500]}{'...' if len(str(content)) > 500 else ''}

## Metadata
{json.dumps(metadata, indent=2, default=str)}

## Document Details
- **Point ID**: {point_id}
- **Collection**: {collection_name}
- **Has Vector**: {point.vector is not None}
- **Payload Size**: {len(payload)} fields

## CQRS Information
- **Operation Type**: READ-ONLY Document Retrieval
- **Access Time**: {datetime.utcnow().isoformat()}

## Related Operations
- Collection info: `qdrant://collections/{collection_name}`
- Search similar: `qdrant://collections/{collection_name}/search?query={{content_excerpt}}`

---
*Retrieved via CQRS Resources pattern*
"""
            
        except Exception as e:
            logger.error(f"Failed to get document {point_id} from {collection_name}: {e}")
            
            # Provide specific guidance for UUID format errors
            error_guidance = ""
            if "Unable to parse UUID" in str(e):
                error_guidance = """
## UUID Format Required
This collection uses UUID format for point IDs. Examples:
- Valid: `a1b2c3d4-e5f6-7890-1234-567890abcdef`
- Invalid: `simple_text_id`

To find valid point IDs, use the search operation first.
"""
            
            return f"""# Error: Document Retrieval Failed

## Error Details
- **Collection**: {collection_name}
- **Point ID**: {point_id}
- **Error Type**: {type(e).__name__}
- **Message**: {str(e)}
{error_guidance}
## Troubleshooting
1. Use search to find valid point IDs: `qdrant://collections/{collection_name}/search?query=text`
2. Ensure point ID is in correct format (UUID or integer)
3. Check if document exists in collection
4. Verify collection is accessible

## Suggested Next Steps
- Search collection: `qdrant://collections/{collection_name}/search?query=content+keywords`
- List collections: `qdrant://collections`

---
*Error from CQRS Resources*
"""
    
    async def search_collection(
        self, 
        collection_name: str, 
        query: str, 
        limit: int = 5,
        with_vectors: bool = False
    ) -> str:
        """
        Perform raw vector search on collection (READ-ONLY).
        
        Resource URI: qdrant://collections/{collection_name}/search?query={text}&limit={n}
        """
        try:
            # Generate query embedding
            query_embedding = await asyncio.to_thread(
                self.embeddings.embed_query,
                query
            )
            
            # Perform vector search
            search_results = await asyncio.to_thread(
                self.qdrant_client.search,
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
                with_payload=True,
                with_vectors=with_vectors
            )
            
            if not search_results:
                return f"""# No Search Results

## Query Details
- **Collection**: {collection_name}
- **Query**: {query}
- **Limit**: {limit}
- **Results**: 0 documents found

## Suggestions
1. Try broader search terms
2. Check if collection has documents
3. Verify collection exists and is populated

---
*CQRS Resource: Read-Only Search*
"""
            
            # Format results
            results_text = []
            for i, hit in enumerate(search_results, 1):
                payload = hit.payload or {}
                content = payload.get('page_content', payload.get('content', 'No content'))
                metadata = payload.get('metadata', {})
                
                results_text.append(f"""## Result {i} (Score: {hit.score:.4f})
**Point ID**: {hit.id}
**Content**: {str(content)[:200]}{'...' if len(str(content)) > 200 else ''}
**Metadata**: {json.dumps(metadata, default=str) if metadata else 'None'}
""")
            
            return f"""# Search Results: {query}

## Query Information
- **Collection**: {collection_name}
- **Query**: {query}
- **Results Found**: {len(search_results)}
- **Search Limit**: {limit}

{chr(10).join(results_text)}

## CQRS Information
- **Operation Type**: READ-ONLY Vector Search
- **Embedding Model**: text-embedding-3-small
- **Search Time**: {datetime.utcnow().isoformat()}

## Available Actions
- Get specific document: `qdrant://collections/{collection_name}/documents/{{point_id}}`
- Collection info: `qdrant://collections/{collection_name}`

---
*Raw vector search via CQRS Resources*
"""
            
        except Exception as e:
            logger.error(f"Failed to search collection {collection_name}: {e}")
            return f"""# Search Error

## Error Details
- **Collection**: {collection_name}
- **Query**: {query}
- **Error Type**: {type(e).__name__}
- **Message**: {str(e)}

## Troubleshooting
1. Verify collection exists and has documents
2. Check query text is valid
3. Ensure embeddings service is available

---
*Error from CQRS Resources*
"""
    
    async def get_collection_stats(self, collection_name: str) -> str:
        """
        Get detailed collection statistics (READ-ONLY).
        
        Resource URI: qdrant://collections/{collection_name}/stats
        """
        try:
            # Get collection info
            collection_info = await asyncio.to_thread(
                self.qdrant_client.get_collection,
                collection_name=collection_name
            )
            
            # Get point count
            count_result = await asyncio.to_thread(
                self.qdrant_client.count,
                collection_name=collection_name
            )
            
            # Try to get cluster info (may not be available in all deployments)
            try:
                cluster_info = await asyncio.to_thread(
                    self.qdrant_client.get_cluster_info
                )
                cluster_status = "Available"
            except:
                cluster_info = None
                cluster_status = "Not Available"
            
            # Extract vector configuration (handle both dict and object formats)
            vectors_config = collection_info.config.params.vectors
            if isinstance(vectors_config, dict):
                # Qdrant often uses empty string as default vector name
                vector_params = vectors_config.get('', vectors_config.get(list(vectors_config.keys())[0] if vectors_config else None))
                if vector_params:
                    vector_size = getattr(vector_params, 'size', 'Unknown')
                    distance_metric = getattr(vector_params, 'distance', 'Unknown')
                else:
                    vector_size = distance_metric = 'Unknown'
            else:
                vector_size = getattr(vectors_config, 'size', 'Unknown')
                distance_metric = getattr(vectors_config, 'distance', 'Unknown')
            
            return f"""# Collection Statistics: {collection_name}

## Basic Statistics
- **Total Points**: {count_result.count}
- **Vector Dimension**: {vector_size}
- **Distance Metric**: {distance_metric}
- **Collection Status**: {collection_info.status}

## Configuration
- **Optimizer Status**: {collection_info.optimizer_status}
- **Indexing**: {'Enabled' if vectors_config else 'Disabled'}

## System Information
- **Cluster Status**: {cluster_status}
- **Qdrant URL**: {self.settings.qdrant_url}
- **Last Checked**: {datetime.utcnow().isoformat()}

## CQRS Resource Information
- **Access Pattern**: Read-Only Statistics
- **Data Freshness**: Real-time
- **Resource Type**: Collection Statistics

## Available Collections
{chr(10).join([f"- {col}" for col in self.known_collections])}

## Usage Examples
```
# Get collection info
@server:qdrant://collections/{collection_name}

# Search documents
@server:qdrant://collections/{collection_name}/search?query=your+search&limit=5

# Get specific document
@server:qdrant://collections/{collection_name}/documents/point_id
```

---
*Statistics via CQRS Resources pattern*
"""
            
        except Exception as e:
            logger.error(f"Failed to get stats for {collection_name}: {e}")
            return f"""# Statistics Error

## Error Details
- **Collection**: {collection_name}
- **Error Type**: {type(e).__name__}
- **Message**: {str(e)}

## Common Issues
1. Collection may not exist
2. Qdrant service may be unavailable
3. Network connectivity issues

---
*Error from CQRS Resources*
"""
    
    async def list_collections(self) -> str:
        """
        List all available collections (READ-ONLY).
        
        Resource URI: qdrant://collections
        """
        try:
            # Get all collections
            collections = await asyncio.to_thread(
                self.qdrant_client.get_collections
            )
            
            # Get detailed info for each collection
            collection_details = []
            for collection in collections.collections:
                try:
                    count_result = await asyncio.to_thread(
                        self.qdrant_client.count,
                        collection_name=collection.name
                    )
                    collection_details.append({
                        'name': collection.name,
                        'count': count_result.count
                    })
                except Exception as e:
                    collection_details.append({
                        'name': collection.name,
                        'count': f'Error: {str(e)}'
                    })
            
            # Format response
            details_text = []
            for detail in collection_details:
                details_text.append(f"- **{detail['name']}**: {detail['count']} documents")
            
            return f"""# Qdrant Collections

## Available Collections
{chr(10).join(details_text)}

## Total Collections
{len(collection_details)} collections available

## CQRS Resource Access
Access each collection using these URI patterns:

### Collection Information
```
@server:qdrant://collections/{{collection_name}}
```

### Document Retrieval
```
@server:qdrant://collections/{{collection_name}}/documents/{{point_id}}
```

### Vector Search
```
@server:qdrant://collections/{{collection_name}}/search?query={{text}}&limit={{n}}
```

### Statistics
```
@server:qdrant://collections/{{collection_name}}/stats
```

## System Information
- **Qdrant URL**: {self.settings.qdrant_url}
- **Query Time**: {datetime.utcnow().isoformat()}
- **Access Pattern**: Read-Only Resource

---
*Collection listing via CQRS Resources*
"""
            
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return f"""# Collections List Error

## Error Details
- **Error Type**: {type(e).__name__}
- **Message**: {str(e)}
- **Qdrant URL**: {self.settings.qdrant_url}

## Troubleshooting
1. Verify Qdrant service is running
2. Check network connectivity
3. Ensure proper authentication if required

---
*Error from CQRS Resources*
"""


# Global instance for FastMCP integration
qdrant_resources = QdrantResourceProvider()


# FastMCP Resource Functions (for integration with existing MCP server)
async def get_collection_info_resource(collection_name: str) -> str:
    """FastMCP resource for collection information."""
    return await qdrant_resources.get_collection_info(collection_name)

async def get_document_resource(collection_name: str, point_id: str) -> str:
    """FastMCP resource for document retrieval."""
    return await qdrant_resources.get_document_by_id(collection_name, point_id)

async def search_collection_resource(collection_name: str, query: str, limit: int = 5) -> str:
    """FastMCP resource for collection search."""
    return await qdrant_resources.search_collection(collection_name, query, limit)

async def get_collection_stats_resource(collection_name: str) -> str:
    """FastMCP resource for collection statistics."""
    return await qdrant_resources.get_collection_stats(collection_name)

async def list_collections_resource() -> str:
    """FastMCP resource for listing all collections."""
    return await qdrant_resources.list_collections()


if __name__ == "__main__":
    # Test the resource provider
    import asyncio
    
    async def test_resources():
        """Test CQRS resources functionality."""
        provider = QdrantResourceProvider()
        
        print("Testing CQRS Qdrant Resources...")
        
        # Test collection listing
        print("\n1. Listing collections:")
        result = await provider.list_collections()
        print(result[:500] + "..." if len(result) > 500 else result)
        
        # Test collection info
        print("\n2. Getting collection info:")
        result = await provider.get_collection_info("johnwick_baseline")
        print(result[:500] + "..." if len(result) > 500 else result)
        
        # Test search
        print("\n3. Testing search:")
        result = await provider.search_collection("johnwick_baseline", "action movie", limit=2)
        print(result[:500] + "..." if len(result) > 500 else result)
        
        print("\nCQRS Resources test completed!")
    
    asyncio.run(test_resources())
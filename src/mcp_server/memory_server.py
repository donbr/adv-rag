#!/usr/bin/env python3
"""
FastMCP Memory Server - Brain-inspired memory system with PostgreSQL + pgvector
Implements Tools for memory storage (mutations) and Resources for memory retrieval (read-only)
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import asyncpg
import numpy as np
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Add project root to Python path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import our existing embeddings module
from src.embeddings import get_openai_embeddings
from src.settings import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for memory operations
class MemoryInput(BaseModel):
    content: str = Field(..., description="The content to store in memory")
    memory_type: str = Field(default="short_term", description="Type of memory: short_term, long_term, episodic, semantic")
    importance: str = Field(default="medium", description="Importance level: low, medium, high, critical")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    source_context: Optional[str] = Field(None, description="Context where this memory originated")

class ConsolidationInput(BaseModel):
    memory_type: Optional[str] = Field(None, description="Type of memories to consolidate (optional)")
    min_importance: str = Field(default="medium", description="Minimum importance level for consolidation")

class ForgetInput(BaseModel):
    memory_id: Optional[str] = Field(None, description="Specific memory ID to forget")
    memory_type: Optional[str] = Field(None, description="Type of memories to forget")
    older_than_days: Optional[int] = Field(None, description="Forget memories older than N days")

# Memory Server Class
class MemoryServer:
    def __init__(self):
        self.settings = get_settings()
        self.embeddings = get_openai_embeddings()
        self.db_pool: Optional[asyncpg.Pool] = None
        
    async def initialize_db_pool(self):
        """Initialize database connection pool"""
        try:
            # Database connection parameters
            db_config = {
                'host': os.getenv('POSTGRES_HOST', 'localhost'),
                'port': int(os.getenv('POSTGRES_PORT', '5432')),
                'database': os.getenv('POSTGRES_DB', 'memory_db'),
                'user': os.getenv('POSTGRES_USER', 'memory_user'),
                'password': os.getenv('POSTGRES_PASSWORD', 'memory_pass'),
            }
            
            self.db_pool = await asyncpg.create_pool(
                min_size=2,
                max_size=10,
                **db_config
            )
            logger.info("Database connection pool initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close_db_pool(self):
        """Close database connection pool"""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("Database connection pool closed")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI embeddings"""
        try:
            # Use our existing embeddings module
            embedding_result = await self.embeddings.aembed_query(text)
            return embedding_result
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def store_memory(self, memory_input: MemoryInput) -> Dict[str, Any]:
        """Store a new memory (Tool - has side effects)"""
        try:
            # Generate embedding for the content
            embedding = await self.generate_embedding(memory_input.content)
            
            async with self.db_pool.acquire() as conn:
                # Insert memory into database
                memory_id = await conn.fetchval("""
                    INSERT INTO memories (content, embedding, memory_type, importance, tags, metadata, source_context)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                """, 
                memory_input.content,
                embedding,
                memory_input.memory_type,
                memory_input.importance,
                memory_input.tags,
                json.dumps(memory_input.metadata),
                memory_input.source_context
                )
                
                logger.info(f"Stored memory with ID: {memory_id}")
                
                return {
                    "success": True,
                    "memory_id": str(memory_id),
                    "content": memory_input.content,
                    "memory_type": memory_input.memory_type,
                    "importance": memory_input.importance,
                    "created_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def consolidate_memories(self, consolidation_input: ConsolidationInput) -> Dict[str, Any]:
        """Consolidate memories (Tool - has side effects)"""
        try:
            async with self.db_pool.acquire() as conn:
                # Run consolidation function
                consolidated_count = await conn.fetchval("SELECT consolidate_memories()")
                
                # Apply memory decay
                await conn.execute("SELECT apply_memory_decay()")
                
                logger.info(f"Consolidated {consolidated_count} memories")
                
                return {
                    "success": True,
                    "consolidated_count": consolidated_count,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to consolidate memories: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def forget_memories(self, forget_input: ForgetInput) -> Dict[str, Any]:
        """Forget memories (Tool - has side effects)"""
        try:
            async with self.db_pool.acquire() as conn:
                deleted_count = 0
                
                if forget_input.memory_id:
                    # Delete specific memory
                    result = await conn.execute(
                        "DELETE FROM memories WHERE id = $1",
                        UUID(forget_input.memory_id)
                    )
                    deleted_count = int(result.split()[-1])
                    
                elif forget_input.older_than_days:
                    # Delete old memories
                    result = await conn.execute("""
                        DELETE FROM memories 
                        WHERE created_at < NOW() - INTERVAL '%s days'
                        AND memory_type = COALESCE($1, memory_type)
                    """, forget_input.older_than_days, forget_input.memory_type)
                    deleted_count = int(result.split()[-1])
                
                logger.info(f"Forgot {deleted_count} memories")
                
                return {
                    "success": True,
                    "deleted_count": deleted_count,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to forget memories: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def retrieve_memories(self, query: str, memory_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve memories by similarity search (Resource - read-only)"""
        try:
            # Generate embedding for query
            query_embedding = await self.generate_embedding(query)
            
            async with self.db_pool.acquire() as conn:
                # Determine memory types to search
                if memory_type:
                    memory_types = [memory_type]
                else:
                    memory_types = ['short_term', 'long_term', 'episodic', 'semantic']
                
                # Search for similar memories
                rows = await conn.fetch("""
                    SELECT * FROM find_similar_memories($1, $2, $3, $4)
                """, query_embedding, memory_types, 0.6, limit)
                
                memories = []
                for row in rows:
                    memories.append({
                        "id": str(row['id']),
                        "content": row['content'],
                        "memory_type": row['memory_type'],
                        "importance": row['importance'],
                        "similarity": float(row['similarity']),
                        "created_at": row['created_at'].isoformat(),
                        "last_accessed": row['last_accessed'].isoformat()
                    })
                
                logger.info(f"Retrieved {len(memories)} memories for query: {query}")
                return memories
                
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []

# Initialize memory server
memory_server = MemoryServer()

# Create FastMCP server
mcp = FastMCP("FastMCP Memory System")

# Tools (memory storage operations - have side effects)
@mcp.tool()
async def store_memory(memory_input: MemoryInput) -> Dict[str, Any]:
    """Store a new memory in the brain-inspired memory system.
    
    This tool creates a new memory entry with automatic embedding generation,
    categorization by memory type, and importance scoring.
    """
    if not memory_server.db_pool:
        await memory_server.initialize_db_pool()
    
    return await memory_server.store_memory(memory_input)

@mcp.tool()
async def consolidate_memories(consolidation_input: ConsolidationInput) -> Dict[str, Any]:
    """Consolidate memories by promoting important short-term memories to long-term.
    
    This tool implements brain-inspired memory consolidation, automatically
    promoting frequently accessed or high-importance memories.
    """
    if not memory_server.db_pool:
        await memory_server.initialize_db_pool()
    
    return await memory_server.consolidate_memories(consolidation_input)

@mcp.tool()
async def forget_memories(forget_input: ForgetInput) -> Dict[str, Any]:
    """Forget memories by ID, type, or age.
    
    This tool implements selective forgetting, allowing removal of specific
    memories or bulk deletion based on criteria.
    """
    if not memory_server.db_pool:
        await memory_server.initialize_db_pool()
    
    return await memory_server.forget_memories(forget_input)

# Resources (memory retrieval operations - read-only, parameterized access)
@mcp.resource("memory://all/{query}")
async def retrieve_all_memories(query: str) -> str:
    """Retrieve memories from all memory types using similarity search."""
    if not memory_server.db_pool:
        await memory_server.initialize_db_pool()
    
    memories = await memory_server.retrieve_memories(query, memory_type=None, limit=10)
    
    if not memories:
        return f"No memories found for query: {query}"
    
    result = f"Found {len(memories)} memories for '{query}':\n\n"
    for memory in memories:
        result += f"**{memory['memory_type'].title()} Memory** (Similarity: {memory['similarity']:.2f})\n"
        result += f"Content: {memory['content']}\n"
        result += f"Importance: {memory['importance']}\n"
        result += f"Created: {memory['created_at']}\n\n"
    
    return result

@mcp.resource("memory://short_term/{query}")
async def retrieve_short_term_memories(query: str) -> str:
    """Retrieve short-term memories using similarity search."""
    if not memory_server.db_pool:
        await memory_server.initialize_db_pool()
    
    memories = await memory_server.retrieve_memories(query, memory_type="short_term", limit=5)
    
    if not memories:
        return f"No short-term memories found for query: {query}"
    
    result = f"Found {len(memories)} short-term memories for '{query}':\n\n"
    for memory in memories:
        result += f"Content: {memory['content']}\n"
        result += f"Similarity: {memory['similarity']:.2f}\n"
        result += f"Created: {memory['created_at']}\n\n"
    
    return result

@mcp.resource("memory://long_term/{query}")
async def retrieve_long_term_memories(query: str) -> str:
    """Retrieve long-term memories using similarity search."""
    if not memory_server.db_pool:
        await memory_server.initialize_db_pool()
    
    memories = await memory_server.retrieve_memories(query, memory_type="long_term", limit=10)
    
    if not memories:
        return f"No long-term memories found for query: {query}"
    
    result = f"Found {len(memories)} long-term memories for '{query}':\n\n"
    for memory in memories:
        result += f"Content: {memory['content']}\n"
        result += f"Similarity: {memory['similarity']:.2f}\n"
        result += f"Importance: {memory['importance']}\n"
        result += f"Created: {memory['created_at']}\n\n"
    
    return result

@mcp.resource("memory://episodic/{query}")
async def retrieve_episodic_memories(query: str) -> str:
    """Retrieve episodic memories (specific events/contexts) using similarity search."""
    if not memory_server.db_pool:
        await memory_server.initialize_db_pool()
    
    memories = await memory_server.retrieve_memories(query, memory_type="episodic", limit=8)
    
    if not memories:
        return f"No episodic memories found for query: {query}"
    
    result = f"Found {len(memories)} episodic memories for '{query}':\n\n"
    for memory in memories:
        result += f"Content: {memory['content']}\n"
        result += f"Similarity: {memory['similarity']:.2f}\n"
        result += f"Created: {memory['created_at']}\n\n"
    
    return result

@mcp.resource("memory://semantic/{query}")
async def retrieve_semantic_memories(query: str) -> str:
    """Retrieve semantic memories (general knowledge/patterns) using similarity search."""
    if not memory_server.db_pool:
        await memory_server.initialize_db_pool()
    
    memories = await memory_server.retrieve_memories(query, memory_type="semantic", limit=10)
    
    if not memories:
        return f"No semantic memories found for query: {query}"
    
    result = f"Found {len(memories)} semantic memories for '{query}':\n\n"
    for memory in memories:
        result += f"Content: {memory['content']}\n"
        result += f"Similarity: {memory['similarity']:.2f}\n"
        result += f"Importance: {memory['importance']}\n"
        result += f"Created: {memory['created_at']}\n\n"
    
    return result

# Health check resource
@mcp.resource("memory://health")
async def memory_health() -> str:
    """Check memory system health and statistics."""
    try:
        if not memory_server.db_pool:
            await memory_server.initialize_db_pool()
        
        async with memory_server.db_pool.acquire() as conn:
            # Get memory statistics
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_memories,
                    COUNT(*) FILTER (WHERE memory_type = 'short_term') as short_term_count,
                    COUNT(*) FILTER (WHERE memory_type = 'long_term') as long_term_count,
                    COUNT(*) FILTER (WHERE memory_type = 'episodic') as episodic_count,
                    COUNT(*) FILTER (WHERE memory_type = 'semantic') as semantic_count,
                    AVG(access_count) as avg_access_count,
                    MAX(created_at) as latest_memory
                FROM memories
            """)
            
            return f"""Memory System Health Report:
            
Total Memories: {stats['total_memories']}
- Short-term: {stats['short_term_count']}
- Long-term: {stats['long_term_count']}
- Episodic: {stats['episodic_count']}
- Semantic: {stats['semantic_count']}

Average Access Count: {stats['avg_access_count']:.2f}
Latest Memory: {stats['latest_memory']}

Database Status: Connected ✅
Embeddings: OpenAI text-embedding-3-small ✅
Vector Search: pgvector enabled ✅
"""
    
    except Exception as e:
        return f"Memory System Health: ERROR - {str(e)}"

# Cleanup function
async def cleanup():
    """Cleanup resources on shutdown"""
    await memory_server.close_db_pool()

if __name__ == "__main__":
    import signal
    
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal, cleaning up...")
        asyncio.create_task(cleanup())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the MCP server
    mcp.run(transport="stdio") 
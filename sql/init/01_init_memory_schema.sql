-- FastMCP Memory System Database Schema
-- Brain-inspired memory architecture with PostgreSQL + pgvector

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create enum for memory types
CREATE TYPE memory_type AS ENUM ('short_term', 'long_term', 'episodic', 'semantic');

-- Create enum for importance levels
CREATE TYPE importance_level AS ENUM ('low', 'medium', 'high', 'critical');

-- Main memories table
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI text-embedding-3-small dimension
    memory_type memory_type NOT NULL DEFAULT 'short_term',
    importance importance_level NOT NULL DEFAULT 'medium',
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    source_context TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    decay_factor REAL DEFAULT 1.0,
    consolidation_score REAL DEFAULT 0.0,
    
    -- Indexes for performance
    CONSTRAINT memories_embedding_check CHECK (vector_dims(embedding) = 1536)
);

-- Memory consolidation tracking
CREATE TABLE memory_consolidation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_memory_ids UUID[] NOT NULL,
    consolidated_memory_id UUID REFERENCES memories(id),
    consolidation_type VARCHAR(50) NOT NULL,
    consolidation_score REAL NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Memory relationships (for associative memory)
CREATE TABLE memory_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_a_id UUID REFERENCES memories(id) ON DELETE CASCADE,
    memory_b_id UUID REFERENCES memories(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    strength REAL NOT NULL DEFAULT 0.5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(memory_a_id, memory_b_id, relationship_type)
);

-- Create indexes for performance
CREATE INDEX idx_memories_type ON memories(memory_type);
CREATE INDEX idx_memories_importance ON memories(importance);
CREATE INDEX idx_memories_created_at ON memories(created_at);
CREATE INDEX idx_memories_last_accessed ON memories(last_accessed);
CREATE INDEX idx_memories_tags ON memories USING GIN(tags);
CREATE INDEX idx_memories_metadata ON memories USING GIN(metadata);

-- Vector similarity search index
CREATE INDEX idx_memories_embedding ON memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Consolidation indexes
CREATE INDEX idx_consolidation_created_at ON memory_consolidation(created_at);
CREATE INDEX idx_consolidation_type ON memory_consolidation(consolidation_type);

-- Relationship indexes
CREATE INDEX idx_relationships_memory_a ON memory_relationships(memory_a_id);
CREATE INDEX idx_relationships_memory_b ON memory_relationships(memory_b_id);
CREATE INDEX idx_relationships_type ON memory_relationships(relationship_type);

-- Function to update last_accessed timestamp
CREATE OR REPLACE FUNCTION update_memory_access()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_accessed = NOW();
    NEW.access_count = OLD.access_count + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update access tracking
CREATE TRIGGER trigger_update_memory_access
    BEFORE UPDATE ON memories
    FOR EACH ROW
    WHEN (OLD.content IS DISTINCT FROM NEW.content OR OLD.embedding IS DISTINCT FROM NEW.embedding)
    EXECUTE FUNCTION update_memory_access();

-- Function for memory decay (short-term memories fade over time)
CREATE OR REPLACE FUNCTION apply_memory_decay()
RETURNS void AS $$
BEGIN
    UPDATE memories 
    SET decay_factor = GREATEST(0.1, decay_factor * 0.95)
    WHERE memory_type = 'short_term' 
    AND last_accessed < NOW() - INTERVAL '1 hour';
END;
$$ LANGUAGE plpgsql;

-- Function to find similar memories using vector similarity
CREATE OR REPLACE FUNCTION find_similar_memories(
    query_embedding vector(1536),
    memory_types memory_type[] DEFAULT ARRAY['short_term', 'long_term', 'episodic', 'semantic'],
    similarity_threshold REAL DEFAULT 0.7,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    memory_type memory_type,
    importance importance_level,
    similarity REAL,
    created_at TIMESTAMP WITH TIME ZONE,
    last_accessed TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.content,
        m.memory_type,
        m.importance,
        1 - (m.embedding <=> query_embedding) AS similarity,
        m.created_at,
        m.last_accessed
    FROM memories m
    WHERE m.memory_type = ANY(memory_types)
    AND 1 - (m.embedding <=> query_embedding) >= similarity_threshold
    ORDER BY m.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Function for memory consolidation (promote important short-term to long-term)
CREATE OR REPLACE FUNCTION consolidate_memories()
RETURNS INTEGER AS $$
DECLARE
    consolidated_count INTEGER := 0;
    memory_record RECORD;
BEGIN
    -- Find high-importance, frequently accessed short-term memories
    FOR memory_record IN
        SELECT id, content, embedding, importance, access_count, created_at
        FROM memories
        WHERE memory_type = 'short_term'
        AND (importance IN ('high', 'critical') OR access_count >= 5)
        AND created_at < NOW() - INTERVAL '1 day'
    LOOP
        -- Promote to long-term memory
        UPDATE memories
        SET memory_type = 'long_term',
            consolidation_score = LEAST(1.0, (memory_record.access_count::REAL / 10.0) + 
                                       CASE memory_record.importance
                                           WHEN 'critical' THEN 0.9
                                           WHEN 'high' THEN 0.7
                                           WHEN 'medium' THEN 0.5
                                           ELSE 0.3
                                       END)
        WHERE id = memory_record.id;
        
        consolidated_count := consolidated_count + 1;
    END LOOP;
    
    RETURN consolidated_count;
END;
$$ LANGUAGE plpgsql;

-- Create initial system memory
INSERT INTO memories (content, memory_type, importance, tags, metadata) VALUES
('FastMCP Memory System initialized with brain-inspired architecture', 'semantic', 'high', 
 ARRAY['system', 'initialization'], 
 '{"system": true, "version": "1.0", "features": ["pgvector", "consolidation", "decay"]}');

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO memory_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO memory_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO memory_user; 
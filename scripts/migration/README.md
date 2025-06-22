# PostgreSQL pgvector to Qdrant Migration

This directory contains tools for migrating vector data from PostgreSQL pgvector tables to Qdrant collections, preserving embeddings and metadata for continued use with the current RAG system.

## Migration Purpose

The legacy code in `legacy/code/` uses PostgreSQL pgvector for vector storage and RAGAS for golden dataset generation. This migration script allows you to:

- **Preserve existing embeddings** without re-computing them
- **Maintain golden dataset linkage** for Phoenix experiments
- **Migrate to Qdrant** for better performance and MCP integration
- **Retain all metadata** including RAGAS-generated test data

## Quick Start

### Prerequisites

1. **Running Services**:
   ```bash
   # Start PostgreSQL (legacy)
   docker run -it --rm --name pgvector-container \
     -e POSTGRES_USER=langchain \
     -e POSTGRES_PASSWORD=langchain \
     -e POSTGRES_DB=langchain \
     -p 6024:5432 \
     pgvector/pgvector:pg16
   
   # Start Qdrant (current)
   docker-compose up -d qdrant
   ```

2. **Environment Setup**:
   ```bash
   # Activate virtual environment
   source .venv/bin/activate
   
   # Set PostgreSQL password if needed
   export POSTGRES_PASSWORD=langchain
   ```

### Migration Commands

```bash
# Dry run to validate migration
python scripts/migration/pgvector_to_qdrant_migration.py --dry-run

# Run actual migration
python scripts/migration/pgvector_to_qdrant_migration.py

# Custom batch size for large datasets
python scripts/migration/pgvector_to_qdrant_migration.py --batch-size 200

# Override PostgreSQL password
python scripts/migration/pgvector_to_qdrant_migration.py --postgres-password your_password
```

## Migration Process

### 1. Data Extraction
- Connects to PostgreSQL pgvector database
- Extracts vectors, documents, and metadata in batches
- Preserves UUID identifiers and all metadata fields

### 2. Collection Creation
- Creates Qdrant collections with proper configuration
- Uses cosine distance metric (matching legacy implementation)
- Vector size: 1536 (text-embedding-3-small)

### 3. Data Loading
- Converts PostgreSQL data types to Qdrant format
- Preserves document content and all metadata
- Maintains referential integrity for Phoenix experiments

### 4. Validation
- Generates detailed migration report
- Tracks success/failure rates
- Preserves original data (non-destructive)

## Table Mappings

| PostgreSQL Table | Qdrant Collection | Purpose |
|------------------|-------------------|---------|
| `johnwick_baseline_documents` | `johnwick_baseline` | Basic chunking strategy |
| `johnwick_semantic_documents` | `johnwick_semantic` | Semantic chunking strategy |

## Configuration

The migration script uses these default settings:

```python
@dataclass
class MigrationConfig:
    # PostgreSQL (legacy)
    postgres_host: str = "localhost"
    postgres_port: str = "6024"
    postgres_user: str = "langchain"
    postgres_password: str = "langchain"
    postgres_db: str = "langchain"
    
    # Qdrant (current)
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    
    # Migration settings
    batch_size: int = 100
    vector_size: int = 1536
    distance_metric: Distance = Distance.COSINE
```

## Migration Report

Each migration generates a detailed JSON report:

```json
{
  "status": "SUCCESS",
  "start_time": "2025-06-22T10:00:00",
  "end_time": "2025-06-22T10:05:00",
  "summary": {
    "total_records": 2500,
    "migrated_records": 2500,
    "failed_records": 0,
    "success_rate": 100.0
  },
  "table_migrations": [...]
}
```

## Integration with Current System

After migration, the current RAG system can immediately use the migrated data:

```bash
# Verify collections exist
curl http://localhost:6333/collections

# Test retrieval with migrated data
curl -X POST "http://localhost:8000/invoke/semantic_retriever" \
     -H "Content-Type: application/json" \
     -d '{"question": "What makes John Wick movies popular?"}'
```

## Golden Dataset Preservation

The migration preserves RAGAS-generated golden datasets:

1. **Document Metadata**: All original metadata fields preserved
2. **Phoenix Linkage**: Experiment tracking data maintained
3. **Evaluation Metrics**: Ready for continued Phoenix experiments
4. **Test Questions**: RAGAS-generated Q&A pairs preserved

## Troubleshooting

### Common Issues

**Connection Errors**:
```bash
# Check PostgreSQL
docker ps | grep pgvector
netstat -tulpn | grep 6024

# Check Qdrant
docker ps | grep qdrant
curl http://localhost:6333/health
```

**Memory Issues**:
```bash
# Reduce batch size
python scripts/migration/pgvector_to_qdrant_migration.py --batch-size 50
```

**Permission Errors**:
```bash
# Verify PostgreSQL password
python -c "
import os
from sqlalchemy import create_engine
engine = create_engine('postgresql://langchain:langchain@localhost:6024/langchain')
print(engine.execute('SELECT 1').scalar())
"
```

### Validation Commands

```bash
# Check PostgreSQL table counts
python -c "
from sqlalchemy import create_engine
engine = create_engine('postgresql://langchain:langchain@localhost:6024/langchain')
print('Baseline:', engine.execute('SELECT COUNT(*) FROM johnwick_baseline_documents').scalar())
print('Semantic:', engine.execute('SELECT COUNT(*) FROM johnwick_semantic_documents').scalar())
"

# Check Qdrant collection counts
curl "http://localhost:6333/collections/johnwick_baseline" | jq '.result.points_count'
curl "http://localhost:6333/collections/johnwick_semantic" | jq '.result.points_count'
```

## Best Practices

1. **Always run dry-run first** to validate configuration
2. **Backup PostgreSQL data** before migration (though script is non-destructive)
3. **Monitor migration progress** via logs and reports
4. **Validate data integrity** after migration
5. **Keep migration reports** for audit trails

## Next Steps

After successful migration:

1. **Update ingestion pipeline** to use Qdrant directly
2. **Decommission PostgreSQL** (after validation)
3. **Run Phoenix experiments** with migrated data
4. **Update documentation** to reflect new architecture

The migration enables you to leverage the current RAG system's MCP integration while preserving all the valuable RAGAS-generated evaluation data from the legacy implementation.
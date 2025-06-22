#!/usr/bin/env python3
"""
PostgreSQL pgvector to Qdrant Migration Script

Migrates existing vector data from PostgreSQL pgvector tables to Qdrant collections,
preserving embeddings, metadata, and golden dataset linkage for Phoenix experiments.

Based on analysis of legacy/code implementation:
- Maintains johnwick_baseline_documents and johnwick_semantic_documents collections
- Preserves RAGAS golden dataset compatibility
- Retains all metadata fields for Phoenix experiment tracking
"""
import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import json

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, BatchRequest
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class MigrationConfig:
    """Configuration for PostgreSQL to Qdrant migration"""
    # PostgreSQL settings (from legacy code)
    postgres_user: str = "langchain"
    postgres_password: str = "langchain"
    postgres_host: str = "localhost"
    postgres_port: str = "6024"
    postgres_db: str = "langchain"
    
    # Qdrant settings (matching current implementation)
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_grpc_port: int = 6334
    
    # Table/Collection mappings
    table_mappings: Dict[str, str] = None
    
    # Migration settings
    batch_size: int = 100
    vector_size: int = 1536
    distance_metric: Distance = Distance.COSINE
    dry_run: bool = False
    
    def __post_init__(self):
        if self.table_mappings is None:
            self.table_mappings = {
                "johnwick_baseline_documents": "johnwick_baseline",
                "johnwick_semantic_documents": "johnwick_semantic"
            }
    
    @property
    def postgres_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


class PostgreSQLExtractor:
    """Extract vector data from PostgreSQL pgvector tables"""
    
    def __init__(self, config: MigrationConfig):
        self.config = config
        self.engine = create_engine(config.postgres_url)
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get table schema information"""
        query = text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = :table_name
            ORDER BY ordinal_position;
        """)
        
        with self.engine.connect() as conn:
            result = conn.execute(query, {"table_name": table_name})
            columns = [dict(row._mapping) for row in result]
        
        return {"table_name": table_name, "columns": columns}
    
    def get_table_count(self, table_name: str) -> int:
        """Get total record count for table"""
        query = text(f"SELECT COUNT(*) as count FROM {table_name}")
        
        with self.engine.connect() as conn:
            result = conn.execute(query)
            return result.fetchone().count
    
    def extract_vectors_batch(self, table_name: str, offset: int, batch_size: int) -> List[Dict[str, Any]]:
        """Extract a batch of vectors and metadata from PostgreSQL"""
        # Query adapted from legacy langchain_postgres schema
        query = text(f"""
            SELECT 
                id,
                document,
                cmetadata,
                embedding
            FROM {table_name}
            ORDER BY id
            OFFSET :offset
            LIMIT :batch_size
        """)
        
        with self.engine.connect() as conn:
            result = conn.execute(query, {"offset": offset, "batch_size": batch_size})
            rows = []
            
            for row in result:
                # Convert PostgreSQL data types to Python types
                metadata = dict(row.cmetadata) if row.cmetadata else {}
                
                # Extract embedding vector (pgvector format)
                embedding = list(row.embedding) if row.embedding else None
                
                rows.append({
                    "id": str(row.id),  # Convert UUID to string for Qdrant
                    "document": row.document,
                    "metadata": metadata,
                    "embedding": embedding
                })
            
            return rows


class QdrantLoader:
    """Load vector data into Qdrant collections"""
    
    def __init__(self, config: MigrationConfig):
        self.config = config
        self.client = QdrantClient(
            host=config.qdrant_host,
            port=config.qdrant_port,
            grpc_port=config.qdrant_grpc_port
        )
    
    def create_collection(self, collection_name: str) -> bool:
        """Create Qdrant collection with proper configuration"""
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            existing_names = [col.name for col in collections]
            
            if collection_name in existing_names:
                logger.warning(f"Collection {collection_name} already exists")
                if not self.config.dry_run:
                    response = input(f"Delete and recreate collection {collection_name}? (y/N): ")
                    if response.lower() == 'y':
                        self.client.delete_collection(collection_name)
                    else:
                        return False
            
            if not self.config.dry_run:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.config.vector_size,
                        distance=self.config.distance_metric
                    )
                )
                logger.info(f"✅ Created collection: {collection_name}")
            else:
                logger.info(f"🔍 [DRY RUN] Would create collection: {collection_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating collection {collection_name}: {e}")
            return False
    
    def load_vectors_batch(self, collection_name: str, vectors: List[Dict[str, Any]]) -> bool:
        """Load a batch of vectors into Qdrant collection"""
        try:
            points = []
            
            for vector_data in vectors:
                if not vector_data.get("embedding"):
                    logger.warning(f"Skipping record {vector_data['id']} - no embedding")
                    continue
                
                # Prepare payload (metadata + document content)
                payload = {
                    "document": vector_data["document"],
                    **vector_data["metadata"]
                }
                
                point = PointStruct(
                    id=vector_data["id"],
                    vector=vector_data["embedding"],
                    payload=payload
                )
                points.append(point)
            
            if not self.config.dry_run and points:
                self.client.upsert(
                    collection_name=collection_name,
                    points=points
                )
                logger.info(f"✅ Loaded {len(points)} points to {collection_name}")
            else:
                logger.info(f"🔍 [DRY RUN] Would load {len(points)} points to {collection_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading batch to {collection_name}: {e}")
            return False


class MigrationRunner:
    """Orchestrate the migration process"""
    
    def __init__(self, config: MigrationConfig):
        self.config = config
        self.extractor = PostgreSQLExtractor(config)
        self.loader = QdrantLoader(config)
        self.migration_stats = {}
    
    def validate_prerequisites(self) -> bool:
        """Validate that all prerequisites are met"""
        try:
            # Test PostgreSQL connection
            with self.extractor.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ PostgreSQL connection successful")
            
            # Test Qdrant connection
            self.loader.client.get_collections()
            logger.info("✅ Qdrant connection successful")
            
            # Validate tables exist
            for pg_table in self.config.table_mappings.keys():
                try:
                    count = self.extractor.get_table_count(pg_table)
                    logger.info(f"✅ Table {pg_table}: {count} records")
                except Exception as e:
                    logger.error(f"❌ Table {pg_table} not accessible: {e}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Prerequisites validation failed: {e}")
            return False
    
    def migrate_table(self, pg_table: str, qdrant_collection: str) -> Dict[str, Any]:
        """Migrate a single table to Qdrant collection"""
        logger.info(f"🚀 Starting migration: {pg_table} → {qdrant_collection}")
        
        # Initialize stats
        stats = {
            "table_name": pg_table,
            "collection_name": qdrant_collection,
            "total_records": 0,
            "migrated_records": 0,
            "failed_records": 0,
            "start_time": datetime.now(),
            "end_time": None
        }
        
        try:
            # Get total record count
            total_records = self.extractor.get_table_count(pg_table)
            stats["total_records"] = total_records
            logger.info(f"📊 Total records to migrate: {total_records}")
            
            # Create Qdrant collection
            if not self.loader.create_collection(qdrant_collection):
                raise Exception(f"Failed to create collection {qdrant_collection}")
            
            # Migrate in batches
            offset = 0
            while offset < total_records:
                logger.info(f"📦 Processing batch: {offset}-{min(offset + self.config.batch_size, total_records)}")
                
                # Extract batch from PostgreSQL
                vectors = self.extractor.extract_vectors_batch(
                    pg_table, offset, self.config.batch_size
                )
                
                if not vectors:
                    break
                
                # Load batch to Qdrant
                if self.loader.load_vectors_batch(qdrant_collection, vectors):
                    stats["migrated_records"] += len(vectors)
                else:
                    stats["failed_records"] += len(vectors)
                
                offset += self.config.batch_size
            
            stats["end_time"] = datetime.now()
            duration = stats["end_time"] - stats["start_time"]
            logger.info(f"✅ Migration completed in {duration}")
            logger.info(f"📈 Success rate: {stats['migrated_records']}/{stats['total_records']} ({stats['migrated_records']/stats['total_records']*100:.1f}%)")
            
        except Exception as e:
            logger.error(f"❌ Migration failed for {pg_table}: {e}")
            stats["error"] = str(e)
            stats["end_time"] = datetime.now()
        
        return stats
    
    def run_migration(self) -> Dict[str, Any]:
        """Run complete migration process"""
        logger.info("🚀 Starting PostgreSQL to Qdrant migration")
        
        if not self.validate_prerequisites():
            return {"status": "FAILED", "error": "Prerequisites validation failed"}
        
        migration_results = {
            "status": "SUCCESS",
            "start_time": datetime.now(),
            "table_migrations": [],
            "summary": {}
        }
        
        try:
            # Migrate each table
            for pg_table, qdrant_collection in self.config.table_mappings.items():
                stats = self.migrate_table(pg_table, qdrant_collection)
                migration_results["table_migrations"].append(stats)
            
            # Calculate summary statistics
            total_records = sum(s["total_records"] for s in migration_results["table_migrations"])
            migrated_records = sum(s["migrated_records"] for s in migration_results["table_migrations"])
            failed_records = sum(s["failed_records"] for s in migration_results["table_migrations"])
            
            migration_results["summary"] = {
                "total_tables": len(self.config.table_mappings),
                "total_records": total_records,
                "migrated_records": migrated_records,
                "failed_records": failed_records,
                "success_rate": migrated_records / total_records * 100 if total_records > 0 else 0
            }
            
            migration_results["end_time"] = datetime.now()
            duration = migration_results["end_time"] - migration_results["start_time"]
            
            logger.info("🎉 Migration completed!")
            logger.info(f"⏱️  Total duration: {duration}")
            logger.info(f"📊 Overall success rate: {migration_results['summary']['success_rate']:.1f}%")
            
        except Exception as e:
            logger.error(f"❌ Migration process failed: {e}")
            migration_results["status"] = "FAILED"
            migration_results["error"] = str(e)
        
        return migration_results


def main():
    """Main execution function"""
    load_dotenv()
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Migrate PostgreSQL pgvector data to Qdrant")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run without actual migration")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for migration")
    parser.add_argument("--postgres-password", help="PostgreSQL password (overrides .env)")
    args = parser.parse_args()
    
    # Create configuration
    config = MigrationConfig(
        dry_run=args.dry_run,
        batch_size=args.batch_size
    )
    
    # Override postgres password if provided
    if args.postgres_password:
        config.postgres_password = args.postgres_password
    elif os.getenv("POSTGRES_PASSWORD"):
        config.postgres_password = os.getenv("POSTGRES_PASSWORD")
    
    logger.info("🔧 Migration Configuration:")
    logger.info(f"  PostgreSQL: {config.postgres_host}:{config.postgres_port}/{config.postgres_db}")
    logger.info(f"  Qdrant: {config.qdrant_host}:{config.qdrant_port}")
    logger.info(f"  Batch size: {config.batch_size}")
    logger.info(f"  Dry run: {config.dry_run}")
    logger.info(f"  Tables to migrate: {list(config.table_mappings.keys())}")
    
    # Run migration
    runner = MigrationRunner(config)
    results = runner.run_migration()
    
    # Save migration report
    report_file = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"📋 Migration report saved: {report_file}")
    
    return results


if __name__ == "__main__":
    results = main()
    exit_code = 0 if results["status"] == "SUCCESS" else 1
    exit(exit_code)
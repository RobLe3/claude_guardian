"""
Database management for Claude Guardian
Handles PostgreSQL, Qdrant, and Redis connections
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

try:
    import asyncpg
    import redis.asyncio as redis
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
except ImportError:
    # Graceful handling if dependencies aren't installed yet
    asyncpg = None
    redis = None
    QdrantClient = None
    models = None

from .config import DatabaseConfig

logger = logging.getLogger(__name__)


@dataclass
class ConnectionHealth:
    """Health status for database connections"""
    postgres: bool = False
    qdrant: bool = False
    redis: bool = False
    
    @property
    def all_healthy(self) -> bool:
        return self.postgres and self.qdrant and self.redis


class DatabaseManager:
    """Manages all database connections and operations"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.postgres_pool: Optional[asyncpg.Pool] = None
        self.qdrant_client: Optional[QdrantClient] = None
        self.redis_client: Optional[redis.Redis] = None
        
    async def initialize(self) -> None:
        """Initialize all database connections"""
        logger.info("🔌 Initializing database connections...")
        
        # Initialize PostgreSQL
        if asyncpg:
            try:
                self.postgres_pool = await asyncpg.create_pool(
                    self.config.postgres_url,
                    min_size=1,
                    max_size=10,
                    command_timeout=30
                )
                logger.info("✅ PostgreSQL connection established")
            except Exception as e:
                logger.warning(f"⚠️ PostgreSQL connection failed: {e}")
        
        # Initialize Qdrant
        if QdrantClient:
            try:
                self.qdrant_client = QdrantClient(url=self.config.qdrant_url)
                # Test connection
                collections = self.qdrant_client.get_collections()
                logger.info(f"✅ Qdrant connection established ({len(collections.collections)} collections)")
            except Exception as e:
                logger.warning(f"⚠️ Qdrant connection failed: {e}")
        
        # Initialize Redis
        if redis:
            try:
                self.redis_client = redis.from_url(self.config.redis_url)
                await self.redis_client.ping()
                logger.info("✅ Redis connection established")
            except Exception as e:
                logger.warning(f"⚠️ Redis connection failed: {e}")
    
    async def health_check(self) -> bool:
        """Check health of all database connections"""
        health = ConnectionHealth()
        
        # Check PostgreSQL
        if self.postgres_pool:
            try:
                async with self.postgres_pool.acquire() as conn:
                    await conn.execute('SELECT 1')
                health.postgres = True
            except:
                health.postgres = False
        
        # Check Qdrant
        if self.qdrant_client:
            try:
                self.qdrant_client.get_collections()
                health.qdrant = True
            except:
                health.qdrant = False
        
        # Check Redis
        if self.redis_client:
            try:
                await self.redis_client.ping()
                health.redis = True
            except:
                health.redis = False
        
        return health.all_healthy
    
    async def seed_initial_data(self) -> None:
        """Seed initial security data and collections"""
        logger.info("🌱 Seeding initial security data...")
        
        if self.qdrant_client and models:
            # Create security collections if they don't exist
            collections_to_create = [
                "security_procedures",
                "vulnerability_db", 
                "attack_signatures",
                "threat_patterns"
            ]
            
            existing_collections = {
                c.name for c in self.qdrant_client.get_collections().collections
            }
            
            for collection_name in collections_to_create:
                if collection_name not in existing_collections:
                    try:
                        self.qdrant_client.create_collection(
                            collection_name=collection_name,
                            vectors_config=models.VectorParams(
                                size=384,  # all-MiniLM-L6-v2 embedding size
                                distance=models.Distance.COSINE
                            )
                        )
                        logger.info(f"✅ Created collection: {collection_name}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to create collection {collection_name}: {e}")
        
        if self.postgres_pool:
            # Create basic tables if they don't exist
            try:
                async with self.postgres_pool.acquire() as conn:
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS security_events (
                            id SERIAL PRIMARY KEY,
                            timestamp TIMESTAMPTZ DEFAULT NOW(),
                            event_type VARCHAR(100),
                            severity VARCHAR(20),
                            source VARCHAR(100),
                            description TEXT,
                            metadata JSONB
                        )
                    """)
                    
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS scan_results (
                            id SERIAL PRIMARY KEY,
                            timestamp TIMESTAMPTZ DEFAULT NOW(),
                            scan_type VARCHAR(50),
                            target_hash VARCHAR(64),
                            threat_level VARCHAR(20),
                            findings JSONB,
                            processing_time_ms INTEGER
                        )
                    """)
                    
                logger.info("✅ Database schema initialized")
            except Exception as e:
                logger.warning(f"⚠️ Schema initialization failed: {e}")
    
    async def close(self) -> None:
        """Close all database connections"""
        logger.info("🔌 Closing database connections...")
        
        if self.postgres_pool:
            await self.postgres_pool.close()
            
        if self.redis_client:
            await self.redis_client.close()
            
        # Qdrant client doesn't need explicit closing
        logger.info("✅ All connections closed")

    # Convenience methods for common operations
    async def log_security_event(self, event_type: str, severity: str, 
                                 description: str, metadata: Dict[str, Any] = None):
        """Log a security event to PostgreSQL"""
        if not self.postgres_pool:
            return
            
        try:
            async with self.postgres_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO security_events (event_type, severity, description, metadata)
                    VALUES ($1, $2, $3, $4)
                """, event_type, severity, description, metadata or {})
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    async def store_scan_result(self, scan_type: str, target_hash: str,
                               threat_level: str, findings: Dict[str, Any],
                               processing_time_ms: int):
        """Store scan results in PostgreSQL"""
        if not self.postgres_pool:
            return
            
        try:
            async with self.postgres_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO scan_results (scan_type, target_hash, threat_level, findings, processing_time_ms)
                    VALUES ($1, $2, $3, $4, $5)
                """, scan_type, target_hash, threat_level, findings, processing_time_ms)
        except Exception as e:
            logger.error(f"Failed to store scan result: {e}")
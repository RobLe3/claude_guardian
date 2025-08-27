#!/usr/bin/env python3
"""
Claude Guardian Database Performance Benchmark Suite
Tests connection pooling, CRUD operations, and performance metrics
"""

import asyncio
import asyncpg
import redis.asyncio as redis
import time
import statistics
import json
import logging
import psutil
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

# Configuration
DATABASE_CONFIG = {
    'postgres': {
        'url': 'postgresql://cguser:CHANGE_THIS_SECURE_PASSWORD_123!@localhost:5432/claude_guardian',
        'min_size': 1,
        'max_size': 10,
        'command_timeout': 30
    },
    'redis': {
        'url': 'redis://:CHANGE_THIS_REDIS_PASSWORD_123!@localhost:6379/0'
    },
    'qdrant': {
        'url': 'http://localhost:6333'
    }
}

@dataclass
class BenchmarkResult:
    """Container for benchmark results"""
    operation: str
    database: str
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    median_time_ms: float
    std_dev_ms: float
    operations_per_second: float
    success_rate: float
    error_count: int
    total_operations: int
    timestamp: str

@dataclass
class ConnectionBenchmark:
    """Connection establishment benchmark results"""
    database: str
    avg_connection_time_ms: float
    min_connection_time_ms: float
    max_connection_time_ms: float
    success_rate: float
    connection_pool_size: int
    max_concurrent_connections: int

class DatabaseBenchmark:
    """Main benchmark class for testing database performance"""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.connection_results: List[ConnectionBenchmark] = []
        self.postgres_pool: Optional[asyncpg.Pool] = None
        self.redis_client: Optional[redis.Redis] = None
        self.qdrant_client: Optional[QdrantClient] = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def initialize_connections(self):
        """Initialize all database connections"""
        self.logger.info("🔌 Initializing database connections...")
        
        # PostgreSQL
        try:
            self.postgres_pool = await asyncpg.create_pool(
                DATABASE_CONFIG['postgres']['url'],
                min_size=DATABASE_CONFIG['postgres']['min_size'],
                max_size=DATABASE_CONFIG['postgres']['max_size'],
                command_timeout=DATABASE_CONFIG['postgres']['command_timeout']
            )
            self.logger.info("✅ PostgreSQL pool created")
        except Exception as e:
            self.logger.error(f"❌ PostgreSQL connection failed: {e}")
        
        # Redis
        try:
            self.redis_client = redis.from_url(DATABASE_CONFIG['redis']['url'])
            await self.redis_client.ping()
            self.logger.info("✅ Redis connection established")
        except Exception as e:
            self.logger.error(f"❌ Redis connection failed: {e}")
        
        # Qdrant
        if QDRANT_AVAILABLE:
            try:
                self.qdrant_client = QdrantClient(url=DATABASE_CONFIG['qdrant']['url'])
                collections = self.qdrant_client.get_collections()
                self.logger.info(f"✅ Qdrant connection established ({len(collections.collections)} collections)")
            except Exception as e:
                self.logger.error(f"❌ Qdrant connection failed: {e}")
    
    async def benchmark_connection_establishment(self):
        """Benchmark connection establishment times"""
        self.logger.info("📊 Benchmarking connection establishment times...")
        
        # PostgreSQL connection benchmark
        await self._benchmark_postgres_connections()
        
        # Redis connection benchmark
        await self._benchmark_redis_connections()
        
        # Qdrant connection benchmark
        if QDRANT_AVAILABLE:
            await self._benchmark_qdrant_connections()
    
    async def _benchmark_postgres_connections(self):
        """Benchmark PostgreSQL connection establishment"""
        times = []
        success_count = 0
        
        for i in range(20):  # Test 20 connections
            start_time = time.perf_counter()
            try:
                conn = await asyncpg.connect(DATABASE_CONFIG['postgres']['url'])
                await conn.execute('SELECT 1')
                await conn.close()
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)
                success_count += 1
            except Exception as e:
                self.logger.warning(f"Connection {i} failed: {e}")
        
        if times:
            result = ConnectionBenchmark(
                database="PostgreSQL",
                avg_connection_time_ms=statistics.mean(times),
                min_connection_time_ms=min(times),
                max_connection_time_ms=max(times),
                success_rate=success_count / 20,
                connection_pool_size=DATABASE_CONFIG['postgres']['max_size'],
                max_concurrent_connections=10
            )
            self.connection_results.append(result)
    
    async def _benchmark_redis_connections(self):
        """Benchmark Redis connection establishment"""
        times = []
        success_count = 0
        
        for i in range(20):
            start_time = time.perf_counter()
            try:
                temp_client = redis.from_url(DATABASE_CONFIG['redis']['url'])
                await temp_client.ping()
                await temp_client.close()
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)
                success_count += 1
            except Exception as e:
                self.logger.warning(f"Redis connection {i} failed: {e}")
        
        if times:
            result = ConnectionBenchmark(
                database="Redis",
                avg_connection_time_ms=statistics.mean(times),
                min_connection_time_ms=min(times),
                max_connection_time_ms=max(times),
                success_rate=success_count / 20,
                connection_pool_size=1,
                max_concurrent_connections=100
            )
            self.connection_results.append(result)
    
    async def _benchmark_qdrant_connections(self):
        """Benchmark Qdrant connection establishment"""
        times = []
        success_count = 0
        
        for i in range(20):
            start_time = time.perf_counter()
            try:
                temp_client = QdrantClient(url=DATABASE_CONFIG['qdrant']['url'])
                temp_client.get_collections()
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)
                success_count += 1
            except Exception as e:
                self.logger.warning(f"Qdrant connection {i} failed: {e}")
        
        if times:
            result = ConnectionBenchmark(
                database="Qdrant",
                avg_connection_time_ms=statistics.mean(times),
                min_connection_time_ms=min(times),
                max_connection_time_ms=max(times),
                success_rate=success_count / 20,
                connection_pool_size=1,
                max_concurrent_connections=50
            )
            self.connection_results.append(result)
    
    async def benchmark_postgres_operations(self):
        """Benchmark PostgreSQL CRUD operations"""
        if not self.postgres_pool:
            self.logger.warning("PostgreSQL pool not available, skipping benchmarks")
            return
        
        self.logger.info("📊 Benchmarking PostgreSQL operations...")
        
        # Setup test table
        await self._setup_postgres_test_table()
        
        # Benchmark operations
        await self._benchmark_postgres_inserts()
        await self._benchmark_postgres_selects()
        await self._benchmark_postgres_updates()
        await self._benchmark_postgres_deletes()
        await self._benchmark_postgres_complex_queries()
    
    async def _setup_postgres_test_table(self):
        """Setup PostgreSQL test table"""
        async with self.postgres_pool.acquire() as conn:
            await conn.execute("""
                DROP TABLE IF EXISTS benchmark_test;
                CREATE TABLE benchmark_test (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    email VARCHAR(100),
                    age INTEGER,
                    data JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                CREATE INDEX idx_benchmark_email ON benchmark_test(email);
                CREATE INDEX idx_benchmark_age ON benchmark_test(age);
            """)
    
    async def _benchmark_postgres_inserts(self):
        """Benchmark PostgreSQL INSERT operations"""
        times = []
        success_count = 0
        error_count = 0
        num_operations = 1000
        
        for i in range(num_operations):
            start_time = time.perf_counter()
            try:
                async with self.postgres_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO benchmark_test (name, email, age, data)
                        VALUES ($1, $2, $3, $4)
                    """, f"User_{i}", f"user_{i}@example.com", 20 + (i % 50),
                        json.dumps({"test_data": f"data_{i}", "index": i}))
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)
                success_count += 1
            except Exception as e:
                error_count += 1
                self.logger.warning(f"Insert {i} failed: {e}")
        
        if times:
            result = BenchmarkResult(
                operation="INSERT",
                database="PostgreSQL",
                avg_time_ms=statistics.mean(times),
                min_time_ms=min(times),
                max_time_ms=max(times),
                median_time_ms=statistics.median(times),
                std_dev_ms=statistics.stdev(times) if len(times) > 1 else 0,
                operations_per_second=1000 / statistics.mean(times) if times else 0,
                success_rate=success_count / num_operations,
                error_count=error_count,
                total_operations=num_operations,
                timestamp=datetime.now().isoformat()
            )
            self.results.append(result)
    
    async def _benchmark_postgres_selects(self):
        """Benchmark PostgreSQL SELECT operations"""
        times = []
        success_count = 0
        error_count = 0
        num_operations = 1000
        
        for i in range(num_operations):
            start_time = time.perf_counter()
            try:
                async with self.postgres_pool.acquire() as conn:
                    await conn.fetch(
                        "SELECT * FROM benchmark_test WHERE age > $1 LIMIT 10",
                        20 + (i % 30)
                    )
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)
                success_count += 1
            except Exception as e:
                error_count += 1
                self.logger.warning(f"Select {i} failed: {e}")
        
        if times:
            result = BenchmarkResult(
                operation="SELECT",
                database="PostgreSQL",
                avg_time_ms=statistics.mean(times),
                min_time_ms=min(times),
                max_time_ms=max(times),
                median_time_ms=statistics.median(times),
                std_dev_ms=statistics.stdev(times) if len(times) > 1 else 0,
                operations_per_second=1000 / statistics.mean(times) if times else 0,
                success_rate=success_count / num_operations,
                error_count=error_count,
                total_operations=num_operations,
                timestamp=datetime.now().isoformat()
            )
            self.results.append(result)
    
    async def _benchmark_postgres_updates(self):
        """Benchmark PostgreSQL UPDATE operations"""
        times = []
        success_count = 0
        error_count = 0
        num_operations = 500
        
        for i in range(num_operations):
            start_time = time.perf_counter()
            try:
                async with self.postgres_pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE benchmark_test SET age = $1 WHERE id = $2",
                        25 + (i % 40), (i % 1000) + 1
                    )
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)
                success_count += 1
            except Exception as e:
                error_count += 1
                self.logger.warning(f"Update {i} failed: {e}")
        
        if times:
            result = BenchmarkResult(
                operation="UPDATE",
                database="PostgreSQL",
                avg_time_ms=statistics.mean(times),
                min_time_ms=min(times),
                max_time_ms=max(times),
                median_time_ms=statistics.median(times),
                std_dev_ms=statistics.stdev(times) if len(times) > 1 else 0,
                operations_per_second=1000 / statistics.mean(times) if times else 0,
                success_rate=success_count / num_operations,
                error_count=error_count,
                total_operations=num_operations,
                timestamp=datetime.now().isoformat()
            )
            self.results.append(result)
    
    async def _benchmark_postgres_deletes(self):
        """Benchmark PostgreSQL DELETE operations"""
        times = []
        success_count = 0
        error_count = 0
        num_operations = 100
        
        for i in range(num_operations):
            start_time = time.perf_counter()
            try:
                async with self.postgres_pool.acquire() as conn:
                    await conn.execute(
                        "DELETE FROM benchmark_test WHERE id = $1",
                        (i % 1000) + 1
                    )
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)
                success_count += 1
            except Exception as e:
                error_count += 1
                self.logger.warning(f"Delete {i} failed: {e}")
        
        if times:
            result = BenchmarkResult(
                operation="DELETE",
                database="PostgreSQL",
                avg_time_ms=statistics.mean(times),
                min_time_ms=min(times),
                max_time_ms=max(times),
                median_time_ms=statistics.median(times),
                std_dev_ms=statistics.stdev(times) if len(times) > 1 else 0,
                operations_per_second=1000 / statistics.mean(times) if times else 0,
                success_rate=success_count / num_operations,
                error_count=error_count,
                total_operations=num_operations,
                timestamp=datetime.now().isoformat()
            )
            self.results.append(result)
    
    async def _benchmark_postgres_complex_queries(self):
        """Benchmark PostgreSQL complex queries"""
        times = []
        success_count = 0
        error_count = 0
        num_operations = 100
        
        for i in range(num_operations):
            start_time = time.perf_counter()
            try:
                async with self.postgres_pool.acquire() as conn:
                    await conn.fetch("""
                        SELECT 
                            age, 
                            COUNT(*) as count,
                            AVG(LENGTH(name)) as avg_name_length,
                            MIN(created_at) as earliest,
                            MAX(created_at) as latest
                        FROM benchmark_test 
                        WHERE age BETWEEN $1 AND $2
                        GROUP BY age 
                        ORDER BY count DESC 
                        LIMIT 10
                    """, 20 + (i % 20), 40 + (i % 20))
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)
                success_count += 1
            except Exception as e:
                error_count += 1
                self.logger.warning(f"Complex query {i} failed: {e}")
        
        if times:
            result = BenchmarkResult(
                operation="COMPLEX_QUERY",
                database="PostgreSQL",
                avg_time_ms=statistics.mean(times),
                min_time_ms=min(times),
                max_time_ms=max(times),
                median_time_ms=statistics.median(times),
                std_dev_ms=statistics.stdev(times) if len(times) > 1 else 0,
                operations_per_second=1000 / statistics.mean(times) if times else 0,
                success_rate=success_count / num_operations,
                error_count=error_count,
                total_operations=num_operations,
                timestamp=datetime.now().isoformat()
            )
            self.results.append(result)
    
    async def benchmark_redis_operations(self):
        """Benchmark Redis operations"""
        if not self.redis_client:
            self.logger.warning("Redis client not available, skipping benchmarks")
            return
        
        self.logger.info("📊 Benchmarking Redis operations...")
        
        await self._benchmark_redis_strings()
        await self._benchmark_redis_hashes()
        await self._benchmark_redis_lists()
        await self._benchmark_redis_sets()
    
    async def _benchmark_redis_strings(self):
        """Benchmark Redis string operations"""
        times = []
        success_count = 0
        error_count = 0
        num_operations = 1000
        
        # SET operations
        for i in range(num_operations):
            start_time = time.perf_counter()
            try:
                await self.redis_client.set(f"test_key_{i}", f"test_value_{i}")
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)
                success_count += 1
            except Exception as e:
                error_count += 1
                self.logger.warning(f"Redis SET {i} failed: {e}")
        
        if times:
            result = BenchmarkResult(
                operation="SET",
                database="Redis",
                avg_time_ms=statistics.mean(times),
                min_time_ms=min(times),
                max_time_ms=max(times),
                median_time_ms=statistics.median(times),
                std_dev_ms=statistics.stdev(times) if len(times) > 1 else 0,
                operations_per_second=1000 / statistics.mean(times) if times else 0,
                success_rate=success_count / num_operations,
                error_count=error_count,
                total_operations=num_operations,
                timestamp=datetime.now().isoformat()
            )
            self.results.append(result)
        
        # GET operations
        times = []
        success_count = 0
        error_count = 0
        
        for i in range(num_operations):
            start_time = time.perf_counter()
            try:
                await self.redis_client.get(f"test_key_{i}")
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)
                success_count += 1
            except Exception as e:
                error_count += 1
                self.logger.warning(f"Redis GET {i} failed: {e}")
        
        if times:
            result = BenchmarkResult(
                operation="GET",
                database="Redis",
                avg_time_ms=statistics.mean(times),
                min_time_ms=min(times),
                max_time_ms=max(times),
                median_time_ms=statistics.median(times),
                std_dev_ms=statistics.stdev(times) if len(times) > 1 else 0,
                operations_per_second=1000 / statistics.mean(times) if times else 0,
                success_rate=success_count / num_operations,
                error_count=error_count,
                total_operations=num_operations,
                timestamp=datetime.now().isoformat()
            )
            self.results.append(result)
    
    async def _benchmark_redis_hashes(self):
        """Benchmark Redis hash operations"""
        times = []
        success_count = 0
        error_count = 0
        num_operations = 500
        
        for i in range(num_operations):
            start_time = time.perf_counter()
            try:
                await self.redis_client.hset(
                    f"hash_key_{i}", 
                    mapping={
                        "field1": f"value1_{i}",
                        "field2": f"value2_{i}",
                        "field3": json.dumps({"data": f"test_{i}"})
                    }
                )
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)
                success_count += 1
            except Exception as e:
                error_count += 1
                self.logger.warning(f"Redis HSET {i} failed: {e}")
        
        if times:
            result = BenchmarkResult(
                operation="HSET",
                database="Redis",
                avg_time_ms=statistics.mean(times),
                min_time_ms=min(times),
                max_time_ms=max(times),
                median_time_ms=statistics.median(times),
                std_dev_ms=statistics.stdev(times) if len(times) > 1 else 0,
                operations_per_second=1000 / statistics.mean(times) if times else 0,
                success_rate=success_count / num_operations,
                error_count=error_count,
                total_operations=num_operations,
                timestamp=datetime.now().isoformat()
            )
            self.results.append(result)
    
    async def _benchmark_redis_lists(self):
        """Benchmark Redis list operations"""
        times = []
        success_count = 0
        error_count = 0
        num_operations = 500
        
        for i in range(num_operations):
            start_time = time.perf_counter()
            try:
                await self.redis_client.lpush(f"list_key_{i % 10}", f"item_{i}")
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)
                success_count += 1
            except Exception as e:
                error_count += 1
                self.logger.warning(f"Redis LPUSH {i} failed: {e}")
        
        if times:
            result = BenchmarkResult(
                operation="LPUSH",
                database="Redis",
                avg_time_ms=statistics.mean(times),
                min_time_ms=min(times),
                max_time_ms=max(times),
                median_time_ms=statistics.median(times),
                std_dev_ms=statistics.stdev(times) if len(times) > 1 else 0,
                operations_per_second=1000 / statistics.mean(times) if times else 0,
                success_rate=success_count / num_operations,
                error_count=error_count,
                total_operations=num_operations,
                timestamp=datetime.now().isoformat()
            )
            self.results.append(result)
    
    async def _benchmark_redis_sets(self):
        """Benchmark Redis set operations"""
        times = []
        success_count = 0
        error_count = 0
        num_operations = 500
        
        for i in range(num_operations):
            start_time = time.perf_counter()
            try:
                await self.redis_client.sadd(f"set_key_{i % 5}", f"member_{i}")
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)
                success_count += 1
            except Exception as e:
                error_count += 1
                self.logger.warning(f"Redis SADD {i} failed: {e}")
        
        if times:
            result = BenchmarkResult(
                operation="SADD",
                database="Redis",
                avg_time_ms=statistics.mean(times),
                min_time_ms=min(times),
                max_time_ms=max(times),
                median_time_ms=statistics.median(times),
                std_dev_ms=statistics.stdev(times) if len(times) > 1 else 0,
                operations_per_second=1000 / statistics.mean(times) if times else 0,
                success_rate=success_count / num_operations,
                error_count=error_count,
                total_operations=num_operations,
                timestamp=datetime.now().isoformat()
            )
            self.results.append(result)
    
    async def benchmark_qdrant_operations(self):
        """Benchmark Qdrant vector operations"""
        if not self.qdrant_client or not QDRANT_AVAILABLE:
            self.logger.warning("Qdrant client not available, skipping benchmarks")
            return
        
        self.logger.info("📊 Benchmarking Qdrant operations...")
        
        # Setup test collection
        await self._setup_qdrant_collection()
        
        # Benchmark operations
        await self._benchmark_qdrant_inserts()
        await self._benchmark_qdrant_searches()
    
    async def _setup_qdrant_collection(self):
        """Setup Qdrant test collection"""
        collection_name = "benchmark_test_collection"
        
        try:
            # Delete if exists
            try:
                self.qdrant_client.delete_collection(collection_name)
            except:
                pass
            
            # Create new collection
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=128,  # Test vector size
                    distance=models.Distance.COSINE
                )
            )
            self.logger.info(f"Created test collection: {collection_name}")
        except Exception as e:
            self.logger.error(f"Failed to setup Qdrant collection: {e}")
    
    async def _benchmark_qdrant_inserts(self):
        """Benchmark Qdrant vector insertions"""
        times = []
        success_count = 0
        error_count = 0
        num_operations = 100
        collection_name = "benchmark_test_collection"
        
        for i in range(num_operations):
            start_time = time.perf_counter()
            try:
                # Generate random vector
                import random
                vector = [random.random() for _ in range(128)]
                
                self.qdrant_client.upsert(
                    collection_name=collection_name,
                    points=[
                        models.PointStruct(
                            id=i,
                            vector=vector,
                            payload={"index": i, "type": "test"}
                        )
                    ]
                )
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)
                success_count += 1
            except Exception as e:
                error_count += 1
                self.logger.warning(f"Qdrant INSERT {i} failed: {e}")
        
        if times:
            result = BenchmarkResult(
                operation="VECTOR_INSERT",
                database="Qdrant",
                avg_time_ms=statistics.mean(times),
                min_time_ms=min(times),
                max_time_ms=max(times),
                median_time_ms=statistics.median(times),
                std_dev_ms=statistics.stdev(times) if len(times) > 1 else 0,
                operations_per_second=1000 / statistics.mean(times) if times else 0,
                success_rate=success_count / num_operations,
                error_count=error_count,
                total_operations=num_operations,
                timestamp=datetime.now().isoformat()
            )
            self.results.append(result)
    
    async def _benchmark_qdrant_searches(self):
        """Benchmark Qdrant vector searches"""
        times = []
        success_count = 0
        error_count = 0
        num_operations = 100
        collection_name = "benchmark_test_collection"
        
        for i in range(num_operations):
            start_time = time.perf_counter()
            try:
                # Generate random query vector
                import random
                query_vector = [random.random() for _ in range(128)]
                
                self.qdrant_client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=10
                )
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)
                success_count += 1
            except Exception as e:
                error_count += 1
                self.logger.warning(f"Qdrant SEARCH {i} failed: {e}")
        
        if times:
            result = BenchmarkResult(
                operation="VECTOR_SEARCH",
                database="Qdrant",
                avg_time_ms=statistics.mean(times),
                min_time_ms=min(times),
                max_time_ms=max(times),
                median_time_ms=statistics.median(times),
                std_dev_ms=statistics.stdev(times) if len(times) > 1 else 0,
                operations_per_second=1000 / statistics.mean(times) if times else 0,
                success_rate=success_count / num_operations,
                error_count=error_count,
                total_operations=num_operations,
                timestamp=datetime.now().isoformat()
            )
            self.results.append(result)
    
    async def monitor_resource_usage(self) -> Dict[str, Any]:
        """Monitor database resource usage"""
        self.logger.info("📊 Monitoring database resource usage...")
        
        # Get container stats
        container_stats = {}
        
        try:
            import docker
            client = docker.from_env()
            
            for container_name in ['claude-guardian-postgres', 'claude-guardian-redis', 'claude-guardian-qdrant']:
                try:
                    container = client.containers.get(container_name)
                    stats = container.stats(stream=False)
                    
                    # Calculate CPU usage
                    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                               stats['precpu_stats']['cpu_usage']['total_usage']
                    system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                                  stats['precpu_stats']['system_cpu_usage']
                    cpu_percent = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0
                    
                    # Memory usage
                    memory_usage = stats['memory_stats']['usage']
                    memory_limit = stats['memory_stats']['limit']
                    memory_percent = (memory_usage / memory_limit) * 100
                    
                    container_stats[container_name] = {
                        'cpu_percent': cpu_percent,
                        'memory_usage_mb': memory_usage / (1024 * 1024),
                        'memory_percent': memory_percent,
                        'memory_limit_mb': memory_limit / (1024 * 1024),
                        'status': container.status
                    }
                except Exception as e:
                    self.logger.warning(f"Failed to get stats for {container_name}: {e}")
        except ImportError:
            self.logger.warning("Docker library not available for resource monitoring")
        
        # System resource usage
        system_stats = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage_percent': psutil.disk_usage('/').percent
        }
        
        return {
            'containers': container_stats,
            'system': system_stats,
            'timestamp': datetime.now().isoformat()
        }
    
    async def cleanup(self):
        """Cleanup database connections and test data"""
        self.logger.info("🧹 Cleaning up...")
        
        # Close PostgreSQL pool
        if self.postgres_pool:
            await self.postgres_pool.close()
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        # Cleanup Qdrant test collection
        if self.qdrant_client:
            try:
                self.qdrant_client.delete_collection("benchmark_test_collection")
            except:
                pass
    
    def generate_report(self, resource_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_operations_tested': sum(r.total_operations for r in self.results),
                'databases_tested': len(set(r.database for r in self.results)),
                'operation_types': len(set(r.operation for r in self.results)),
                'overall_success_rate': sum(r.success_rate for r in self.results) / len(self.results) if self.results else 0
            },
            'connection_benchmarks': [asdict(r) for r in self.connection_results],
            'operation_benchmarks': [asdict(r) for r in self.results],
            'resource_usage': resource_stats,
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        # Analyze results for recommendations
        postgres_results = [r for r in self.results if r.database == "PostgreSQL"]
        redis_results = [r for r in self.results if r.database == "Redis"]
        qdrant_results = [r for r in self.results if r.database == "Qdrant"]
        
        # PostgreSQL recommendations
        if postgres_results:
            avg_insert_time = next((r.avg_time_ms for r in postgres_results if r.operation == "INSERT"), 0)
            if avg_insert_time > 5:
                recommendations.append("PostgreSQL: Consider batch inserts for better performance")
            
            avg_select_time = next((r.avg_time_ms for r in postgres_results if r.operation == "SELECT"), 0)
            if avg_select_time > 10:
                recommendations.append("PostgreSQL: Review query optimization and indexing strategy")
        
        # Redis recommendations
        if redis_results:
            avg_set_time = next((r.avg_time_ms for r in redis_results if r.operation == "SET"), 0)
            if avg_set_time > 1:
                recommendations.append("Redis: Consider connection pooling or pipelining for better performance")
        
        # Qdrant recommendations
        if qdrant_results:
            avg_search_time = next((r.avg_time_ms for r in qdrant_results if r.operation == "VECTOR_SEARCH"), 0)
            if avg_search_time > 50:
                recommendations.append("Qdrant: Consider optimizing vector dimensions or indexing parameters")
        
        # Connection recommendations
        postgres_conn = next((r for r in self.connection_results if r.database == "PostgreSQL"), None)
        if postgres_conn and postgres_conn.avg_connection_time_ms > 100:
            recommendations.append("PostgreSQL: High connection establishment time - review network configuration")
        
        return recommendations

async def main():
    """Main benchmark execution function"""
    benchmark = DatabaseBenchmark()
    
    try:
        print("🚀 Starting Claude Guardian Database Performance Benchmark")
        print("=" * 60)
        
        # Initialize connections
        await benchmark.initialize_connections()
        
        # Run benchmarks
        await benchmark.benchmark_connection_establishment()
        await benchmark.benchmark_postgres_operations()
        await benchmark.benchmark_redis_operations()
        await benchmark.benchmark_qdrant_operations()
        
        # Monitor resource usage
        resource_stats = await benchmark.monitor_resource_usage()
        
        # Generate report
        report = benchmark.generate_report(resource_stats)
        
        # Save report
        with open('database_performance_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Display summary
        print("\n📊 BENCHMARK RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total Operations Tested: {report['summary']['total_operations_tested']}")
        print(f"Databases Tested: {report['summary']['databases_tested']}")
        print(f"Operation Types: {report['summary']['operation_types']}")
        print(f"Overall Success Rate: {report['summary']['overall_success_rate']:.2%}")
        
        print("\n🔗 CONNECTION BENCHMARKS")
        print("-" * 30)
        for conn in report['connection_benchmarks']:
            print(f"{conn['database']}: {conn['avg_connection_time_ms']:.2f}ms avg")
        
        print("\n⚡ OPERATION PERFORMANCE")
        print("-" * 30)
        for op in report['operation_benchmarks']:
            print(f"{op['database']} {op['operation']}: {op['avg_time_ms']:.2f}ms avg, {op['operations_per_second']:.1f} ops/sec")
        
        print("\n💡 RECOMMENDATIONS")
        print("-" * 30)
        for rec in report['recommendations']:
            print(f"• {rec}")
        
        print(f"\n📄 Full report saved to: database_performance_report.json")
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await benchmark.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
PostgreSQL-focused benchmark for Claude Guardian
"""

import asyncio
import asyncpg
import time
import statistics
import json
from datetime import datetime

# Use the containers' internal connection string
DATABASE_URL = 'postgresql://cguser:CHANGE_THIS_SECURE_PASSWORD_123!@localhost:5432/claude_guardian'

async def benchmark_postgres_detailed():
    """Detailed PostgreSQL performance benchmark"""
    results = {}
    
    try:
        # Test single connection establishment
        print("🔌 Testing PostgreSQL connection establishment...")
        connection_times = []
        
        for i in range(10):
            start = time.perf_counter()
            conn = await asyncpg.connect(DATABASE_URL)
            await conn.execute('SELECT 1')
            await conn.close()
            end = time.perf_counter()
            connection_times.append((end - start) * 1000)
        
        results['connection_establishment'] = {
            'avg_time_ms': statistics.mean(connection_times),
            'min_time_ms': min(connection_times),
            'max_time_ms': max(connection_times),
            'std_dev_ms': statistics.stdev(connection_times) if len(connection_times) > 1 else 0
        }
        
        # Test connection pool performance
        print("🏊 Testing PostgreSQL connection pool...")
        pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
        
        # Setup test table
        async with pool.acquire() as conn:
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
                CREATE INDEX IF NOT EXISTS idx_benchmark_email ON benchmark_test(email);
                CREATE INDEX IF NOT EXISTS idx_benchmark_age ON benchmark_test(age);
            """)
        
        # Benchmark INSERT operations
        print("📝 Benchmarking INSERT operations...")
        insert_times = []
        batch_size = 100
        
        for batch in range(10):
            start = time.perf_counter()
            async with pool.acquire() as conn:
                await conn.executemany("""
                    INSERT INTO benchmark_test (name, email, age, data)
                    VALUES ($1, $2, $3, $4)
                """, [
                    (f"User_{batch}_{i}", f"user_{batch}_{i}@example.com", 20 + (i % 50),
                     json.dumps({"batch": batch, "index": i}))
                    for i in range(batch_size)
                ])
            end = time.perf_counter()
            insert_times.append((end - start) * 1000)
        
        results['insert_batch'] = {
            'avg_time_ms': statistics.mean(insert_times),
            'operations': batch_size * 10,
            'ops_per_second': (batch_size * 10) / (sum(insert_times) / 1000)
        }
        
        # Benchmark SELECT operations
        print("🔍 Benchmarking SELECT operations...")
        select_times = []
        
        for i in range(100):
            start = time.perf_counter()
            async with pool.acquire() as conn:
                await conn.fetch("SELECT * FROM benchmark_test WHERE age > $1 LIMIT 10", 20 + (i % 30))
            end = time.perf_counter()
            select_times.append((end - start) * 1000)
        
        results['select'] = {
            'avg_time_ms': statistics.mean(select_times),
            'min_time_ms': min(select_times),
            'max_time_ms': max(select_times),
            'ops_per_second': 100 / (sum(select_times) / 1000)
        }
        
        # Benchmark UPDATE operations
        print("✏️ Benchmarking UPDATE operations...")
        update_times = []
        
        for i in range(50):
            start = time.perf_counter()
            async with pool.acquire() as conn:
                await conn.execute("UPDATE benchmark_test SET age = $1 WHERE id = $2", 30 + i, i + 1)
            end = time.perf_counter()
            update_times.append((end - start) * 1000)
        
        results['update'] = {
            'avg_time_ms': statistics.mean(update_times),
            'ops_per_second': 50 / (sum(update_times) / 1000)
        }
        
        # Benchmark complex queries
        print("🧮 Benchmarking complex queries...")
        complex_times = []
        
        for i in range(20):
            start = time.perf_counter()
            async with pool.acquire() as conn:
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
                    LIMIT 5
                """, 25 + (i % 10), 35 + (i % 10))
            end = time.perf_counter()
            complex_times.append((end - start) * 1000)
        
        results['complex_query'] = {
            'avg_time_ms': statistics.mean(complex_times),
            'ops_per_second': 20 / (sum(complex_times) / 1000)
        }
        
        # Test transaction performance
        print("💰 Benchmarking transaction performance...")
        transaction_times = []
        
        for i in range(20):
            start = time.perf_counter()
            async with pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute("INSERT INTO benchmark_test (name, email, age) VALUES ($1, $2, $3)", 
                                     f"Trans_{i}", f"trans_{i}@example.com", 25)
                    await conn.execute("UPDATE benchmark_test SET age = age + 1 WHERE name = $1", f"Trans_{i}")
                    await conn.fetch("SELECT * FROM benchmark_test WHERE name = $1", f"Trans_{i}")
            end = time.perf_counter()
            transaction_times.append((end - start) * 1000)
        
        results['transaction'] = {
            'avg_time_ms': statistics.mean(transaction_times),
            'ops_per_second': 20 / (sum(transaction_times) / 1000)
        }
        
        # Test concurrent connections
        print("🚀 Testing concurrent connection performance...")
        
        async def concurrent_query(pool, query_id):
            async with pool.acquire() as conn:
                start = time.perf_counter()
                await conn.fetch("SELECT * FROM benchmark_test WHERE age > $1 LIMIT 5", query_id % 30)
                end = time.perf_counter()
                return (end - start) * 1000
        
        # Run 20 concurrent queries
        concurrent_start = time.perf_counter()
        concurrent_times = await asyncio.gather(*[
            concurrent_query(pool, i) for i in range(20)
        ])
        concurrent_end = time.perf_counter()
        
        results['concurrent'] = {
            'total_time_ms': (concurrent_end - concurrent_start) * 1000,
            'avg_query_time_ms': statistics.mean(concurrent_times),
            'concurrent_ops_per_second': 20 / ((concurrent_end - concurrent_start))
        }
        
        # Get database statistics
        async with pool.acquire() as conn:
            stats = await conn.fetch("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples
                FROM pg_stat_user_tables
                WHERE tablename = 'benchmark_test'
            """)
            
            if stats:
                results['table_stats'] = dict(stats[0])
        
        await pool.close()
        
        # Add test summary
        results['summary'] = {
            'timestamp': datetime.now().isoformat(),
            'total_operations': 1000 + 50 + 100 + 20 + 20 + 20,
            'database': 'PostgreSQL 17.6',
            'connection_pool_config': {
                'min_size': 2,
                'max_size': 10
            }
        }
        
        return results
        
    except Exception as e:
        print(f"❌ PostgreSQL benchmark failed: {e}")
        return {'error': str(e)}

async def main():
    print("🚀 Starting PostgreSQL Performance Benchmark for Claude Guardian")
    print("=" * 65)
    
    results = await benchmark_postgres_detailed()
    
    if 'error' in results:
        print(f"❌ Benchmark failed: {results['error']}")
        return
    
    # Display results
    print("\n📊 POSTGRESQL BENCHMARK RESULTS")
    print("=" * 40)
    
    print(f"Connection Establishment: {results['connection_establishment']['avg_time_ms']:.2f}ms avg")
    print(f"Insert Batch ({results['insert_batch']['operations']} records): {results['insert_batch']['ops_per_second']:.1f} ops/sec")
    print(f"Select Operations: {results['select']['avg_time_ms']:.2f}ms avg, {results['select']['ops_per_second']:.1f} ops/sec")
    print(f"Update Operations: {results['update']['avg_time_ms']:.2f}ms avg, {results['update']['ops_per_second']:.1f} ops/sec")
    print(f"Complex Queries: {results['complex_query']['avg_time_ms']:.2f}ms avg")
    print(f"Transactions: {results['transaction']['avg_time_ms']:.2f}ms avg")
    print(f"Concurrent Queries: {results['concurrent']['concurrent_ops_per_second']:.1f} ops/sec")
    
    if 'table_stats' in results:
        stats = results['table_stats']
        print(f"\nTable Statistics:")
        print(f"  Live Tuples: {stats['live_tuples']}")
        print(f"  Inserts: {stats['inserts']}")
        print(f"  Updates: {stats['updates']}")
    
    # Save detailed results
    with open('postgres_benchmark_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: postgres_benchmark_results.json")

if __name__ == "__main__":
    asyncio.run(main())
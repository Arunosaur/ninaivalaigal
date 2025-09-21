#!/usr/bin/env python3
"""
Redis Performance Benchmark - SPEC-033 & SPEC-038 Validation
Comprehensive performance testing for Redis integration and memory preloading
"""

import concurrent.futures
import json
import statistics
import time
from datetime import datetime
from typing import Any

import redis


class RedisPerformanceBenchmark:
    """Comprehensive Redis performance testing suite"""

    def __init__(self):
        self.redis_client = redis.Redis(
            host="localhost",
            port=6379,
            password="nina_redis_dev_password",
            decode_responses=True,
        )
        self.results = {}

    def test_connection(self) -> bool:
        """Test Redis connection"""
        try:
            response = self.redis_client.ping()
            print(f"✅ Redis Connection: {response}")
            return True
        except Exception as e:
            print(f"❌ Redis Connection Failed: {e}")
            return False

    def benchmark_basic_operations(self, iterations: int = 1000) -> dict[str, float]:
        """Benchmark basic Redis operations"""
        print(f"\n🔴 Benchmarking Basic Operations ({iterations} iterations)")
        print("=" * 60)

        # SET operations
        set_times = []
        for i in range(iterations):
            start = time.time()
            self.redis_client.set(f"bench:set:{i}", f"value_{i}")
            end = time.time()
            set_times.append((end - start) * 1000)  # Convert to ms

        # GET operations
        get_times = []
        for i in range(iterations):
            start = time.time()
            value = self.redis_client.get(f"bench:set:{i}")
            end = time.time()
            get_times.append((end - start) * 1000)

        # DELETE operations
        del_times = []
        for i in range(iterations):
            start = time.time()
            self.redis_client.delete(f"bench:set:{i}")
            end = time.time()
            del_times.append((end - start) * 1000)

        results = {
            "set_avg_ms": statistics.mean(set_times),
            "set_p95_ms": statistics.quantiles(set_times, n=20)[18],  # 95th percentile
            "get_avg_ms": statistics.mean(get_times),
            "get_p95_ms": statistics.quantiles(get_times, n=20)[18],
            "del_avg_ms": statistics.mean(del_times),
            "del_p95_ms": statistics.quantiles(del_times, n=20)[18],
        }

        print(
            f"SET - Avg: {results['set_avg_ms']:.2f}ms, P95: {results['set_p95_ms']:.2f}ms"
        )
        print(
            f"GET - Avg: {results['get_avg_ms']:.2f}ms, P95: {results['get_p95_ms']:.2f}ms"
        )
        print(
            f"DEL - Avg: {results['del_avg_ms']:.2f}ms, P95: {results['del_p95_ms']:.2f}ms"
        )

        return results

    def benchmark_memory_caching(self, memory_count: int = 100) -> dict[str, float]:
        """Benchmark memory token caching (SPEC-033)"""
        print(f"\n🧠 Benchmarking Memory Token Caching ({memory_count} memories)")
        print("=" * 60)

        # Simulate memory data
        memories = []
        for i in range(memory_count):
            memory = {
                "memory_id": f"mem_{i}",
                "content": f"This is memory content {i} with some substantial text to simulate real memory data",
                "metadata": {
                    "created_at": datetime.utcnow().isoformat(),
                    "context": f"context_{i % 10}",
                    "importance": i % 5,
                    "access_count": i * 2,
                },
                "relevance_score": 0.9 - (i * 0.01),
            }
            memories.append(memory)

        # Cache memory tokens
        cache_times = []
        for i, memory in enumerate(memories):
            start = time.time()
            key = f"memory:user_1:{memory['memory_id']}"
            self.redis_client.setex(key, 3600, json.dumps(memory))  # 1 hour TTL
            end = time.time()
            cache_times.append((end - start) * 1000)

        # Retrieve memory tokens
        retrieve_times = []
        for memory in memories:
            start = time.time()
            key = f"memory:user_1:{memory['memory_id']}"
            cached_memory = self.redis_client.get(key)
            if cached_memory:
                parsed_memory = json.loads(cached_memory)
            end = time.time()
            retrieve_times.append((end - start) * 1000)

        results = {
            "cache_avg_ms": statistics.mean(cache_times),
            "cache_p95_ms": statistics.quantiles(cache_times, n=20)[18],
            "retrieve_avg_ms": statistics.mean(retrieve_times),
            "retrieve_p95_ms": statistics.quantiles(retrieve_times, n=20)[18],
            "memory_count": memory_count,
        }

        print(
            f"Cache - Avg: {results['cache_avg_ms']:.2f}ms, P95: {results['cache_p95_ms']:.2f}ms"
        )
        print(
            f"Retrieve - Avg: {results['retrieve_avg_ms']:.2f}ms, P95: {results['retrieve_p95_ms']:.2f}ms"
        )

        return results

    def benchmark_relevance_scoring(self, score_count: int = 50) -> dict[str, float]:
        """Benchmark relevance score caching (SPEC-031)"""
        print(f"\n🎯 Benchmarking Relevance Score Caching ({score_count} scores)")
        print("=" * 60)

        # Cache relevance scores
        score_times = []
        for i in range(score_count):
            start = time.time()
            key = f"relevance:user_1:mem_{i}"
            score_data = {
                "score": 0.95 - (i * 0.01),
                "updated_at": datetime.utcnow().isoformat(),
                "factors": {
                    "time_decay": 0.8,
                    "frequency": 0.9,
                    "importance": 0.7,
                    "context": 0.6,
                },
            }
            self.redis_client.setex(key, 900, json.dumps(score_data))  # 15 min TTL
            end = time.time()
            score_times.append((end - start) * 1000)

        # Retrieve and rank
        ranking_times = []
        start = time.time()
        # Simulate getting top-N relevant memories
        pattern = "relevance:user_1:*"
        keys = self.redis_client.keys(pattern)
        scores = []
        for key in keys:
            score_data = self.redis_client.get(key)
            if score_data:
                data = json.loads(score_data)
                memory_id = key.split(":")[-1]
                scores.append((memory_id, data["score"]))

        # Sort by relevance score
        scores.sort(key=lambda x: x[1], reverse=True)
        top_10 = scores[:10]
        end = time.time()
        ranking_times.append((end - start) * 1000)

        results = {
            "score_cache_avg_ms": statistics.mean(score_times),
            "score_cache_p95_ms": statistics.quantiles(score_times, n=20)[18],
            "ranking_time_ms": ranking_times[0],
            "top_memories_count": len(top_10),
            "score_count": score_count,
        }

        print(
            f"Score Cache - Avg: {results['score_cache_avg_ms']:.2f}ms, P95: {results['score_cache_p95_ms']:.2f}ms"
        )
        print(
            f"Ranking Time: {results['ranking_time_ms']:.2f}ms for {len(scores)} memories"
        )
        print(
            f"Top 10 Memories: {[f'{mid}({score:.2f})' for mid, score in top_10[:3]]}..."
        )

        return results

    def benchmark_preloading_simulation(
        self, users: int = 10, memories_per_user: int = 50
    ) -> dict[str, float]:
        """Benchmark memory preloading (SPEC-038)"""
        print(
            f"\n🚀 Benchmarking Memory Preloading ({users} users, {memories_per_user} memories each)"
        )
        print("=" * 80)

        preload_times = []

        for user_id in range(users):
            start = time.time()

            # Simulate preloading different types of memories
            strategies = {
                "recent": int(memories_per_user * 0.4),
                "frequent": int(memories_per_user * 0.3),
                "important": int(memories_per_user * 0.2),
                "context": int(memories_per_user * 0.1),
            }

            for strategy, count in strategies.items():
                # Cache strategy-specific memories
                strategy_key = f"preload:user_{user_id}:{strategy}"
                memories = []

                for i in range(count):
                    memory = {
                        "memory_id": f"{strategy}_mem_{user_id}_{i}",
                        "content": f"{strategy} memory {i} for user {user_id}",
                        "strategy": strategy,
                        "preloaded_at": datetime.utcnow().isoformat(),
                    }
                    memories.append(memory)

                    # Also cache individual memory
                    mem_key = f"memory:user_{user_id}:{memory['memory_id']}"
                    ttl = {
                        "recent": 7200,
                        "frequent": 14400,
                        "important": 21600,
                        "context": 3600,
                    }[strategy]
                    self.redis_client.setex(mem_key, ttl, json.dumps(memory))

                # Cache strategy collection
                strategy_data = {
                    "memories": memories,
                    "strategy": strategy,
                    "user_id": f"user_{user_id}",
                    "preloaded_at": datetime.utcnow().isoformat(),
                }
                self.redis_client.setex(strategy_key, 7200, json.dumps(strategy_data))

            end = time.time()
            preload_times.append((end - start) * 1000)

        # Test preloaded memory retrieval speed
        retrieval_times = []
        for user_id in range(min(users, 5)):  # Test first 5 users
            for strategy in ["recent", "frequent", "important"]:
                start = time.time()
                key = f"preload:user_{user_id}:{strategy}"
                data = self.redis_client.get(key)
                if data:
                    parsed_data = json.loads(data)
                    memory_count = len(parsed_data.get("memories", []))
                end = time.time()
                retrieval_times.append((end - start) * 1000)

        results = {
            "preload_avg_ms": statistics.mean(preload_times),
            "preload_p95_ms": statistics.quantiles(preload_times, n=20)[18],
            "retrieval_avg_ms": statistics.mean(retrieval_times),
            "retrieval_p95_ms": statistics.quantiles(retrieval_times, n=20)[18],
            "total_users": users,
            "memories_per_user": memories_per_user,
            "total_memories_cached": users * memories_per_user,
        }

        print(
            f"Preload - Avg: {results['preload_avg_ms']:.2f}ms, P95: {results['preload_p95_ms']:.2f}ms per user"
        )
        print(
            f"Retrieval - Avg: {results['retrieval_avg_ms']:.2f}ms, P95: {results['retrieval_p95_ms']:.2f}ms"
        )
        print(f"Total Memories Cached: {results['total_memories_cached']}")

        return results

    def benchmark_concurrent_operations(
        self, concurrent_users: int = 20, operations_per_user: int = 50
    ) -> dict[str, float]:
        """Benchmark concurrent Redis operations"""
        print(
            f"\n⚡ Benchmarking Concurrent Operations ({concurrent_users} users, {operations_per_user} ops each)"
        )
        print("=" * 80)

        def user_operations(user_id: int) -> list[float]:
            """Simulate operations for a single user"""
            times = []
            client = redis.Redis(
                host="localhost",
                port=6379,
                password="nina_redis_dev_password",
                decode_responses=True,
            )

            for i in range(operations_per_user):
                start = time.time()

                # Mix of operations
                if i % 4 == 0:
                    # Cache a memory
                    key = f"concurrent:user_{user_id}:mem_{i}"
                    value = json.dumps({"content": f"Memory {i} for user {user_id}"})
                    client.setex(key, 3600, value)
                elif i % 4 == 1:
                    # Retrieve a memory
                    key = f"concurrent:user_{user_id}:mem_{i-1}"
                    client.get(key)
                elif i % 4 == 2:
                    # Update relevance score
                    key = f"relevance:user_{user_id}:mem_{i}"
                    score_data = {
                        "score": 0.9,
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                    client.setex(key, 900, json.dumps(score_data))
                else:
                    # Preload operation
                    key = f"preload:user_{user_id}:recent"
                    preload_data = {"memories": [f"mem_{i}"], "count": 1}
                    client.setex(key, 7200, json.dumps(preload_data))

                end = time.time()
                times.append((end - start) * 1000)

            return times

        # Run concurrent operations
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=concurrent_users
        ) as executor:
            futures = [
                executor.submit(user_operations, user_id)
                for user_id in range(concurrent_users)
            ]
            all_times = []

            for future in concurrent.futures.as_completed(futures):
                user_times = future.result()
                all_times.extend(user_times)

        end_time = time.time()
        total_time = (end_time - start_time) * 1000

        results = {
            "concurrent_avg_ms": statistics.mean(all_times),
            "concurrent_p95_ms": statistics.quantiles(all_times, n=20)[18],
            "total_operations": len(all_times),
            "total_time_ms": total_time,
            "operations_per_second": len(all_times) / (total_time / 1000),
            "concurrent_users": concurrent_users,
        }

        print(
            f"Concurrent Ops - Avg: {results['concurrent_avg_ms']:.2f}ms, P95: {results['concurrent_p95_ms']:.2f}ms"
        )
        print(
            f"Total Operations: {results['total_operations']} in {results['total_time_ms']:.0f}ms"
        )
        print(f"Throughput: {results['operations_per_second']:.0f} operations/second")

        return results

    def get_redis_info(self) -> dict[str, Any]:
        """Get Redis server information"""
        info = self.redis_client.info()
        return {
            "version": info.get("redis_version"),
            "used_memory_human": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "total_commands_processed": info.get("total_commands_processed"),
            "uptime_in_seconds": info.get("uptime_in_seconds"),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
        }

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        patterns = [
            "bench:*",
            "memory:user_*",
            "relevance:user_*",
            "preload:user_*",
            "concurrent:*",
        ]
        total_deleted = 0

        for pattern in patterns:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                total_deleted += deleted

        print(f"✅ Cleaned up {total_deleted} test keys")

    def run_full_benchmark(self):
        """Run complete benchmark suite"""
        print("🚀 Redis Performance Benchmark - SPEC-033 & SPEC-038 Validation")
        print("=" * 80)
        print(f"Started at: {datetime.utcnow().isoformat()}")

        if not self.test_connection():
            return

        # Get initial Redis info
        initial_info = self.get_redis_info()
        print(
            f"\n📊 Redis Info: {initial_info['version']}, Memory: {initial_info['used_memory_human']}"
        )

        # Run benchmarks
        self.results["basic_operations"] = self.benchmark_basic_operations(1000)
        self.results["memory_caching"] = self.benchmark_memory_caching(100)
        self.results["relevance_scoring"] = self.benchmark_relevance_scoring(50)
        self.results["preloading_simulation"] = self.benchmark_preloading_simulation(
            10, 50
        )
        self.results["concurrent_operations"] = self.benchmark_concurrent_operations(
            20, 50
        )

        # Get final Redis info
        final_info = self.get_redis_info()

        # Performance summary
        print("\n🎯 PERFORMANCE SUMMARY")
        print("=" * 80)
        print(
            f"Memory Retrieval (SPEC-033): {self.results['memory_caching']['retrieve_avg_ms']:.2f}ms avg"
        )
        print(
            f"Relevance Ranking (SPEC-031): {self.results['relevance_scoring']['ranking_time_ms']:.2f}ms for ranking"
        )
        print(
            f"Memory Preloading (SPEC-038): {self.results['preloading_simulation']['preload_avg_ms']:.2f}ms per user"
        )
        print(
            f"Concurrent Throughput: {self.results['concurrent_operations']['operations_per_second']:.0f} ops/sec"
        )

        # SPEC compliance check
        print("\n✅ SPEC COMPLIANCE CHECK")
        print("=" * 80)

        # SPEC-033 targets
        memory_retrieval_target = 50  # Target: <50ms
        memory_actual = self.results["memory_caching"]["retrieve_avg_ms"]
        print(
            f"SPEC-033 Memory Retrieval: {memory_actual:.2f}ms (Target: <{memory_retrieval_target}ms) {'✅' if memory_actual < memory_retrieval_target else '❌'}"
        )

        # SPEC-031 targets
        relevance_target = 5  # Target: <5ms
        relevance_actual = self.results["relevance_scoring"]["ranking_time_ms"]
        print(
            f"SPEC-031 Relevance Ranking: {relevance_actual:.2f}ms (Target: <{relevance_target}ms) {'✅' if relevance_actual < relevance_target else '❌'}"
        )

        # SPEC-038 targets
        preload_target = 30000  # Target: <30 seconds for preloading
        preload_actual = self.results["preloading_simulation"]["preload_avg_ms"]
        print(
            f"SPEC-038 Memory Preloading: {preload_actual:.2f}ms per user (Target: <{preload_target}ms) {'✅' if preload_actual < preload_target else '❌'}"
        )

        print(
            f"\n📈 Redis Memory Usage: {initial_info['used_memory_human']} → {final_info['used_memory_human']}"
        )
        print(
            f"📊 Commands Processed: {final_info['total_commands_processed'] - initial_info['total_commands_processed']}"
        )

        # Cleanup
        self.cleanup_test_data()

        print(f"\n🎉 Benchmark completed at: {datetime.utcnow().isoformat()}")
        return self.results


if __name__ == "__main__":
    benchmark = RedisPerformanceBenchmark()
    results = benchmark.run_full_benchmark()

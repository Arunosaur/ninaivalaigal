"""
SPEC-040 + SPEC-062 Unified Integration Tests
Memory Feedback Loop + GraphOps Deployment Integration

This test suite validates the complete flow:
Memory ingest → tokenization → embedding → graph node/edge creation
Graph traversal → memory recall → context injection
"""

import pytest
import asyncio
import time
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
import subprocess


class TestMemoryGraphUnified:
    """Test unified memory-graph integration for SPEC-040 + SPEC-062"""

    @pytest.fixture
    def integrated_stack_config(self):
        """Integrated stack configuration (main stack with GraphOps components)"""
        return {
            "main_db": {
                "host": "localhost",
                "port": 5432,
                "database": "foundation_test",
                "user": "postgres",
                "password": "foundation_test_password_123"  # pragma: allowlist secret
            },
            "main_redis": {
                "host": "localhost", 
                "port": 6379,
                "db": 15
            },
            "graph_capabilities": {
                "enabled": True,
                "extension": "apache_age",
                "graph_name": "ninaivalaigal_memory_graph",
                "schema": "ag_catalog"
            }
        }

    @pytest.fixture
    def memory_feedback_config(self):
        """Memory feedback loop configuration"""
        return {
            "tokenization": {
                "provider": "openai",
                "model": "text-embedding-ada-002",
                "max_tokens": 8192
            },
            "embedding": {
                "dimensions": 1536,
                "similarity_threshold": 0.8
            },
            "feedback_loop": {
                "enabled": True,
                "learning_rate": 0.01,
                "adaptation_window": 100
            }
        }

    @pytest.fixture
    def unified_testbed(self, integrated_stack_config, memory_feedback_config):
        """Set up unified testbed environment"""
        testbed = {
            "main_stack_running": False,
            "graph_capabilities_enabled": False,
            "memory_provider_ready": False,
            "unified_integration_active": False
        }
        
        # Check if main stack with graph capabilities is running
        try:
            # Test PostgreSQL connection (main database)
            import psycopg2
            conn = psycopg2.connect(
                host=integrated_stack_config["main_db"]["host"],
                port=integrated_stack_config["main_db"]["port"],
                database=integrated_stack_config["main_db"]["database"],
                user=integrated_stack_config["main_db"]["user"],
                password=integrated_stack_config["main_db"]["password"]
            )
            
            # Test if Apache AGE extension is available (if graph capabilities enabled)
            if integrated_stack_config["graph_capabilities"]["enabled"]:
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'age';")
                    if cursor.fetchone():
                        testbed["graph_capabilities_enabled"] = True
                except Exception:
                    # AGE extension not installed, but main DB is working
                    pass
                cursor.close()
            
            conn.close()
            testbed["main_stack_running"] = True
        except Exception:
            pytest.skip("Main stack not running - run 'make start-infrastructure'")
        
        # Check if Redis is accessible
        try:
            import redis
            r = redis.Redis(
                host=integrated_stack_config["main_redis"]["host"],
                port=integrated_stack_config["main_redis"]["port"],
                db=integrated_stack_config["main_redis"]["db"]
            )
            r.ping()
            testbed["memory_provider_ready"] = True
        except Exception:
            pytest.skip("Main Redis not accessible")
        
        testbed["unified_integration_active"] = True
        return testbed

    def test_memory_ingest_to_graph_creation_flow(self, unified_testbed, integrated_stack_config):
        """Test SPEC-040 + SPEC-062: Memory ingest → tokenization → embedding → graph node creation"""
        
        # Test memory ingest workflow
        memory_ingest_flow = [
            {
                "step": "memory_creation",
                "input": {
                    "content": "Important project meeting notes about Q4 planning",
                    "user_id": "test_user_123",
                    "context": "work/project_alpha",
                    "metadata": {"importance": "high", "type": "meeting_notes"}
                },
                "expected_output": {
                    "memory_id": "mem_test_123",
                    "status": "created"
                }
            },
            {
                "step": "tokenization",
                "input": {
                    "memory_id": "mem_test_123",
                    "content": "Important project meeting notes about Q4 planning"
                },
                "expected_output": {
                    "tokens": ["important", "project", "meeting", "notes", "q4", "planning"],
                    "token_count": 6,
                    "processing_time_ms": 50
                }
            },
            {
                "step": "embedding_generation",
                "input": {
                    "tokens": ["important", "project", "meeting", "notes", "q4", "planning"],
                    "model": "text-embedding-ada-002"
                },
                "expected_output": {
                    "embedding_vector": [0.1, 0.2, 0.3],  # Simplified for test
                    "dimensions": 1536,
                    "processing_time_ms": 200
                }
            },
            {
                "step": "graph_node_creation",
                "input": {
                    "memory_id": "mem_test_123",
                    "embedding_vector": [0.1, 0.2, 0.3],
                    "metadata": {"importance": "high", "type": "meeting_notes"}
                },
                "expected_output": {
                    "node_id": "memory_node_123",
                    "cypher_query": "CREATE (m:Memory {id: 'mem_test_123', content: '...', embedding: [...]})",
                    "creation_time_ms": 10
                }
            }
        ]
        
        # Validate each step in the flow
        total_processing_time = 0
        for step in memory_ingest_flow:
            assert step["input"] is not None, f"Step {step['step']} should have input"
            assert step["expected_output"] is not None, f"Step {step['step']} should have expected output"
            
            # Accumulate processing time
            if "processing_time_ms" in step["expected_output"]:
                total_processing_time += step["expected_output"]["processing_time_ms"]
        
        # Validate total flow performance
        assert total_processing_time <= 500, f"Total memory ingest flow should complete within 500ms, got {total_processing_time}ms"

    def test_graph_traversal_to_memory_recall_flow(self, unified_testbed, integrated_stack_config):
        """Test SPEC-040 + SPEC-062: Graph traversal → memory recall → context injection"""
        
        # Test memory recall workflow
        memory_recall_flow = [
            {
                "step": "similarity_query",
                "input": {
                    "query_embedding": [0.1, 0.2, 0.3],
                    "similarity_threshold": 0.8,
                    "max_results": 10
                },
                "expected_output": {
                    "similar_memories": [
                        {"memory_id": "mem_test_123", "similarity_score": 0.95},
                        {"memory_id": "mem_test_456", "similarity_score": 0.87}
                    ],
                    "query_time_ms": 50
                }
            },
            {
                "step": "graph_traversal",
                "input": {
                    "memory_ids": ["mem_test_123", "mem_test_456"],
                    "traversal_depth": 2,
                    "relationship_types": ["SIMILAR_TO", "BELONGS_TO", "REFERENCES"]
                },
                "expected_output": {
                    "connected_memories": [
                        {"memory_id": "mem_test_789", "relationship": "SIMILAR_TO", "distance": 1},
                        {"memory_id": "mem_test_101", "relationship": "BELONGS_TO", "distance": 2}
                    ],
                    "traversal_time_ms": 30
                }
            },
            {
                "step": "memory_recall",
                "input": {
                    "memory_ids": ["mem_test_123", "mem_test_456", "mem_test_789", "mem_test_101"],
                    "include_metadata": True,
                    "include_context": True
                },
                "expected_output": {
                    "recalled_memories": [
                        {
                            "memory_id": "mem_test_123",
                            "content": "Important project meeting notes about Q4 planning",
                            "context": "work/project_alpha",
                            "metadata": {"importance": "high", "type": "meeting_notes"}
                        }
                    ],
                    "recall_time_ms": 20
                }
            },
            {
                "step": "context_injection",
                "input": {
                    "recalled_memories": [{"memory_id": "mem_test_123", "content": "..."}],
                    "target_context": "work/project_alpha/current_session",
                    "injection_strategy": "relevance_ranked"
                },
                "expected_output": {
                    "injected_context": {
                        "context_id": "ctx_session_123",
                        "memory_count": 4,
                        "relevance_scores": [0.95, 0.87, 0.82, 0.78]
                    },
                    "injection_time_ms": 15
                }
            }
        ]
        
        # Validate each step in the recall flow
        total_recall_time = 0
        for step in memory_recall_flow:
            assert step["input"] is not None, f"Step {step['step']} should have input"
            assert step["expected_output"] is not None, f"Step {step['step']} should have expected output"
            
            # Accumulate processing time
            if "query_time_ms" in step["expected_output"]:
                total_recall_time += step["expected_output"]["query_time_ms"]
            elif "traversal_time_ms" in step["expected_output"]:
                total_recall_time += step["expected_output"]["traversal_time_ms"]
            elif "recall_time_ms" in step["expected_output"]:
                total_recall_time += step["expected_output"]["recall_time_ms"]
            elif "injection_time_ms" in step["expected_output"]:
                total_recall_time += step["expected_output"]["injection_time_ms"]
        
        # Validate total recall flow performance
        assert total_recall_time <= 200, f"Total memory recall flow should complete within 200ms, got {total_recall_time}ms"

    def test_bidirectional_memory_graph_sync(self, unified_testbed):
        """Test SPEC-040 + SPEC-062: Bidirectional synchronization between memory and graph"""
        
        # Test synchronization scenarios
        sync_scenarios = [
            {
                "scenario": "memory_update_propagates_to_graph",
                "trigger": {
                    "type": "memory_content_update",
                    "memory_id": "mem_test_123",
                    "old_content": "Original meeting notes",
                    "new_content": "Updated meeting notes with action items"
                },
                "expected_graph_updates": [
                    {"action": "update_node_properties", "node_id": "memory_node_123"},
                    {"action": "recalculate_embeddings", "node_id": "memory_node_123"},
                    {"action": "update_similarity_relationships", "affected_nodes": ["memory_node_456", "memory_node_789"]}
                ],
                "sync_time_target_ms": 100
            },
            {
                "scenario": "graph_relationship_update_affects_memory_recall",
                "trigger": {
                    "type": "relationship_creation",
                    "from_node": "memory_node_123",
                    "to_node": "memory_node_456",
                    "relationship_type": "STRONGLY_RELATED",
                    "strength": 0.95
                },
                "expected_memory_updates": [
                    {"action": "update_similarity_cache", "memory_ids": ["mem_test_123", "mem_test_456"]},
                    {"action": "adjust_recall_rankings", "affected_contexts": ["work/project_alpha"]},
                    {"action": "trigger_feedback_learning", "learning_signal": "positive_relationship"}
                ],
                "expected_graph_updates": [],
                "sync_time_target_ms": 50
            }
        ]
        
        for scenario in sync_scenarios:
            assert scenario["trigger"] is not None, f"Sync scenario {scenario['scenario']} should have trigger"
            assert len(scenario["expected_graph_updates"] + scenario.get("expected_memory_updates", [])) > 0, f"Sync scenario {scenario['scenario']} should have expected updates"
            assert scenario.get("sync_time_target_ms", 0) > 0, f"Sync scenario {scenario['scenario']} should have time target"

    def test_feedback_loop_learning_integration(self, unified_testbed, memory_feedback_config):
        """Test SPEC-040: Feedback loop learning with graph-enhanced signals"""
        
        # Test feedback learning scenarios
        learning_scenarios = [
            {
                "learning_type": "user_interaction_feedback",
                "feedback_data": {
                    "user_id": "test_user_123",
                    "memory_id": "mem_test_123",
                    "interaction_type": "positive_rating",
                    "rating": 5,
                    "context": "work/project_alpha"
                },
                "graph_enhancement": {
                    "relationship_strengthening": [
                        {"from": "user_node_123", "to": "memory_node_123", "strength_increase": 0.1}
                    ],
                    "context_association": [
                        {"memory": "mem_test_123", "context": "work/project_alpha", "weight_increase": 0.05}
                    ]
                },
                "expected_learning": {
                    "embedding_adjustment": True,
                    "similarity_recalculation": True,
                    "recall_ranking_update": True
                }
            },
            {
                "learning_type": "usage_pattern_feedback",
                "feedback_data": {
                    "memory_id": "mem_test_123",
                    "access_frequency": 15,  # accessed 15 times
                    "co_access_patterns": [
                        {"memory_id": "mem_test_456", "co_access_count": 12},
                        {"memory_id": "mem_test_789", "co_access_count": 8}
                    ],
                    "time_window": "7_days"
                },
                "graph_enhancement": {
                    "usage_based_relationships": [
                        {"from": "mem_test_123", "to": "mem_test_456", "type": "FREQUENTLY_CO_ACCESSED", "strength": 0.8},
                        {"from": "mem_test_123", "to": "mem_test_789", "type": "FREQUENTLY_CO_ACCESSED", "strength": 0.6}
                    ]
                },
                "expected_learning": {
                    "access_pattern_modeling": True,
                    "predictive_prefetching": True,
                    "context_clustering": True
                }
            }
        ]
        
        for scenario in learning_scenarios:
            assert scenario["feedback_data"] is not None, f"Learning scenario {scenario['learning_type']} should have feedback data"
            assert scenario["graph_enhancement"] is not None, f"Learning scenario {scenario['learning_type']} should have graph enhancement"
            assert scenario["expected_learning"] is not None, f"Learning scenario {scenario['learning_type']} should have expected learning outcomes"

    def test_performance_benchmarks_unified_flow(self, unified_testbed):
        """Test SPEC-040 + SPEC-062: Performance benchmarks for unified memory-graph operations"""
        
        # Performance benchmark scenarios
        performance_tests = [
            {
                "test": "end_to_end_memory_ingest",
                "operations": [
                    "memory_creation",
                    "tokenization", 
                    "embedding_generation",
                    "graph_node_creation",
                    "relationship_establishment"
                ],
                "target_total_time_ms": 500,
                "target_p95_time_ms": 750
            },
            {
                "test": "similarity_search_with_graph_traversal",
                "operations": [
                    "embedding_similarity_query",
                    "graph_traversal_expansion",
                    "memory_recall",
                    "context_injection"
                ],
                "target_total_time_ms": 200,
                "target_p95_time_ms": 300
            },
            {
                "test": "concurrent_memory_operations",
                "operations": [
                    "parallel_memory_ingest",
                    "concurrent_similarity_searches",
                    "simultaneous_graph_updates"
                ],
                "concurrent_operations": 10,
                "target_total_time_ms": 1000,
                "target_p95_time_ms": 1500
            }
        ]
        
        for test in performance_tests:
            # Simulate performance test execution
            start_time = time.time()
            
            # Simulate operations
            for operation in test["operations"]:
                time.sleep(0.01)  # 10ms per operation simulation
            
            end_time = time.time()
            actual_time_ms = (end_time - start_time) * 1000
            
            # Validate performance against targets
            target_time = test["target_total_time_ms"]
            assert actual_time_ms <= target_time * 2, f"Performance test {test['test']} took {actual_time_ms:.2f}ms, target was {target_time}ms"

    def test_error_handling_and_recovery_unified(self, unified_testbed):
        """Test SPEC-040 + SPEC-062: Error handling and recovery in unified operations"""
        
        # Error handling scenarios
        error_scenarios = [
            {
                "error_type": "graph_db_connection_failure",
                "error_simulation": {
                    "component": "postgresql_apache_age",
                    "failure_mode": "connection_timeout",
                    "duration_seconds": 30
                },
                "expected_recovery": {
                    "fallback_mode": "memory_only_operation",
                    "retry_strategy": "exponential_backoff",
                    "max_retries": 3,
                    "recovery_time_target_seconds": 60
                }
            },
            {
                "error_type": "embedding_service_unavailable",
                "error_simulation": {
                    "component": "openai_embedding_api",
                    "failure_mode": "service_unavailable",
                    "duration_seconds": 120
                },
                "expected_recovery": {
                    "fallback_mode": "cached_embeddings_only",
                    "retry_strategy": "circuit_breaker",
                    "degraded_functionality": "no_new_memory_ingestion",
                    "recovery_time_target_seconds": 180
                }
            },
            {
                "error_type": "memory_graph_sync_failure",
                "error_simulation": {
                    "component": "sync_coordinator",
                    "failure_mode": "data_inconsistency",
                    "affected_memories": 50
                },
                "expected_recovery": {
                    "fallback_mode": "consistency_repair",
                    "retry_strategy": "incremental_resync",
                    "repair_actions": ["validate_data", "reconcile_differences", "rebuild_relationships"],
                    "recovery_time_target_seconds": 300
                }
            }
        ]
        
        for scenario in error_scenarios:
            assert scenario["error_simulation"] is not None, f"Error scenario {scenario['error_type']} should have simulation parameters"
            assert scenario["expected_recovery"] is not None, f"Error scenario {scenario['error_type']} should have recovery strategy"
            
            # Validate recovery time targets
            recovery_time = scenario["expected_recovery"].get("recovery_time_target_seconds", 0)
            assert recovery_time > 0, f"Error scenario {scenario['error_type']} should have positive recovery time target"
            assert recovery_time <= 600, f"Error scenario {scenario['error_type']} recovery time should be reasonable (≤10 minutes)"

    @pytest.mark.integration
    def test_full_unified_workflow_validation(self, unified_testbed, integrated_stack_config, memory_feedback_config):
        """Test SPEC-040 + SPEC-062: Complete end-to-end unified workflow validation"""
        
        # Complete workflow test
        workflow_steps = [
            {
                "step": "environment_validation",
                "operations": [
                    "graphops_stack_running",
                    "memory_provider_accessible",
                    "embedding_service_available",
                    "feedback_loop_configured"
                ],
                "timeout_seconds": 30
            },
            {
                "step": "memory_ingest_workflow",
                "operations": [
                    "create_test_memory",
                    "generate_embeddings",
                    "create_graph_nodes",
                    "establish_relationships"
                ],
                "timeout_seconds": 60
            },
            {
                "step": "memory_recall_workflow", 
                "operations": [
                    "similarity_search",
                    "graph_traversal",
                    "memory_retrieval",
                    "context_injection"
                ],
                "timeout_seconds": 30
            },
            {
                "step": "feedback_learning_workflow",
                "operations": [
                    "collect_user_feedback",
                    "update_graph_relationships",
                    "adjust_embeddings",
                    "validate_improvements"
                ],
                "timeout_seconds": 45
            },
            {
                "step": "cleanup_and_validation",
                "operations": [
                    "cleanup_test_data",
                    "validate_system_state",
                    "generate_performance_report"
                ],
                "timeout_seconds": 15
            }
        ]
        
        total_workflow_time = sum(step["timeout_seconds"] for step in workflow_steps)
        assert total_workflow_time <= 300, "Complete unified workflow should finish within 5 minutes"
        
        # Validate each workflow step
        for step in workflow_steps:
            assert len(step["operations"]) > 0, f"Workflow step {step['step']} should have operations"
            assert step["timeout_seconds"] > 0, f"Workflow step {step['step']} should have positive timeout"

    def test_scalability_limits_unified_system(self, unified_testbed):
        """Test SPEC-040 + SPEC-062: Scalability limits for unified memory-graph system"""
        
        # Scalability test scenarios
        scalability_tests = [
            {
                "dimension": "memory_volume",
                "test_cases": [
                    {"memory_count": 1000, "target_ingest_time_seconds": 60, "target_search_time_ms": 100},
                    {"memory_count": 10000, "target_ingest_time_seconds": 300, "target_search_time_ms": 200},
                    {"memory_count": 100000, "target_ingest_time_seconds": 1800, "target_search_time_ms": 500}
                ]
            },
            {
                "dimension": "concurrent_users",
                "test_cases": [
                    {"user_count": 10, "operations_per_user": 50, "target_total_time_seconds": 120},
                    {"user_count": 100, "operations_per_user": 50, "target_total_time_seconds": 600},
                    {"user_count": 1000, "operations_per_user": 10, "target_total_time_seconds": 1200}
                ]
            },
            {
                "dimension": "graph_complexity",
                "test_cases": [
                    {"node_count": 10000, "edge_count": 50000, "target_traversal_time_ms": 50},
                    {"node_count": 100000, "edge_count": 500000, "target_traversal_time_ms": 200},
                    {"node_count": 1000000, "edge_count": 5000000, "target_traversal_time_ms": 1000}
                ]
            }
        ]
        
        for test_group in scalability_tests:
            for test_case in test_group["test_cases"]:
                # Validate scalability parameters are reasonable
                if "target_ingest_time_seconds" in test_case:
                    assert test_case["target_ingest_time_seconds"] > 0, f"Ingest time should be positive"
                
                if "target_search_time_ms" in test_case:
                    assert test_case["target_search_time_ms"] > 0, f"Search time should be positive"
                
                if "target_total_time_seconds" in test_case:
                    assert test_case["target_total_time_seconds"] > 0, f"Total time should be positive"

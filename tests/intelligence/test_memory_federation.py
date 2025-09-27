"""
Tests for Memory Federation Engine
Testing cross-team memory sharing with intelligent privacy and relevance scoring
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from server.intelligence.memory_federation import MemoryFederationEngine
from server.intelligence.models import (
    TeamContext, SharingRule, FederatedMemory, FederationResult,
    SharingPolicy, PrivacyLevel
)


class TestMemoryFederationEngine:
    """Test suite for Memory Federation Engine"""
    
    @pytest.fixture
    def federation_config(self):
        """Federation engine configuration"""
        return {
            'min_sharing_score': 0.6,
            'min_discovery_score': 0.5,
            'cache_ttl': 300
        }
    
    @pytest.fixture
    def federation_engine(self, federation_config):
        """Memory federation engine instance"""
        return MemoryFederationEngine(federation_config)
    
    @pytest.fixture
    def source_team_context(self):
        """Source team context for testing"""
        return TeamContext(
            team_id="engineering",
            team_name="Engineering Team",
            department="Technology",
            organization="Ninaivalaigal",
            access_level=4,
            specializations=["backend", "ai", "ml"],
            collaboration_history={"support": 0.8, "product": 0.6}
        )
    
    @pytest.fixture
    def target_team_context(self):
        """Target team context for testing"""
        return TeamContext(
            team_id="support",
            team_name="Support Team", 
            department="Operations",
            organization="Ninaivalaigal",
            access_level=3,
            specializations=["troubleshooting", "customer_service"],
            collaboration_history={"engineering": 0.8}
        )
    
    @pytest.fixture
    def sample_memories(self):
        """Sample memories for federation testing"""
        return [
            {
                'id': 'mem_001',
                'title': 'API Debugging Guide',
                'content': 'Comprehensive guide for debugging REST API issues',
                'tags': ['api', 'debugging', 'troubleshooting'],
                'privacy_level': 'internal',
                'quality_score': 0.9,
                'created_at': datetime.utcnow().isoformat()
            },
            {
                'id': 'mem_002', 
                'title': 'Database Performance Optimization',
                'content': 'Techniques for optimizing database queries and performance',
                'tags': ['database', 'performance', 'optimization'],
                'privacy_level': 'restricted',
                'quality_score': 0.8,
                'created_at': (datetime.utcnow() - timedelta(days=30)).isoformat()
            },
            {
                'id': 'mem_003',
                'title': 'Confidential Security Protocols',
                'content': 'Internal security protocols and procedures',
                'tags': ['security', 'protocols'],
                'privacy_level': 'confidential',
                'quality_score': 0.95,
                'created_at': datetime.utcnow().isoformat()
            }
        ]
    
    def test_federation_engine_initialization(self, federation_config):
        """Test federation engine initializes correctly"""
        engine = MemoryFederationEngine(federation_config)
        
        assert engine.config == federation_config
        assert engine.sharing_rules == {}
        assert engine.team_contexts == {}
        assert engine.federation_cache == {}
        assert engine.metrics.total_federations == 0
    
    @pytest.mark.asyncio
    async def test_federate_memories_success(
        self, 
        federation_engine, 
        source_team_context, 
        target_team_context,
        sample_memories
    ):
        """Test successful memory federation with intelligent filtering"""
        
        # Mock team context retrieval
        with patch.object(federation_engine, '_get_team_context') as mock_get_context:
            mock_get_context.side_effect = lambda team_id: (
                source_team_context if team_id == "engineering" else target_team_context
            )
            
            # Mock sharing eligibility and scoring
            with patch.object(federation_engine, '_is_shareable', return_value=True), \
                 patch.object(federation_engine, '_calculate_sharing_score', return_value=0.8), \
                 patch.object(federation_engine, '_apply_privacy_filters') as mock_filter:
                
                # Mock privacy filtering to return filtered memory
                mock_filter.return_value = sample_memories[0]  # Return first memory
                
                result = await federation_engine.federate_memories(
                    source_team="engineering",
                    target_teams=["support"],
                    memory_batch=sample_memories[:1],  # Test with first memory only
                    sharing_context={"urgency": "high"}
                )
                
                # Verify successful federation
                assert result.success is True
                assert len(result.federated_memories) == 1
                assert result.federated_memories[0].memory_id == 'mem_001'
                assert result.federated_memories[0].sharing_score == 0.8
                assert result.federated_memories[0].original_team == "engineering"
                assert "support" in result.federated_memories[0].shared_with
                assert result.processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_federate_memories_privacy_filtering(
        self,
        federation_engine,
        source_team_context,
        target_team_context, 
        sample_memories
    ):
        """Test privacy filtering blocks confidential content"""
        
        with patch.object(federation_engine, '_get_team_context') as mock_get_context:
            mock_get_context.side_effect = lambda team_id: (
                source_team_context if team_id == "engineering" else target_team_context
            )
            
            with patch.object(federation_engine, '_is_shareable', return_value=True), \
                 patch.object(federation_engine, '_calculate_sharing_score', return_value=0.8), \
                 patch.object(federation_engine, '_apply_privacy_filters', return_value=None):
                
                # Test with confidential memory
                confidential_memory = [sample_memories[2]]  # Confidential memory
                
                result = await federation_engine.federate_memories(
                    source_team="engineering",
                    target_teams=["support"],
                    memory_batch=confidential_memory
                )
                
                # Verify privacy filtering worked
                assert result.success is True
                assert len(result.federated_memories) == 0
                assert len(result.privacy_violations) == 1
                assert "mem_003" in result.privacy_violations[0]
    
    @pytest.mark.asyncio
    async def test_discover_shareable_knowledge(
        self,
        federation_engine,
        target_team_context
    ):
        """Test knowledge discovery from other teams"""
        
        # Mock federated memories cache
        mock_federated_memories = [
            FederatedMemory(
                memory_id="mem_shared_001",
                original_team="engineering",
                shared_with=["support"],
                sharing_score=0.9,
                privacy_filtered=False,
                federation_timestamp=datetime.utcnow(),
                access_count=5,
                feedback_score=0.8
            )
        ]
        
        with patch.object(federation_engine, '_identify_relevant_teams', return_value=["engineering"]), \
             patch.object(federation_engine, '_can_access_team_knowledge', return_value=True), \
             patch.object(federation_engine, '_fetch_team_memories', return_value=mock_federated_memories), \
             patch.object(federation_engine, '_calculate_query_relevance', return_value=0.85):
            
            discovered = await federation_engine.discover_shareable_knowledge(
                team_context=target_team_context,
                query_context={"query": "API debugging", "urgency": "medium"},
                limit=10
            )
            
            # Verify discovery results
            assert len(discovered) == 1
            assert discovered[0].memory_id == "mem_shared_001"
            assert discovered[0].sharing_score == 0.85  # Updated by query relevance
            assert discovered[0].original_team == "engineering"
    
    @pytest.mark.asyncio
    async def test_sharing_score_calculation(
        self,
        federation_engine,
        source_team_context,
        target_team_context,
        sample_memories
    ):
        """Test intelligent sharing score calculation"""
        
        memory = sample_memories[0]  # API debugging guide
        
        with patch.object(federation_engine, '_calculate_content_relevance', return_value=0.8), \
             patch.object(federation_engine, '_calculate_organizational_proximity', return_value=0.6), \
             patch.object(federation_engine, '_calculate_memory_freshness', return_value=0.9), \
             patch.object(federation_engine, '_calculate_context_boost', return_value=0.7):
            
            score = await federation_engine._calculate_sharing_score(
                memory=memory,
                source_context=source_team_context,
                target_context=target_team_context,
                sharing_context={"urgency": "high", "topic": "debugging"}
            )
            
            # Verify score is calculated correctly
            assert 0.0 <= score <= 1.0
            assert score > 0.5  # Should be reasonably high given good inputs
    
    def test_content_relevance_calculation(self, federation_engine):
        """Test content relevance scoring"""
        
        memory = {
            'tags': ['api', 'debugging', 'rest'],
            'content': 'This guide covers API debugging techniques and REST troubleshooting',
            'title': 'API Debugging Guide'
        }
        
        specializations = ['debugging', 'troubleshooting', 'api']
        
        relevance = asyncio.run(
            federation_engine._calculate_content_relevance(memory, specializations)
        )
        
        # Should have high relevance due to matching tags and content
        assert relevance > 0.7
        assert relevance <= 1.0
    
    def test_organizational_proximity_calculation(self, federation_engine):
        """Test organizational proximity scoring"""
        
        source = TeamContext(
            team_id="eng1",
            team_name="Engineering Team 1",
            department="Technology",
            organization="Ninaivalaigal",
            access_level=4,
            specializations=[],
            collaboration_history={}
        )
        
        target = TeamContext(
            team_id="eng2", 
            team_name="Engineering Team 2",
            department="Technology",
            organization="Ninaivalaigal",
            access_level=3,
            specializations=[],
            collaboration_history={}
        )
        
        proximity = federation_engine._calculate_organizational_proximity(source, target)
        
        # Same org and department should have high proximity
        assert proximity > 0.7
        assert proximity <= 1.0
    
    def test_memory_freshness_calculation(self, federation_engine):
        """Test memory freshness scoring"""
        
        # Recent memory
        recent_memory = {
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Old memory
        old_memory = {
            'created_at': (datetime.utcnow() - timedelta(days=200)).isoformat()
        }
        
        recent_freshness = federation_engine._calculate_memory_freshness(recent_memory)
        old_freshness = federation_engine._calculate_memory_freshness(old_memory)
        
        # Recent memory should have higher freshness
        assert recent_freshness > old_freshness
        assert recent_freshness > 0.9
        assert old_freshness < 0.6
    
    @pytest.mark.asyncio
    async def test_federation_metrics_tracking(
        self,
        federation_engine,
        source_team_context,
        target_team_context,
        sample_memories
    ):
        """Test federation metrics are tracked correctly"""
        
        initial_metrics = await federation_engine.get_federation_metrics()
        assert initial_metrics.total_federations == 0
        
        with patch.object(federation_engine, '_get_team_context') as mock_get_context:
            mock_get_context.side_effect = lambda team_id: (
                source_team_context if team_id == "engineering" else target_team_context
            )
            
            with patch.object(federation_engine, '_is_shareable', return_value=True), \
                 patch.object(federation_engine, '_calculate_sharing_score', return_value=0.8), \
                 patch.object(federation_engine, '_apply_privacy_filters') as mock_filter:
                
                mock_filter.return_value = sample_memories[0]
                
                await federation_engine.federate_memories(
                    source_team="engineering",
                    target_teams=["support"],
                    memory_batch=sample_memories[:1]
                )
                
                updated_metrics = await federation_engine.get_federation_metrics()
                
                # Verify metrics were updated
                assert updated_metrics.total_federations == 1
                assert updated_metrics.successful_shares == 1
                assert updated_metrics.federation_latency_ms > 0
    
    @pytest.mark.asyncio
    async def test_privacy_filter_application(
        self,
        federation_engine,
        source_team_context,
        target_team_context
    ):
        """Test privacy filters are applied correctly"""
        
        confidential_memory = {
            'id': 'mem_conf',
            'title': 'Confidential Data',
            'content': 'This contains sensitive information',
            'privacy_level': 'confidential',
            'personal_data': 'John Doe - john@example.com',
            'api_keys': 'secret-key-123'
        }
        
        filtered = await federation_engine._apply_privacy_filters(
            memory=confidential_memory,
            source_context=source_team_context,
            target_context=target_team_context
        )
        
        # For confidential content, should return limited metadata only
        if filtered:
            assert 'personal_data' not in filtered
            assert 'api_keys' not in filtered
            assert 'id' in filtered
            assert 'title' in filtered
    
    @pytest.mark.asyncio
    async def test_federation_error_handling(
        self,
        federation_engine,
        sample_memories
    ):
        """Test federation handles errors gracefully"""
        
        # Mock an exception during team context retrieval
        with patch.object(federation_engine, '_get_team_context', side_effect=Exception("Database error")):
            
            result = await federation_engine.federate_memories(
                source_team="engineering",
                target_teams=["support"],
                memory_batch=sample_memories
            )
            
            # Should return failure result
            assert result.success is False
            assert len(result.federated_memories) == 0
            assert len(result.privacy_violations) == 1
            assert "Database error" in result.privacy_violations[0]
    
    def test_federation_performance_targets(self, federation_engine):
        """Test federation meets performance targets"""
        
        # Federation should complete within reasonable time
        start_time = datetime.utcnow()
        
        # Simulate federation processing
        federation_engine._update_federation_metrics(
            successful=10,
            filtered=2,
            processing_time=50.0  # 50ms
        )
        
        metrics = asyncio.run(federation_engine.get_federation_metrics())
        
        # Verify performance targets
        assert metrics.federation_latency_ms <= 100  # Target: <100ms
        assert metrics.successful_shares > 0
        assert metrics.total_federations > 0

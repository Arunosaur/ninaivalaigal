#!/usr/bin/env python3
"""
Test Suite for Universal AI Wrapper
Tests the core functionality of AI prompt enhancement with mem0 memories
"""

import asyncio
import os
import sys
from datetime import datetime
from unittest.mock import patch

import pytest

# Add server path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))


# Mock the config loading to avoid import issues
def mock_load_config():
    return {"database_url": "sqlite:///test.db", "jwt_secret": "test_secret"}


# Patch the load_config function before importing
with patch("main.load_config", mock_load_config):
    from universal_ai_wrapper import (
        AIContext,
        AIModel,
        MCPAIEnhancer,
        MemoryContext,
        UniversalAIWrapper,
    )


class TestUniversalAIWrapper:
    """Test cases for UniversalAIWrapper"""

    @pytest.fixture
    def wrapper(self):
        """Create wrapper instance for testing"""
        return UniversalAIWrapper()

    @pytest.fixture
    def sample_context(self):
        """Sample AI context for testing"""
        return AIContext(
            file_path="test.ts",
            language="typescript",
            cursor_position=100,
            surrounding_code="function authenticateUser(token: string) {\n  // cursor here\n}",
            user_id=1,
            team_id=1,
            organization_id=1,
            project_context="auth-system",
            ai_model=AIModel.COPILOT,
            ide_name="vscode",
        )

    @pytest.fixture
    def sample_memories(self):
        """Sample memories for testing"""
        return [
            MemoryContext(
                content="Always validate JWT tokens before processing",
                context_name="personal",
                memory_type="security",
                relevance_score=3.0,
                created_at=datetime.now().isoformat(),
            ),
            MemoryContext(
                content="Team standard: Use bcrypt for password hashing",
                context_name="team",
                memory_type="standard",
                relevance_score=2.5,
                created_at=datetime.now().isoformat(),
            ),
            MemoryContext(
                content="Organization policy: All auth functions must have error handling",
                context_name="organization",
                memory_type="policy",
                relevance_score=2.0,
                created_at=datetime.now().isoformat(),
            ),
        ]

    @pytest.mark.asyncio
    async def test_enhance_ai_prompt_success(
        self, wrapper, sample_context, sample_memories
    ):
        """Test successful AI prompt enhancement"""
        with patch.object(
            wrapper, "_get_hierarchical_memories", return_value=sample_memories
        ):
            with patch.object(wrapper, "_store_ai_interaction", return_value=None):
                result = await wrapper.enhance_ai_prompt(
                    sample_context, "Complete the user authentication function"
                )

                assert result["enhancement_applied"] is True
                assert len(result["memories_used"]) == 3
                assert "Personal Coding Preferences:" in result["enhanced_prompt"]
                assert "Team Standards & Patterns:" in result["enhanced_prompt"]
                assert "Organizational Guidelines:" in result["enhanced_prompt"]

    @pytest.mark.asyncio
    async def test_enhance_ai_prompt_no_memories(self, wrapper, sample_context):
        """Test AI prompt enhancement with no memories"""
        with patch.object(wrapper, "_get_hierarchical_memories", return_value=[]):
            result = await wrapper.enhance_ai_prompt(
                sample_context, "Complete the function"
            )

            assert result["enhancement_applied"] is False
            assert len(result["memories_used"]) == 0
            assert result["enhanced_prompt"] == "Complete the function"

    @pytest.mark.asyncio
    async def test_get_hierarchical_memories(self, wrapper, sample_context):
        """Test hierarchical memory retrieval"""
        mock_personal = [
            MemoryContext(
                "Personal memory", "personal", "memory", 3.0, datetime.now().isoformat()
            )
        ]
        mock_team = [
            MemoryContext(
                "Team memory", "team", "memory", 2.0, datetime.now().isoformat()
            )
        ]

        with patch.object(wrapper, "_get_memories_by_level") as mock_get_memories:
            mock_get_memories.side_effect = [mock_personal, mock_team, [], []]

            memories = await wrapper._get_hierarchical_memories(sample_context)

            # Should call for personal, team, organization levels
            assert mock_get_memories.call_count >= 2
            assert len(memories) >= 1

    def test_rank_memories_by_relevance(self, wrapper, sample_context, sample_memories):
        """Test memory ranking algorithm"""
        ranked_memories = wrapper._rank_memories_by_relevance(
            sample_memories, sample_context
        )

        # Personal memories should rank highest
        personal_memory = next(
            (m for m in ranked_memories if m.context_name == "personal"), None
        )
        assert personal_memory is not None
        assert personal_memory.relevance_score >= 3.0

        # Memories should be sorted by relevance
        scores = [m.relevance_score for m in ranked_memories]
        assert scores == sorted(scores, reverse=True)

    def test_build_enhanced_prompt(self, wrapper, sample_context, sample_memories):
        """Test enhanced prompt building"""
        enhanced_prompt = wrapper._build_enhanced_prompt(
            "Complete the authentication function", sample_memories, sample_context
        )

        assert "# Personal Coding Preferences:" in enhanced_prompt
        assert "# Team Standards & Patterns:" in enhanced_prompt
        assert "# Organizational Guidelines:" in enhanced_prompt
        assert "Complete the authentication function" in enhanced_prompt
        assert "Language: typescript" in enhanced_prompt
        assert "IDE: vscode" in enhanced_prompt

    def test_extract_code_keywords(self, wrapper):
        """Test code keyword extraction"""
        code = """
        async function authenticateUser(token: string) {
            const decoded = jwt.verify(token);
            return await database.findUser(decoded.id);
        }
        """

        keywords = wrapper._extract_code_keywords(code)

        assert "async" in keywords
        assert "function" in keywords
        assert "jwt" in keywords or "token" in keywords
        assert "database" in keywords

    def test_get_file_type(self, wrapper):
        """Test file type extraction"""
        assert wrapper._get_file_type("test.ts") == "ts"
        assert wrapper._get_file_type("app.py") == "py"
        assert wrapper._get_file_type("component.jsx") == "jsx"
        assert wrapper._get_file_type("README.md") == "md"


class TestMCPAIEnhancer:
    """Test cases for MCP AI Enhancer"""

    @pytest.fixture
    def enhancer(self):
        """Create MCP AI enhancer for testing"""
        return MCPAIEnhancer()

    @pytest.mark.asyncio
    async def test_enhance_prompt_mcp_tool(self, enhancer):
        """Test MCP tool interface for prompt enhancement"""
        mock_result = {
            "enhanced_prompt": "Enhanced prompt with memories",
            "memories_used": [{"content": "Test memory"}],
            "enhancement_applied": True,
        }

        with patch.object(
            enhancer.wrapper, "enhance_ai_prompt", return_value=mock_result
        ):
            result = await enhancer.enhance_prompt(
                file_path="test.ts",
                language="typescript",
                prompt="Complete function",
                ai_model="github_copilot",
                user_id=1,
            )

            assert "✅ Enhanced prompt with 1 memories:" in result
            assert "Enhanced prompt with memories" in result

    @pytest.mark.asyncio
    async def test_enhance_prompt_no_enhancement(self, enhancer):
        """Test MCP tool when no enhancement is applied"""
        mock_result = {
            "enhanced_prompt": "Original prompt",
            "memories_used": [],
            "enhancement_applied": False,
        }

        with patch.object(
            enhancer.wrapper, "enhance_ai_prompt", return_value=mock_result
        ):
            result = await enhancer.enhance_prompt(
                file_path="test.ts", language="typescript", prompt="Original prompt"
            )

            assert "ℹ️ No relevant memories found" in result
            assert "Original prompt" in result

    @pytest.mark.asyncio
    async def test_enhance_prompt_error_handling(self, enhancer):
        """Test MCP tool error handling"""
        with patch.object(
            enhancer.wrapper, "enhance_ai_prompt", side_effect=Exception("Test error")
        ):
            result = await enhancer.enhance_prompt(
                file_path="test.ts", language="typescript", prompt="Test prompt"
            )

            assert "❌ Error enhancing prompt: Test error" in result


class TestAIContext:
    """Test cases for AIContext data model"""

    def test_ai_context_creation(self):
        """Test AIContext creation with all fields"""
        context = AIContext(
            file_path="test.py",
            language="python",
            cursor_position=50,
            surrounding_code="def test():\n    pass",
            user_id=1,
            team_id=2,
            organization_id=3,
            project_name="test-project",
            project_context="testing",
            ai_model=AIModel.GPT,
            interaction_type="completion",
            ide_name="vscode",
            workspace_path="/workspace",
        )

        assert context.file_path == "test.py"
        assert context.language == "python"
        assert context.ai_model == AIModel.GPT
        assert context.user_id == 1
        assert context.team_id == 2
        assert context.organization_id == 3

    def test_ai_context_defaults(self):
        """Test AIContext with default values"""
        context = AIContext(
            file_path="test.js",
            language="javascript",
            cursor_position=0,
            surrounding_code="",
        )

        assert context.user_id is None
        assert context.team_id is None
        assert context.ai_model == AIModel.GENERIC
        assert context.interaction_type == "completion"


class TestMemoryContext:
    """Test cases for MemoryContext data model"""

    def test_memory_context_creation(self):
        """Test MemoryContext creation"""
        memory = MemoryContext(
            content="Test memory content",
            context_name="personal",
            memory_type="preference",
            relevance_score=2.5,
            created_at=datetime.now().isoformat(),
            source="mem0",
        )

        assert memory.content == "Test memory content"
        assert memory.context_name == "personal"
        assert memory.memory_type == "preference"
        assert memory.relevance_score == 2.5
        assert memory.source == "mem0"


class TestIntegration:
    """Integration tests for the complete workflow"""

    @pytest.mark.asyncio
    async def test_end_to_end_enhancement_workflow(self):
        """Test complete end-to-end AI enhancement workflow"""
        # Mock MCP server response
        mock_mcp_response = "• Personal: Always use TypeScript interfaces\n• Team: Follow React hooks pattern"

        wrapper = UniversalAIWrapper()

        with patch.object(wrapper, "_query_mcp_server", return_value=mock_mcp_response):
            with patch.object(wrapper, "_store_ai_interaction", return_value=None):
                context = AIContext(
                    file_path="component.tsx",
                    language="typescript",
                    cursor_position=150,
                    surrounding_code="interface UserProps {\n  // cursor here\n}",
                    user_id=1,
                    team_id=1,
                    project_context="react-app",
                    ai_model=AIModel.COPILOT,
                    ide_name="vscode",
                )

                result = await wrapper.enhance_ai_prompt(
                    context, "Complete the UserProps interface"
                )

                assert result["enhancement_applied"] is True
                assert len(result["memories_used"]) > 0
                assert "Personal Coding Preferences:" in result["enhanced_prompt"]
                assert "Complete the UserProps interface" in result["enhanced_prompt"]
                assert "typescript" in result["enhanced_prompt"]


# Performance Tests
class TestPerformance:
    """Performance tests for AI enhancement"""

    @pytest.mark.asyncio
    async def test_enhancement_latency(self):
        """Test that enhancement completes within performance targets"""
        wrapper = UniversalAIWrapper()

        # Mock fast responses
        with patch.object(wrapper, "_query_mcp_server", return_value="• Fast memory"):
            with patch.object(wrapper, "_store_ai_interaction", return_value=None):
                context = AIContext(
                    file_path="test.js",
                    language="javascript",
                    cursor_position=0,
                    surrounding_code="",
                    ai_model=AIModel.GENERIC,
                )

                start_time = asyncio.get_event_loop().time()

                await wrapper.enhance_ai_prompt(context, "Test prompt")

                end_time = asyncio.get_event_loop().time()
                latency = (end_time - start_time) * 1000  # Convert to milliseconds

                # Should complete within 200ms target
                assert (
                    latency < 200
                ), f"Enhancement took {latency}ms, exceeds 200ms target"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])

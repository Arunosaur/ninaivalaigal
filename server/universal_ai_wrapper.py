#!/usr/bin/env python3
"""
Universal AI Wrapper for mem0 MCP Integration
Works with any AI model (Copilot, Claude, GPT, etc.) via clean MCP architecture
No IDE extensions required - pure MCP protocol integration
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

# Import MCP components
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import DatabaseManager
from main import load_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIModel(Enum):
    COPILOT = "github_copilot"
    CLAUDE = "anthropic_claude"
    GPT = "openai_gpt"
    GEMINI = "google_gemini"
    GENERIC = "generic_ai"


@dataclass
class AIContext:
    """Universal context for any AI model interaction"""

    # File context
    file_path: str
    language: str
    cursor_position: int
    surrounding_code: str

    # User context
    user_id: int | None = None
    team_id: int | None = None
    organization_id: int | None = None

    # Project context
    project_name: str | None = None
    project_context: str | None = None

    # AI model context
    ai_model: AIModel = AIModel.GENERIC
    interaction_type: str = "completion"  # completion, chat, review, etc.

    # IDE context
    ide_name: str | None = None
    workspace_path: str | None = None


@dataclass
class MemoryContext:
    """Memory retrieved from mem0"""

    content: str
    context_name: str
    memory_type: str
    relevance_score: float
    created_at: str
    source: str = "mem0"


class UniversalAIWrapper:
    """Universal wrapper that enhances any AI model with mem0 memories via MCP"""

    def __init__(self):
        self.db = DatabaseManager(load_config())
        self.mcp_server_path = os.path.join(os.path.dirname(__file__), "mcp_server.py")

    async def enhance_ai_prompt(
        self, context: AIContext, original_prompt: str
    ) -> dict[str, Any]:
        """Enhance any AI prompt with relevant mem0 memories"""
        try:
            # Get relevant memories from all levels
            memories = await self._get_hierarchical_memories(context)

            if not memories:
                return {
                    "enhanced_prompt": original_prompt,
                    "memories_used": [],
                    "enhancement_applied": False,
                }

            # Build enhanced prompt
            enhanced_prompt = self._build_enhanced_prompt(
                original_prompt, memories, context
            )

            # Store interaction for learning
            await self._store_ai_interaction(
                context, original_prompt, enhanced_prompt, memories
            )

            logger.info(
                f"Enhanced {context.ai_model.value} prompt with {len(memories)} memories"
            )

            return {
                "enhanced_prompt": enhanced_prompt,
                "memories_used": [asdict(m) for m in memories],
                "enhancement_applied": True,
                "context": asdict(context),
            }

        except Exception as e:
            logger.error(f"Error enhancing AI prompt: {e}")
            return {
                "enhanced_prompt": original_prompt,
                "memories_used": [],
                "enhancement_applied": False,
                "error": str(e),
            }

    async def _get_hierarchical_memories(
        self, context: AIContext
    ) -> list[MemoryContext]:
        """Get memories from all hierarchy levels: Personal → Team → Cross-Team → Organizational"""
        all_memories = []

        try:
            # 1. Personal memories (highest priority)
            if context.user_id:
                personal_memories = await self._get_memories_by_level(
                    "personal", context
                )
                all_memories.extend(personal_memories)

            # 2. Team memories
            if context.team_id:
                team_memories = await self._get_memories_by_level("team", context)
                all_memories.extend(team_memories)

            # 3. Cross-team memories (approved access)
            cross_team_memories = await self._get_cross_team_memories(context)
            all_memories.extend(cross_team_memories)

            # 4. Organizational memories (lowest priority but broadest)
            if context.organization_id:
                org_memories = await self._get_memories_by_level(
                    "organization", context
                )
                all_memories.extend(org_memories)

            # 5. Project-specific memories
            if context.project_context:
                project_memories = await self._get_memories_by_level("project", context)
                all_memories.extend(project_memories)

            # Filter, rank, and limit memories
            relevant_memories = self._rank_memories_by_relevance(all_memories, context)

            return relevant_memories[:10]  # Top 10 most relevant

        except Exception as e:
            logger.error(f"Error getting hierarchical memories: {e}")
            return []

    async def _get_memories_by_level(
        self, level: str, context: AIContext
    ) -> list[MemoryContext]:
        """Get memories for a specific hierarchy level"""
        try:
            # Build query based on level and context
            query_filters = {}

            if level == "personal" and context.user_id:
                query_filters["user_id"] = context.user_id
            elif level == "team" and context.team_id:
                query_filters["team_id"] = context.team_id
            elif level == "organization" and context.organization_id:
                query_filters["organization_id"] = context.organization_id
            elif level == "project" and context.project_context:
                query_filters["context"] = context.project_context

            # Get memories from database
            raw_memories = self.db.get_memories(
                context=query_filters.get("context"),
                user_id=query_filters.get("user_id"),
            )

            # Convert to MemoryContext objects
            memories = []
            for memory in raw_memories:
                memories.append(
                    MemoryContext(
                        content=memory.get("data", ""),
                        context_name=memory.get("context", "unknown"),
                        relevance_score=0.7,  # Will be calculated by ranking
                        timestamp=datetime.fromisoformat(
                            memory.get("created_at", datetime.now().isoformat())
                        ),
                        memory_type=level,
                        source=memory.get("source", "database"),
                    )
                )

            return memories

        except Exception as e:
            logger.error(f"Error getting {level} memories: {e}")
            return []

    async def _get_cross_team_memories(self, context: AIContext) -> list[MemoryContext]:
        """Get cross-team memories that user has approved access to"""
        try:
            # For now, return empty list - will implement with approval workflow
            return []

        except Exception as e:
            logger.error(f"Error getting cross-team memories: {e}")
            return []

    async def _query_mcp_server(self, tool: str, params: dict[str, Any]) -> str:
        """Query mem0 MCP server"""
        try:
            # Build MCP request
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": tool, "arguments": params},
            }

            # Execute MCP server query via subprocess
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                self.mcp_server_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate(
                input=json.dumps(mcp_request).encode()
            )

            if process.returncode == 0:
                response = json.loads(stdout.decode())
                return response.get("result", "")
            else:
                logger.error(f"MCP server error: {stderr.decode()}")
                return ""

        except Exception as e:
            logger.error(f"Error querying MCP server: {e}")
            return ""

    def _parse_memories_response(
        self, response: str, level: str
    ) -> list[MemoryContext]:
        """Parse memory response from MCP server into MemoryContext objects"""
        memories = []

        try:
            lines = response.split("\n")
            current_memory = None

            for line in lines:
                line = line.strip()
                if line.startswith("•") or line.startswith("-"):
                    if current_memory:
                        memories.append(current_memory)

                    current_memory = MemoryContext(
                        content=line[1:].strip(),
                        context_name=level,
                        memory_type="memory",
                        relevance_score=1.0,
                        created_at=datetime.now().isoformat(),
                    )
                elif line and current_memory:
                    current_memory.content += " " + line

            if current_memory:
                memories.append(current_memory)

        except Exception as e:
            logger.error(f"Error parsing memories response: {e}")

        return memories

    def _rank_memories_by_relevance(
        self, memories: list[MemoryContext], context: AIContext
    ) -> list[MemoryContext]:
        """Rank memories by relevance to current context"""
        for memory in memories:
            score = 0
            content_lower = memory.content.lower()

            # Language relevance
            if context.language.lower() in content_lower:
                score += 3

            # File type relevance
            file_type = self._get_file_type(context.file_path)
            if file_type in content_lower:
                score += 2

            # AI model specific relevance
            if context.ai_model.value in content_lower:
                score += 2

            # Code pattern relevance
            code_keywords = self._extract_code_keywords(context.surrounding_code)
            for keyword in code_keywords:
                if keyword.lower() in content_lower:
                    score += 1

            # Context hierarchy bonus
            if memory.context_name == "personal":
                score += 3  # Personal memories are most relevant
            elif memory.context_name == "team":
                score += 2
            elif memory.context_name == "organization":
                score += 1

            memory.relevance_score = score

        # Sort by relevance score
        memories.sort(key=lambda x: x.relevance_score, reverse=True)
        return memories

    def _build_enhanced_prompt(
        self, original_prompt: str, memories: list[MemoryContext], context: AIContext
    ) -> str:
        """Build enhanced prompt with hierarchical memories"""
        if not memories:
            return original_prompt

        # Group memories by hierarchy level
        memory_groups = {}
        for memory in memories:
            level = memory.context_name
            if level not in memory_groups:
                memory_groups[level] = []
            memory_groups[level].append(memory)

        # Build hierarchical context
        context_sections = []

        # Personal context (highest priority)
        if "personal" in memory_groups:
            personal_context = "# Personal Coding Preferences:\n"
            for memory in memory_groups["personal"][:3]:  # Top 3 personal memories
                personal_context += f"- {memory.content}\n"
            context_sections.append(personal_context)

        # Team context
        if "team" in memory_groups:
            team_context = "# Team Standards & Patterns:\n"
            for memory in memory_groups["team"][:3]:
                team_context += f"- {memory.content}\n"
            context_sections.append(team_context)

        # Cross-team context
        if "cross_team" in memory_groups:
            cross_team_context = "# Cross-Team Best Practices:\n"
            for memory in memory_groups["cross_team"][:2]:
                cross_team_context += f"- {memory.content}\n"
            context_sections.append(cross_team_context)

        # Organizational context
        if "organization" in memory_groups:
            org_context = "# Organizational Guidelines:\n"
            for memory in memory_groups["organization"][:2]:
                org_context += f"- {memory.content}\n"
            context_sections.append(org_context)

        # Project context
        if "project" in memory_groups:
            project_context = "# Project-Specific Context:\n"
            for memory in memory_groups["project"][:3]:
                project_context += f"- {memory.content}\n"
            context_sections.append(project_context)

        # Combine all context
        if context_sections:
            enhanced_context = "\n".join(context_sections)
            enhanced_context += f"\n# Current Task ({context.ai_model.value}):\n"
            enhanced_prompt = f"{enhanced_context}{original_prompt}"

            # Add metadata
            enhanced_prompt += "\n\n# Context Metadata:"
            enhanced_prompt += f"\n- Language: {context.language}"
            enhanced_prompt += f"\n- File: {os.path.basename(context.file_path)}"
            enhanced_prompt += f"\n- IDE: {context.ide_name or 'Unknown'}"

            return enhanced_prompt

        return original_prompt

    async def _store_ai_interaction(
        self,
        context: AIContext,
        original_prompt: str,
        enhanced_prompt: str,
        memories: list[MemoryContext],
    ):
        """Store AI interaction for future learning"""
        try:
            interaction_data = {
                "ai_model": context.ai_model.value,
                "ide": context.ide_name,
                "language": context.language,
                "file_path": context.file_path,
                "memories_count": len(memories),
                "enhancement_applied": True,
                "timestamp": datetime.now().isoformat(),
            }

            # Store via MCP
            await self._query_mcp_server(
                "remember",
                {
                    "text": f"AI interaction enhanced with {len(memories)} memories for {context.language} in {context.ai_model.value}",
                    "context": f"ai_interactions_{context.project_context or 'default'}",
                    "metadata": interaction_data,
                },
            )

        except Exception as e:
            logger.error(f"Error storing AI interaction: {e}")

    def _get_file_type(self, file_path: str) -> str:
        """Extract file type from path"""
        _, ext = os.path.splitext(file_path)
        return ext.lower().lstrip(".")

    def _extract_code_keywords(self, code: str) -> list[str]:
        """Extract relevant keywords from surrounding code"""
        keywords = []

        # Programming patterns to detect
        patterns = {
            "javascript": [
                "function",
                "const",
                "let",
                "var",
                "async",
                "await",
                "promise",
                "callback",
            ],
            "typescript": [
                "interface",
                "type",
                "class",
                "enum",
                "generic",
                "decorator",
            ],
            "python": [
                "def",
                "class",
                "async",
                "await",
                "lambda",
                "decorator",
                "generator",
            ],
            "react": [
                "component",
                "props",
                "state",
                "hook",
                "useEffect",
                "useState",
                "jsx",
            ],
            "api": [
                "request",
                "response",
                "http",
                "fetch",
                "axios",
                "endpoint",
                "rest",
            ],
            "database": [
                "query",
                "model",
                "schema",
                "table",
                "collection",
                "orm",
                "sql",
            ],
            "testing": ["test", "spec", "mock", "assert", "expect", "describe", "it"],
            "security": [
                "auth",
                "token",
                "jwt",
                "oauth",
                "encrypt",
                "hash",
                "validate",
            ],
        }

        code_lower = code.lower()
        for category, category_patterns in patterns.items():
            for pattern in category_patterns:
                if pattern in code_lower:
                    keywords.append(pattern)

        return list(set(keywords))  # Remove duplicates


# MCP Tool Integration
class MCPAIEnhancer:
    """MCP tool that provides AI enhancement capabilities"""

    def __init__(self):
        self.wrapper = UniversalAIWrapper()

    async def enhance_prompt(self, **kwargs) -> str:
        """MCP tool to enhance AI prompts with mem0 memories"""
        try:
            # Parse context from MCP arguments
            context = AIContext(
                file_path=kwargs.get("file_path", ""),
                language=kwargs.get("language", ""),
                cursor_position=kwargs.get("cursor_position", 0),
                surrounding_code=kwargs.get("surrounding_code", ""),
                user_id=kwargs.get("user_id"),
                team_id=kwargs.get("team_id"),
                organization_id=kwargs.get("organization_id"),
                project_context=kwargs.get("project_context"),
                ai_model=AIModel(kwargs.get("ai_model", "generic_ai")),
                interaction_type=kwargs.get("interaction_type", "completion"),
                ide_name=kwargs.get("ide_name"),
                workspace_path=kwargs.get("workspace_path"),
            )

            original_prompt = kwargs.get("prompt", "")

            # Enhance prompt
            result = await self.wrapper.enhance_ai_prompt(context, original_prompt)

            if result["enhancement_applied"]:
                return f"✅ Enhanced prompt with {len(result['memories_used'])} memories:\n\n{result['enhanced_prompt']}"
            else:
                return f"ℹ️ No relevant memories found. Original prompt:\n\n{result['enhanced_prompt']}"

        except Exception as e:
            return f"❌ Error enhancing prompt: {str(e)}"


# Global instance for MCP integration
mcp_ai_enhancer = MCPAIEnhancer()


# Export functions for MCP server
async def enhance_ai_prompt(**kwargs) -> str:
    """Main function for MCP integration"""
    return await mcp_ai_enhancer.enhance_prompt(**kwargs)


if __name__ == "__main__":
    # Test the universal wrapper
    async def test_wrapper():
        context = AIContext(
            file_path="auth.ts",
            language="typescript",
            cursor_position=150,
            surrounding_code="async function authenticateUser(token: string) {\n  // cursor here\n}",
            user_id=1,
            team_id=1,
            project_context="auth-system",
            ai_model=AIModel.COPILOT,
            ide_name="vscode",
        )

        wrapper = UniversalAIWrapper()
        result = await wrapper.enhance_ai_prompt(
            context,
            "Complete the user authentication function with proper error handling",
        )

        print("Enhanced AI Prompt Result:")
        print(json.dumps(result, indent=2))

    asyncio.run(test_wrapper())

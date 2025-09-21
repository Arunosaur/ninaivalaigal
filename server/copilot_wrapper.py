#!/usr/bin/env python3
"""
GitHub Copilot + mem0 MCP Integration Wrapper
Enhances Copilot prompts with relevant memories from mem0 via MCP protocol
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any

# Import MCP client components
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import DatabaseManager
from main import load_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CopilotContext:
    """Context information for Copilot enhancement"""

    file_path: str
    language: str
    cursor_position: int
    surrounding_code: str
    user_id: int | None = None
    team_id: int | None = None
    project_context: str | None = None


class Mem0CopilotWrapper:
    """Wrapper that enhances Copilot with mem0 memories via MCP"""

    def __init__(self):
        self.db = DatabaseManager(load_config())
        self.mcp_server_path = os.path.join(os.path.dirname(__file__), "mcp_server.py")

    async def enhance_copilot_prompt(
        self, context: CopilotContext, original_prompt: str
    ) -> str:
        """Enhance Copilot prompt with relevant mem0 memories"""
        try:
            # Get relevant memories from mem0
            relevant_memories = await self._get_relevant_memories(context)

            if not relevant_memories:
                return original_prompt

            # Build enhanced prompt
            enhanced_prompt = self._build_enhanced_prompt(
                original_prompt, relevant_memories, context
            )

            logger.info(f"Enhanced prompt with {len(relevant_memories)} memories")
            return enhanced_prompt

        except Exception as e:
            logger.error(f"Error enhancing prompt: {e}")
            return original_prompt

    async def _get_relevant_memories(
        self, context: CopilotContext
    ) -> list[dict[str, Any]]:
        """Get relevant memories based on context"""
        memories = []

        try:
            # Get personal memories
            if context.user_id:
                personal_memories = await self._query_mcp_server(
                    "recall",
                    {
                        "context": "personal",
                        "user_id": context.user_id,
                        "language": context.language,
                        "file_type": self._get_file_type(context.file_path),
                    },
                )
                memories.extend(personal_memories)

            # Get team memories
            if context.team_id:
                team_memories = await self._query_mcp_server(
                    "recall",
                    {
                        "context": "team",
                        "team_id": context.team_id,
                        "language": context.language,
                    },
                )
                memories.extend(team_memories)

            # Get project-specific memories
            if context.project_context:
                project_memories = await self._query_mcp_server(
                    "recall",
                    {"context": context.project_context, "language": context.language},
                )
                memories.extend(project_memories)

            # Filter and rank memories by relevance
            relevant_memories = self._filter_relevant_memories(memories, context)

            return relevant_memories[:5]  # Limit to top 5 most relevant

        except Exception as e:
            logger.error(f"Error getting relevant memories: {e}")
            return []

    async def _query_mcp_server(
        self, tool: str, params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Query mem0 MCP server for memories"""
        try:
            # Build MCP request
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": tool, "arguments": params},
            }

            # Execute MCP server query
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
                if "result" in response:
                    return self._parse_memory_response(response["result"])

            return []

        except Exception as e:
            logger.error(f"Error querying MCP server: {e}")
            return []

    def _parse_memory_response(self, response: str) -> list[dict[str, Any]]:
        """Parse memory response from MCP server"""
        memories = []
        try:
            # Parse the response text to extract memories
            lines = response.split("\n")
            current_memory = {}

            for line in lines:
                line = line.strip()
                if line.startswith("•") or line.startswith("-"):
                    if current_memory:
                        memories.append(current_memory)
                    current_memory = {
                        "content": line[1:].strip(),
                        "relevance": 1.0,
                        "type": "memory",
                    }
                elif line and current_memory:
                    current_memory["content"] += " " + line

            if current_memory:
                memories.append(current_memory)

        except Exception as e:
            logger.error(f"Error parsing memory response: {e}")

        return memories

    def _filter_relevant_memories(
        self, memories: list[dict[str, Any]], context: CopilotContext
    ) -> list[dict[str, Any]]:
        """Filter and rank memories by relevance to current context"""
        relevant = []

        for memory in memories:
            content = memory.get("content", "").lower()
            relevance_score = 0

            # Language-specific relevance
            if context.language.lower() in content:
                relevance_score += 2

            # File type relevance
            file_type = self._get_file_type(context.file_path)
            if file_type in content:
                relevance_score += 1

            # Code pattern relevance
            code_keywords = self._extract_code_keywords(context.surrounding_code)
            for keyword in code_keywords:
                if keyword.lower() in content:
                    relevance_score += 1

            if relevance_score > 0:
                memory["relevance_score"] = relevance_score
                relevant.append(memory)

        # Sort by relevance score
        relevant.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return relevant

    def _build_enhanced_prompt(
        self,
        original_prompt: str,
        memories: list[dict[str, Any]],
        context: CopilotContext,
    ) -> str:
        """Build enhanced prompt with mem0 memories"""
        if not memories:
            return original_prompt

        # Build memory context
        memory_context = "# Relevant Context from mem0:\n"
        for i, memory in enumerate(memories, 1):
            memory_context += f"{i}. {memory['content']}\n"

        memory_context += "\n# Current Task:\n"

        # Combine with original prompt
        enhanced_prompt = f"{memory_context}{original_prompt}"

        # Add language-specific guidance
        if context.language:
            enhanced_prompt += f"\n\n# Language: {context.language}"
            enhanced_prompt += f"\n# File: {os.path.basename(context.file_path)}"

        return enhanced_prompt

    def _get_file_type(self, file_path: str) -> str:
        """Extract file type from path"""
        _, ext = os.path.splitext(file_path)
        return ext.lower().lstrip(".")

    def _extract_code_keywords(self, code: str) -> list[str]:
        """Extract relevant keywords from surrounding code"""
        keywords = []

        # Common programming keywords to look for
        common_patterns = [
            "function",
            "class",
            "interface",
            "type",
            "const",
            "let",
            "var",
            "async",
            "await",
            "promise",
            "callback",
            "event",
            "handler",
            "component",
            "props",
            "state",
            "hook",
            "effect",
            "context",
            "api",
            "request",
            "response",
            "http",
            "fetch",
            "axios",
            "database",
            "query",
            "model",
            "schema",
            "table",
            "collection",
        ]

        code_lower = code.lower()
        for pattern in common_patterns:
            if pattern in code_lower:
                keywords.append(pattern)

        return keywords

    async def store_copilot_interaction(
        self, context: CopilotContext, prompt: str, suggestion: str, accepted: bool
    ):
        """Store Copilot interaction in mem0 for future reference"""
        try:
            interaction_data = {
                "type": "copilot_interaction",
                "prompt": prompt,
                "suggestion": suggestion,
                "accepted": accepted,
                "language": context.language,
                "file_path": context.file_path,
                "timestamp": datetime.now().isoformat(),
            }

            # Store via MCP server
            await self._query_mcp_server(
                "remember",
                {
                    "text": f"Copilot {'accepted' if accepted else 'rejected'}: {suggestion[:100]}...",
                    "context": context.project_context or "copilot_interactions",
                    "metadata": interaction_data,
                },
            )

            logger.info(
                f"Stored Copilot interaction: {'accepted' if accepted else 'rejected'}"
            )

        except Exception as e:
            logger.error(f"Error storing Copilot interaction: {e}")


class VSCodeCopilotBridge:
    """Bridge between VS Code, Copilot, and mem0"""

    def __init__(self):
        self.wrapper = Mem0CopilotWrapper()

    async def handle_copilot_request(
        self, request_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle Copilot completion request with mem0 enhancement"""
        try:
            # Extract context from VS Code request
            context = CopilotContext(
                file_path=request_data.get("document", {}).get("uri", ""),
                language=request_data.get("document", {}).get("languageId", ""),
                cursor_position=request_data.get("position", {}).get("character", 0),
                surrounding_code=request_data.get("context", {}).get("prefix", "")
                + request_data.get("context", {}).get("suffix", ""),
                user_id=request_data.get("user_id"),
                team_id=request_data.get("team_id"),
                project_context=request_data.get("project_context"),
            )

            # Get original prompt (this would come from Copilot's internal prompt)
            original_prompt = request_data.get("prompt", "Generate code completion")

            # Enhance prompt with mem0 memories
            enhanced_prompt = await self.wrapper.enhance_copilot_prompt(
                context, original_prompt
            )

            return {
                "success": True,
                "enhanced_prompt": enhanced_prompt,
                "context": context.__dict__,
            }

        except Exception as e:
            logger.error(f"Error handling Copilot request: {e}")
            return {
                "success": False,
                "error": str(e),
                "original_prompt": request_data.get("prompt", ""),
            }


# Global instance
copilot_bridge = VSCodeCopilotBridge()


async def enhance_copilot_with_mem0(request_data: dict[str, Any]) -> dict[str, Any]:
    """Main function to enhance Copilot with mem0 memories"""
    return await copilot_bridge.handle_copilot_request(request_data)


if __name__ == "__main__":
    # Test the wrapper
    async def test_wrapper():
        context = CopilotContext(
            file_path="test.ts",
            language="typescript",
            cursor_position=100,
            surrounding_code="function handleUserAuth() {\n  // cursor here\n}",
            user_id=1,
            project_context="auth-system",
        )

        wrapper = Mem0CopilotWrapper()
        enhanced = await wrapper.enhance_copilot_prompt(
            context, "Complete the user authentication function"
        )

        print("Enhanced prompt:")
        print(enhanced)

    asyncio.run(test_wrapper())

#!/usr/bin/env python3
"""
mem0 Enhanced AI Tool Integrations
Provides seamless integration with various AI tools and platforms
"""

import asyncio
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import aiohttp

# Import existing mem0 components
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import DatabaseManager
from main import load_config
from performance_monitor import record_memory_operation, record_request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AIToolConfig:
    """Configuration for an AI tool integration"""
    name: str
    api_endpoint: str
    api_key_env: str
    supported_features: list[str]
    rate_limit_per_minute: int
    timeout_seconds: int
    retry_attempts: int

@dataclass
class AIInteraction:
    """Represents an interaction with an AI tool"""
    tool_name: str
    interaction_type: str  # 'query', 'response', 'error', 'completion'
    content: str
    metadata: dict[str, Any]
    timestamp: datetime
    context_id: str | None = None
    user_id: int | None = None

class AIToolIntegration:
    """Base class for AI tool integrations"""

    def __init__(self, config: AIToolConfig):
        self.config = config
        self.session = None
        self.last_request_time = 0
        self.request_count = 0
        self.reset_time = time.time()

    async def initialize(self):
        """Initialize the AI tool connection"""
        raise NotImplementedError

    async def send_query(self, query: str, context: dict[str, Any] = None) -> dict[str, Any]:
        """Send a query to the AI tool"""
        raise NotImplementedError

    async def get_context(self, context_id: str) -> dict[str, Any]:
        """Get context information from the AI tool"""
        raise NotImplementedError

    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        current_time = time.time()

        # Reset counter if minute has passed
        if current_time - self.reset_time >= 60:
            self.request_count = 0
            self.reset_time = current_time

        if self.request_count >= self.config.rate_limit_per_minute:
            return False

        self.request_count += 1
        return True

    def _wait_for_rate_limit(self):
        """Wait if we've hit rate limits"""
        current_time = time.time()
        time_since_reset = current_time - self.reset_time

        if time_since_reset < 60 and self.request_count >= self.config.rate_limit_per_minute:
            wait_time = 60 - time_since_reset
            time.sleep(wait_time)
            self.request_count = 0
            self.reset_time = time.time()

class OpenAIIntegration(AIToolIntegration):
    """Integration with OpenAI API"""

    async def initialize(self):
        self.api_key = os.getenv(self.config.api_key_env)
        if not self.api_key:
            raise ValueError(f"API key not found in environment: {self.config.api_key_env}")

        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )

    async def send_query(self, query: str, context: dict[str, Any] = None) -> dict[str, Any]:
        if not self._check_rate_limit():
            self._wait_for_rate_limit()

        payload = {
            "model": context.get("model", "gpt-3.5-turbo") if context else "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": query}],
            "max_tokens": context.get("max_tokens", 1000) if context else 1000,
            "temperature": context.get("temperature", 0.7) if context else 0.7
        }

        start_time = time.time()
        try:
            async with self.session.post(
                f"{self.config.api_endpoint}/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            ) as response:
                response_time = time.time() - start_time
                record_request("openai_api", "POST", response_time, response.status)

                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "response": result["choices"][0]["message"]["content"],
                        "usage": result.get("usage", {}),
                        "model": result.get("model", ""),
                        "response_time": response_time
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"API error {response.status}: {error_text}",
                        "response_time": response_time
                    }

        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"OpenAI API error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time": response_time
            }

    async def get_context(self, context_id: str) -> dict[str, Any]:
        # OpenAI doesn't have persistent contexts, return empty
        return {"context_id": context_id, "conversations": []}

class AnthropicIntegration(AIToolIntegration):
    """Integration with Anthropic Claude API"""

    async def initialize(self):
        self.api_key = os.getenv(self.config.api_key_env)
        if not self.api_key:
            raise ValueError(f"API key not found in environment: {self.config.api_key_env}")

        self.session = aiohttp.ClientSession(
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
        )

    async def send_query(self, query: str, context: dict[str, Any] = None) -> dict[str, Any]:
        if not self._check_rate_limit():
            self._wait_for_rate_limit()

        payload = {
            "model": context.get("model", "claude-3-sonnet-20240229") if context else "claude-3-sonnet-20240229",
            "max_tokens": context.get("max_tokens", 1000) if context else 1000,
            "messages": [{"role": "user", "content": query}]
        }

        start_time = time.time()
        try:
            async with self.session.post(
                f"{self.config.api_endpoint}/messages",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            ) as response:
                response_time = time.time() - start_time
                record_request("anthropic_api", "POST", response_time, response.status)

                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "response": result["content"][0]["text"],
                        "usage": result.get("usage", {}),
                        "model": result.get("model", ""),
                        "response_time": response_time
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"API error {response.status}: {error_text}",
                        "response_time": response_time
                    }

        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Anthropic API error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time": response_time
            }

    async def get_context(self, context_id: str) -> dict[str, Any]:
        # Anthropic doesn't have persistent contexts, return empty
        return {"context_id": context_id, "conversations": []}

class GitHubCopilotIntegration(AIToolIntegration):
    """Integration with GitHub Copilot (via VS Code extension API)"""

    async def initialize(self):
        # GitHub Copilot integration would typically be handled through VS Code extension
        # This is a placeholder for potential API integration
        self.session = None

    async def send_query(self, query: str, context: dict[str, Any] = None) -> dict[str, Any]:
        # GitHub Copilot doesn't have a direct API
        # This would need to be integrated through VS Code extension
        return {
            "success": False,
            "error": "GitHub Copilot integration requires VS Code extension",
            "response_time": 0
        }

    async def get_context(self, context_id: str) -> dict[str, Any]:
        return {"context_id": context_id, "tool": "github_copilot", "status": "extension_required"}

class AIIntegrationManager:
    """Manages all AI tool integrations"""

    def __init__(self):
        self.integrations: dict[str, AIToolIntegration] = {}
        self.interactions: list[AIInteraction] = []
        self.db = DatabaseManager(load_config())

        # Define supported AI tools
        self.tool_configs = {
            "openai": AIToolConfig(
                name="OpenAI",
                api_endpoint="https://api.openai.com/v1",
                api_key_env="OPENAI_API_KEY",
                supported_features=["chat", "completion", "embedding"],
                rate_limit_per_minute=60,
                timeout_seconds=30,
                retry_attempts=3
            ),
            "anthropic": AIToolConfig(
                name="Anthropic",
                api_endpoint="https://api.anthropic.com",
                api_key_env="ANTHROPIC_API_KEY",
                supported_features=["chat", "completion"],
                rate_limit_per_minute=50,
                timeout_seconds=30,
                retry_attempts=3
            ),
            "github_copilot": AIToolConfig(
                name="GitHub Copilot",
                api_endpoint="",  # No direct API
                api_key_env="",
                supported_features=["code_completion", "code_generation"],
                rate_limit_per_minute=1000,
                timeout_seconds=10,
                retry_attempts=1
            )
        }

    async def initialize_integrations(self):
        """Initialize all configured AI tool integrations"""
        for tool_name, config in self.tool_configs.items():
            api_key_env = config.api_key_env
            if api_key_env and os.getenv(api_key_env):
                try:
                    if tool_name == "openai":
                        integration = OpenAIIntegration(config)
                    elif tool_name == "anthropic":
                        integration = AnthropicIntegration(config)
                    elif tool_name == "github_copilot":
                        integration = GitHubCopilotIntegration(config)
                    else:
                        continue

                    await integration.initialize()
                    self.integrations[tool_name] = integration
                    logger.info(f"Initialized {tool_name} integration")
                except Exception as e:
                    logger.error(f"Failed to initialize {tool_name}: {e}")
            else:
                logger.debug(f"Skipping {tool_name} - API key not configured")

    async def query_ai_tool(self, tool_name: str, query: str, context: dict[str, Any] = None) -> dict[str, Any]:
        """Query a specific AI tool"""
        if tool_name not in self.integrations:
            return {
                "success": False,
                "error": f"AI tool '{tool_name}' not configured or available"
            }

        integration = self.integrations[tool_name]

        # Record the interaction
        interaction = AIInteraction(
            tool_name=tool_name,
            interaction_type="query",
            content=query,
            metadata=context or {},
            timestamp=datetime.now()
        )
        self.interactions.append(interaction)

        try:
            result = await integration.send_query(query, context)

            # Record the response
            response_interaction = AIInteraction(
                tool_name=tool_name,
                interaction_type="response" if result["success"] else "error",
                content=result.get("response", result.get("error", "")),
                metadata={"success": result["success"], "response_time": result.get("response_time", 0)},
                timestamp=datetime.now()
            )
            self.interactions.append(response_interaction)

            # Store in mem0 database if successful
            if result["success"]:
                await self._store_ai_interaction(interaction, response_interaction)

            return result

        except Exception as e:
            logger.error(f"Error querying {tool_name}: {e}")
            error_interaction = AIInteraction(
                tool_name=tool_name,
                interaction_type="error",
                content=str(e),
                metadata={"exception": type(e).__name__},
                timestamp=datetime.now()
            )
            self.interactions.append(error_interaction)

            return {
                "success": False,
                "error": str(e),
                "response_time": 0
            }

    async def _store_ai_interaction(self, query: AIInteraction, response: AIInteraction):
        """Store AI interaction in mem0 database"""
        try:
            # Store query
            await self.db.add_memory(
                context="ai_interactions",
                memory_type="ai_query",
                source=query.tool_name,
                data={
                    "content": query.content,
                    "metadata": query.metadata,
                    "timestamp": query.timestamp.isoformat(),
                    "interaction_type": "query"
                }
            )

            # Store response
            await self.db.add_memory(
                context="ai_interactions",
                memory_type="ai_response",
                source=response.tool_name,
                data={
                    "content": response.content,
                    "metadata": response.metadata,
                    "timestamp": response.timestamp.isoformat(),
                    "interaction_type": "response"
                }
            )

            record_memory_operation("ai_interaction_stored", True)

        except Exception as e:
            logger.error(f"Failed to store AI interaction: {e}")
            record_memory_operation("ai_interaction_stored", False)

    def get_supported_tools(self) -> list[str]:
        """Get list of supported AI tools"""
        return list(self.integrations.keys())

    def get_tool_capabilities(self, tool_name: str) -> dict[str, Any]:
        """Get capabilities of a specific AI tool"""
        if tool_name not in self.integrations:
            return {"error": f"Tool '{tool_name}' not available"}

        config = self.tool_configs.get(tool_name)
        if not config:
            return {"error": f"Configuration not found for '{tool_name}'"}

        return {
            "name": config.name,
            "supported_features": config.supported_features,
            "rate_limit_per_minute": config.rate_limit_per_minute,
            "timeout_seconds": config.timeout_seconds,
            "configured": True
        }

    def get_interaction_history(self, tool_name: str = None, limit: int = 100) -> list[dict[str, Any]]:
        """Get interaction history"""
        filtered_interactions = self.interactions

        if tool_name:
            filtered_interactions = [i for i in filtered_interactions if i.tool_name == tool_name]

        # Return most recent interactions
        recent_interactions = sorted(filtered_interactions, key=lambda x: x.timestamp, reverse=True)[:limit]

        return [asdict(interaction) for interaction in recent_interactions]

    async def cleanup(self):
        """Clean up all integrations"""
        for integration in self.integrations.values():
            await integration.cleanup()

# Global AI integration manager instance
ai_manager = AIIntegrationManager()

async def get_ai_manager() -> AIIntegrationManager:
    """Get the global AI integration manager instance"""
    return ai_manager

# Convenience functions for easy integration
async def query_ai_tool(tool_name: str, query: str, context: dict[str, Any] = None) -> dict[str, Any]:
    """Convenience function to query an AI tool"""
    return await ai_manager.query_ai_tool(tool_name, query, context)

def get_supported_ai_tools() -> list[str]:
    """Convenience function to get supported AI tools"""
    return ai_manager.get_supported_tools()

def get_ai_tool_capabilities(tool_name: str) -> dict[str, Any]:
    """Convenience function to get AI tool capabilities"""
    return ai_manager.get_tool_capabilities(tool_name)

def get_ai_interaction_history(tool_name: str = None, limit: int = 100) -> list[dict[str, Any]]:
    """Convenience function to get AI interaction history"""
    return ai_manager.get_interaction_history(tool_name, limit)

async def initialize_ai_integrations():
    """Convenience function to initialize AI integrations"""
    await ai_manager.initialize_integrations()

async def cleanup_ai_integrations():
    """Convenience function to cleanup AI integrations"""
    await ai_manager.cleanup()

if __name__ == "__main__":
    # Example usage
    async def main():
        await initialize_ai_integrations()

        tools = get_supported_ai_tools()
        print(f"Available AI tools: {tools}")

        if tools:
            # Query the first available tool
            result = await query_ai_tool(tools[0], "Hello, can you help me with coding?")
            print(f"AI Response: {result}")

        await cleanup_ai_integrations()

    asyncio.run(main())

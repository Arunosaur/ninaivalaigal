"""
AI Tools for SPEC-063 Agentic Core
Interfaces with AI models with memory injection and guardrails
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class AIToolchain:
    """
    AI toolchain for agentic execution with memory injection and guardrails.

    Provides scoped AI operations with:
    - Memory context injection
    - User-based permissions and guardrails
    - Multiple AI model support
    - Chain-of-thought tracing
    - Response validation and safety
    """

    def __init__(self):
        self.supported_models = ["openai", "claude", "local_llm"]
        self.default_model = "openai"  # Would be configurable

        # Safety and guardrail settings
        self.max_response_length = 4000
        self.max_memory_injection = 20
        self.safety_filters = ["harmful_content", "personal_info", "system_prompts"]

        # Performance tracking
        self.metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "avg_response_time": 0.0,
            "memory_injections": 0,
        }

    async def inject_memory_context(
        self,
        prompt: str,
        memories: List[Dict],
        user_context: Dict,
        max_memories: int = 10,
    ) -> str:
        """
        Inject relevant memories into the AI prompt for context-aware responses.

        Args:
            prompt: Original user prompt
            memories: List of relevant memories
            user_context: User context data
            max_memories: Maximum memories to inject

        Returns:
            Enhanced prompt with memory context
        """
        if not memories:
            return prompt

        # Limit memories to prevent prompt bloat
        limited_memories = memories[: min(max_memories, self.max_memory_injection)]

        # Build memory context section
        memory_context = "\n--- RELEVANT MEMORY CONTEXT ---\n"

        for i, memory in enumerate(limited_memories, 1):
            memory_text = memory.get("content", "")
            memory_timestamp = memory.get("timestamp", "")
            memory_context += f"{i}. {memory_text}"
            if memory_timestamp:
                memory_context += f" (from {memory_timestamp})"
            memory_context += "\n"

        memory_context += "--- END MEMORY CONTEXT ---\n\n"

        # Inject user preferences if available
        user_prefs = user_context.get("preferences", {})
        if user_prefs:
            memory_context += "User Preferences:\n"
            for key, value in user_prefs.items():
                memory_context += f"- {key}: {value}\n"
            memory_context += "\n"

        # Combine with original prompt
        enhanced_prompt = f"{memory_context}User Request: {prompt}"

        self.metrics["memory_injections"] += 1

        logger.info(
            "Memory context injected",
            memories_injected=len(limited_memories),
            original_length=len(prompt),
            enhanced_length=len(enhanced_prompt),
        )

        return enhanced_prompt

    async def generate_response(
        self,
        prompt: str,
        user_id: str,
        context,
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate AI response with safety guardrails and context awareness.

        Args:
            prompt: The prompt to send to AI
            user_id: User identifier for logging and permissions
            context: Execution context
            model: AI model to use (defaults to configured default)
            temperature: Response creativity (0.0-1.0)

        Returns:
            AI-generated response
        """
        start_time = time.time()
        model = model or self.default_model

        try:
            # Check permissions
            if not context.check_permission("can_use_ai"):
                raise PermissionError("User does not have AI usage permissions")

            # Apply safety filters to prompt
            filtered_prompt = await self._apply_safety_filters(prompt)

            # Generate response (mock implementation)
            response = await self._call_ai_model(
                model=model,
                prompt=filtered_prompt,
                temperature=temperature,
                user_id=user_id,
            )

            # Apply safety filters to response
            safe_response = await self._apply_response_filters(response)

            # Update metrics
            response_time = time.time() - start_time
            self._update_metrics(True, response_time)

            # Record in context
            context.add_execution_step(
                "ai_response_generated",
                {
                    "model": model,
                    "prompt_length": len(filtered_prompt),
                    "response_length": len(safe_response),
                    "temperature": temperature,
                    "response_time": response_time,
                },
            )

            context.update_performance_metric("ai_calls")

            logger.info(
                "AI response generated",
                user_id=user_id,
                model=model,
                prompt_length=len(filtered_prompt),
                response_length=len(safe_response),
                response_time=response_time,
            )

            return safe_response

        except Exception as e:
            response_time = time.time() - start_time
            self._update_metrics(False, response_time)

            logger.error(
                "AI response generation failed",
                user_id=user_id,
                model=model,
                error=str(e),
                response_time=response_time,
            )

            # Return a safe fallback response
            return "I apologize, but I'm unable to generate a response at this time. Please try again later."

    async def generate_summary(
        self,
        memories: List[Dict],
        user_prompt: str,
        context,
        summary_type: str = "comprehensive",
    ) -> str:
        """Generate intelligent summary of memories."""
        if not memories:
            return "No memories available to summarize."

        # Build summarization prompt
        summary_prompt = (
            f"Please provide a {summary_type} summary of the following memories:\n\n"
        )

        for i, memory in enumerate(memories[:20], 1):  # Limit to 20 memories
            content = memory.get("content", "")
            timestamp = memory.get("timestamp", "")
            summary_prompt += f"{i}. {content}"
            if timestamp:
                summary_prompt += f" ({timestamp})"
            summary_prompt += "\n"

        summary_prompt += f"\nUser's specific request: {user_prompt}\n"
        summary_prompt += "Please provide a clear, organized summary that addresses the user's request."

        return await self.generate_response(
            prompt=summary_prompt,
            user_id=context.user_id,
            context=context,
            temperature=0.3,  # Lower temperature for more focused summaries
        )

    async def _apply_safety_filters(self, prompt: str) -> str:
        """Apply safety filters to the input prompt."""
        # Mock implementation - in production, this would use actual safety filters
        filtered_prompt = prompt

        # Remove potential system prompt injections
        dangerous_patterns = ["ignore previous instructions", "system:", "assistant:"]
        for pattern in dangerous_patterns:
            if pattern.lower() in filtered_prompt.lower():
                logger.warning("Potential prompt injection detected", pattern=pattern)
                filtered_prompt = filtered_prompt.replace(pattern, "[FILTERED]")

        return filtered_prompt

    async def _apply_response_filters(self, response: str) -> str:
        """Apply safety filters to the AI response."""
        # Mock implementation - in production, this would use actual content filters
        safe_response = response

        # Truncate if too long
        if len(safe_response) > self.max_response_length:
            safe_response = (
                safe_response[: self.max_response_length]
                + "... [Response truncated for safety]"
            )

        return safe_response

    async def _call_ai_model(
        self,
        model: str,
        prompt: str,
        temperature: float,
        user_id: str,
    ) -> str:
        """Call the specified AI model (mock implementation)."""
        # Simulate AI call delay
        await asyncio.sleep(0.5)

        # Mock response based on prompt analysis
        if "summarize" in prompt.lower():
            return "Here is a comprehensive summary of the provided information: [AI-generated summary would appear here]"
        elif "analyze" in prompt.lower():
            return "Based on my analysis: [AI-generated analysis would appear here]"
        elif "generate" in prompt.lower() or "create" in prompt.lower():
            return "Here is the generated content: [AI-generated content would appear here]"
        else:
            return "Based on the provided context and your request: [AI-generated response would appear here]"

    def _update_metrics(self, success: bool, response_time: float):
        """Update AI toolchain metrics."""
        self.metrics["total_calls"] += 1

        if success:
            self.metrics["successful_calls"] += 1
        else:
            self.metrics["failed_calls"] += 1

        # Update average response time
        if self.metrics["total_calls"] > 0:
            total_time = (
                self.metrics["avg_response_time"] * (self.metrics["total_calls"] - 1)
                + response_time
            )
            self.metrics["avg_response_time"] = total_time / self.metrics["total_calls"]

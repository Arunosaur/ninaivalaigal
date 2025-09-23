"""
Intention Router for SPEC-063 Agentic Core
Detects execution intent and routes to appropriate micro-agent chains
"""

import re
from typing import Any, Dict, List, Optional

import structlog

from .execution_modes import ExecutionMode

logger = structlog.get_logger(__name__)


class IntentionRouter:
    """
    Intelligent intent detection and routing system.

    Analyzes user prompts to determine the most appropriate execution mode
    and routing strategy for optimal results.
    """

    def __init__(self):
        # Intent patterns for different execution modes
        self.intent_patterns = {
            ExecutionMode.SEARCH: [
                r"\b(find|search|look\s+for|locate|discover)\b",
                r"\b(what|where|when|who)\b.*\?",
                r"\bshow\s+me\b",
                r"\blist\b.*\b(all|everything)\b",
            ],
            ExecutionMode.SUMMARIZATION: [
                r"\b(summarize|summary|overview|recap)\b",
                r"\btell\s+me\s+about\b",
                r"\bwhat\s+is\b.*\babout\b",
                r"\bgive\s+me\s+a\s+(summary|overview)\b",
                r"\bexplain\s+briefly\b",
            ],
            ExecutionMode.ANALYTICS: [
                r"\b(analyze|analysis|insights|trends|patterns)\b",
                r"\b(statistics|stats|metrics|data)\b",
                r"\bhow\s+(many|much|often)\b",
                r"\b(compare|comparison|versus|vs)\b",
                r"\b(performance|efficiency|effectiveness)\b",
            ],
            ExecutionMode.GENERATION: [
                r"\b(create|generate|write|compose|draft)\b",
                r"\bmake\s+me\s+a\b",
                r"\bhelp\s+me\s+(write|create)\b",
                r"\bgenerate\s+a\b",
                r"\bcome\s+up\s+with\b",
            ],
            ExecutionMode.MEMORY_ANALYSIS: [
                r"\bmemory\s+(analysis|network|connections)\b",
                r"\bhow\s+are.*\bconnected\b",
                r"\brelationships?\s+between\b",
                r"\bmemory\s+(patterns|structure)\b",
                r"\banalyze\s+my\s+memories\b",
            ],
            ExecutionMode.GRAPH_REASONING: [
                r"\b(reasoning|logic|inference|deduce)\b",
                r"\bwhy\s+(did|would|should)\b",
                r"\bexplain\s+the\s+(connection|relationship)\b",
                r"\bhow\s+does.*\brelate\s+to\b",
                r"\bwhat\s+led\s+to\b",
                r"\bgraph\s+(reasoning|analysis)\b",
            ],
            ExecutionMode.INFERENCE: [
                # Default fallback patterns
                r"\bwhat\s+do\s+you\s+think\b",
                r"\bhelp\s+me\s+(understand|figure\s+out)\b",
                r"\bcan\s+you\b",
                r"\bplease\b",
            ],
        }

        # Context clues for mode selection
        self.context_clues = {
            "data_keywords": ["data", "dataset", "table", "csv", "json", "database"],
            "memory_keywords": ["memory", "remember", "recall", "past", "history"],
            "analysis_keywords": [
                "analyze",
                "insights",
                "trends",
                "patterns",
                "statistics",
            ],
            "creative_keywords": ["create", "generate", "write", "compose", "design"],
            "search_keywords": ["find", "search", "locate", "discover", "show"],
        }

        # Mode priorities (higher = more specific, lower = more general)
        self.mode_priorities = {
            ExecutionMode.GRAPH_REASONING: 10,
            ExecutionMode.MEMORY_ANALYSIS: 9,
            ExecutionMode.ANALYTICS: 8,
            ExecutionMode.GENERATION: 7,
            ExecutionMode.SUMMARIZATION: 6,
            ExecutionMode.SEARCH: 5,
            ExecutionMode.INFERENCE: 1,  # Default fallback
        }

    async def route_intent(
        self,
        user_prompt: str,
        execution_context=None,
    ) -> ExecutionMode:
        """
        Analyze user prompt and determine the most appropriate execution mode.

        Args:
            user_prompt: The user's input text
            execution_context: Optional execution context for additional clues

        Returns:
            ExecutionMode enum indicating the best routing choice
        """
        prompt_lower = user_prompt.lower()

        # Score each mode based on pattern matching
        mode_scores = {}

        for mode, patterns in self.intent_patterns.items():
            score = 0

            # Check pattern matches
            for pattern in patterns:
                matches = len(re.findall(pattern, prompt_lower, re.IGNORECASE))
                score += matches * 2  # Base score for pattern match

            # Apply priority weighting
            score *= self.mode_priorities.get(mode, 1)

            mode_scores[mode] = score

        # Add context-based scoring
        if execution_context:
            context_scores = self._analyze_context_clues(
                prompt_lower, execution_context
            )
            for mode, context_score in context_scores.items():
                mode_scores[mode] = mode_scores.get(mode, 0) + context_score

        # Add semantic analysis scoring
        semantic_scores = self._semantic_analysis(prompt_lower)
        for mode, semantic_score in semantic_scores.items():
            mode_scores[mode] = mode_scores.get(mode, 0) + semantic_score

        # Select the highest scoring mode
        if not mode_scores or all(score == 0 for score in mode_scores.values()):
            selected_mode = ExecutionMode.INFERENCE  # Default fallback
        else:
            selected_mode = max(mode_scores.items(), key=lambda x: x[1])[0]

        logger.info(
            "Intent routing completed",
            selected_mode=selected_mode.value,
            mode_scores={mode.value: score for mode, score in mode_scores.items()},
            prompt_length=len(user_prompt),
        )

        return selected_mode

    def _analyze_context_clues(
        self,
        prompt_lower: str,
        execution_context,
    ) -> Dict[ExecutionMode, float]:
        """Analyze context clues to boost certain mode scores."""
        context_scores = {}

        # Check for data-related context
        if any(
            keyword in prompt_lower for keyword in self.context_clues["data_keywords"]
        ):
            context_scores[ExecutionMode.ANALYTICS] = 3
            context_scores[ExecutionMode.SEARCH] = 2

        # Check for memory-related context
        if any(
            keyword in prompt_lower for keyword in self.context_clues["memory_keywords"]
        ):
            context_scores[ExecutionMode.MEMORY_ANALYSIS] = 4
            context_scores[ExecutionMode.GRAPH_REASONING] = 3
            context_scores[ExecutionMode.SEARCH] = 2

        # Check for analysis context
        if any(
            keyword in prompt_lower
            for keyword in self.context_clues["analysis_keywords"]
        ):
            context_scores[ExecutionMode.ANALYTICS] = 4
            context_scores[ExecutionMode.MEMORY_ANALYSIS] = 2

        # Check for creative context
        if any(
            keyword in prompt_lower
            for keyword in self.context_clues["creative_keywords"]
        ):
            context_scores[ExecutionMode.GENERATION] = 4
            context_scores[ExecutionMode.INFERENCE] = 2

        # Check for search context
        if any(
            keyword in prompt_lower for keyword in self.context_clues["search_keywords"]
        ):
            context_scores[ExecutionMode.SEARCH] = 4
            context_scores[ExecutionMode.MEMORY_ANALYSIS] = 2

        # Context data analysis
        if execution_context and hasattr(execution_context, "context_data"):
            context_data = execution_context.context_data

            # If specific memory or context IDs are provided, boost graph reasoning
            if context_data.get("memory_id") or context_data.get("context_id"):
                context_scores[ExecutionMode.GRAPH_REASONING] = (
                    context_scores.get(ExecutionMode.GRAPH_REASONING, 0) + 5
                )

            # If analysis type is specified, boost analytics
            if context_data.get("analysis_type"):
                context_scores[ExecutionMode.ANALYTICS] = (
                    context_scores.get(ExecutionMode.ANALYTICS, 0) + 5
                )

            # If generation type is specified, boost generation
            if context_data.get("generation_type"):
                context_scores[ExecutionMode.GENERATION] = (
                    context_scores.get(ExecutionMode.GENERATION, 0) + 5
                )

        return context_scores

    def _semantic_analysis(self, prompt_lower: str) -> Dict[ExecutionMode, float]:
        """Perform semantic analysis for more nuanced intent detection."""
        semantic_scores = {}

        # Question vs statement analysis
        if "?" in prompt_lower:
            if any(
                word in prompt_lower
                for word in ["what", "how", "why", "when", "where", "who"]
            ):
                if "why" in prompt_lower or "how" in prompt_lower:
                    semantic_scores[ExecutionMode.GRAPH_REASONING] = 2
                    semantic_scores[ExecutionMode.INFERENCE] = 2
                else:
                    semantic_scores[ExecutionMode.SEARCH] = 2
                    semantic_scores[ExecutionMode.INFERENCE] = 1

        # Imperative vs interrogative
        imperative_verbs = [
            "create",
            "generate",
            "make",
            "write",
            "find",
            "show",
            "analyze",
            "summarize",
        ]
        if any(prompt_lower.startswith(verb) for verb in imperative_verbs):
            if prompt_lower.startswith(("create", "generate", "make", "write")):
                semantic_scores[ExecutionMode.GENERATION] = 3
            elif prompt_lower.startswith(("find", "show")):
                semantic_scores[ExecutionMode.SEARCH] = 3
            elif prompt_lower.startswith("analyze"):
                semantic_scores[ExecutionMode.ANALYTICS] = 3
            elif prompt_lower.startswith("summarize"):
                semantic_scores[ExecutionMode.SUMMARIZATION] = 3

        # Length-based heuristics
        word_count = len(prompt_lower.split())
        if word_count > 20:
            # Longer prompts often need summarization or complex reasoning
            semantic_scores[ExecutionMode.SUMMARIZATION] = 1
            semantic_scores[ExecutionMode.GRAPH_REASONING] = 1
        elif word_count < 5:
            # Short prompts often need search or simple inference
            semantic_scores[ExecutionMode.SEARCH] = 1
            semantic_scores[ExecutionMode.INFERENCE] = 1

        # Complexity indicators
        complex_indicators = [
            "relationship",
            "connection",
            "because",
            "therefore",
            "however",
            "although",
        ]
        if any(indicator in prompt_lower for indicator in complex_indicators):
            semantic_scores[ExecutionMode.GRAPH_REASONING] = 2
            semantic_scores[ExecutionMode.ANALYTICS] = 1

        return semantic_scores

    def get_routing_explanation(
        self,
        user_prompt: str,
        selected_mode: ExecutionMode,
        execution_context=None,
    ) -> Dict[str, Any]:
        """
        Provide explanation for why a particular mode was selected.
        Useful for debugging and user transparency.
        """
        prompt_lower = user_prompt.lower()

        # Re-run analysis to get scores
        mode_scores = {}
        matched_patterns = {}

        for mode, patterns in self.intent_patterns.items():
            score = 0
            matches = []

            for pattern in patterns:
                pattern_matches = re.findall(pattern, prompt_lower, re.IGNORECASE)
                if pattern_matches:
                    matches.extend(pattern_matches)
                    score += len(pattern_matches) * 2

            score *= self.mode_priorities.get(mode, 1)
            mode_scores[mode] = score
            if matches:
                matched_patterns[mode] = matches

        return {
            "selected_mode": selected_mode.value,
            "mode_scores": {mode.value: score for mode, score in mode_scores.items()},
            "matched_patterns": {
                mode.value: patterns for mode, patterns in matched_patterns.items()
            },
            "prompt_analysis": {
                "length": len(user_prompt),
                "word_count": len(user_prompt.split()),
                "has_question": "?" in user_prompt,
                "complexity_indicators": [
                    indicator
                    for indicator in [
                        "relationship",
                        "connection",
                        "because",
                        "therefore",
                    ]
                    if indicator in prompt_lower
                ],
            },
        }

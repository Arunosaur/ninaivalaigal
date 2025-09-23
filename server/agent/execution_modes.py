"""
Execution modes for the agentic core system.
Separated to avoid circular imports.
"""

from enum import Enum


class ExecutionMode(Enum):
    """Available execution modes for the agentic core."""

    INFERENCE = "inference"
    SEARCH = "search"
    SUMMARIZATION = "summarization"
    ANALYTICS = "analytics"
    GENERATION = "generation"
    MEMORY_ANALYSIS = "memory_analysis"
    GRAPH_REASONING = "graph_reasoning"

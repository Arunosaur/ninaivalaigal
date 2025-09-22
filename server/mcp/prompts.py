"""
MCP Prompts for ninaivalaigal
Extracted from monolithic mcp_server.py for better organization

This addresses external code review feedback:
- Break down monolithic files (mcp_server.py 929 lines → focused modules)
- Improve code organization and maintainability
"""

import json

from .server import get_initialized_components, mcp

# Try to import MCP types, fallback if not available
try:
    from mcp.types import Prompt
except ImportError:

    class Prompt:
        def __init__(self, name, description, messages):
            self.name = name
            self.description = description
            self.messages = messages


# Get initialized components
components = get_initialized_components()
db = components["db"]
DEFAULT_USER_ID = components["DEFAULT_USER_ID"]


@mcp.prompt()
async def analyze_context(context_name: str) -> Prompt:
    """Generate a prompt to analyze memories in a context"""
    try:
        memories = db.get_memories(context_name, user_id=DEFAULT_USER_ID)

        if not memories:
            return Prompt(
                name=f"analyze-context-{context_name}",
                description=f"Analysis prompt for empty context '{context_name}'",
                messages=[
                    {
                        "role": "user",
                        "content": f"The context '{context_name}' is empty. No memories to analyze.",
                    }
                ],
            )

        # Prepare memory data for analysis
        memory_texts = []
        for memory in memories:
            if isinstance(memory.get("data"), dict):
                text = memory["data"].get("text", "")
            else:
                text = str(memory.get("data", ""))

            if text:
                memory_texts.append(
                    {
                        "text": text,
                        "type": memory.get("type", "unknown"),
                        "source": memory.get("source", "unknown"),
                        "created_at": memory.get("created_at", "unknown"),
                    }
                )

        analysis_prompt = f"""Please analyze the memories in the context '{context_name}'.

Context: {context_name}
Total memories: {len(memories)}
User ID: {DEFAULT_USER_ID}

Memories to analyze:
{json.dumps(memory_texts, indent=2)}

Please provide:
1. Summary of key themes and topics
2. Chronological patterns or trends
3. Memory types and sources breakdown
4. Potential relationships between memories
5. Suggestions for organization or next actions
6. Any gaps or missing information you notice

Focus on actionable insights that would help the user better understand and utilize this context."""

        return Prompt(
            name=f"analyze-context-{context_name}",
            description=f"Analysis prompt for context '{context_name}' with {len(memories)} memories",
            messages=[{"role": "user", "content": analysis_prompt}],
        )

    except Exception as e:
        return Prompt(
            name=f"analyze-context-{context_name}-error",
            description=f"Error analyzing context '{context_name}'",
            messages=[
                {
                    "role": "user",
                    "content": f"Error analyzing context '{context_name}': {str(e)}",
                }
            ],
        )


@mcp.prompt()
async def summarize_session() -> Prompt:
    """Generate a prompt to summarize current session memories"""
    try:
        # Get recent memories across all contexts for session summary
        recent_memories = db.get_recent_memories(limit=20, user_id=DEFAULT_USER_ID)

        if not recent_memories:
            return Prompt(
                name="summarize-session-empty",
                description="Session summary for user with no recent memories",
                messages=[
                    {
                        "role": "user",
                        "content": f"No recent memories found for user {DEFAULT_USER_ID}. Session appears to be just starting or no activity has been recorded.",
                    }
                ],
            )

        # Group memories by context
        context_groups = {}
        for memory in recent_memories:
            context = memory.get("context", "unknown")
            if context not in context_groups:
                context_groups[context] = []
            context_groups[context].append(memory)

        # Prepare session data
        session_data = {
            "user_id": DEFAULT_USER_ID,
            "total_recent_memories": len(recent_memories),
            "active_contexts": len(context_groups),
            "context_breakdown": {
                context: len(memories) for context, memories in context_groups.items()
            },
            "memories_by_context": context_groups,
        }

        summary_prompt = f"""Please provide a comprehensive session summary based on recent memory activity.

Session Data:
{json.dumps(session_data, indent=2, default=str)}

Please provide:
1. **Session Overview**: What has the user been working on?
2. **Context Analysis**: Which contexts are most active and what do they contain?
3. **Activity Patterns**: What types of activities or topics are prominent?
4. **Key Insights**: What are the main themes or focuses of this session?
5. **Recommendations**: What should the user focus on next or what actions might be helpful?
6. **Context Connections**: Are there relationships between different contexts that suggest broader projects or themes?

Focus on providing actionable insights that help the user understand their recent activity and plan next steps effectively."""

        return Prompt(
            name="summarize-session",
            description=f"Session summary with {len(recent_memories)} recent memories across {len(context_groups)} contexts",
            messages=[{"role": "user", "content": summary_prompt}],
        )

    except Exception as e:
        return Prompt(
            name="summarize-session-error",
            description="Error generating session summary",
            messages=[
                {
                    "role": "user",
                    "content": f"Error generating session summary: {str(e)}",
                }
            ],
        )


@mcp.prompt()
async def enhance_memory_context(context_name: str, new_memory_text: str) -> Prompt:
    """Generate a prompt to enhance a new memory with existing context"""
    try:
        existing_memories = db.get_memories(context_name, user_id=DEFAULT_USER_ID)

        # Prepare context for enhancement
        context_summary = []
        if existing_memories:
            for memory in existing_memories[-5:]:  # Last 5 memories for context
                if isinstance(memory.get("data"), dict):
                    text = memory["data"].get("text", "")
                else:
                    text = str(memory.get("data", ""))

                if text:
                    context_summary.append(
                        {
                            "text": text[:200] + "..." if len(text) > 200 else text,
                            "type": memory.get("type", "unknown"),
                            "created_at": memory.get("created_at", "unknown"),
                        }
                    )

        enhancement_prompt = f"""Please help enhance and contextualize a new memory entry.

Context: {context_name}
New Memory Text: {new_memory_text}

Existing Context (last 5 memories):
{json.dumps(context_summary, indent=2) if context_summary else "No existing memories in this context"}

Please provide:
1. **Enhanced Memory**: An improved version of the new memory that includes relevant context and connections
2. **Relationships**: How this memory relates to existing memories in the context
3. **Tags/Categories**: Suggested tags or categories for better organization
4. **Follow-up Questions**: Questions that might help capture additional relevant information
5. **Context Insights**: How this memory fits into the broader context theme
6. **Suggested Actions**: Any actions or next steps this memory might suggest

Focus on making the memory more useful and connected to the existing knowledge in this context."""

        return Prompt(
            name=f"enhance-memory-{context_name}",
            description=f"Memory enhancement prompt for context '{context_name}'",
            messages=[{"role": "user", "content": enhancement_prompt}],
        )

    except Exception as e:
        return Prompt(
            name=f"enhance-memory-{context_name}-error",
            description=f"Error enhancing memory for context '{context_name}'",
            messages=[
                {
                    "role": "user",
                    "content": f"Error enhancing memory for context '{context_name}': {str(e)}",
                }
            ],
        )


@mcp.prompt()
async def cross_context_insights() -> Prompt:
    """Generate a prompt to find insights across multiple contexts"""
    try:
        # Get all contexts for the user
        all_contexts = db.get_all_contexts(user_id=DEFAULT_USER_ID)

        if not all_contexts:
            return Prompt(
                name="cross-context-insights-empty",
                description="Cross-context analysis with no contexts",
                messages=[
                    {
                        "role": "user",
                        "content": f"No contexts found for user {DEFAULT_USER_ID}. Cannot perform cross-context analysis.",
                    }
                ],
            )

        # Sample memories from each context
        context_samples = {}
        for context_info in all_contexts:
            context_name = context_info.get("name")
            if context_name:
                memories = db.get_memories(context_name, user_id=DEFAULT_USER_ID)
                if memories:
                    # Take first and last memory as sample
                    samples = []
                    if len(memories) >= 1:
                        samples.append(memories[0])
                    if len(memories) >= 2:
                        samples.append(memories[-1])

                    context_samples[context_name] = {
                        "total_memories": len(memories),
                        "sample_memories": samples,
                        "context_info": context_info,
                    }

        insights_prompt = f"""Please analyze patterns and insights across multiple contexts for comprehensive understanding.

User ID: {DEFAULT_USER_ID}
Total Contexts: {len(all_contexts)}
Contexts with Memories: {len(context_samples)}

Context Data:
{json.dumps(context_samples, indent=2, default=str)}

Please provide:
1. **Cross-Context Themes**: What common themes or topics appear across different contexts?
2. **Workflow Patterns**: What workflows or processes can you identify from the context relationships?
3. **Knowledge Gaps**: What areas might benefit from additional context or memory capture?
4. **Context Relationships**: How do the different contexts relate to each other?
5. **Optimization Suggestions**: How could the context organization be improved?
6. **Strategic Insights**: What strategic insights emerge from this cross-context view?
7. **Action Items**: What specific actions would help improve knowledge management across contexts?

Focus on providing high-level insights that help optimize the overall knowledge management strategy."""

        return Prompt(
            name="cross-context-insights",
            description=f"Cross-context analysis across {len(context_samples)} active contexts",
            messages=[{"role": "user", "content": insights_prompt}],
        )

    except Exception as e:
        return Prompt(
            name="cross-context-insights-error",
            description="Error generating cross-context insights",
            messages=[
                {
                    "role": "user",
                    "content": f"Error generating cross-context insights: {str(e)}",
                }
            ],
        )

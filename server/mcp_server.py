#!/opt/homebrew/anaconda3/bin/python
"""
mem0 MCP Server - Model Context Protocol implementation
Provides memory management capabilities as MCP tools, resources, and prompts
"""

import asyncio
import json
from typing import Any, Optional, List, Dict
from mcp.server.fastmcp import FastMCP
from mcp.types import Resource, TextResourceContents, Tool, Prompt
from datetime import datetime

# Import existing mem0 components
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from auth import load_config

# Initialize MCP server
mcp = FastMCP("mem0")

# Initialize database and config
database_url = load_config()
db = DatabaseManager(database_url)

@mcp.tool()
async def remember(text: str, context: str = None) -> str:
    """Store a memory in the specified context
    
    Args:
        text: The text content to remember
        context: Context name to store the memory in (optional)
    
    Returns:
        Confirmation message
    """
    try:
        # Parse JSON if text looks like structured data
        try:
            data = json.loads(text)
            memory_type = data.get("type", "note")
            source = data.get("source", "mcp")
            memory_data = data.get("data", {"text": text})
        except (json.JSONDecodeError, TypeError):
            # Plain text memory
            memory_type = "note"
            source = "mcp"
            memory_data = {"text": text}
        
        # Use default context if none provided
        if not context:
            context = "default"
            
        try:
            db.add_memory(context, "note", "mcp", {"text": text, "timestamp": str(datetime.now()), "context": context})
            return f"Memory stored successfully in context: {context}"
        except Exception as e:
            return f"Error storing memory: {e}"
        
    except Exception as e:
        return f"Error storing memory: {str(e)}"

@mcp.tool()
async def recall(context: str = None, query: str = None) -> List[Dict[str, Any]]:
    """Retrieve memories from context, optionally filtered by query
    
    Args:
        context: Context name to retrieve from (optional, returns all if not specified)
        query: Text query to filter memories (optional)
    
    Returns:
        List of matching memories
    """
    try:
        if context:
            # Get memories from specific context
            memories = db.get_memories(context)
        else:
            # Get all memories across contexts
            memories = db.get_all_memories()
        
        # Apply text filtering if query provided
        if query and memories:
            filtered_memories = []
            query_lower = query.lower()
            for memory in memories:
                # Search in memory text content
                memory_text = ""
                if isinstance(memory.get("data"), dict):
                    memory_text = memory["data"].get("text", "")
                elif isinstance(memory.get("data"), str):
                    memory_text = memory["data"]
                
                if query_lower in memory_text.lower():
                    filtered_memories.append(memory)
            memories = filtered_memories
        
        return memories
        
    except Exception as e:
        return [{"error": f"Error retrieving memories: {str(e)}"}]

@mcp.tool()
async def context_start(context_name: str) -> str:
    """Start recording to a specific context
    
    Args:
        context_name: Name of the context to start recording to
    
    Returns:
        Confirmation message
    """
    try:
        # Start context recording
        db.start_context(context_name)
        return f"Started recording to context: {context_name}"
        
    except Exception as e:
        return f"Error starting context: {str(e)}"

@mcp.tool()
async def context_stop() -> str:
    """Stop active recording
    
    Returns:
        Confirmation message
    """
    try:
        # Stop context recording
        db.stop_context()
        return "Stopped recording"
        
    except Exception as e:
        return f"Error stopping context: {str(e)}"

@mcp.tool()
async def list_contexts() -> List[str]:
    """List all available contexts
    
    Returns:
        List of context names
    """
    try:
        contexts = db.get_contexts()
        return contexts
        
    except Exception as e:
        return [f"Error listing contexts: {str(e)}"]

@mcp.resource("mem0://contexts")
async def list_all_contexts() -> Resource:
    """Provide list of all contexts as a resource"""
    try:
        contexts = db.get_contexts()
        content = "\n".join(f"- {context}" for context in contexts)
        
        return Resource(
            uri="mem0://contexts",
            name="Available Contexts",
            description="List of all available memory contexts",
            mimeType="text/plain"
        )
    except Exception as e:
        return Resource(
            uri="mem0://contexts",
            name="Context List Error",
            description=f"Error retrieving contexts: {str(e)}",
            mimeType="text/plain"
        )

@mcp.resource("mem0://context/{context_name}")
async def get_context_memories(context_name: str) -> Resource:
    """Provide all memories for a specific context"""
    try:
        memories = db.get_memories(context_name)
        content = json.dumps(memories, indent=2)
        
        return Resource(
            uri=f"mem0://context/{context_name}",
            name=f"Context: {context_name}",
            description=f"All memories from context '{context_name}'",
            mimeType="application/json"
        )
    except Exception as e:
        return Resource(
            uri=f"mem0://context/{context_name}",
            name=f"Context Error: {context_name}",
            description=f"Error retrieving context: {str(e)}",
            mimeType="text/plain"
        )

@mcp.resource("mem0://recent")
async def get_recent_memories() -> Resource:
    """Provide recently added memories across all contexts"""
    try:
        memories = db.get_recent_memories(limit=50)
        content = json.dumps(memories, indent=2)
        
        return Resource(
            uri="mem0://recent",
            name="Recent Memories",
            description="Recently added memories across all contexts",
            mimeType="application/json"
        )
    except Exception as e:
        return Resource(
            uri="mem0://recent",
            name="Recent Memories Error", 
            description=f"Error retrieving recent memories: {str(e)}",
            mimeType="text/plain"
        )

@mcp.prompt()
async def analyze_context(context_name: str) -> Prompt:
    """Generate a prompt to analyze memories in a context"""
    try:
        memories = db.get_memories(context_name)
        memory_count = len(memories)
        
        prompt_text = f"""Analyze the memories in context '{context_name}':

Context: {context_name}
Total memories: {memory_count}

Please analyze these memories and provide insights about:
1. Common themes and patterns
2. Key activities and events
3. Important decisions or outcomes
4. Potential next steps or recommendations

Recent memories from this context:
{json.dumps(memories[:10], indent=2)}
"""
        
        return Prompt(
            name=f"analyze-context-{context_name}",
            description=f"Analyze memories in context '{context_name}'",
            arguments=[
                {"name": "context_name", "description": "Context to analyze", "required": True}
            ]
        )
    except Exception as e:
        return Prompt(
            name="analyze-context-error",
            description=f"Error creating analysis prompt: {str(e)}",
            arguments=[]
        )

@mcp.prompt()
async def summarize_session() -> Prompt:
    """Generate a prompt to summarize current session memories"""
    try:
        recent_memories = db.get_recent_memories(limit=20)
        
        prompt_text = f"""Summarize the current development session:

Recent activity ({len(recent_memories)} memories):

Please provide a summary including:
1. What was accomplished
2. Key decisions made
3. Current state and context
4. Next steps or outstanding items

Recent memories:
{json.dumps(recent_memories, indent=2)}
"""
        
        return Prompt(
            name="summarize-session",
            description="Summarize current development session",
            arguments=[]
        )
    except Exception as e:
        return Prompt(
            name="summarize-session-error",
            description=f"Error creating summary prompt: {str(e)}",
            arguments=[]
        )

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()

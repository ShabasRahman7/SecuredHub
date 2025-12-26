"""
Base classes and registry for AI Agent tools.

Tools are functions the agent can call to interact with external systems.
"""

from typing import Callable, Any, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Definition of a tool the agent can use."""
    
    name: str
    description: str
    parameters: dict  # JSON Schema for function parameters
    function: Callable
    is_async: bool = True


class ToolRegistry:
    """
    Registry of available tools.
    
    Tools are functions the AI agent can call to fetch data
    or perform actions.
    """
    
    _tools: dict[str, ToolDefinition] = {}
    
    @classmethod
    def register(cls, tool: ToolDefinition) -> None:
        """Register a tool."""
        cls._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    @classmethod
    def get(cls, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name."""
        return cls._tools.get(name)
    
    @classmethod
    def list_tools(cls) -> list[str]:
        """List all tool names."""
        return list(cls._tools.keys())
    
    @classmethod
    def get_function_declarations(cls) -> list[dict]:
        """
        Get tool declarations in format expected by Gemini.
        
        Returns list of function declarations for Gemini's tools parameter.
        """
        declarations = []
        for name, tool in cls._tools.items():
            declarations.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            })
        return declarations
    
    @classmethod
    async def execute(cls, name: str, **kwargs) -> Any:
        """
        Execute a tool by name.
        
        Args:
            name: Tool name
            **kwargs: Arguments to pass to the tool
            
        Returns:
            Tool result
        """
        tool = cls.get(name)
        if tool is None:
            raise ValueError(f"Unknown tool: {name}")
        
        logger.info(f"Executing tool: {name} with args: {kwargs}")
        
        if tool.is_async:
            result = await tool.function(**kwargs)
        else:
            result = tool.function(**kwargs)
        
        logger.info(f"Tool {name} returned: {type(result).__name__}")
        return result


# Tool result models
class ToolResult(BaseModel):
    """Standard tool result wrapper."""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


def tool(name: str, description: str, parameters: dict, is_async: bool = True):
    """
    Decorator to register a function as a tool.
    
    Usage:
        @tool(
            name="get_evaluation",
            description="Fetch evaluation details",
            parameters={...}
        )
        async def get_evaluation(evaluation_id: int):
            ...
    """
    def decorator(func: Callable) -> Callable:
        ToolRegistry.register(
            ToolDefinition(
                name=name,
                description=description,
                parameters=parameters,
                function=func,
                is_async=is_async,
            )
        )
        return func
    return decorator

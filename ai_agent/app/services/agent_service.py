"""
Agent Service with multi-provider support and proper tool calling.

Supports both Groq (free) and Gemini backends with full ReAct loop.
"""

import json
import logging
from typing import Optional

from app.config import get_settings
from app.models.agent import AgentResponse, ReasoningStep, ToolCall
from app.tools.base import ToolRegistry
import app.tools.evaluation_tools
import app.tools.enhanced_tools  # Register enhanced tools

logger = logging.getLogger(__name__)


AGENT_SYSTEM_PROMPT = """You are a senior compliance engineer AI with deep expertise in SOC2 Type II and ISO-27001.

## Your Role
Analyze compliance evaluations and help developers pass security audits.

## Available Tools

**Data Tools:**
- get_evaluation: Fetch evaluation details (score, grade, pass/fail counts)
- get_failures: Fetch failed rules with evidence (CALL THIS FIRST)
- get_repository: Fetch repository info
- get_score_history: Fetch historical scores for trends

**Compliance Knowledge Tools:**
- search_knowledge: Search SOC2/ISO-27001 control details
- get_framework_mapping: Get framework mappings for a rule

**Analysis & Generation Tools:**
- calculate_impact: Calculate exact score improvement per fix (ALWAYS USE THIS)
- generate_fix: Create ready-to-commit fix files (CODEOWNERS, dependabot.yml, etc.)

## How to Respond

1. ALWAYS call get_failures first to see what's broken
2. ALWAYS call calculate_impact to show exact score improvements
3. When user asks "how to fix X", call generate_fix to provide actual file content
4. Map every issue to SOC2/ISO-27001 controls

## Response Format

Structure your response like this:

📊 **Current Score: X% (Grade: Y)**

🔴 **Fix #1: [Rule Name]** (+X% → Y%)
- SOC2: CC6.1 | ISO: A.9.2.3
- Why it matters: [Business impact]
- How to fix: [Specific steps]

[If user asks for fixes, include generated file content]

🎯 **If all fixed: 100% (Grade: A)**

Be specific, actionable, and always ground recommendations in real data from tools."""


class AgentService:
    """
    AI Agent with full ReAct loop for both Groq and Gemini.
    
    Uses tool calling to fetch real data before generating responses.
    """
    
    def __init__(self):
        settings = get_settings()
        self.provider = settings.llm_provider
        
        if self.provider == "groq":
            self._init_groq()
        else:
            self._init_gemini()
    
    def _init_groq(self):
        """Initialize Groq client."""
        from groq import Groq
        settings = get_settings()
        
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is required. Get free key at https://console.groq.com")
        
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.groq_model
        logger.info(f"Initialized AgentService with Groq model: {self.model}")
    
    def _init_gemini(self):
        """Initialize Gemini client."""
        from google import genai
        settings = get_settings()
        
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required")
        
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model
        logger.info(f"Initialized AgentService with Gemini model: {self.model}")
    
    async def run(
        self,
        goal: str,
        evaluation_id: Optional[int] = None,
        repository_id: Optional[int] = None,
        max_steps: int = 5,
    ) -> AgentResponse:
        """Execute the agent with ReAct loop."""
        logger.info(f"Agent starting with goal: {goal} (provider: {self.provider})")
        
        # Build initial context
        context = f"Goal: {goal}"
        if evaluation_id:
            context += f"\nEvaluation ID: {evaluation_id}"
        if repository_id:
            context += f"\nRepository ID: {repository_id}"
        
        reasoning_steps: list[ReasoningStep] = []
        tool_calls: list[ToolCall] = []
        
        try:
            if self.provider == "groq":
                result = await self._run_groq_with_tools(
                    context, goal, max_steps, reasoning_steps, tool_calls
                )
            else:
                result = await self._run_gemini(
                    context, goal, max_steps, reasoning_steps, tool_calls
                )
            
            if not reasoning_steps:
                reasoning_steps.append(ReasoningStep(
                    step_number=1,
                    thought="Analyzed the goal and generated response",
                    action=None,
                    observation=None,
                ))
            
            return AgentResponse(
                goal=goal,
                result=result,
                reasoning_steps=reasoning_steps,
                tool_calls=tool_calls,
                steps_taken=len(reasoning_steps),
                model_used=self.model,
                success=True,
            )
            
        except Exception as e:
            logger.error(f"Agent error: {e}", exc_info=True)
            reasoning_steps.append(ReasoningStep(
                step_number=len(reasoning_steps) + 1,
                thought=f"Error occurred: {e}",
                action=None,
                observation=str(e),
            ))
            return AgentResponse(
                goal=goal,
                result=f"Analysis incomplete due to errors. Gathered {len(tool_calls)} data points.",
                reasoning_steps=reasoning_steps,
                tool_calls=tool_calls,
                steps_taken=len(reasoning_steps),
                model_used=self.model,
                success=False,
            )
    
    def _get_groq_tools(self) -> list:
        """Convert ToolRegistry tools to Groq format."""
        declarations = ToolRegistry.get_function_declarations()
        if not declarations:
            return []
        
        tools = []
        for decl in declarations:
            tools.append({
                "type": "function",
                "function": {
                    "name": decl["name"],
                    "description": decl["description"],
                    "parameters": decl["parameters"],
                }
            })
        return tools
    
    async def _run_groq_with_tools(
        self,
        initial_context: str,
        goal: str,
        max_steps: int,
        reasoning_steps: list,
        tool_calls: list,
    ) -> str:
        """Run agent with Groq and proper tool calling (ReAct loop)."""
        
        # Get tools in Groq format
        tools = self._get_groq_tools()
        logger.info(f"Groq agent has {len(tools)} tools available")
        
        # Build message history
        messages = [
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": initial_context}
        ]
        
        step = 0
        while step < max_steps:
            step += 1
            logger.info(f"Groq agent step {step}/{max_steps}")
            
            # Call Groq with tools
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto",
                temperature=0.2,
                max_tokens=2000,
            )
            
            assistant_message = response.choices[0].message
            
            # Check if model wants to call tools
            if assistant_message.tool_calls:
                logger.info(f"Model requested {len(assistant_message.tool_calls)} tool calls")
                
                # Add assistant message with tool calls to history
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in assistant_message.tool_calls
                    ]
                })
                
                # Execute each tool call
                for tc in assistant_message.tool_calls:
                    tool_name = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        args = {}
                    
                    logger.info(f"Executing tool: {tool_name} with args: {args}")
                    
                    # Execute the tool
                    try:
                        result = await ToolRegistry.execute(tool_name, **args)
                        result_str = json.dumps(result, default=str)
                        
                        # Truncate if too long
                        if len(result_str) > 2000:
                            result_str = result_str[:2000] + "..."
                            
                    except Exception as e:
                        logger.error(f"Tool {tool_name} error: {e}")
                        result = {"error": str(e)}
                        result_str = json.dumps(result)
                    
                    # Track tool call
                    tool_calls.append(ToolCall(
                        tool_name=tool_name,
                        arguments=args,
                        result=result if isinstance(result, dict) else {"data": result},
                    ))
                    
                    # Add reasoning step
                    reasoning_steps.append(ReasoningStep(
                        step_number=step,
                        thought=f"I need to call {tool_name} to gather data",
                        action=f"{tool_name}({json.dumps(args)})",
                        observation=result_str[:500],
                    ))
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tool_name,
                        "content": result_str,
                    })
            
            else:
                # No tool calls - model generated final response
                final_content = assistant_message.content
                
                reasoning_steps.append(ReasoningStep(
                    step_number=step,
                    thought="I have gathered enough data, generating final response",
                    action=None,
                    observation=None,
                ))
                
                logger.info(f"Groq agent completed in {step} steps with {len(tool_calls)} tool calls")
                return final_content
        
        # Max steps reached - generate summary
        logger.warning(f"Groq agent reached max steps ({max_steps})")
        return f"Analysis completed after {step} steps. Gathered data from {len(tool_calls)} tool calls. Please refine your question for more specific results."
    
    async def _run_gemini(
        self,
        context: str,
        goal: str,
        max_steps: int,
        reasoning_steps: list,
        tool_calls: list,
    ) -> str:
        """Run agent with Gemini (with tool calling)."""
        from google.genai import types
        
        tools = self._get_gemini_tools()
        messages = [context]
        
        step = 0
        while step < max_steps:
            step += 1
            logger.info(f"Gemini agent step {step}/{max_steps}")
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=messages,
                config=types.GenerateContentConfig(
                    system_instruction=AGENT_SYSTEM_PROMPT,
                    temperature=0.2,
                    tools=tools if tools else None,
                ),
            )
            
            function_calls = response.function_calls
            
            if function_calls:
                for fc in function_calls:
                    tool_name = fc.name
                    args = dict(fc.args) if fc.args else {}
                    
                    logger.info(f"Agent calling tool: {tool_name}")
                    
                    try:
                        result = await ToolRegistry.execute(tool_name, **args)
                        result_str = json.dumps(result, default=str)[:500]
                    except Exception as e:
                        result = {"error": str(e)}
                        result_str = str(e)
                    
                    tool_calls.append(ToolCall(
                        tool_name=tool_name,
                        arguments=args,
                        result=result,
                    ))
                    
                    reasoning_steps.append(ReasoningStep(
                        step_number=step,
                        thought=f"I need to call {tool_name}",
                        action=f"{tool_name}({args})",
                        observation=result_str,
                    ))
                    
                    messages.append(
                        types.Part.from_function_response(name=tool_name, response=result)
                    )
            else:
                reasoning_steps.append(ReasoningStep(
                    step_number=step,
                    thought="Generated final response",
                    action=None,
                    observation=None,
                ))
                return response.text
        
        return f"Analysis completed after {step} steps. Gathered {len(tool_calls)} data points."
    
    def _get_gemini_tools(self) -> list:
        """Get tools in Gemini format."""
        from google.genai import types
        
        declarations = ToolRegistry.get_function_declarations()
        if not declarations:
            return []
        
        function_declarations = []
        for decl in declarations:
            function_declarations.append(
                types.FunctionDeclaration(
                    name=decl["name"],
                    description=decl["description"],
                    parameters=decl["parameters"],
                )
            )
        
        return [types.Tool(function_declarations=function_declarations)]

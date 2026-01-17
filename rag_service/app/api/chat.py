from fastapi import APIRouter, HTTPException
from ..models.schemas import (
    ChatInitRequest, ChatInitResponse,
    ChatRequest, ChatResponse
)
from ..knowledge.retrieval import KnowledgeRetriever
from ..llm.groq_client import GroqLLM
from ..llm.prompt_builder import PromptBuilder

router = APIRouter(prefix="/chat", tags=["chat"])

retriever = KnowledgeRetriever()
llm = GroqLLM()
prompt_builder = PromptBuilder()

@router.post("/init", response_model=ChatInitResponse)
async def initialize_chat(request: ChatInitRequest):
    try:
        initial_message = prompt_builder.build_initial_message(request.finding)
        
        return ChatInitResponse(
            message=initial_message,
            finding_id=request.finding_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat init failed: {str(e)}")

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        finding = request.finding or {}
        
        retrieved_context = retriever.retrieve_for_question(
            request.message,
            {
                "file_path": finding.get("file_path", ""),
                "rule_id": finding.get("rule_id", ""),
                "tool": finding.get("tool", "")
            }
        )
        
        messages = prompt_builder.build_chat_messages(
            finding=finding,
            retrieved_context=retrieved_context,
            user_message=request.message,
            conversation_history=request.conversation_history
        )
        
        ai_reply = llm.chat(messages)
        
        return ChatResponse(
            reply=ai_reply,
            finding_id=request.finding_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


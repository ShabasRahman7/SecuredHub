from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.models.schemas import HealthResponse
from app.knowledge.vector_store import VectorStore
from app.core.config import EMBEDDING_MODEL, GROQ_MODEL

app = FastAPI(
    title="SecuredHub RAG Service",
    description="AI-powered security fix suggestions using RAG",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    vector_store = VectorStore()
    kb_count = vector_store.count()
    
    return HealthResponse(
        status="healthy",
        knowledge_base_count=kb_count,
        embedding_model=EMBEDDING_MODEL,
        llm_model=GROQ_MODEL
    )

@app.get("/")
async def root():
    return {
        "service": "SecuredHub RAG Service",
        "version": "2.0.0",
        "docs": "/docs"
    }

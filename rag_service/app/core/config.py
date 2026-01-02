"""Configuration and settings for RAG service"""
import os
from pathlib import Path

# paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CHROMA_DB_DIR = DATA_DIR / "chroma_db"

# lLM Configuration
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_MODEL = "llama-3.3-70b-versatile"

# embedding Model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# chromaDB Configuration
COLLECTION_NAME = "security_knowledge_2025"

# retrieval Configuration
MAX_RESULTS = 5
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

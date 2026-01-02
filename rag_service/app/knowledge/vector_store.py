"""ChromaDB vector store with sentence transformer embeddings."""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
from ..core.config import CHROMA_DB_DIR, COLLECTION_NAME, EMBEDDING_MODEL

class VectorStore:
    
    def __init__(self):
        self.client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)
    
    def add_documents(
        self, 
        texts: List[str], 
        metadatas: List[Dict], 
        ids: List[str]
    ) -> None:
        embeddings = self.embedder.encode(texts, show_progress_bar=True).tolist()
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
            ids=ids
        )
    
    def search(
        self,
        query: str,
        filters: Optional[Dict] = None,
        n_results: int = 5
    ) -> Dict:
        query_embedding = self.embedder.encode([query])[0].tolist()
        
        return self.collection.query(
            query_embeddings=[query_embedding],
            where=filters,
            n_results=n_results
        )
    
    def count(self) -> int:
        return self.collection.count()
    
    def delete_collection(self) -> None:
        self.client.delete_collection(name=COLLECTION_NAME)

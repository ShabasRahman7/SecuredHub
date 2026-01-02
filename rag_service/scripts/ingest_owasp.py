"""
OWASP Top 10:2025 Knowledge Base Ingestion Script
Downloads and processes OWASP Top 10:2025 documentation into ChromaDB
"""
import sys
import os
sys.path.append('/app')

from app.knowledge.vector_store import VectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from app.core.config import CHUNK_SIZE, CHUNK_OVERLAP

# oWASP Top 10:2025 URLs (from official OWASP website)
OWASP_2025_URLS = {
    "A01:2025-Broken_Access_Control": "https://owasp.org/Top10/2025/A01_2025-Broken_Access_Control/",
    "A02:2025-Security_Misconfiguration": "https://owasp.org/Top10/2025/A02_2025-Security_Misconfiguration/",
    "A03:2025-Software_Supply_Chain_Failures": "https://owasp.org/Top10/2025/A03_2025-Software_Supply_Chain_Failures/",
    "A04:2025-Cryptographic_Failures": "https://owasp.org/Top10/2025/A04_2025-Cryptographic_Failures/",
    "A05:2025-Injection": "https://owasp.org/Top10/2025/A05_2025-Injection/",
    "A06:2025-Insecure_Design": "https://owasp.org/Top10/2025/A06_2025-Insecure_Design/",
    "A07:2025-Authentication_Failures": "https://owasp.org/Top10/2025/A07_2025-Authentication_Failures/",
    "A08:2025-Software_or_Data_Integrity_Failures": "https://owasp.org/Top10/2025/A08_2025-Software_or_Data_Integrity_Failures/",
    "A09:2025-Security_Logging_and_Alerting_Failures": "https://owasp.org/Top10/2025/A09_2025-Security_Logging_and_Alerting_Failures/",
    "A10:2025-Mishandling_of_Exceptional_Conditions": "https://owasp.org/Top10/2025/A10_2025-Mishandling_of_Exceptional_Conditions/",
}

def ingest_owasp_2025():
    """Download and ingest OWASP Top 10:2025"""
    print("[STARTING] OWASP Top 10:2025 ingestion...")
    
    vector_store = VectorStore()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    all_texts = []
    all_metadatas = []
    all_ids = []
    chunk_counter = 0
    
    for category, url in OWASP_2025_URLS.items():
        print(f"  [PROCESSING] {category}...")
        try:
            loader = WebBaseLoader(url)
            docs = loader.load()
            
            for doc in docs:
                # splitting into chunks
                chunks = text_splitter.split_text(doc.page_content)
                
                for chunk in chunks:
                    # cleaning and validate chunk
                    chunk = chunk.strip()
                    if len(chunk) < 50:  # skipping very short chunks
                        continue
                    
                    all_texts.append(chunk)
                    all_metadatas.append({
                        "source": "OWASP",
                        "version": "2025",
                        "category": category,
                        "year": 2025,
                        "url": url
                    })
                    all_ids.append(f"owasp2025_{category}_{chunk_counter}")
                    chunk_counter += 1
            
            print(f"    [LOADED] {category}: {len(chunks)} chunks")
        except Exception as e:
            print(f"    [ERROR] Failed to load {category}: {e}")
    
    # adding all documents to vector store
    if all_texts:
        print(f"\n[STORING] Adding {len(all_texts)} chunks to ChromaDB...")
        vector_store.add_documents(all_texts, all_metadatas, all_ids)
        print(f"[SUCCESS] Ingestion complete! Total chunks in DB: {vector_store.count()}")
    else:
        print("[WARNING] No documents to ingest")

if __name__ == "__main__":
    ingest_owasp_2025()

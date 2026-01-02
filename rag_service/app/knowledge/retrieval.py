"""Retrieval logic with hybrid search"""
from typing import Dict, List, Optional
from .vector_store import VectorStore
from ..core.config import MAX_RESULTS

class KnowledgeRetriever:
    
    def __init__(self):
        self.vector_store = VectorStore()
    
    def retrieve_for_finding(self, finding: Dict) -> str:
        # retrieving relevant knowledge for a specific finding
        # building query from finding
        query = f"{finding['title']} {finding. get('description', '')} {finding['rule_id']}"
        
        # detect framework from file path
        framework = self._detect_framework(finding.get('file_path', ''))
        
        # building metadata filters
        filters = self._build_filters(finding['rule_id'], framework)
        
        # retrieving relevant chunks
        results = self.vector_store.search(
            query=query,
            filters=filters,
            n_results=MAX_RESULTS
        )
        
        return self._format_context(results)
    
    def retrieve_for_question(self, question: str, finding: Dict) -> str:
        # retrieving relevant knowledge for a user question
        framework = self._detect_framework(finding.get('file_path', ''))
        
        # broader search for questions
        filters = {"$or": [
            {"source": "OWASP"},
            {"source": "CWE"},
            {"framework": framework}
        ]}
        
        results = self.vector_store.search(
            query=question,
            filters=filters,
            n_results=MAX_RESULTS
        )
        
        return self._format_context(results)
    
    def _detect_framework(self, file_path: str) -> str:
        file_path_lower = file_path.lower()
        
        if "django" in file_path_lower or "manage.py" in file_path_lower:
            return "django"
        elif "flask" in file_path_lower:
            return "flask"
        elif ".py" in file_path_lower:
            return "python"
        
        return "general"
    
    def _build_filters(self, rule_id: str, framework: str) -> Optional[Dict]:
        # prioritize exact rule matches, then framework, then general
        return {"$or": [
            {"rule_id": rule_id},
            {"framework": framework},
            {"source": "OWASP"},
            {"source": "CWE"}
        ]}
    
    def _format_context(self, results: Dict) -> str:
        if not results['documents'] or not results['documents'][0]:
            return "No relevant documentation found in knowledge base."
        
        context_parts = []
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        
        for doc, metadata in zip(documents, metadatas):
            source = metadata.get('source', 'Unknown')
            category = metadata.get('category', '')
            
            header = f"[{source}"
            if category:
                header += f" - {category}"
            header += "]"
            
            context_parts.append(f"{header}\n{doc}\n")
        
        return "\n---\n".join(context_parts)

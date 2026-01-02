"""System prompts and context builders for LLM"""
from typing import Dict, List

SYSTEM_PROMPT = """You are an expert security engineer helping developers fix vulnerabilities.

You have access to authoritative security knowledge from:
- OWASP Top 10:2025 (latest security risks)
- CWE Top 25 2024 (common weaknesses)
- Bandit security rules
- Framework-specific best practices (Django, Flask)

When answering:
1. Be precise and actionable
2. Provide code examples when relevant
3. Reference standards (CWE, OWASP) when applicable
4. Explain the security risk clearly
5. Suggest the safest fix, not just the quickest

Use the provided context to ground your answer. If you don't have relevant information, say so."""

class PromptBuilder:
    
    @staticmethod
    def build_initial_message(finding: Dict) -> str:
        # generating first AI message when chat opens
        return f"""I'm analyzing **Finding #{finding['id']}**: {finding['title']}

**Location:** `{finding['file_path']}` (line {finding.get('line_number', 'N/A')})
**Severity:** {finding['severity'].upper()}
**Rule:** {finding['rule_id']}

I've retrieved relevant security knowledge from OWASP 2025, CWE 2024, and framework docs. How can I help you fix this?"""
    
    @staticmethod
    def build_chat_messages(
        finding: Dict,
        retrieved_context: str,
        user_message: str,
        conversation_history: List[Dict]
    ) -> List[Dict[str, str]]:
        # building complete message list for LLM
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"**Finding Context:**\n{finding}"},
            {"role": "system", "content": f"**Retrieved Knowledge:**\n{retrieved_context}"}
        ]
        
        # adding conversation history (user and assistant messages only)
        for msg in conversation_history:
            if msg['role'] in ['user', 'assistant']:
                messages.append(msg)
        
        # adding current user message
        messages.append({"role": "user", "content": user_message})
        
        return messages

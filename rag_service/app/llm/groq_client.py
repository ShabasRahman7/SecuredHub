"""Groq LLM client using SDK 1.0.0"""
from groq import Groq
from typing import List, Dict
from ..core.config import GROQ_API_KEY, GROQ_MODEL

class GroqLLM:
    
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY environment variable not set")
        
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = GROQ_MODEL
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 1024
    ) -> str:
        # generating response using Groq Llama 3.3 70B
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1,
            stream=False
        )
        
        return response.choices[0].message.content

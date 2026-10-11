"""LLM Provider abstraction supporting Groq API and mock/demo generation."""
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.config import get_settings

logger = logging.getLogger("querymind.llm")
settings = get_settings()

class LLMProvider(ABC):
    """Abstract interface for LLM SQL generation."""

    @abstractmethod
    def generate_sql(self, prompt: str) -> Dict[str, Any]:
        """Generates SQL and explanation from prompt context."""
        pass

class GroqLLMProvider(LLMProvider):
    """Production Groq API integration using llama-3.3-70b-versatile."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        self._client = None
        if self.api_key:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
                logger.info(f"Initialized Groq client with model '{self.model}'.")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")

    def is_available(self) -> bool:
        return self._client is not None and bool(self.api_key)

    def generate_sql(self, prompt: str) -> Dict[str, Any]:
        if not self.is_available():
            raise RuntimeError("Groq API provider is not configured or missing API key.")

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are QueryMind AI, an elite PostgreSQL Data Architect. "
                            "You generate strictly read-only, valid PostgreSQL queries and return JSON only."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=800
            )

            raw_content = response.choices[0].message.content
            data = json.loads(raw_content)
            return {
                "sql": data.get("sql", "").strip(),
                "explanation": data.get("explanation", ""),
                "tables_used": data.get("tables_used", []),
                "is_ambiguous": data.get("is_ambiguous", False),
                "clarification_question": data.get("clarification_question"),
                "assumptions": data.get("assumptions", [])
            }
        except Exception as e:
            logger.error(f"Groq API generation error: {e}")
            raise e

def get_llm_provider() -> LLMProvider:
    """Factory function returning configured LLM provider."""
    return GroqLLMProvider()

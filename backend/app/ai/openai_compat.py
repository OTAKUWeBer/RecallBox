import json
import logging
import httpx
from typing import List, Dict, Any, Optional
from app.ai.base import AIProvider
from app.ai.local_heuristic import LocalHeuristicProvider
from app.core.config import settings

logger = logging.getLogger("recallbox.ai.openai")

class OpenAICompatibleProvider(AIProvider):
    """OpenAI compatible provider (supporting OpenAI, Groq, Together, DeepSeek, LocalAI, vLLM)."""
    
    def __init__(self):
        self.fallback = LocalHeuristicProvider()
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL.rstrip('/')
        self.model = settings.OPENAI_MODEL
        self.embed_model = settings.OPENAI_EMBED_MODEL

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def summarize(self, text: str, title: Optional[str] = None) -> str:
        if not self.api_key:
            return await self.fallback.summarize(text, title)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are a concise summarizer for a personal memory system. Provide 2-3 sentences max on what this is and why it's useful."},
                            {"role": "user", "content": f"Title: {title or ''}\n\nContent:\n{text[:4000]}"}
                        ],
                        "temperature": 0.3
                    }
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.warning(f"OpenAI summarize failed: {e}")
        return await self.fallback.summarize(text, title)

    async def extract_topics_and_entities(self, text: str, title: Optional[str] = None) -> Dict[str, List[str]]:
        if not self.api_key:
            return await self.fallback.extract_topics_and_entities(text, title)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "Extract topics, entities, and suggested tags in JSON format: {\"topics\": [...], \"entities\": [...], \"suggested_tags\": [...]}"},
                            {"role": "user", "content": f"Title: {title or ''}\n\n{text[:3000]}"}
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.2
                    }
                )
                if resp.status_code == 200:
                    raw = resp.json()["choices"][0]["message"]["content"]
                    return json.loads(raw)
        except Exception as e:
            logger.warning(f"OpenAI topic extraction failed: {e}")
        return await self.fallback.extract_topics_and_entities(text, title)

    async def extract_possible_actions(self, text: str, user_why: Optional[str] = None) -> List[str]:
        return await self.fallback.extract_possible_actions(text, user_why)

    async def calculate_importance(self, text: str, title: str, user_why: Optional[str] = None) -> float:
        return await self.fallback.calculate_importance(text, title, user_why)

    async def embed(self, text: str) -> List[float]:
        if not self.api_key:
            return await self.fallback.embed(text)
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    f"{self.base_url}/embeddings",
                    headers=self._headers(),
                    json={
                        "model": self.embed_model,
                        "input": text[:2000]
                    }
                )
                if resp.status_code == 200:
                    return resp.json()["data"][0]["embedding"]
        except Exception as e:
            logger.warning(f"OpenAI embeddings failed: {e}")
        return await self.fallback.embed(text)

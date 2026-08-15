import json
import logging
import httpx
from typing import List, Dict, Any, Optional
from app.ai.base import AIProvider
from app.ai.local_heuristic import LocalHeuristicProvider
from app.core.config import settings

logger = logging.getLogger("recallbox.ai.ollama")

class OllamaProvider(AIProvider):
    """Ollama AI provider for local LLMs and embeddings."""
    
    def __init__(self):
        self.fallback = LocalHeuristicProvider()
        self.base_url = settings.OLLAMA_BASE_URL.rstrip('/')
        self.model = settings.OLLAMA_MODEL
        self.embed_model = settings.OLLAMA_EMBED_MODEL

    async def summarize(self, text: str, title: Optional[str] = None) -> str:
        try:
            prompt = f"Summarize the following text concisely in 2-3 sentences. Focus on what this is and why it is useful:\n\nTitle: {title or ''}\n\n{text[:4000]}"
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False}
                )
                if resp.status_code == 200:
                    return resp.json().get("response", "").strip()
        except Exception as e:
            logger.warning(f"Ollama summarize failed, falling back to heuristic: {e}")
        return await self.fallback.summarize(text, title)

    async def extract_topics_and_entities(self, text: str, title: Optional[str] = None) -> Dict[str, List[str]]:
        try:
            prompt = (
                f"Extract key topics, entities, and suggested tags from this text in valid JSON format:\n"
                f"{{\"topics\": [\"...\"], \"entities\": [\"...\"], \"suggested_tags\": [\"...\"]}}\n\n"
                f"Title: {title or ''}\nText: {text[:3000]}"
            )
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False, "format": "json"}
                )
                if resp.status_code == 200:
                    raw = resp.json().get("response", "{}")
                    return json.loads(raw)
        except Exception as e:
            logger.warning(f"Ollama topic extraction failed, using heuristic: {e}")
        return await self.fallback.extract_topics_and_entities(text, title)

    async def extract_possible_actions(self, text: str, user_why: Optional[str] = None) -> List[str]:
        return await self.fallback.extract_possible_actions(text, user_why)

    async def calculate_importance(self, text: str, title: str, user_why: Optional[str] = None) -> float:
        return await self.fallback.calculate_importance(text, title, user_why)

    async def embed(self, text: str) -> List[float]:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.embed_model, "prompt": text[:2000]}
                )
                if resp.status_code == 200:
                    return resp.json().get("embedding", [])
        except Exception as e:
            logger.warning(f"Ollama embeddings failed, using heuristic hash: {e}")
        return await self.fallback.embed(text)

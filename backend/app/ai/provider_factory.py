import logging
from app.ai.base import AIProvider
from app.ai.local_heuristic import LocalHeuristicProvider
from app.ai.ollama import OllamaProvider
from app.ai.openai_compat import OpenAICompatibleProvider
from app.core.config import settings

logger = logging.getLogger("recallbox.ai.factory")

_provider_instance: AIProvider = None

def get_ai_provider() -> AIProvider:
    """Returns configured AI Provider singleton."""
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance
        
    provider_type = settings.AI_PROVIDER.lower()
    
    if provider_type == "ollama":
        _provider_instance = OllamaProvider()
        logger.info(f"Initialized Ollama AI Provider ({settings.OLLAMA_MODEL})")
    elif provider_type == "openai":
        _provider_instance = OpenAICompatibleProvider()
        logger.info(f"Initialized OpenAI Compatible AI Provider ({settings.OPENAI_MODEL})")
    else:
        _provider_instance = LocalHeuristicProvider()
        logger.info("Initialized Local Offline Heuristic AI Provider (zero network/cloud dependencies)")
        
    return _provider_instance

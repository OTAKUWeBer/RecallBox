from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class AIProvider(ABC):
    """Abstract interface for AI Providers in RecallBox."""
    
    @abstractmethod
    async def summarize(self, text: str, title: Optional[str] = None) -> str:
        """Generate a concise summary of the captured text."""
        pass
        
    @abstractmethod
    async def extract_topics_and_entities(self, text: str, title: Optional[str] = None) -> Dict[str, List[str]]:
        """Extract topics, entities, and suggested tags from text."""
        pass
        
    @abstractmethod
    async def extract_possible_actions(self, text: str, user_why: Optional[str] = None) -> List[str]:
        """Detect possible follow-up actions (e.g. 'Try locally', 'Read docs', 'Compare')."""
        pass
        
    @abstractmethod
    async def calculate_importance(self, text: str, title: str, user_why: Optional[str] = None) -> float:
        """Score importance between 0.0 and 1.0 based on information density and explicit intent."""
        pass
        
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate vector embedding for semantic search."""
        pass

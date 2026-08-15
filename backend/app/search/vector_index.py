import json
import math
import logging
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.entities import Memory

logger = logging.getLogger("recallbox.search.vector")

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculates cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)

def search_vectors(db: Session, query_embedding: List[float], limit: int = 50, min_similarity: float = 0.2) -> List[Tuple[str, float]]:
    """
    Scans memory embeddings and returns (memory_id, cosine_similarity) sorted descending.
    Scales efficiently for local personal memory collections (<100k records).
    """
    if not query_embedding:
        return []
        
    memories = db.query(Memory.id, Memory.embedding_json).filter(Memory.embedding_json.isnot(None)).all()
    scored = []
    
    for mem_id, emb_json in memories:
        if not emb_json:
            continue
        try:
            emb = json.loads(emb_json)
            sim = cosine_similarity(query_embedding, emb)
            if sim >= min_similarity:
                scored.append((mem_id, float(sim)))
        except Exception:
            continue
            
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]

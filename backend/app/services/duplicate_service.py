import hashlib
import json
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from app.models.entities import Memory
from app.security.sanitizer import normalize_url
from app.search.vector_index import cosine_similarity

def calculate_content_hash(text: str) -> str:
    """Computes SHA-256 hash of clean trimmed content."""
    if not text:
        return ""
    normalized = " ".join(text.strip().lower().split())
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def detect_duplicate(
    db: Session,
    source_url: Optional[str] = None,
    content: Optional[str] = None,
    embedding: Optional[List[float]] = None
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Checks for exact, canonical, content-hash, or semantic near-duplicates.
    Returns: (is_duplicate, matched_memory_id, duplicate_reason)
    """
    # 1. Exact or Canonical URL Match
    if source_url:
        canon_url = normalize_url(source_url)
        existing = db.query(Memory).filter(
            (Memory.source_url == source_url) | (Memory.canonical_url == canon_url)
        ).first()
        if existing:
            return True, existing.id, f"Identical URL already saved: '{existing.title}'"

    # 2. Content SHA-256 Hash Match
    if content and len(content.strip()) > 50:
        c_hash = calculate_content_hash(content)
        existing_hash = db.query(Memory).filter(Memory.content_hash == c_hash).first()
        if existing_hash:
            return True, existing_hash.id, f"Identical content already saved: '{existing_hash.title}'"

    # 3. High Semantic Similarity Match (>0.92 cosine similarity)
    if embedding:
        memories = db.query(Memory.id, Memory.title, Memory.embedding_json).filter(Memory.embedding_json.isnot(None)).all()
        for mem_id, title, emb_json in memories:
            if not emb_json:
                continue
            try:
                emb = json.loads(emb_json)
                sim = cosine_similarity(embedding, emb)
                if sim > 0.92:
                    return True, mem_id, f"Near-identical memory found ({round(sim*100)}% match): '{title}'"
            except Exception:
                continue

    return False, None, None

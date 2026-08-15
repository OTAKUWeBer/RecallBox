import math
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.entities import Memory
from app.models.schemas import SearchResultItem, SearchResponse, MemoryRead
from app.search.fts import search_fts
from app.search.vector_index import search_vectors
from app.ai.provider_factory import get_ai_provider

def calculate_recency_score(captured_at: datetime) -> float:
    """Calculates recency decay score between 0.0 and 1.0 (half-life ~60 days)."""
    if not captured_at:
        return 0.5
    now = datetime.now(timezone.utc)
    if captured_at.tzinfo is None:
        captured_at = captured_at.replace(tzinfo=timezone.utc)
    days_old = max((now - captured_at).total_seconds() / 86400.0, 0.0)
    # Exponential decay with half life of 60 days
    return math.exp(-days_old / 60.0)

async def perform_hybrid_search(
    db: Session,
    query: str,
    limit: int = 20,
    offset: int = 0,
    source_type: Optional[str] = None,
    status: Optional[str] = None,
    tag: Optional[str] = None,
    min_importance: Optional[float] = None
) -> SearchResponse:
    """
    Executes hybrid search across FTS5 full-text, semantic vectors, and metadata filters.
    Applies Reciprocal Rank Fusion (RRF) and domain-specific relevance weighting.
    """
    if not query or not query.strip():
        return SearchResponse(query="", total_results=0, results=[])

    ai_provider = get_ai_provider()
    
    # 1. Lexical FTS5 search
    fts_results = search_fts(db, query, limit=100)
    fts_rank_map = {mem_id: (rank_idx + 1, score, hl) for rank_idx, (mem_id, score, hl) in enumerate(fts_results)}
    
    # 2. Semantic vector search
    query_vector = await ai_provider.embed(query)
    vector_results = search_vectors(db, query_vector, limit=100, min_similarity=0.15)
    vector_rank_map = {mem_id: (rank_idx + 1, sim) for rank_idx, (mem_id, sim) in enumerate(vector_results)}
    
    # Combine candidate IDs
    all_candidate_ids = set(fts_rank_map.keys()).union(set(vector_rank_map.keys()))
    
    if not all_candidate_ids:
        return SearchResponse(
            query=query,
            total_results=0,
            results=[],
            confidence_statement="No strong match found for this query."
        )

    # Fetch candidate memory records from DB
    query_builder = db.query(Memory).filter(Memory.id.in_(all_candidate_ids))
    if source_type:
        query_builder = query_builder.filter(Memory.source_type == source_type)
    if status:
        query_builder = query_builder.filter(Memory.status == status)
    if min_importance is not None:
        query_builder = query_builder.filter(Memory.importance >= min_importance)
        
    candidates = query_builder.all()
    
    # Filter by tag if requested
    if tag:
        tag_lower = tag.lower()
        candidates = [c for c in candidates if any(t.name.lower() == tag_lower for t in c.tags)]
        
    k = 60.0  # RRF constant
    scored_items: List[SearchResultItem] = []
    
    for mem in candidates:
        fts_info = fts_rank_map.get(mem.id)
        vec_info = vector_rank_map.get(mem.id)
        
        # Reciprocal Rank Fusion component
        rrf_score = 0.0
        fts_score_val = 0.0
        vec_score_val = 0.0
        highlights = []
        
        if fts_info:
            fts_rank, fts_score_val, hl = fts_info
            rrf_score += (1.0 / (k + fts_rank)) * 1.2  # Slight lexical priority for exact match
            if hl:
                highlights.append(hl)
                
        if vec_info:
            vec_rank, vec_score_val = vec_info
            rrf_score += (1.0 / (k + vec_rank)) * 1.0
            
        # Metadata boosts
        recency_factor = calculate_recency_score(mem.captured_at) * 0.15
        importance_factor = (mem.importance or 0.5) * 0.2
        intent_factor = 0.1 if (mem.user_why and len(mem.user_why.strip()) > 0) else 0.0
        access_factor = min((mem.access_count or 1) * 0.02, 0.1)
        
        final_score = round(rrf_score + recency_factor + importance_factor + intent_factor + access_factor, 4)
        
        # Serialize MemoryRead
        import json
        tags_list = [t.name for t in mem.tags]
        entities_list = json.loads(mem.entities_json or "[]")
        topics_list = json.loads(mem.topics_json or "[]")
        actions_list = json.loads(mem.possible_actions_json or "[]")
        metadata_dict = json.loads(mem.extra_metadata_json or "{}")
        
        mem_read = MemoryRead(
            id=mem.id,
            title=mem.title,
            content=mem.content,
            summary=mem.summary,
            user_why=mem.user_why,
            source=mem.source,
            source_url=mem.source_url,
            canonical_url=mem.canonical_url,
            source_type=mem.source_type,
            author=mem.author,
            favicon_url=mem.favicon_url,
            captured_at=mem.captured_at,
            updated_at=mem.updated_at,
            last_accessed_at=mem.last_accessed_at,
            access_count=mem.access_count or 1,
            importance=mem.importance or 0.5,
            confidence=mem.confidence or 1.0,
            status=mem.status or "inbox",
            is_favorite=mem.is_favorite or False,
            tags=tags_list,
            entities=entities_list,
            topics=topics_list,
            possible_actions=actions_list,
            reminders=[],
            relationships=[],
            extra_metadata=metadata_dict
        )
        
        scored_items.append(SearchResultItem(
            memory=mem_read,
            score=final_score,
            fts_rank=fts_score_val if fts_info else None,
            vector_rank=vec_score_val if vec_info else None,
            matched_highlights=highlights
        ))
        
    # Sort descending by final hybrid score
    scored_items.sort(key=lambda x: x.score, reverse=True)
    
    total = len(scored_items)
    paginated = scored_items[offset:offset + limit]
    
    confidence = "High confidence matches found." if total > 0 and paginated[0].score > 0.05 else "Moderate matches found."
    
    return SearchResponse(
        query=query,
        total_results=total,
        results=paginated,
        confidence_statement=confidence
    )

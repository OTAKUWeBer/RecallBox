import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.entities import Memory
from app.models.schemas import WhyDidISaveThisResponse, ContextReconstructionItem
from app.search.vector_index import cosine_similarity

def reconstruct_save_context(db: Session, memory_id: str) -> WhyDidISaveThisResponse:
    """
    Reconstructs the temporal, associative, and intent context for why a memory was saved.
    Strictly evidence-backed: never hallucinates facts or links.
    """
    memory = db.query(Memory).filter(Memory.id == memory_id).first()
    if not memory:
        raise ValueError("Memory not found")

    now = datetime.now(timezone.utc)
    captured_at = memory.captured_at
    if captured_at.tzinfo is None:
        captured_at = captured_at.replace(tzinfo=timezone.utc)
        
    days_ago = max(int((now - captured_at).total_seconds() // 86400), 0)

    # 1. Look for user's explicit note
    user_explicit_why = memory.user_why.strip() if memory.user_why else None

    # 2. Find temporal research cluster (items captured within +/- 24 hours)
    window_start = captured_at - timedelta(hours=24)
    window_end = captured_at + timedelta(hours=24)
    
    surrounding_memories = db.query(Memory).filter(
        Memory.id != memory.id,
        Memory.captured_at >= window_start,
        Memory.captured_at <= window_end
    ).all()

    # Parse current memory embedding and topics
    cur_embedding = json.loads(memory.embedding_json) if memory.embedding_json else []
    cur_topics = set(json.loads(memory.topics_json or "[]"))
    cur_tags = {t.name.lower() for t in memory.tags}

    related_items: List[ContextReconstructionItem] = []
    research_topics = set(cur_topics)

    for sm in surrounding_memories:
        sm_embedding = json.loads(sm.embedding_json) if sm.embedding_json else []
        sm_topics = set(json.loads(sm.topics_json or "[]"))
        sm_tags = {t.name.lower() for t in sm.tags}

        # Calculate similarity
        sim = cosine_similarity(cur_embedding, sm_embedding) if (cur_embedding and sm_embedding) else 0.0
        shared_topics = cur_topics.intersection(sm_topics)
        shared_tags = cur_tags.intersection(sm_tags)

        is_relevant = sim > 0.35 or len(shared_topics) > 0 or len(shared_tags) > 0

        if is_relevant or len(surrounding_memories) <= 3:
            rel_type = "Saved in the same research session"
            if len(shared_topics) > 0:
                rel_type = f"Shared topic: {', '.join(list(shared_topics)[:2])}"
            elif sim > 0.6:
                rel_type = "Semantically related research"

            sm_captured = sm.captured_at
            if sm_captured.tzinfo is None:
                sm_captured = sm_captured.replace(tzinfo=timezone.utc)

            related_items.append(ContextReconstructionItem(
                memory_id=sm.id,
                title=sm.title,
                source_url=sm.source_url,
                captured_at=sm_captured,
                relationship=rel_type,
                similarity_score=round(sim, 2)
            ))

            research_topics.update(sm_topics)

    # Sort related items by similarity/relevance
    related_items.sort(key=lambda x: x.similarity_score, reverse=True)
    top_related = related_items[:5]

    # Generate synthesized factual context summary
    summary_parts = []
    
    if days_ago == 0:
        summary_parts.append("You saved this today.")
    elif days_ago == 1:
        summary_parts.append("You saved this yesterday.")
    else:
        summary_parts.append(f"You saved this {days_ago} days ago.")

    if user_explicit_why:
        summary_parts.append(f"At the time, you noted: \"{user_explicit_why}\"")

    if top_related and research_topics:
        topic_str = ", ".join(list(research_topics)[:4])
        summary_parts.append(f"You were exploring items related to {topic_str}, and saved {len(top_related)} related item{'s' if len(top_related) > 1 else ''} around that time.")
    elif not user_explicit_why and not top_related:
        summary_parts.append("We don't have enough surrounding session context to determine why you saved this.")

    context_summary = " ".join(summary_parts)

    return WhyDidISaveThisResponse(
        memory_id=memory.id,
        title=memory.title,
        saved_days_ago=days_ago,
        captured_at=captured_at,
        user_explicit_why=user_explicit_why,
        active_research_trail=list(research_topics)[:6],
        related_memories_saved_around_then=top_related,
        context_summary=context_summary,
        evidence_backed=True
    )

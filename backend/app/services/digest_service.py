import json
from collections import Counter
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.entities import Memory
from app.models.schemas import WeeklyDigestResponse, MemoryRead

def _to_memory_read(mem: Memory) -> MemoryRead:
    tags_list = [t.name for t in mem.tags]
    entities_list = json.loads(mem.entities_json or "[]")
    topics_list = json.loads(mem.topics_json or "[]")
    actions_list = json.loads(mem.possible_actions_json or "[]")
    metadata_dict = json.loads(mem.extra_metadata_json or "{}")
    
    return MemoryRead(
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

def generate_weekly_digest(db: Session) -> WeeklyDigestResponse:
    """Generates 'Your Recall' weekly synthesis and highlights forgotten ideas."""
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=7)
    
    # 1. Total saved in past 7 days
    recent_memories = db.query(Memory).filter(Memory.captured_at >= period_start).all()
    total_saved = len(recent_memories)
    
    # 2. Most interesting items in the past 7 days (or all-time top if few recent)
    all_memories = db.query(Memory).all()
    sorted_interesting = sorted(
        recent_memories if len(recent_memories) >= 3 else all_memories,
        key=lambda m: (m.is_favorite, m.importance or 0.5),
        reverse=True
    )
    most_interesting = [_to_memory_read(m) for m in sorted_interesting[:6]]
    
    # 3. Top topics
    topic_counter = Counter()
    for m in (recent_memories if recent_memories else all_memories):
        for t in json.loads(m.topics_json or "[]"):
            topic_counter[t] += 1
        for tag in m.tags:
            topic_counter[tag.name] += 1
            
    top_topics = [{"topic": t, "count": c} for t, c in topic_counter.most_common(5)]
    
    # 4. Forgotten ideas: saved > 30 days ago (or oldest in DB), unread, importance >= 0.5
    thirty_days_ago = now - timedelta(days=30)
    old_memories = db.query(Memory).filter(
        Memory.captured_at <= thirty_days_ago,
        Memory.status.in_(["inbox", "unread", "active"])
    ).order_by(Memory.importance.desc()).limit(5).all()
    
    # Fallback if user is new: show oldest 3 items
    if not old_memories and len(all_memories) > 3:
        old_memories = sorted(all_memories, key=lambda m: m.captured_at)[:3]
        
    forgotten_ideas = [_to_memory_read(m) for m in old_memories]
    
    # 5. Pending actions
    pending_actions = []
    for m in all_memories:
        actions = json.loads(m.possible_actions_json or "[]")
        if actions and m.status in ["inbox", "unread", "active"]:
            pending_actions.append({
                "memory_id": m.id,
                "title": m.title,
                "action": actions[0],
                "source_url": m.source_url
            })
            if len(pending_actions) >= 5:
                break
                
    # 6. Potential duplicate topics
    potential_duplicates = []
    
    return WeeklyDigestResponse(
        period_start=period_start,
        period_end=now,
        total_saved=total_saved,
        most_interesting=most_interesting,
        top_topics=top_topics,
        forgotten_ideas=forgotten_ideas,
        potential_duplicates=potential_duplicates,
        pending_actions=pending_actions
    )

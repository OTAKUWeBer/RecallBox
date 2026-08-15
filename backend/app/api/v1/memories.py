import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import Memory, Tag, Reminder, MemoryEvent
from app.models.schemas import MemoryCreate, MemoryUpdate, MemoryRead, ReminderCreate, ReminderRead
from app.services.memory_service import create_memory, to_memory_read
from app.search.fts import sync_fts_entry

router = APIRouter(prefix="/memories", tags=["Memories"])

@router.post("", response_model=MemoryRead, status_code=status.HTTP_201_CREATED)
async def capture_memory(data: MemoryCreate, db: Session = Depends(get_db)):
    """Capture a new memory from extension, web UI, CLI, or MCP."""
    memory = await create_memory(db, data)
    return to_memory_read(memory)

@router.get("", response_model=List[MemoryRead])
def list_memories(
    status_filter: Optional[str] = Query(None, alias="status"),
    source_type: Optional[str] = None,
    tag: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List memories with filtering by status, source type, tag, or favorites."""
    query = db.query(Memory)
    
    if status_filter:
        query = query.filter(Memory.status == status_filter)
    if source_type:
        query = query.filter(Memory.source_type == source_type)
    if is_favorite is not None:
        query = query.filter(Memory.is_favorite == is_favorite)
    if tag:
        tag_lower = tag.lower()
        query = query.join(Memory.tags).filter(Tag.name == tag_lower)
        
    memories = query.order_by(Memory.captured_at.desc()).offset(offset).limit(limit).all()
    return [to_memory_read(m) for m in memories]

@router.get("/{memory_id}", response_model=MemoryRead)
def get_memory(memory_id: str, db: Session = Depends(get_db)):
    """Retrieve memory details and increment access count."""
    memory = db.query(Memory).filter(Memory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
        
    memory.access_count = (memory.access_count or 0) + 1
    memory.last_accessed_at = datetime.now(timezone.utc)
    db.commit()
    
    return to_memory_read(memory)

@router.patch("/{memory_id}", response_model=MemoryRead)
def update_memory(memory_id: str, data: MemoryUpdate, db: Session = Depends(get_db)):
    """Update memory metadata, notes, tags, or status."""
    memory = db.query(Memory).filter(Memory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
        
    if data.title is not None:
        memory.title = data.title
    if data.content is not None:
        memory.content = data.content
    if data.summary is not None:
        memory.summary = data.summary
    if data.user_why is not None:
        memory.user_why = data.user_why
    if data.source_type is not None:
        memory.source_type = data.source_type
    if data.importance is not None:
        memory.importance = data.importance
    if data.status is not None:
        memory.status = data.status
    if data.is_favorite is not None:
        memory.is_favorite = data.is_favorite
    if data.topics is not None:
        memory.topics_json = json.dumps(data.topics)
    if data.possible_actions is not None:
        memory.possible_actions_json = json.dumps(data.possible_actions)
        
    if data.tags is not None:
        memory.tags.clear()
        for t_name in data.tags:
            clean_t = t_name.strip().lower()
            if clean_t:
                tag_obj = db.query(Tag).filter(Tag.name == clean_t).first()
                if not tag_obj:
                    tag_obj = Tag(name=clean_t)
                    db.add(tag_obj)
                memory.tags.append(tag_obj)
                
    memory.updated_at = datetime.now(timezone.utc)
    
    event = MemoryEvent(memory=memory, event_type="updated", payload_json=json.dumps({"status": memory.status}))
    db.add(event)
    
    db.commit()
    db.refresh(memory)
    
    sync_fts_entry(
        db, memory.id, memory.title, memory.content, memory.summary,
        memory.user_why, [t.name for t in memory.tags], memory.source_url
    )
    
    return to_memory_read(memory)

@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(memory_id: str, db: Session = Depends(get_db)):
    """Delete a memory permanently."""
    memory = db.query(Memory).filter(Memory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
        
    from sqlalchemy import text
    db.execute(text("DELETE FROM memories_fts WHERE id = :id"), {"id": memory_id})
    db.delete(memory)
    db.commit()
    return None

@router.post("/{memory_id}/remind", response_model=ReminderRead)
def add_reminder(memory_id: str, data: ReminderCreate, db: Session = Depends(get_db)):
    """Set a follow-up reminder for a memory."""
    memory = db.query(Memory).filter(Memory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
        
    reminder = Reminder(
        memory=memory,
        remind_at=data.remind_at,
        note=data.note or f"Follow-up on: {memory.title}"
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    
    return ReminderRead(
        id=reminder.id,
        memory_id=reminder.memory_id,
        remind_at=reminder.remind_at,
        note=reminder.note,
        is_completed=reminder.is_completed,
        triggered_at=reminder.triggered_at,
        created_at=reminder.created_at,
        memory_title=memory.title
    )

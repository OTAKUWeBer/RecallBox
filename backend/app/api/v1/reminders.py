from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import Reminder, Memory
from app.models.schemas import ReminderCreate, ReminderRead

router = APIRouter(prefix="/reminders", tags=["Reminders"])

@router.get("", response_model=List[ReminderRead])
def list_reminders(db: Session = Depends(get_db)):
    """List all scheduled and active reminders."""
    reminders = db.query(Reminder).order_by(Reminder.remind_at.asc()).all()
    return [
        ReminderRead(
            id=r.id,
            memory_id=r.memory_id,
            remind_at=r.remind_at,
            note=r.note,
            is_completed=r.is_completed,
            triggered_at=r.triggered_at,
            created_at=r.created_at,
            memory_title=r.memory.title if r.memory else "Deleted Memory"
        ) for r in reminders
    ]

@router.patch("/{reminder_id}/complete", response_model=ReminderRead)
def complete_reminder(reminder_id: str, db: Session = Depends(get_db)):
    """Mark a reminder as completed/resolved."""
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
        
    reminder.is_completed = True
    reminder.triggered_at = datetime.now(timezone.utc)
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
        memory_title=reminder.memory.title if reminder.memory else ""
    )

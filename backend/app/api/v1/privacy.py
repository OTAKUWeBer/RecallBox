import os
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.core.config import settings
from app.models.entities import Memory, Attachment
from app.models.schemas import PrivacyStatsResponse

router = APIRouter(prefix="/privacy", tags=["Privacy Center"])

class PurgeConfirmRequest(BaseModel):
    confirm_phrase: str = Field(..., description="Must exactly match 'PERMANENTLY PURGE ALL DATA'")

@router.get("/stats", response_model=PrivacyStatsResponse)
def get_privacy_statistics(db: Session = Depends(get_db)):
    """Retrieve local storage, zero telemetry, and privacy audit statistics."""
    mem_count = db.query(Memory).count()
    att_count = db.query(Attachment).count()
    emb_count = db.query(Memory).filter(Memory.embedding_json.isnot(None)).count()
    
    db_size = 0
    if settings.DB_PATH.exists():
        db_size = os.path.getsize(settings.DB_PATH)
        
    return PrivacyStatsResponse(
        stored_memories_count=mem_count,
        stored_attachments_count=att_count,
        stored_embeddings_count=emb_count,
        cloud_sync_status="OFF (Local SQLite Database)",
        active_ai_provider=settings.AI_PROVIDER,
        telemetry_status="OFF (Zero Data Uploaded)",
        db_size_bytes=db_size
    )

@router.post("/purge")
def purge_all_local_data(payload: PurgeConfirmRequest, db: Session = Depends(get_db)):
    """
    Permanently delete all stored memories, embeddings, and indices.
    Requires exact confirmation phrase 'PERMANENTLY PURGE ALL DATA' and valid API key.
    """
    if payload.confirm_phrase != "PERMANENTLY PURGE ALL DATA":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purge aborted: Confirmation phrase does not match 'PERMANENTLY PURGE ALL DATA'."
        )
        
    try:
        db.execute(text("DELETE FROM memories_fts"))
        db.execute(text("DELETE FROM relationships"))
        db.execute(text("DELETE FROM reminders"))
        db.execute(text("DELETE FROM memory_events"))
        db.execute(text("DELETE FROM memory_tags"))
        db.execute(text("DELETE FROM memory_collections"))
        db.execute(text("DELETE FROM memories"))
        db.execute(text("DELETE FROM tags"))
        db.execute(text("DELETE FROM collections"))
        db.commit()
        return {"status": "success", "message": "All local data permanently purged."}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to purge database: {str(e)}"
        )

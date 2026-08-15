from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.schemas import WhyDidISaveThisResponse
from app.services.context_service import reconstruct_save_context

router = APIRouter(prefix="/context", tags=["Context Reconstruction"])

@router.get("/{memory_id}", response_model=WhyDidISaveThisResponse)
def get_why_saved_context(memory_id: str, db: Session = Depends(get_db)):
    """
    Reconstruct the user's research trail and context for why this item was saved.
    100% evidence-backed with zero hallucination.
    """
    try:
        return reconstruct_save_context(db, memory_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Memory not found")

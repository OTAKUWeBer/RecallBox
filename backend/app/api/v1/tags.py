from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import Tag
from app.models.schemas import TagRead

router = APIRouter(prefix="/tags", tags=["Tags"])

@router.get("", response_model=List[TagRead])
def list_tags(db: Session = Depends(get_db)):
    """List all unique tags."""
    return db.query(Tag).order_by(Tag.name.asc()).all()

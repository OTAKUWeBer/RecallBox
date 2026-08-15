from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.schemas import WeeklyDigestResponse
from app.services.digest_service import generate_weekly_digest

router = APIRouter(prefix="/digest", tags=["Weekly Digest"])

@router.get("", response_model=WeeklyDigestResponse)
def get_weekly_digest(db: Session = Depends(get_db)):
    """Generate 'Your Recall' weekly synthesis and forgotten ideas."""
    return generate_weekly_digest(db)

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import Collection
from app.models.schemas import CollectionCreate, CollectionRead

router = APIRouter(prefix="/collections", tags=["Collections"])

@router.get("", response_model=List[CollectionRead])
def list_collections(db: Session = Depends(get_db)):
    """List all collections with memory counts."""
    collections = db.query(Collection).order_by(Collection.name.asc()).all()
    res = []
    for c in collections:
        res.append(CollectionRead(
            id=c.id,
            name=c.name,
            description=c.description,
            is_auto=c.is_auto,
            created_at=c.created_at,
            memory_count=len(c.memories)
        ))
    return res

@router.post("", response_model=CollectionRead, status_code=status.HTTP_201_CREATED)
def create_collection(data: CollectionCreate, db: Session = Depends(get_db)):
    """Create a new memory collection."""
    col = Collection(
        name=data.name,
        description=data.description,
        is_auto=data.is_auto
    )
    db.add(col)
    db.commit()
    db.refresh(col)
    return CollectionRead(
        id=col.id,
        name=col.name,
        description=col.description,
        is_auto=col.is_auto,
        created_at=col.created_at,
        memory_count=0
    )

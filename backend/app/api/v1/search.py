from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.schemas import SearchQuery, SearchResponse
from app.search.hybrid_search import perform_hybrid_search

router = APIRouter(prefix="/search", tags=["Search"])

@router.post("", response_model=SearchResponse)
async def hybrid_search_endpoint(params: SearchQuery, db: Session = Depends(get_db)):
    """
    Execute hybrid search over memories with FTS5 lexical matching,
    vector semantic similarity, recency decay, and importance ranking.
    """
    return await perform_hybrid_search(
        db=db,
        query=params.query,
        limit=params.limit,
        offset=params.offset,
        source_type=params.source_type,
        status=params.status,
        tag=params.tag,
        min_importance=params.min_importance
    )

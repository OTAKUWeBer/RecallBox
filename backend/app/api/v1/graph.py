from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import Memory, Relationship
from app.models.schemas import GraphDataResponse, GraphNode, GraphEdge

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])

@router.get("", response_model=GraphDataResponse)
def get_graph_data(db: Session = Depends(get_db)):
    """Retrieve all nodes and relationship edges for the knowledge graph view."""
    memories = db.query(Memory).all()
    relationships = db.query(Relationship).all()
    
    nodes = [
        GraphNode(
            id=m.id,
            label=m.title[:45] + ("..." if len(m.title) > 45 else ""),
            source_type=m.source_type or "article",
            importance=m.importance or 0.5,
            tags=[t.name for t in m.tags]
        ) for m in memories
    ]
    
    edges = [
        GraphEdge(
            id=r.id,
            source=r.source_memory_id,
            target=r.target_memory_id,
            type=r.relationship_type,
            confidence=r.confidence or 0.8,
            reason=r.reason
        ) for r in relationships
    ]
    
    return GraphDataResponse(nodes=nodes, edges=edges)

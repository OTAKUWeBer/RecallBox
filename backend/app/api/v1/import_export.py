import json
from fastapi import APIRouter, Depends, UploadFile, File, Response, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.import_export_service import generate_export_zip, import_html_bookmarks
from app.models.entities import Memory, Tag
from app.search.fts import sync_fts_entry

router = APIRouter(prefix="/export", tags=["Import / Export"])
import_router = APIRouter(prefix="/import", tags=["Import / Export"])

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_IMPORT_ITEMS = 5000

async def read_bounded_file(file: UploadFile, max_bytes: int = MAX_UPLOAD_SIZE) -> bytes:
    """Reads uploaded file with strict memory size bounds to prevent DoS."""
    content = bytearray()
    chunk_size = 64 * 1024  # 64 KB
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        content.extend(chunk)
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Uploaded file exceeds maximum allowed limit of {max_bytes // (1024 * 1024)}MB."
            )
    return bytes(content)

@router.get("/zip")
def export_all_zip(db: Session = Depends(get_db)):
    """Exports all memories, markdown notes, graph, and manifest as a downloadable ZIP."""
    zip_buffer = generate_export_zip(db)
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=recallbox-export.zip"}
    )

@import_router.post("/bookmarks")
async def import_browser_bookmarks(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Import bookmarks from Chrome, Firefox, Safari, Brave, or Edge HTML export with size limits."""
    content = await read_bounded_file(file)
    html_text = content.decode("utf-8", errors="ignore")
    count = await import_html_bookmarks(db, html_text)
    return {"status": "success", "imported_count": count}

@import_router.post("/json")
async def import_json_dump(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Import memories from a RecallBox JSON export with bounding and item validation."""
    content = await read_bounded_file(file)
    try:
        data = json.loads(content.decode("utf-8", errors="ignore"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file structure.")
        
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="Expected JSON array of memories.")
        
    if len(data) > MAX_IMPORT_ITEMS:
        raise HTTPException(
            status_code=400,
            detail=f"Import batch too large: maximum allowed items per import is {MAX_IMPORT_ITEMS}."
        )
        
    count = 0
    for item in data:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "Imported Item"))[:500]
        raw_content = str(item.get("content", ""))[:50000]
        raw_summary = str(item.get("summary", ""))[:5000]
        raw_why = str(item.get("user_why", ""))[:2000]
        
        mem = Memory(
            title=title,
            content=raw_content,
            summary=raw_summary,
            user_why=raw_why,
            source=str(item.get("source", "json_import"))[:50],
            source_url=str(item.get("source_url"))[:2000] if item.get("source_url") else None,
            source_type=str(item.get("source_type", "article"))[:50],
            importance=float(item.get("importance", 0.5)),
            status=str(item.get("status", "inbox"))[:50],
            is_favorite=bool(item.get("is_favorite", False)),
            topics_json=json.dumps(item.get("topics", []) if isinstance(item.get("topics"), list) else []),
            entities_json=json.dumps(item.get("entities", []) if isinstance(item.get("entities"), list) else []),
            possible_actions_json=json.dumps(item.get("possible_actions", []) if isinstance(item.get("possible_actions"), list) else [])
        )
        
        tags_input = item.get("tags", [])
        if isinstance(tags_input, list):
            for t_name in tags_input[:20]:  # limit tags
                clean_t = str(t_name).strip().lower()[:50]
                if clean_t:
                    tag = db.query(Tag).filter(Tag.name == clean_t).first()
                    if not tag:
                        tag = Tag(name=clean_t)
                        db.add(tag)
                    mem.tags.append(tag)
            
        db.add(mem)
        db.commit()
        db.refresh(mem)
        
        sync_fts_entry(
            db, mem.id, mem.title, mem.content, mem.summary,
            mem.user_why, [t.name for t in mem.tags], mem.source_url
        )
        count += 1
        
    return {"status": "success", "imported_count": count}

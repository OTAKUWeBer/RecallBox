import io
import json
import zipfile
import re
from datetime import datetime, timezone
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from app.models.entities import Memory, Tag, Relationship, MemoryEvent
from app.search.fts import sync_fts_entry
from app.ai.provider_factory import get_ai_provider

def generate_export_zip(db: Session) -> io.BytesIO:
    """Generates a complete offline export ZIP with JSON data, Markdown notes, graph, and manifest."""
    memories = db.query(Memory).all()
    relationships = db.query(Relationship).all()
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 1. Manifest
        manifest = {
            "version": "1.0",
            "app": "RecallBox",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_memories": len(memories),
            "total_relationships": len(relationships)
        }
        zip_file.writestr("manifest.json", json.dumps(manifest, indent=2))
        
        # 2. Complete JSON Dump
        memories_dump = []
        for m in memories:
            mem_data = {
                "id": m.id,
                "title": m.title,
                "content": m.content,
                "summary": m.summary,
                "user_why": m.user_why,
                "source": m.source,
                "source_url": m.source_url,
                "canonical_url": m.canonical_url,
                "source_type": m.source_type,
                "author": m.author,
                "captured_at": m.captured_at.isoformat() if m.captured_at else None,
                "importance": m.importance,
                "status": m.status,
                "is_favorite": m.is_favorite,
                "tags": [t.name for t in m.tags],
                "topics": json.loads(m.topics_json or "[]"),
                "entities": json.loads(m.entities_json or "[]"),
                "possible_actions": json.loads(m.possible_actions_json or "[]"),
                "extra_metadata": json.loads(m.extra_metadata_json or "{}")
            }
            memories_dump.append(mem_data)
            
            # 3. Individual Markdown Note with YAML frontmatter
            safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', m.title[:40]).strip('_')
            date_prefix = m.captured_at.strftime("%Y-%m-%d") if m.captured_at else "undated"
            filename = f"memories/{date_prefix}_{m.id[:8]}_{safe_title}.md"
            
            md_content = (
                f"---\n"
                f"title: \"{m.title}\"\n"
                f"id: \"{m.id}\"\n"
                f"url: \"{m.source_url or ''}\"\n"
                f"source_type: \"{m.source_type or ''}\"\n"
                f"captured_at: \"{m.captured_at.isoformat() if m.captured_at else ''}\"\n"
                f"tags: [{', '.join([t.name for t in m.tags])}]\n"
                f"importance: {m.importance}\n"
                f"status: \"{m.status}\"\n"
                f"---\n\n"
                f"# {m.title}\n\n"
                f"> **Why I saved this:** {m.user_why or 'No note recorded.'}\n\n"
                f"**Summary:** {m.summary or ''}\n\n"
                f"## Content\n\n"
                f"{m.content or ''}\n"
            )
            zip_file.writestr(filename, md_content)
            
        zip_file.writestr("memories.json", json.dumps(memories_dump, indent=2))
        
        # 4. Graph dump
        graph_dump = {
            "relationships": [
                {
                    "source_id": r.source_memory_id,
                    "target_id": r.target_memory_id,
                    "type": r.relationship_type,
                    "confidence": r.confidence,
                    "reason": r.reason
                } for r in relationships
            ]
        }
        zip_file.writestr("graph.json", json.dumps(graph_dump, indent=2))
        
    zip_buffer.seek(0)
    return zip_buffer

async def import_html_bookmarks(db: Session, html_content: str) -> int:
    """Parses Netscape Bookmark format (standard for Chrome, Firefox, Safari) and ingests memories."""
    soup = BeautifulSoup(html_content, "html.parser")
    links = soup.find_all("a")
    imported_count = 0
    ai_provider = get_ai_provider()
    
    for a in links:
        href = a.get("href")
        if not href or not href.startswith("http"):
            continue
            
        title = a.get_text(strip=True) or href
        add_date_raw = a.get("add_date")
        tags_raw = a.get("tags")
        
        captured_dt = datetime.now(timezone.utc)
        if add_date_raw and add_date_raw.isdigit():
            try:
                captured_dt = datetime.fromtimestamp(int(add_date_raw), tz=timezone.utc)
            except Exception:
                pass
                
        tag_names = [t.strip() for t in tags_raw.split(",")] if tags_raw else []
        if not tag_names:
            tag_names = ["imported-bookmark"]
            
        # AI heuristic analysis
        ai_res = await ai_provider.extract_topics_and_entities(title, title)
        summary = f"Imported bookmark: {title}"
        embedding = await ai_provider.embed(f"{title} {summary}")
        
        memory = Memory(
            title=title,
            content=f"Imported bookmark from browser. URL: {href}",
            summary=summary,
            source="browser_import",
            source_url=href,
            canonical_url=href,
            source_type="link",
            captured_at=captured_dt,
            importance=0.5,
            status="inbox",
            topics_json=json.dumps(ai_res["topics"]),
            entities_json=json.loads(json.dumps(ai_res["entities"])),
            embedding_json=json.dumps(embedding)
        )
        
        # Tags
        for tn in tag_names:
            tag = db.query(Tag).filter(Tag.name == tn.lower()).first()
            if not tag:
                tag = Tag(name=tn.lower())
                db.add(tag)
            memory.tags.append(tag)
            
        db.add(memory)
        db.commit()
        db.refresh(memory)
        
        sync_fts_entry(
            db, memory.id, memory.title, memory.content, memory.summary,
            memory.user_why, [t.name for t in memory.tags], memory.source_url
        )
        imported_count += 1
        
    return imported_count

import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from app.models.entities import Memory, Tag, Relationship, Reminder, MemoryEvent
from app.models.schemas import MemoryCreate, MemoryUpdate, MemoryRead, ReminderRead, RelationshipRead
from app.security.ssrf import is_safe_url
from app.security.sanitizer import sanitize_html, extract_plain_text, normalize_url
from app.services.duplicate_service import detect_duplicate, calculate_content_hash
from app.search.fts import sync_fts_entry
from app.search.vector_index import cosine_similarity
from app.ai.provider_factory import get_ai_provider

logger = logging.getLogger("recallbox.services.memory")

async def fetch_url_metadata(url: str) -> Dict[str, Any]:
    """Fetches URL metadata with strict SSRF protection and content extraction."""
    is_safe, reason = is_safe_url(url)
    if not is_safe:
        logger.warning(f"Blocked URL fetch due to SSRF policy ({reason}): {url}")
        return {
            "title": url,
            "content": f"[Local or blocked address - content not scraped: {reason}]",
            "source_type": "link",
            "author": None,
            "favicon_url": None,
            "extra_metadata": {}
        }
        
    # Check specialized sources
    # 1. GitHub Repository
    github_match = re.match(r'https?://github\.com/([^/]+)/([^/]+)/?', url)
    if github_match:
        owner, repo_name = github_match.group(1), github_match.group(2)
        return {
            "title": f"{owner}/{repo_name}",
            "content": f"GitHub repository for {owner}/{repo_name}. URL: {url}",
            "source_type": "repository",
            "author": owner,
            "favicon_url": "https://github.githubassets.com/favicons/favicon.svg",
            "extra_metadata": {"owner": owner, "repo": repo_name, "source": "github"}
        }

    # 2. YouTube Video
    if "youtube.com" in url or "youtu.be" in url:
        return {
            "title": "YouTube Video",
            "content": f"Saved YouTube video. URL: {url}",
            "source_type": "video",
            "author": "YouTube Creator",
            "favicon_url": "https://www.youtube.com/s/desktop/favicon.ico",
            "extra_metadata": {"source": "youtube"}
        }

    # 3. Generic Web Page
    try:
        from app.security.ssrf import safe_fetch_url
        success, response_text, final_url = await safe_fetch_url(url)
        if not success:
            logger.warning(f"URL fetch rejected or failed for {url}: {response_text}")
            return {
                "title": url,
                "content": f"[Content not scraped: {response_text}]",
                "source_type": "link",
                "author": None,
                "favicon_url": None,
                "extra_metadata": {}
            }

        soup = BeautifulSoup(response_text, "html.parser")
        
        # Extract title
        title_tag = soup.find("title")
        og_title = soup.find("meta", property="og:title")
        title = og_title["content"] if (og_title and og_title.get("content")) else (title_tag.get_text(strip=True) if title_tag else url)
        
        # Extract meta description
        meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description")
        desc_text = meta_desc["content"] if (meta_desc and meta_desc.get("content")) else ""
        
        # Extract main readable text
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()
            
        body_text = soup.get_text(separator=" ", strip=True)
        clean_content = extract_plain_text(f"{desc_text}\n\n{body_text[:4000]}")
        
        # Extract favicon
        favicon_tag = soup.find("link", rel=lambda x: x and "icon" in x.lower())
        favicon_url = favicon_tag.get("href") if favicon_tag else None
        if favicon_url and not favicon_url.startswith("http"):
            from urllib.parse import urljoin
            favicon_url = urljoin(final_url or url, favicon_url)
            
        author_tag = soup.find("meta", attrs={"name": "author"})
        author = author_tag["content"] if (author_tag and author_tag.get("content")) else None
        
        return {
            "title": title[:500],
            "content": clean_content[:6000],
            "source_type": "article",
            "author": author,
            "favicon_url": favicon_url,
            "extra_metadata": {"meta_description": desc_text}
        }
    except Exception as e:
        logger.warning(f"Error processing URL {url}: {e}")

    return {
        "title": url,
        "content": "",
        "source_type": "link",
        "author": None,
        "favicon_url": None,
        "extra_metadata": {}
    }

async def create_memory(db: Session, data: MemoryCreate) -> Memory:
    """Core memory creation with automated enrichment and relationship linking."""
    ai_provider = get_ai_provider()
    
    # 1. Fetch metadata if URL is provided and content is empty
    title = data.title
    content = data.content or ""
    source_type = data.source_type or "article"
    author = data.author
    favicon_url = data.favicon_url
    extra_metadata = {}
    
    if data.source_url:
        canon_url = normalize_url(data.source_url)
        if not content or not title:
            meta = await fetch_url_metadata(data.source_url)
            title = title or meta["title"]
            content = content or meta["content"]
            source_type = meta["source_type"] if source_type == "article" else source_type
            author = author or meta["author"]
            favicon_url = favicon_url or meta["favicon_url"]
            extra_metadata.update(meta.get("extra_metadata", {}))
    else:
        canon_url = None
        
    title = title or "Quick Note"
    content_clean = extract_plain_text(content)
    
    # 2. AI Summarization & Topic Extraction
    summary = data.summary
    if not summary:
        summary = await ai_provider.summarize(content_clean, title)
        
    ai_analysis = await ai_provider.extract_topics_and_entities(f"{title}\n{content_clean}", title)
    topics = ai_analysis.get("topics", [])
    entities = ai_analysis.get("entities", [])
    suggested_tags = ai_analysis.get("suggested_tags", [])
    
    possible_actions = await ai_provider.extract_possible_actions(f"{title}\n{content_clean}", data.user_why)
    
    # 3. Importance score
    importance = data.importance
    if importance is None:
        importance = await ai_provider.calculate_importance(content_clean, title, data.user_why)
        
    # 4. Semantic Embedding
    text_to_embed = f"{title}\n{summary}\n{data.user_why or ''}\n{' '.join(topics)}"
    embedding = await ai_provider.embed(text_to_embed)
    
    # 5. Content Hash & Duplicate Check
    c_hash = calculate_content_hash(content_clean)
    
    # 6. Construct Memory entity
    memory = Memory(
        title=title,
        content=content_clean,
        summary=summary,
        user_why=data.user_why,
        source=data.source or "web",
        source_url=data.source_url,
        canonical_url=canon_url,
        source_type=source_type,
        author=author,
        favicon_url=favicon_url,
        content_hash=c_hash,
        importance=importance,
        confidence=1.0,
        status="inbox",
        is_favorite=False,
        topics_json=json.dumps(topics),
        entities_json=json.dumps(entities),
        possible_actions_json=json.dumps(possible_actions),
        embedding_json=json.dumps(embedding),
        extra_metadata_json=json.dumps(extra_metadata)
    )
    
    # Associate tags (explicit + suggested)
    combined_tag_names = set(data.tags)
    for st in suggested_tags[:3]:
        combined_tag_names.add(st)
        
    for tag_name in combined_tag_names:
        clean_tag = tag_name.strip().lower()
        if clean_tag:
            tag_obj = db.query(Tag).filter(Tag.name == clean_tag).first()
            if not tag_obj:
                tag_obj = Tag(name=clean_tag)
                db.add(tag_obj)
            memory.tags.append(tag_obj)
            
    # Optional 1-click reminder
    if data.remind_at:
        reminder = Reminder(
            memory=memory,
            remind_at=data.remind_at,
            note=f"Revisit: {title}"
        )
        db.add(reminder)
        
    # Event Log
    event = MemoryEvent(
        memory=memory,
        event_type="created",
        payload_json=json.dumps({"source": data.source or "web", "has_user_why": bool(data.user_why)})
    )
    db.add(event)
    
    db.add(memory)
    db.commit()
    db.refresh(memory)
    
    # 7. Sync SQLite FTS5 index
    sync_fts_entry(
        db, memory.id, memory.title, memory.content, memory.summary,
        memory.user_why, [t.name for t in memory.tags], memory.source_url
    )
    
    # 8. Auto-connect relationships with existing memories
    await _auto_discover_relationships(db, memory, embedding, topics)
    
    return memory

async def _auto_discover_relationships(db: Session, memory: Memory, embedding: List[float], topics: List[str]):
    """Automatically connects memory to existing memories if topic overlap or cosine similarity is high."""
    if not embedding:
        return
    candidates = db.query(Memory).filter(Memory.id != memory.id).all()
    for cand in candidates:
        cand_topics = set(json.loads(cand.topics_json or "[]"))
        cand_embedding = json.loads(cand.embedding_json) if cand.embedding_json else []
        
        sim = cosine_similarity(embedding, cand_embedding) if cand_embedding else 0.0
        shared_topics = set(topics).intersection(cand_topics)
        
        # Confident relationship threshold
        if sim >= 0.72 or len(shared_topics) >= 2:
            reason = f"Shared topics: {', '.join(list(shared_topics))}" if shared_topics else f"High semantic relevance ({round(sim*100)}%)"
            rel = Relationship(
                source_memory_id=memory.id,
                target_memory_id=cand.id,
                relationship_type="related_to",
                confidence=round(max(sim, 0.75), 2),
                reason=reason
            )
            db.add(rel)
            
    db.commit()

def to_memory_read(mem: Memory) -> MemoryRead:
    tags_list = [t.name for t in mem.tags]
    entities_list = json.loads(mem.entities_json or "[]")
    topics_list = json.loads(mem.topics_json or "[]")
    actions_list = json.loads(mem.possible_actions_json or "[]")
    metadata_dict = json.loads(mem.extra_metadata_json or "{}")
    
    reminders_list = [
        ReminderRead(
            id=r.id,
            memory_id=r.memory_id,
            remind_at=r.remind_at,
            note=r.note,
            is_completed=r.is_completed,
            triggered_at=r.triggered_at,
            created_at=r.created_at,
            memory_title=mem.title
        ) for r in (mem.reminders or [])
    ]
    
    relationships_list = []
    
    return MemoryRead(
        id=mem.id,
        title=mem.title,
        content=mem.content,
        summary=mem.summary,
        user_why=mem.user_why,
        source=mem.source,
        source_url=mem.source_url,
        canonical_url=mem.canonical_url,
        source_type=mem.source_type,
        author=mem.author,
        favicon_url=mem.favicon_url,
        captured_at=mem.captured_at,
        updated_at=mem.updated_at,
        last_accessed_at=mem.last_accessed_at,
        access_count=mem.access_count or 1,
        importance=mem.importance or 0.5,
        confidence=mem.confidence or 1.0,
        status=mem.status or "inbox",
        is_favorite=mem.is_favorite or False,
        tags=tags_list,
        entities=entities_list,
        topics=topics_list,
        possible_actions=actions_list,
        reminders=reminders_list,
        relationships=relationships_list,
        extra_metadata=metadata_dict
    )

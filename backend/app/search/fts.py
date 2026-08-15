import re
import sqlite3
import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger("recallbox.search.fts")

def sanitize_fts_query(raw_query: str) -> str:
    """
    Sanitizes user input for safe SQLite FTS5 queries.
    Strips dangerous characters, handles quotes, and adds prefix wildcard matching.
    """
    if not raw_query:
        return ""
    # Strip characters that break FTS5 syntax
    cleaned = re.sub(r'[\"\*\^\:\(\)\{\}\[\]\~\+\-\=]', ' ', raw_query)
    tokens = [t.strip() for t in cleaned.split() if len(t.strip()) > 0]
    if not tokens:
        return ""
    # Create prefix query for partial word matching: e.g. "dock* OR monitor*"
    fts_tokens = [f'"{t}"*' for t in tokens]
    return " OR ".join(fts_tokens)

def sync_fts_entry(db: Session, memory_id: str, title: str, content: str, summary: str, user_why: str, tags: List[str], source_url: str):
    """Upserts or syncs a memory entry in the SQLite FTS5 index."""
    try:
        tag_str = " ".join(tags) if tags else ""
        # Delete existing FTS entry if present
        db.execute(
            text("DELETE FROM memories_fts WHERE id = :id"),
            {"id": memory_id}
        )
        # Insert updated FTS entry
        db.execute(
            text("""
                INSERT INTO memories_fts(id, title, content, summary, user_why, tags, source_url)
                VALUES(:id, :title, :content, :summary, :user_why, :tags, :source_url)
            """),
            {
                "id": memory_id,
                "title": title or "",
                "content": content or "",
                "summary": summary or "",
                "user_why": user_why or "",
                "tags": tag_str,
                "source_url": source_url or ""
            }
        )
        db.commit()
    except Exception as e:
        logger.error(f"Failed to sync memory {memory_id} to FTS5: {e}")

def search_fts(db: Session, query: str, limit: int = 50) -> List[Tuple[str, float, str]]:
    """
    Executes SQLite FTS5 BM25 search.
    Returns list of (memory_id, fts_rank_score, snippet_highlight).
    """
    sanitized = sanitize_fts_query(query)
    if not sanitized:
        return []
        
    try:
        sql = text("""
            SELECT id, bm25(memories_fts) as rank, snippet(memories_fts, 1, '<b>', '</b>', '...', 12) as highlight
            FROM memories_fts
            WHERE memories_fts MATCH :query
            ORDER BY rank
            LIMIT :limit
        """)
        rows = db.execute(sql, {"query": sanitized, "limit": limit}).fetchall()
        
        results = []
        for r in rows:
            # BM25 in sqlite returns lower is better (negative), so invert for normalized ranking
            bm25_raw = r[1]
            score = 1.0 / (1.0 + abs(bm25_raw))
            results.append((r[0], score, r[2] or ""))
        return results
    except Exception as e:
        logger.warning(f"FTS5 search error for '{query}': {e}")
        return []

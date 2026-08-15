import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Float, Boolean, DateTime, ForeignKey, Table, Integer
)
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

# Association tables for Many-to-Many
memory_tags = Table(
    "memory_tags",
    Base.metadata,
    Column("memory_id", String(36), ForeignKey("memories.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", String(36), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
)

memory_collections = Table(
    "memory_collections",
    Base.metadata,
    Column("memory_id", String(36), ForeignKey("memories.id", ondelete="CASCADE"), primary_key=True),
    Column("collection_id", String(36), ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True)
)

class Memory(Base):
    __tablename__ = "memories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(512), nullable=False, default="Untitled Memory")
    content = Column(Text, nullable=True, default="")
    summary = Column(Text, nullable=True, default="")
    user_why = Column(Text, nullable=True, default="")  # User's capture intention
    
    # Source provenance
    source = Column(String(128), nullable=True, default="web")  # "github", "reddit", "youtube", "web", "quick_note", "screenshot", "cli"
    source_url = Column(String(2048), nullable=True, index=True)
    canonical_url = Column(String(2048), nullable=True, index=True)
    source_type = Column(String(64), nullable=True, default="article")  # "article", "repository", "video", "note", "quote", "code", "image"
    author = Column(String(256), nullable=True)
    favicon_url = Column(String(2048), nullable=True)
    
    # Hashes & Deduplication
    content_hash = Column(String(64), nullable=True, index=True)
    
    # Timestamps
    captured_at = Column(DateTime, default=utc_now, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    last_accessed_at = Column(DateTime, default=utc_now)
    access_count = Column(Integer, default=1)
    
    # Scoring & Status
    importance = Column(Float, default=0.5)  # 0.0 to 1.0
    confidence = Column(Float, default=1.0)
    status = Column(String(32), default="inbox", index=True)  # inbox, unread, active, review, done, archived, dismissed
    is_favorite = Column(Boolean, default=False)
    
    # Serialized JSON fields
    entities_json = Column(Text, default="[]")       # e.g. ["Docker", "Prometheus"]
    topics_json = Column(Text, default="[]")         # e.g. ["DevOps", "Monitoring"]
    possible_actions_json = Column(Text, default="[]") # e.g. ["Try locally", "Read docs"]
    embedding_json = Column(Text, nullable=True)     # JSON array of floats for semantic search
    extra_metadata_json = Column(Text, default="{}") # Provider raw metadata, OG tags, etc.
    
    # Relationships
    tags = relationship("Tag", secondary=memory_tags, back_populates="memories", lazy="joined")
    collections = relationship("Collection", secondary=memory_collections, back_populates="memories", lazy="selectin")
    reminders = relationship("Reminder", back_populates="memory", cascade="all, delete-orphan", lazy="selectin")
    events = relationship("MemoryEvent", back_populates="memory", cascade="all, delete-orphan", lazy="selectin")
    attachments = relationship("Attachment", back_populates="memory", cascade="all, delete-orphan", lazy="selectin")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(128), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now)

    memories = relationship("Memory", secondary=memory_tags, back_populates="tags")


class Collection(Base):
    __tablename__ = "collections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(128), nullable=False, index=True)
    description = Column(String(512), nullable=True)
    is_auto = Column(Boolean, default=False)  # Auto-grouped vs user-created
    created_at = Column(DateTime, default=utc_now)

    memories = relationship("Memory", secondary=memory_collections, back_populates="collections")


class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_memory_id = Column(String(36), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False, index=True)
    target_memory_id = Column(String(36), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column(String(64), nullable=False, default="related_to")  # related_to, supports, contradicts, duplicate_of, derived_from, part_of, follow_up_to, inspired_by, about
    confidence = Column(Float, default=0.8)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    memory_id = Column(String(36), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False, index=True)
    remind_at = Column(DateTime, nullable=False, index=True)
    note = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False, index=True)
    triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    memory = relationship("Memory", back_populates="reminders")


class MemoryEvent(Base):
    __tablename__ = "memory_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    memory_id = Column(String(36), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)  # created, updated, tagged, linked, viewed, archived, completed, deleted
    payload_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=utc_now, index=True)

    memory = relationship("Memory", back_populates="events")


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    memory_id = Column(String(36), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(256), nullable=False)
    file_path = Column(String(1024), nullable=False)
    mime_type = Column(String(128), nullable=False)
    file_size = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)

    memory = relationship("Memory", back_populates="attachments")

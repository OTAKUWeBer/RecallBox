from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# Tag Schemas
class TagBase(BaseModel):
    name: str

class TagRead(TagBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Collection Schemas
class CollectionBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_auto: bool = False

class CollectionCreate(CollectionBase):
    pass

class CollectionRead(CollectionBase):
    id: str
    created_at: datetime
    memory_count: Optional[int] = 0
    model_config = ConfigDict(from_attributes=True)

# Relationship Schemas
class RelationshipBase(BaseModel):
    source_memory_id: str
    target_memory_id: str
    relationship_type: str = "related_to"
    confidence: float = 0.8
    reason: Optional[str] = None

class RelationshipCreate(RelationshipBase):
    pass

class RelationshipRead(RelationshipBase):
    id: str
    created_at: datetime
    target_title: Optional[str] = None
    source_title: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# Reminder Schemas
class ReminderBase(BaseModel):
    remind_at: datetime
    note: Optional[str] = None

class ReminderCreate(ReminderBase):
    memory_id: str

class ReminderRead(ReminderBase):
    id: str
    memory_id: str
    is_completed: bool
    triggered_at: Optional[datetime] = None
    created_at: datetime
    memory_title: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# Memory Capture & CRUD Schemas
class MemoryCreate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    user_why: Optional[str] = None
    source: Optional[str] = "web"
    source_url: Optional[str] = None
    source_type: Optional[str] = "article"
    author: Optional[str] = None
    favicon_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    importance: Optional[float] = None
    remind_at: Optional[datetime] = None  # Optional 1-click reminder on capture

class MemoryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    user_why: Optional[str] = None
    source_type: Optional[str] = None
    importance: Optional[float] = None
    status: Optional[str] = None
    is_favorite: Optional[bool] = None
    tags: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    possible_actions: Optional[List[str]] = None

class MemoryRead(BaseModel):
    id: str
    title: str
    content: Optional[str] = ""
    summary: Optional[str] = ""
    user_why: Optional[str] = ""
    source: Optional[str] = "web"
    source_url: Optional[str] = None
    canonical_url: Optional[str] = None
    source_type: Optional[str] = "article"
    author: Optional[str] = None
    favicon_url: Optional[str] = None
    captured_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime] = None
    access_count: int = 1
    importance: float = 0.5
    confidence: float = 1.0
    status: str = "inbox"
    is_favorite: bool = False
    tags: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    possible_actions: List[str] = Field(default_factory=list)
    reminders: List[ReminderRead] = Field(default_factory=list)
    relationships: List[RelationshipRead] = Field(default_factory=list)
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(from_attributes=True)

# Search Schemas
class SearchQuery(BaseModel):
    query: str
    limit: int = 20
    offset: int = 0
    source_type: Optional[str] = None
    status: Optional[str] = None
    tag: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_importance: Optional[float] = None

class SearchResultItem(BaseModel):
    memory: MemoryRead
    score: float
    fts_rank: Optional[float] = None
    vector_rank: Optional[float] = None
    matched_highlights: List[str] = Field(default_factory=list)

class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResultItem]
    confidence_statement: Optional[str] = None

# "Why did I save this?" Context Reconstruction Schema
class ContextReconstructionItem(BaseModel):
    memory_id: str
    title: str
    source_url: Optional[str] = None
    captured_at: datetime
    relationship: str
    similarity_score: float

class WhyDidISaveThisResponse(BaseModel):
    memory_id: str
    title: str
    saved_days_ago: int
    captured_at: datetime
    user_explicit_why: Optional[str] = None
    active_research_trail: List[str] = Field(default_factory=list)
    related_memories_saved_around_then: List[ContextReconstructionItem] = Field(default_factory=list)
    context_summary: str
    evidence_backed: bool = True

# Weekly Digest Schema ("Your Recall")
class WeeklyDigestResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    total_saved: int
    most_interesting: List[MemoryRead] = Field(default_factory=list)
    top_topics: List[Dict[str, Any]] = Field(default_factory=list)
    forgotten_ideas: List[MemoryRead] = Field(default_factory=list)  # Saved >30d ago, unread
    potential_duplicates: List[Dict[str, Any]] = Field(default_factory=list)
    pending_actions: List[Dict[str, Any]] = Field(default_factory=list)

# Graph View Schemas
class GraphNode(BaseModel):
    id: str
    label: str
    source_type: str
    importance: float
    tags: List[str]

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str
    confidence: float
    reason: Optional[str] = None

class GraphDataResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

# Privacy Center Stats Schema
class PrivacyStatsResponse(BaseModel):
    stored_memories_count: int
    stored_attachments_count: int
    stored_embeddings_count: int
    cloud_sync_status: str = "OFF (Local Only)"
    active_ai_provider: str
    telemetry_status: str = "OFF"
    db_size_bytes: int
    last_backup: Optional[datetime] = None

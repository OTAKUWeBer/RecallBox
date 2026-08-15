import sqlite3
import json
import logging
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger("recallbox.database")

# SQLite URL
SQLALCHEMY_DATABASE_URL = f"sqlite:///{settings.DB_PATH.as_posix()}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

# Enable SQLite foreign keys & WAL mode for performance
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_fts5_tables():
    """Create SQLite FTS5 full-text index for instant hybrid search."""
    with engine.connect() as conn:
        conn.exec_driver_sql("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                id UNINDEXED,
                title,
                content,
                summary,
                user_why,
                tags,
                source_url,
                tokenize = 'porter unicode61'
            );
        """)
        conn.commit()
    logger.info("SQLite FTS5 full-text search index initialized.")

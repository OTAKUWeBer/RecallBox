import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine, init_fts5_tables
from app.security.auth import get_or_create_auth_token
from app.api.router import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("recallbox")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database Tables, FTS5 indices and Auth Token
    logger.info("Initializing RecallBox SQLite Database and FTS5 Indices...")
    Base.metadata.create_all(bind=engine)
    init_fts5_tables()
    # Initialize secure local auth token
    get_or_create_auth_token()
    logger.info("RecallBox backend ready on loopback.")
    yield
    # Shutdown
    logger.info("Shutting down RecallBox backend.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="RecallBox: A local-first personal memory system. Never lose something you wanted to come back to.",
    lifespan=lifespan
)

# Strict CORS middleware: explicitly allow only local frontend origins and browser extension schemes
ALLOWED_ORIGIN_REGEX = r"^(http://(localhost|127\.0\.0\.1):(3000|5173|8765)|(chrome-extension|moz-extension)://.*)$"

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "message": "Welcome to RecallBox API",
        "tagline": "Never lose something you wanted to come back to.",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_PREFIX
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

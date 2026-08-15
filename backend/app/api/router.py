from fastapi import APIRouter, Depends
from app.security.auth import verify_api_key
from app.api.v1 import (
    health,
    auth,
    memories,
    search,
    context,
    graph,
    reminders,
    digest,
    tags,
    collections,
    import_export,
    privacy
)

api_router = APIRouter()

# Public/Unauthenticated Endpoints (Health & Loopback Auth Handshake)
api_router.include_router(health.router)
api_router.include_router(auth.router)

# Protected Endpoints (Require X-RecallBox-Key or Authorization: Bearer <token>)
api_router.include_router(memories.router, dependencies=[Depends(verify_api_key)])
api_router.include_router(search.router, dependencies=[Depends(verify_api_key)])
api_router.include_router(context.router, dependencies=[Depends(verify_api_key)])
api_router.include_router(graph.router, dependencies=[Depends(verify_api_key)])
api_router.include_router(reminders.router, dependencies=[Depends(verify_api_key)])
api_router.include_router(digest.router, dependencies=[Depends(verify_api_key)])
api_router.include_router(tags.router, dependencies=[Depends(verify_api_key)])
api_router.include_router(collections.router, dependencies=[Depends(verify_api_key)])
api_router.include_router(import_export.router, dependencies=[Depends(verify_api_key)])
api_router.include_router(import_export.import_router, dependencies=[Depends(verify_api_key)])
api_router.include_router(privacy.router, dependencies=[Depends(verify_api_key)])

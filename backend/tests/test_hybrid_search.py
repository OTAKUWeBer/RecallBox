import pytest
import asyncio
from app.models.schemas import MemoryCreate
from app.services.memory_service import create_memory
from app.search.hybrid_search import perform_hybrid_search

@pytest.mark.asyncio
async def test_hybrid_search_finds_exact_and_semantic_matches(db_session):
    # Create test memories
    mem1 = await create_memory(db_session, MemoryCreate(
        title="Prometheus Docker Container Monitoring",
        content="Setup Prometheus, Grafana, and cAdvisor to monitor Docker container metrics and CPU utilization.",
        user_why="Need this for production server monitoring",
        tags=["docker", "prometheus", "monitoring"],
        source="web"
    ))
    
    mem2 = await create_memory(db_session, MemoryCreate(
        title="FastAPI Web Framework Tutorial",
        content="Building high-performance async REST APIs in Python with FastAPI and Pydantic v2 schemas.",
        user_why="Backend architecture reference",
        tags=["python", "fastapi"],
        source="web"
    ))

    # Search for Docker monitoring
    search_res = await perform_hybrid_search(db_session, query="Docker monitoring metrics")
    assert search_res.total_results >= 1
    top_result = search_res.results[0]
    assert top_result.memory.id == mem1.id
    assert "Prometheus Docker" in top_result.memory.title

    # Search for Python API
    search_res2 = await perform_hybrid_search(db_session, query="FastAPI async python")
    assert search_res2.total_results >= 1
    assert search_res2.results[0].memory.id == mem2.id

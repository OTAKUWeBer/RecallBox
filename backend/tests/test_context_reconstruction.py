import pytest
from app.models.schemas import MemoryCreate
from app.services.memory_service import create_memory
from app.services.context_service import reconstruct_save_context

@pytest.mark.asyncio
async def test_context_reconstruction_preserves_user_intent_and_temporal_cluster(db_session):
    # Save a primary memory with explicit user note
    mem1 = await create_memory(db_session, MemoryCreate(
        title="VictoriaMetrics vs Prometheus Benchmark",
        content="Benchmarking time-series database ingestion rates and memory usage in Kubernetes clusters.",
        user_why="Deciding between VictoriaMetrics and Prometheus for our VPS cluster",
        tags=["prometheus", "monitoring", "databases"],
        source="web"
    ))

    # Save a related memory in the same research session
    mem2 = await create_memory(db_session, MemoryCreate(
        title="Grafana Dashboard Templates for Docker",
        content="Ready-to-use Grafana dashboards for monitoring system load, memory, and container disk I/O.",
        user_why="Templates to plug into Prometheus",
        tags=["grafana", "monitoring", "docker"],
        source="web"
    ))

    # Reconstruct context for mem1
    context_res = reconstruct_save_context(db_session, mem1.id)
    
    assert context_res.memory_id == mem1.id
    assert context_res.user_explicit_why == "Deciding between VictoriaMetrics and Prometheus for our VPS cluster"
    assert context_res.evidence_backed is True
    assert "Deciding between VictoriaMetrics" in context_res.context_summary
    assert len(context_res.related_memories_saved_around_then) >= 1

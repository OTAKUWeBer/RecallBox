import pytest

def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["local_mode"] is True

def test_capture_and_retrieve_memory(client):
    # Capture memory
    capture_payload = {
        "title": "PostgreSQL Indexing Best Practices",
        "content": "Deep dive into B-Tree, BRIN, and GIN indexes for high volume telemetry tables.",
        "user_why": "Optimize slow queries on event table",
        "source": "web",
        "source_url": "https://example.com/postgres-indexing",
        "tags": ["postgres", "database", "performance"]
    }
    create_resp = client.post("/api/v1/memories", json=capture_payload)
    assert create_resp.status_code == 201
    created_mem = create_resp.json()
    mem_id = created_mem["id"]
    assert created_mem["title"] == "PostgreSQL Indexing Best Practices"
    assert "postgres" in created_mem["tags"]

    # List memories
    list_resp = client.get("/api/v1/memories")
    assert list_resp.status_code == 200
    memories = list_resp.json()
    assert len(memories) >= 1

    # Get single memory
    get_resp = client.get(f"/api/v1/memories/{mem_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == mem_id

    # Search
    search_resp = client.post("/api/v1/search", json={"query": "PostgreSQL indexing"})
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["total_results"] >= 1

    # Context reconstruction
    ctx_resp = client.get(f"/api/v1/context/{mem_id}")
    assert ctx_resp.status_code == 200
    assert ctx_resp.json()["evidence_backed"] is True

    # Graph
    graph_resp = client.get("/api/v1/graph")
    assert graph_resp.status_code == 200
    assert "nodes" in graph_resp.json()

    # Privacy stats
    priv_resp = client.get("/api/v1/privacy/stats")
    assert priv_resp.status_code == 200
    assert priv_resp.json()["telemetry_status"] == "OFF (Zero Data Uploaded)"

    # Export ZIP
    export_resp = client.get("/api/v1/export/zip")
    assert export_resp.status_code == 200
    assert export_resp.headers["content-type"] == "application/zip"

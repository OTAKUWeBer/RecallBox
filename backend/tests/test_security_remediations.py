import pytest
import io
import json
from fastapi.testclient import TestClient
from app.main import app
from app.security.ssrf import is_safe_url, safe_fetch_url
from app.security.auth import get_or_create_auth_token

# ==========================================
# CRIT-01: Local Loopback Auth & CORS Tests
# ==========================================

def test_unauthenticated_request_is_rejected():
    """Unauthenticated request to protected memories endpoint must return 401."""
    with TestClient(app) as raw_client:
        resp = raw_client.get("/api/v1/memories")
        assert resp.status_code == 401
        assert "Unauthorized" in resp.json()["detail"]

def test_invalid_token_is_rejected():
    """Request with forged/incorrect token must return 401."""
    with TestClient(app) as raw_client:
        resp = raw_client.get("/api/v1/memories", headers={"X-RecallBox-Key": "invalid_fake_token_12345"})
        assert resp.status_code == 401

def test_valid_token_in_header_succeeds(auth_token):
    """Request with valid X-RecallBox-Key must succeed."""
    with TestClient(app) as raw_client:
        resp = raw_client.get("/api/v1/memories", headers={"X-RecallBox-Key": auth_token})
        assert resp.status_code == 200

def test_valid_bearer_token_succeeds(auth_token):
    """Request with valid Authorization: Bearer <token> must succeed."""
    with TestClient(app) as raw_client:
        resp = raw_client.get("/api/v1/memories", headers={"Authorization": f"Bearer {auth_token}"})
        assert resp.status_code == 200

def test_untrusted_cors_origin_disallowed():
    """CORS requests from malicious origins must not be allowed."""
    with TestClient(app) as raw_client:
        resp = raw_client.options(
            "/api/v1/memories",
            headers={
                "Origin": "https://evil-attacker.com",
                "Access-Control-Request-Method": "POST"
            }
        )
        # Access-Control-Allow-Origin header must NOT reflect evil origin
        allow_origin = resp.headers.get("access-control-allow-origin")
        assert allow_origin != "https://evil-attacker.com"
        assert allow_origin != "*"

# ==========================================
# CRIT-02: Privacy Purge Gating Tests
# ==========================================

def test_purge_without_auth_fails():
    """POST /api/v1/privacy/purge without auth token must return 401."""
    with TestClient(app) as raw_client:
        resp = raw_client.post("/api/v1/privacy/purge", json={"confirm_phrase": "PERMANENTLY PURGE ALL DATA"})
        assert resp.status_code == 401

def test_purge_with_wrong_confirmation_fails(auth_token):
    """POST /api/v1/privacy/purge with wrong confirmation string must return 400."""
    with TestClient(app) as raw_client:
        resp = raw_client.post(
            "/api/v1/privacy/purge",
            headers={"X-RecallBox-Key": auth_token},
            json={"confirm_phrase": "yes please"}
        )
        assert resp.status_code == 400
        assert "Confirmation phrase does not match" in resp.json()["detail"]

def test_purge_with_correct_confirmation_succeeds(auth_token):
    """POST /api/v1/privacy/purge with exact confirmation phrase must succeed."""
    with TestClient(app) as raw_client:
        # First capture a memory
        raw_client.post(
            "/api/v1/memories",
            headers={"X-RecallBox-Key": auth_token},
            json={"title": "To be purged memory", "content": "Sample"}
        )
        # Purge
        resp = raw_client.post(
            "/api/v1/privacy/purge",
            headers={"X-RecallBox-Key": auth_token},
            json={"confirm_phrase": "PERMANENTLY PURGE ALL DATA"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

        # Verify memories table is empty
        list_resp = raw_client.get("/api/v1/memories", headers={"X-RecallBox-Key": auth_token})
        assert len(list_resp.json()) == 0

# ==========================================
# HIGH-01: Stored XSS Neutralization Tests
# ==========================================

def test_stored_xss_payload_persisted_safely(client):
    """XSS payloads in memory title/content must be saved and retrieved as raw text without execution."""
    xss_payload = "<script>alert('xss')</script><img src=x onerror=alert(1)>"
    resp = client.post("/api/v1/memories", json={
        "title": f"Test XSS: {xss_payload}",
        "content": f"Content payload: {xss_payload}"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "Test XSS" in data["title"]
    
    # Search highlight check
    search_resp = client.post("/api/v1/search", json={"query": "Test XSS"})
    assert search_resp.status_code == 200

# ==========================================
# HIGH-02: SSRF Protection & Hop Validation Tests
# ==========================================

def test_ssrf_blocks_all_internal_targets():
    """Validates that internal hostnames, loopbacks, and cloud metadata IPs are rejected."""
    blocked_urls = [
        "http://localhost:8080/secret",
        "http://127.0.0.1:8765/api/v1/export/zip",
        "http://127.0.0.1.nip.io/data",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/internal",
        "http://0.0.0.0:3000",
        "http://10.0.0.1/admin",
        "http://192.168.1.1/router",
        "http://172.16.0.5/service",
        "file:///etc/passwd",
        "gopher://127.0.0.1:25/",
    ]
    for url in blocked_urls:
        is_safe, reason = is_safe_url(url)
        assert not is_safe, f"Expected {url} to be blocked by SSRF check, but got safe."

# ==========================================
# HIGH-04: MCP Destructive Operation Gating Tests
# ==========================================

@pytest.mark.asyncio
async def test_mcp_forget_is_blocked_by_default():
    """Verify that MCP server denies destructive 'forget' by default."""
    from packages.mcp.recallbox_mcp import RecallBoxMCPServer
    server = RecallBoxMCPServer()
    res = await server.call_tool("forget", {"memory_id": "test-id-123", "user_confirmation": True})
    assert res.get("isError") is True
    assert "Destructive operation blocked" in res["content"][0]["text"]

# ==========================================
# MED-01: Import Size Bounding & Item Limit Tests
# ==========================================

def test_oversized_import_file_rejected(client):
    """Uploading a file exceeding MAX_UPLOAD_SIZE (10MB) must return 413."""
    # 11 MB dummy stream
    oversized_data = b"A" * (11 * 1024 * 1024)
    file_payload = {"file": ("huge_bookmarks.html", io.BytesIO(oversized_data), "text/html")}
    resp = client.post("/api/v1/import/bookmarks", files=file_payload)
    assert resp.status_code == 413
    assert "exceeds maximum allowed limit" in resp.json()["detail"]

def test_json_import_item_limit_enforced(client):
    """Importing JSON array exceeding MAX_IMPORT_ITEMS (5000) must return 400."""
    huge_list = [{"title": f"Item {i}", "content": "test"} for i in range(5001)]
    json_bytes = json.dumps(huge_list).encode("utf-8")
    file_payload = {"file": ("massive.json", io.BytesIO(json_bytes), "application/json")}
    resp = client.post("/api/v1/import/json", files=file_payload)
    assert resp.status_code == 400
    assert "Import batch too large" in resp.json()["detail"]

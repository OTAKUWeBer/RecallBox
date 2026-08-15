import pytest
from app.security.ssrf import is_safe_url
from app.security.sanitizer import sanitize_html, extract_plain_text, normalize_url

def test_ssrf_blocks_private_and_loopback_ips():
    blocked_urls = [
        "http://127.0.0.1:8080/admin",
        "http://localhost:3000",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.1/secrets",
        "http://192.168.1.1/router",
        "http://172.16.0.5/internal",
        "ftp://example.com/file",
        "file:///etc/passwd"
    ]
    for url in blocked_urls:
        is_safe, reason = is_safe_url(url)
        assert not is_safe, f"Expected {url} to be blocked by SSRF check, but got reason: {reason}"

def test_html_sanitizer_removes_malicious_scripts():
    raw_dirty = """
    <div>
        <h1>Safe Heading</h1>
        <script>alert('xss')</script>
        <p>This is safe <img src="x" onerror="alert(1)"> text.</p>
        <a href="https://example.com" onclick="stealCookies()">Link</a>
    </div>
    """
    clean = sanitize_html(raw_dirty)
    assert "<script>" not in clean
    assert "onerror=" not in clean
    assert "onclick=" not in clean
    assert "Safe Heading" in clean
    assert "https://example.com" in clean

def test_url_normalization_strips_tracking_params():
    url_with_tracking = "https://example.com/article?utm_source=twitter&utm_medium=social&fbclid=12345&id=42#section"
    normalized = normalize_url(url_with_tracking)
    assert "utm_source" not in normalized
    assert "fbclid" not in normalized
    assert "id=42" in normalized
    assert normalized.startswith("https://example.com/article?id=42")

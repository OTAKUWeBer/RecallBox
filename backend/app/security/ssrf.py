import socket
import ipaddress
from urllib.parse import urlparse, urljoin
from typing import Tuple, Optional
import httpx
import logging

logger = logging.getLogger("recallbox.security.ssrf")

BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.88.99.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
    # IPv6
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("::/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("::ffff:0:0/96"), # IPv4-mapped IPv6
]

MAX_REDIRECT_HOPS = 5
MAX_RESPONSE_BYTES = 5 * 1024 * 1024 # 5 MB
DEFAULT_TIMEOUT_SECONDS = 6.0

def is_safe_url(url: str) -> Tuple[bool, str]:
    """
    Validates that a URL is safe to fetch and does not resolve to internal/loopback/private IP ranges.
    Returns (is_safe, reason).
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, f"Disallowed scheme '{parsed.scheme}'. Only http and https are allowed."
        
        hostname = parsed.hostname
        if not hostname:
            return False, "Invalid URL: missing hostname."
            
        # Check string representations of localhost & loopbacks
        lower_host = hostname.lower().strip("[]")
        if lower_host in ("localhost", "127.0.0.1", "::1", "0.0.0.0", "0", "169.254.169.254"):
            return False, "Access to localhost or internal metadata is blocked for security."
            
        # Resolve DNS to check all target IP addresses
        addr_info = socket.getaddrinfo(lower_host, None)
        for entry in addr_info:
            ip_str = entry[4][0]
            ip_obj = ipaddress.ip_address(ip_str)
            
            # If IPv4-mapped IPv6 (e.g. ::ffff:127.0.0.1), map to IPv4 for checking
            if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped:
                ip_obj = ip_obj.ipv4_mapped
                
            for blocked_net in BLOCKED_IP_NETWORKS:
                if ip_obj in blocked_net:
                    return False, f"URL resolves to blocked/internal IP range: {ip_str}"
                    
        return True, "Safe URL"
    except socket.gaierror:
        return False, "Failed to resolve hostname in DNS."
    except Exception as e:
        return False, f"URL validation error: {str(e)}"

async def safe_fetch_url(url: str, headers: Optional[dict] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Fetches a URL safely with strict hop-by-hop redirect verification, timeout, and response size bounds.
    Returns (success, response_text_or_reason, final_url).
    """
    current_url = url
    client_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) RecallBox/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    if headers:
        client_headers.update(headers)
        
    for hop in range(MAX_REDIRECT_HOPS + 1):
        is_safe, reason = is_safe_url(current_url)
        if not is_safe:
            logger.warning(f"Blocked URL at hop {hop} due to SSRF policy ({reason}): {current_url}")
            return False, f"SSRF Protection blocked: {reason}", current_url
            
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS, follow_redirects=False) as client:
                resp = await client.get(current_url, headers=client_headers)
                
                # Check for redirects (301, 302, 303, 307, 308)
                if resp.status_code in (301, 302, 303, 307, 308):
                    location = resp.headers.get("Location")
                    if not location:
                        return False, "Redirect with missing Location header", current_url
                    # Resolve relative redirect URLs
                    current_url = urljoin(current_url, location)
                    continue
                    
                if resp.status_code != 200:
                    return False, f"HTTP Error {resp.status_code}", current_url
                    
                # Stream check response content size
                content_bytes = resp.content
                if len(content_bytes) > MAX_RESPONSE_BYTES:
                    content_bytes = content_bytes[:MAX_RESPONSE_BYTES]
                    
                text_content = content_bytes.decode(resp.encoding or "utf-8", errors="ignore")
                return True, text_content, current_url
                
        except httpx.TimeoutException:
            return False, "Request timed out.", current_url
        except Exception as e:
            return False, f"Fetch error: {str(e)}", current_url
            
    return False, f"Exceeded maximum redirects ({MAX_REDIRECT_HOPS})", current_url

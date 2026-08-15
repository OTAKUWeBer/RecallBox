import re
import bleach
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

ALLOWED_HTML_TAGS = [
    'p', 'b', 'i', 'strong', 'em', 'code', 'pre', 'blockquote',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li',
    'a', 'hr', 'br', 'span'
]

ALLOWED_HTML_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    '*': ['class']
}

# Tracking parameters to strip for canonical URL normalization
TRACKING_PARAMS = {
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'fbclid', 'gclid', 'msclkid', 'mc_cid', 'mc_eid', '_ga', '_gl',
    'ref', 'source', 'token'
}

def sanitize_html(raw_html: str) -> str:
    """Sanitizes raw HTML to remove XSS vectors and disallowed script tags."""
    if not raw_html:
        return ""
    return bleach.clean(
        raw_html,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_HTML_ATTRIBUTES,
        strip=True
    )

def extract_plain_text(text_or_html: str) -> str:
    """Strips all HTML tags and collapses redundant whitespace."""
    if not text_or_html:
        return ""
    # Strip HTML tags
    cleaned = re.sub(r'<[^>]+>', ' ', text_or_html)
    # Collapse multiple whitespace/newlines
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def normalize_url(url: str) -> str:
    """Normalizes URL by lowercasing hostname and stripping tracking query parameters."""
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        if not parsed.scheme or not parsed.netloc:
            return url.strip()
            
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        
        # Remove standard default ports
        if (scheme == 'http' and netloc.endswith(':80')) or (scheme == 'https' and netloc.endswith(':443')):
            netloc = netloc.rsplit(':', 1)[0]
            
        # Strip tracking query params
        query_items = parse_qsl(parsed.query, keep_blank_values=True)
        filtered_query = [(k, v) for k, v in query_items if k.lower() not in TRACKING_PARAMS]
        clean_query = urlencode(filtered_query)
        
        # Path clean
        path = parsed.path
        if path.endswith('/') and len(path) > 1:
            path = path[:-1]
            
        return urlunparse((scheme, netloc, path, parsed.params, clean_query, ''))
    except Exception:
        return url.strip()

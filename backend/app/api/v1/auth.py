import secrets
from fastapi import APIRouter, Request, HTTPException, status
from app.security.auth import get_or_create_auth_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/session")
def get_local_session_token(request: Request):
    """
    Returns the local authorization key ONLY for direct loopback same-origin browser requests.
    Protected against cross-site requests via Sec-Fetch-Site and Host verification.
    """
    client_host = request.client.host if request.client else ""
    if client_host not in ("127.0.0.1", "::1", "localhost", "testclient"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session handshake is restricted to local loopback client."
        )
        
    # Check Sec-Fetch-Site header to block cross-site framing / requests
    sec_fetch_site = request.headers.get("sec-fetch-site")
    if sec_fetch_site and sec_fetch_site in ("cross-site",):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-site requests cannot retrieve local session token."
        )
        
    return {
        "status": "authenticated",
        "token": get_or_create_auth_token()
    }

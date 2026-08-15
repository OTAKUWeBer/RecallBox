import os
import secrets
import stat
import logging
from pathlib import Path
from typing import Optional
from fastapi import Header, HTTPException, status, Request
from app.core.config import settings

logger = logging.getLogger("recallbox.security.auth")

_cached_token: Optional[str] = None

def get_or_create_auth_token() -> str:
    """
    Retrieves or generates a cryptographically strong local authorization token.
    Stored locally in data/auth_token with restricted permissions.
    """
    global _cached_token
    if _cached_token is not None:
        return _cached_token
        
    # Check environment variable first
    env_token = os.getenv("RECALLBOX_API_KEY")
    if env_token and len(env_token.strip()) >= 16:
        _cached_token = env_token.strip()
        return _cached_token
        
    token_file: Path = settings.DATA_DIR / "auth_token"
    if token_file.exists():
        try:
            stored = token_file.read_text(encoding="utf-8").strip()
            if len(stored) >= 16:
                _cached_token = stored
                return _cached_token
        except Exception as e:
            logger.warning(f"Could not read auth_token file: {e}")
            
    # Generate new 32-byte secure hex token
    new_token = secrets.token_hex(32)
    try:
        settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
        # Write with restricted file permissions
        token_file.write_text(new_token, encoding="utf-8")
        try:
            # Set owner read/write only on POSIX
            os.chmod(token_file, stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            pass
        logger.info("Generated new secure local loopback authorization token.")
    except Exception as e:
        logger.error(f"Failed to persist auth_token file: {e}")
        
    _cached_token = new_token
    return _cached_token

def verify_api_key(
    x_recallbox_key: Optional[str] = Header(None, alias="X-RecallBox-Key"),
    authorization: Optional[str] = Header(None)
) -> str:
    """
    Validates that incoming requests carry the valid local authorization token.
    Supports either 'X-RecallBox-Key: <token>' or 'Authorization: Bearer <token>'.
    """
    expected_token = get_or_create_auth_token()
    
    # Check X-RecallBox-Key
    if x_recallbox_key and secrets.compare_digest(x_recallbox_key.strip(), expected_token):
        return expected_token
        
    # Check Authorization: Bearer <token>
    if authorization:
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            if secrets.compare_digest(parts[1], expected_token):
                return expected_token
                
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Invalid or missing RecallBox authorization token.",
        headers={"WWW-Authenticate": "Bearer"}
    )

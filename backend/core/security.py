"""
A.N.N. Core Security
====================
Central auth primitives for the modular monolith:
- Admin-token verification (no insecure default; disabled when ADMIN_SECRET unset)
- API-key hashing helpers (keys stored as SHA-256 in the DB)
- Firebase ID-token verification (frontend user auth)
- Combined access dependency for cost-sensitive endpoints
"""

import hashlib
import os
import secrets

from fastapi import Header, HTTPException

from config import get_settings


# ── API-key hashing ────────────────────────────────────

def hash_api_key(raw_key: str) -> str:
    """SHA-256 hash used for at-rest API key storage/lookup."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def key_prefix(raw_key: str) -> str:
    """Short displayable prefix for a raw key (never store/return full keys)."""
    return raw_key[:12] + "…"


# ── Admin auth ─────────────────────────────────────────

def _admin_secret() -> str:
    settings = get_settings()
    return settings.admin_secret or os.getenv("ADMIN_SECRET", "")


async def require_admin(x_admin_token: str | None = Header(None, alias="X-Admin-Token")) -> bool:
    """Admin gate. 503 when no ADMIN_SECRET configured — there is no default token."""
    secret = _admin_secret()
    if not secret:
        raise HTTPException(
            status_code=503,
            detail="Admin access disabled: ADMIN_SECRET is not configured on the server.",
        )
    if not x_admin_token or not secrets.compare_digest(x_admin_token, secret):
        raise HTTPException(status_code=403, detail="Invalid Admin Token")
    return True


# ── Firebase user auth ─────────────────────────────────

def _init_firebase() -> bool:
    try:
        import firebase_admin
    except ImportError:
        return False
    if not firebase_admin._apps:
        settings = get_settings()
        options = {"projectId": settings.firebase_project_id} if settings.firebase_project_id else None
        try:
            firebase_admin.initialize_app(options=options)
        except Exception:
            return False
    return True


async def verify_firebase_token(authorization: str | None = Header(None)) -> dict:
    """Strict Firebase auth dependency — returns the decoded token claims."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Firebase Bearer token.")
    if not _init_firebase():
        raise HTTPException(status_code=503, detail="Firebase auth not configured on the server.")
    from firebase_admin import auth as fb_auth
    try:
        return fb_auth.verify_id_token(authorization.split(" ", 1)[1])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired Firebase ID token.")


# ── Combined gate for cost-sensitive endpoints ─────────

async def require_pipeline_access(
    x_admin_token: str | None = Header(None, alias="X-Admin-Token"),
    x_ann_api_key: str | None = Header(None, alias="X-ANN-API-Key"),
    authorization: str | None = Header(None),
) -> dict:
    """
    Guards endpoints that trigger paid LLM/TTS/video calls.
    Accepts any of: admin token, active B2B API key, Firebase user token.
    In ENV=development, unauthenticated access is allowed for local work.
    """
    settings = get_settings()

    secret = _admin_secret()
    if secret and x_admin_token and secrets.compare_digest(x_admin_token, secret):
        return {"role": "admin"}

    if x_ann_api_key:
        from services.auth import get_client_by_key
        client = await get_client_by_key(x_ann_api_key)
        if client and client.is_active:
            return {"role": "b2b", "client": client.client_name}

    if authorization and authorization.startswith("Bearer ") and _init_firebase():
        from firebase_admin import auth as fb_auth
        try:
            decoded = fb_auth.verify_id_token(authorization.split(" ", 1)[1])
            return {"role": "user", "uid": decoded.get("uid")}
        except Exception:
            pass

    if settings.env.lower() == "development":
        return {"role": "dev"}

    raise HTTPException(
        status_code=401,
        detail="Authentication required: provide X-Admin-Token, X-ANN-API-Key, or a Firebase Bearer token.",
    )

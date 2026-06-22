"""
Admin settings management — runtime API key updates.
"""

import os
from fastapi import APIRouter
from dotenv import set_key

router = APIRouter(tags=["Admin Settings"])

ACCEPTED_KEYS = [
    "LLM_API_KEY", "NEWS_API_KEY", "ALPHA_VANTAGE_KEY",
    "ELEVENLABS_API_KEY", "HEYGEN_API_KEY",
    "TWITTER_BEARER_TOKEN", "FACEBOOK_PAGE_TOKEN",
    "INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_ACCOUNT_ID",
]


def _mask(val: str | None) -> str:
    if not val or len(val) < 8:
        return ""
    return f"{val[:4]}...{val[-4:]}"


@router.get("/api/v1/admin/settings")
async def get_settings():
    return {key: _mask(os.getenv(key)) for key in ACCEPTED_KEYS}


@router.post("/api/v1/admin/settings")
async def update_settings(payload: dict[str, str]):
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        with open(env_path, "w") as f:
            f.write("# A.N.N. Auth Service Configuration\n")

    updated = 0
    for key, val in payload.items():
        if key in ACCEPTED_KEYS and val:
            set_key(env_path, key, val)
            os.environ[key] = val
            updated += 1

    return {"message": f"Successfully updated {updated} API Keys.", "status": "success"}

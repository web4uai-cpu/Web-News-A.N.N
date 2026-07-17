"""Broadcast script read endpoints."""

from fastapi import APIRouter, HTTPException, Query

from core import runtime
from models.schemas import BroadcastScript

router = APIRouter()


@router.get("/api/v1/scripts", response_model=list[BroadcastScript], tags=["Scripts"])
async def list_scripts(limit: int = Query(20, ge=1, le=100)):
    """List all generated broadcast scripts."""
    return runtime.sorted_scripts()[:limit]


@router.get("/api/v1/scripts/latest", tags=["Scripts"])
async def latest_headlines(limit: int = Query(10, ge=1, le=30)):
    """Get latest headlines for the breaking news ticker."""
    return [
        {
            "id": s.id,
            "headline": s.headline,
            "category": s.category,
            "created_at": s.created_at,
        }
        for s in runtime.sorted_scripts()[:limit]
    ]


@router.get("/api/v1/scripts/{script_id}", response_model=BroadcastScript, tags=["Scripts"])
async def get_script(script_id: str):
    """Get a specific script by ID."""
    script = runtime.script_store.get(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found.")
    return script

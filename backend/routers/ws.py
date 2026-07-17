"""WebSocket routes — real-time breaking-news stream (B2B key gated)."""

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from services.auth import get_client_by_key
from services.realtime import ws_manager

router = APIRouter()


@router.websocket("/ws/breaking-news")
async def breaking_news_stream(websocket: WebSocket, api_key: str = Query(None)):
    """
    Real-time WebSocket connection.
    Connects frontend clients instantly to the pipeline pulse without reloading.
    REQUIRES an active B2B API Key or it will silently kill the connection.
    """
    if not api_key:
        await websocket.close(code=1008, reason="Missing API Authentication.")
        return

    client = await get_client_by_key(api_key)
    if not client or not client.is_active:
        await websocket.close(code=1008, reason="Invalid or Suspended API Key.")
        return

    await ws_manager.connect(websocket)
    try:
        while True:
            # Idle wait; server pushes explicitly
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

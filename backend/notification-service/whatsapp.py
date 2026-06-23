"""
WhatsApp Business API — sends news to WhatsApp channels via Cloud API.
Uses pre-approved message templates for broadcast compliance.
"""

import httpx
from config import get_settings

WHATSAPP_API = "https://graph.facebook.com/v19.0"


async def send_template_message(
    headline: str,
    category: str,
    news_url: str,
    language_code: str = "en_US",
) -> dict:
    """
    Send a pre-approved template message to WhatsApp channel subscribers.

    Template must be pre-registered with Meta as "ann_breaking_news" with parameters:
    - {{1}} = headline
    - {{2}} = category
    - {{3}} = news_url
    """
    settings = get_settings()
    wa_token = getattr(settings, "whatsapp_token", "")
    wa_phone_id = getattr(settings, "whatsapp_phone_id", "")
    wa_channel_id = getattr(settings, "whatsapp_channel_id", "")

    if not wa_token or not wa_phone_id:
        return {"status": "skipped", "platform": "whatsapp", "reason": "Not configured"}

    payload = {
        "messaging_product": "whatsapp",
        "to": wa_channel_id,
        "type": "template",
        "template": {
            "name": "ann_breaking_news",
            "language": {"code": language_code},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": headline[:200]},
                        {"type": "text", "text": category.title()},
                        {"type": "text", "text": news_url},
                    ],
                },
            ],
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                f"{WHATSAPP_API}/{wa_phone_id}/messages",
                headers={
                    "Authorization": f"Bearer {wa_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

            if r.status_code == 200:
                msg_id = r.json().get("messages", [{}])[0].get("id", "")
                return {"status": "sent", "platform": "whatsapp", "message_id": msg_id}
            else:
                return {"status": "failed", "platform": "whatsapp", "error": r.text[:200]}

    except Exception as e:
        return {"status": "error", "platform": "whatsapp", "error": str(e)}


async def send_text_message(phone_number: str, text: str) -> dict:
    """Send a direct text message to a specific number (for B2B alerts)."""
    settings = get_settings()
    wa_token = getattr(settings, "whatsapp_token", "")
    wa_phone_id = getattr(settings, "whatsapp_phone_id", "")

    if not wa_token or not wa_phone_id:
        return {"status": "skipped"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{WHATSAPP_API}/{wa_phone_id}/messages",
                headers={
                    "Authorization": f"Bearer {wa_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "messaging_product": "whatsapp",
                    "to": phone_number,
                    "type": "text",
                    "text": {"body": text[:4096]},
                },
            )
            return {"status": "sent" if r.status_code == 200 else "failed"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

"""
Telegram Bot — posts formatted news to Telegram channels.
Uses Telegram Bot API for channel broadcasting.
"""

import httpx
from config import get_settings

TELEGRAM_API = "https://api.telegram.org"


async def send_message(
    headline: str,
    excerpt: str,
    category: str,
    news_url: str,
    audio_url: str | None = None,
    video_url: str | None = None,
) -> dict:
    """Send a formatted news message to the Telegram channel."""
    settings = get_settings()
    bot_token = getattr(settings, "telegram_bot_token", "")
    channel_id = getattr(settings, "telegram_channel_id", "")

    if not bot_token or not channel_id:
        return {"status": "skipped", "platform": "telegram", "reason": "Not configured"}

    emoji_map = {
        "technology": "💻", "finance": "📈", "politics": "🏛️", "business": "💼",
        "health": "🏥", "science": "🔬", "sports": "⚽", "entertainment": "🎬",
        "geopolitics": "🌍", "general": "📰",
    }
    emoji = emoji_map.get(category, "📰")

    message = (
        f"{emoji} *{_escape_md(headline)}*\n\n"
        f"{_escape_md(excerpt[:500])}\n\n"
        f"📂 `{category.upper()}`\n"
        f"🔗 [Read Full Story]({news_url})\n\n"
        f"_🤖 A\\.N\\.N\\. — AI News Network_"
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Send text message
            r = await client.post(
                f"{TELEGRAM_API}/bot{bot_token}/sendMessage",
                json={
                    "chat_id": channel_id,
                    "text": message,
                    "parse_mode": "MarkdownV2",
                    "disable_web_page_preview": False,
                },
            )

            if r.status_code == 200:
                msg_id = r.json().get("result", {}).get("message_id", "")

                # Send audio if available
                if audio_url:
                    await client.post(
                        f"{TELEGRAM_API}/bot{bot_token}/sendAudio",
                        json={
                            "chat_id": channel_id,
                            "audio": audio_url,
                            "caption": f"🎙️ {headline} — AI Broadcast",
                            "reply_to_message_id": msg_id,
                        },
                    )

                # Send video if available
                if video_url:
                    await client.post(
                        f"{TELEGRAM_API}/bot{bot_token}/sendVideo",
                        json={
                            "chat_id": channel_id,
                            "video": video_url,
                            "caption": f"📺 {headline} — AI Anchor Broadcast",
                            "reply_to_message_id": msg_id,
                        },
                    )

                return {"status": "posted", "platform": "telegram", "message_id": msg_id}
            else:
                return {"status": "failed", "platform": "telegram", "error": r.text[:200]}

    except Exception as e:
        return {"status": "error", "platform": "telegram", "error": str(e)}


async def send_breaking_alert(headline: str, news_url: str) -> dict:
    """Send a breaking news alert with a notification sound."""
    settings = get_settings()
    bot_token = getattr(settings, "telegram_bot_token", "")
    channel_id = getattr(settings, "telegram_channel_id", "")

    if not bot_token or not channel_id:
        return {"status": "skipped"}

    message = (
        f"🚨 *BREAKING NEWS* 🚨\n\n"
        f"*{_escape_md(headline)}*\n\n"
        f"🔗 [Read Now]({news_url})\n\n"
        f"_A\\.N\\.N\\. — AI News Network_"
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{TELEGRAM_API}/bot{bot_token}/sendMessage",
                json={
                    "chat_id": channel_id,
                    "text": message,
                    "parse_mode": "MarkdownV2",
                    "disable_notification": False,
                },
            )
            return {"status": "sent" if r.status_code == 200 else "failed"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _escape_md(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    special = r"_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in text)

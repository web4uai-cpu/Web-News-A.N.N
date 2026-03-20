"""
A.N.N. Instagram Auto-Poster
Posts generated news as image cards to Instagram via Meta Graph API.
Generates branded share cards from headlines.
"""

import httpx
from PIL import Image, ImageDraw, ImageFont
import io
import os
import base64
from utils.logger import get_logger
from config import get_settings

log = get_logger("social.instagram")


class InstagramPoster:
    """Post branded news cards to Instagram."""

    GRAPH_API = "https://graph.facebook.com/v19.0"

    def __init__(self):
        settings = get_settings()
        self.access_token = settings.instagram_access_token
        self.account_id = settings.instagram_account_id
        self.enabled = bool(self.access_token and self.account_id)
        self.output_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "output", "social"
        )
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_share_card(
        self,
        headline: str,
        category: str = "NEWS",
        script_id: str = "",
    ) -> str:
        """
        Generate a branded 1080x1080 news card image for Instagram.

        Returns:
            Path to the saved image file.
        """
        width, height = 1080, 1080

        # Create image with dark gradient background
        img = Image.new("RGB", (width, height), color=(8, 8, 16))
        draw = ImageDraw.Draw(img)

        # Background gradient effect (via rectangles)
        for y in range(height):
            r = int(8 + (20 - 8) * (y / height))
            g = int(8 + (10 - 8) * (y / height))
            b = int(16 + (35 - 16) * (y / height))
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Red accent bar at top
        draw.rectangle([(0, 0), (width, 6)], fill=(229, 62, 62))

        # Category badge
        draw.rectangle([(60, 80), (60 + len(category) * 18 + 30, 120)], fill=(229, 62, 62))

        # Try to use a system font, fallback to default
        try:
            font_large = ImageFont.truetype("arial.ttf", 52)
            font_medium = ImageFont.truetype("arial.ttf", 28)
            font_small = ImageFont.truetype("arial.ttf", 20)
            font_cat = ImageFont.truetype("arialbd.ttf", 18)
        except (OSError, IOError):
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_cat = ImageFont.load_default()

        # Category text
        draw.text((75, 87), category.upper(), fill="white", font=font_cat)

        # Headline text with word wrapping
        max_chars_per_line = 22
        words = headline.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line + " " + word) <= max_chars_per_line:
                current_line = (current_line + " " + word).strip()
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        # Draw headline lines
        y_pos = 180
        for line in lines[:5]:  # Max 5 lines
            draw.text((60, y_pos), line, fill="white", font=font_large)
            y_pos += 68

        # Divider line
        draw.line([(60, y_pos + 30), (width - 60, y_pos + 30)], fill=(99, 102, 241), width=2)

        # A.N.N. branding at bottom
        draw.rectangle([(0, height - 100), (width, height)], fill=(14, 14, 26))
        draw.text((60, height - 75), "📺 A.N.N. — AI News Network", fill=(160, 160, 184), font=font_medium)
        draw.text((60, height - 40), "Powered by Artificial Intelligence", fill=(96, 96, 120), font=font_small)

        # Red accent bar at bottom
        draw.rectangle([(0, height - 4), (width, height)], fill=(229, 62, 62))

        # Save
        filename = f"card_{script_id or 'preview'}.png"
        filepath = os.path.join(self.output_dir, filename)
        img.save(filepath, "PNG", quality=95)
        log.info("share_card_created", path=filepath)
        return filepath

    async def post_to_instagram(
        self,
        headline: str,
        category: str = "NEWS",
        script_id: str = "",
        image_url: str = "",
    ) -> dict:
        """
        Post a branded news card to Instagram.

        Note: Instagram Graph API requires the image to be publicly accessible
        via URL. For local dev, you'd need to upload to a CDN first.

        Args:
            headline: News headline for the caption.
            category: Category for context.
            script_id: Script ID for tracking.
            image_url: Publicly accessible image URL.

        Returns:
            Instagram API response or status dict.
        """
        if not self.enabled:
            log.warning("instagram_disabled", reason="No IG credentials configured")
            return {"status": "skipped", "reason": "Instagram not configured"}

        if not image_url:
            # Generate the card locally (for preview/logging)
            card_path = self.generate_share_card(headline, category, script_id)
            return {
                "status": "card_generated",
                "platform": "instagram",
                "card_path": card_path,
                "note": "Upload card to CDN, then provide image_url for posting",
            }

        # Build caption
        caption = (
            f"🔴 BREAKING NEWS\n\n"
            f"{headline}\n\n"
            f"#{category.title().replace(' ', '')} "
            f"#ANN #AINewsNetwork #BreakingNews #News"
        )

        try:
            async with httpx.AsyncClient() as client:
                # Step 1: Create media container
                container_res = await client.post(
                    f"{self.GRAPH_API}/{self.account_id}/media",
                    data={
                        "image_url": image_url,
                        "caption": caption,
                        "access_token": self.access_token,
                    },
                    timeout=15.0,
                )

                if container_res.status_code != 200:
                    return {
                        "status": "failed",
                        "platform": "instagram",
                        "step": "container",
                        "error": container_res.text[:200],
                    }

                container_id = container_res.json().get("id")

                # Step 2: Publish the container
                publish_res = await client.post(
                    f"{self.GRAPH_API}/{self.account_id}/media_publish",
                    data={
                        "creation_id": container_id,
                        "access_token": self.access_token,
                    },
                    timeout=15.0,
                )

                if publish_res.status_code == 200:
                    media_id = publish_res.json().get("id")
                    log.info("instagram_posted", media_id=media_id)
                    return {
                        "status": "posted",
                        "platform": "instagram",
                        "media_id": media_id,
                    }
                else:
                    return {
                        "status": "failed",
                        "platform": "instagram",
                        "step": "publish",
                        "error": publish_res.text[:200],
                    }

        except Exception as e:
            log.error("instagram_exception", error=str(e))
            return {"status": "error", "platform": "instagram", "error": str(e)}

"""
RSS, Atom, and JSON feed generation — extracted from monolith.
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from xml.dom import minidom


def generate_rss(scripts: list[dict], base_url: str, category: str | None = None) -> str:
    ET.register_namespace("atom", "http://www.w3.org/2005/Atom")
    ET.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
    ET.register_namespace("content", "http://purl.org/rss/1.0/modules/content/")

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    title = f"A.N.N. — AI News Network{' — ' + category.title() if category else ''}"
    ET.SubElement(channel, "title").text = title
    ET.SubElement(channel, "link").text = f"{base_url}/news"
    ET.SubElement(channel, "description").text = "AI-powered autonomous news broadcasts"
    ET.SubElement(channel, "language").text = "en"
    ET.SubElement(channel, "generator").text = "A.N.N. Article Service v1.0"
    ET.SubElement(channel, "lastBuildDate").text = _rfc822_now()
    ET.SubElement(channel, "ttl").text = "15"

    for s in scripts:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = s["headline"]
        ET.SubElement(item, "link").text = f"{base_url}/news#script-{s['id']}"
        ET.SubElement(item, "guid", isPermaLink="false").text = f"ann-{s['id']}"
        ET.SubElement(item, "pubDate").text = _rfc822(s["created_at"])
        ET.SubElement(item, "category").text = s.get("category", "general").title()
        excerpt = s.get("english_script", "").replace("[PAUSE]", "").strip()[:500]
        ET.SubElement(item, "description").text = excerpt

    return _prettify(rss)


def generate_atom(scripts: list[dict], base_url: str, category: str | None = None) -> str:
    ns = "http://www.w3.org/2005/Atom"
    ET.register_namespace("", ns)
    feed = ET.Element(f"{{{ns}}}feed")

    title = f"A.N.N. — AI News Network{' — ' + category.title() if category else ''}"
    ET.SubElement(feed, f"{{{ns}}}title").text = title
    ET.SubElement(feed, f"{{{ns}}}id").text = f"{base_url}/feed/atom"
    ET.SubElement(feed, f"{{{ns}}}updated").text = datetime.now(timezone.utc).isoformat()

    author = ET.SubElement(feed, f"{{{ns}}}author")
    ET.SubElement(author, f"{{{ns}}}name").text = "A.N.N. AI News Network"

    for s in scripts:
        entry = ET.SubElement(feed, f"{{{ns}}}entry")
        ET.SubElement(entry, f"{{{ns}}}title").text = s["headline"]
        ET.SubElement(entry, f"{{{ns}}}id").text = f"urn:ann:script:{s['id']}"
        ET.SubElement(entry, f"{{{ns}}}updated").text = _iso(s["created_at"])
        link = ET.SubElement(entry, f"{{{ns}}}link")
        link.set("href", f"{base_url}/news#script-{s['id']}")
        excerpt = s.get("english_script", "").replace("[PAUSE]", "").strip()[:300]
        ET.SubElement(entry, f"{{{ns}}}summary").text = excerpt

    return _prettify(feed)


def generate_json_feed(scripts: list[dict], base_url: str, category: str | None = None) -> dict:
    items = []
    for s in scripts:
        items.append({
            "id": s["id"],
            "title": s["headline"],
            "url": f"{base_url}/news#script-{s['id']}",
            "content_text": s.get("english_script", ""),
            "content_hindi": s.get("hindi_script", ""),
            "summary": s.get("english_script", "").replace("[PAUSE]", "")[:300],
            "date_published": s["created_at"] if isinstance(s["created_at"], str) else s["created_at"].isoformat(),
            "tags": [s.get("category", "general")],
            "_ann": {
                "word_count_en": s.get("word_count_en", 0),
                "word_count_hi": s.get("word_count_hi", 0),
                "duration_seconds": s.get("estimated_duration_seconds", 0),
            },
        })

    return {
        "version": "https://jsonfeed.org/version/1.1",
        "title": "A.N.N. — AI News Network",
        "home_page_url": f"{base_url}/news",
        "feed_url": f"{base_url}/feed/json",
        "description": "AI-powered autonomous news broadcasts",
        "items": items,
    }


def _rfc822(dt) -> str:
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%a, %d %b %Y %H:%M:%S %z")

def _rfc822_now() -> str:
    return _rfc822(datetime.now(timezone.utc))

def _iso(dt) -> str:
    if isinstance(dt, str):
        return dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

def _prettify(element: ET.Element) -> str:
    rough = ET.tostring(element, encoding="unicode", xml_declaration=True)
    try:
        return minidom.parseString(rough).toprettyxml(indent="  ")
    except Exception:
        return rough

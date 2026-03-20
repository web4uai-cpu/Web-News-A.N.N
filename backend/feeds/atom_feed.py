"""
A.N.N. Atom Feed Generator
Generates Atom 1.0 XML feeds for modern feed readers and aggregators.
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from xml.dom import minidom
from models.schemas import BroadcastScript


def generate_atom_feed(
    scripts: list[BroadcastScript],
    base_url: str = "http://localhost:8000",
    title: str = "A.N.N. — AI News Network",
    subtitle: str = "AI-powered autonomous news broadcasts",
    category: str | None = None,
) -> str:
    """
    Generate a valid Atom 1.0 XML feed.

    Args:
        scripts: List of broadcast scripts.
        base_url: Public server URL.
        title: Feed title.
        subtitle: Feed subtitle.
        category: Optional category filter.

    Returns:
        Valid Atom 1.0 XML string.
    """
    ns = "http://www.w3.org/2005/Atom"
    ET.register_namespace("", ns)

    feed = ET.Element(f"{{{ns}}}feed")

    # Feed metadata
    feed_title = f"{title} — {category.title()}" if category else title
    ET.SubElement(feed, f"{{{ns}}}title").text = feed_title
    ET.SubElement(feed, f"{{{ns}}}subtitle").text = subtitle
    ET.SubElement(feed, f"{{{ns}}}id").text = f"{base_url}/feed/atom"
    ET.SubElement(feed, f"{{{ns}}}updated").text = _iso8601_now()
    ET.SubElement(feed, f"{{{ns}}}generator", uri=base_url, version="1.0").text = (
        "A.N.N. AI News Network"
    )
    ET.SubElement(feed, f"{{{ns}}}rights").text = (
        f"© {datetime.now().year} A.N.N. AI News Network"
    )

    # Links
    feed_url = f"{base_url}/feed/atom"
    if category:
        feed_url += f"?category={category}"

    self_link = ET.SubElement(feed, f"{{{ns}}}link")
    self_link.set("href", feed_url)
    self_link.set("rel", "self")
    self_link.set("type", "application/atom+xml")

    alt_link = ET.SubElement(feed, f"{{{ns}}}link")
    alt_link.set("href", f"{base_url}/news")
    alt_link.set("rel", "alternate")
    alt_link.set("type", "text/html")

    # Author
    author = ET.SubElement(feed, f"{{{ns}}}author")
    ET.SubElement(author, f"{{{ns}}}name").text = "A.N.N. AI News Network"
    ET.SubElement(author, f"{{{ns}}}uri").text = base_url

    # Entries
    for script in scripts:
        entry = ET.SubElement(feed, f"{{{ns}}}entry")
        ET.SubElement(entry, f"{{{ns}}}title").text = script.headline
        ET.SubElement(entry, f"{{{ns}}}id").text = f"urn:ann:script:{script.id}"
        ET.SubElement(entry, f"{{{ns}}}updated").text = _iso8601(script.created_at)
        ET.SubElement(entry, f"{{{ns}}}published").text = _iso8601(script.created_at)

        link = ET.SubElement(entry, f"{{{ns}}}link")
        link.set("href", f"{base_url}/news#script-{script.id}")
        link.set("rel", "alternate")

        cat = ET.SubElement(entry, f"{{{ns}}}category")
        cat.set("term", script.category.value)
        cat.set("label", script.category.value.title())

        # Summary
        excerpt = script.english_script.replace("[PAUSE]", "").strip()[:300]
        ET.SubElement(entry, f"{{{ns}}}summary").text = excerpt

        # Full content
        content_html = (
            f"<h2>{_esc(script.headline)}</h2>"
            f"<p>{_esc(script.english_script)}</p>"
            f"<hr/><p><strong>हिन्दी:</strong> {_esc(script.hindi_script)}</p>"
        )
        content_el = ET.SubElement(entry, f"{{{ns}}}content")
        content_el.set("type", "html")
        content_el.text = content_html

    return _prettify(feed)


def _iso8601(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _iso8601_now() -> str:
    return _iso8601(datetime.now(timezone.utc))


def _esc(text: str) -> str:
    if not text:
        return ""
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def _prettify(element: ET.Element) -> str:
    rough = ET.tostring(element, encoding="unicode", xml_declaration=True)
    try:
        dom = minidom.parseString(rough)
        return dom.toprettyxml(indent="  ")
    except Exception:
        return rough

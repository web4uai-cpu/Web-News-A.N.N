from models.schemas import BroadcastScript, NewsCategory
from feeds.rss_feed import generate_rss_feed
from feeds.atom_feed import generate_atom_feed
from datetime import datetime, timezone

def test_feeds():
    print("Testing RSS and Atom feed generation...")

    script = BroadcastScript(
        headline="AI Revolutionizes News",
        english_script="A brand new AI has taken over the news. [PAUSE] It is incredible.",
        hindi_script="एक बिल्कुल नए एआई ने खबर पर कब्जा कर लिया है। [PAUSE] यह अविश्वसनीय है।",
        translations={"Hindi": "एक बिल्कुल नए एआई ने खबर पर कब्जा कर लिया है। [PAUSE] यह अविश्वसनीय है।"},
        category=NewsCategory.TECHNOLOGY,
        source_url="https://example.com",
    )
    # Set explicit datetime for testing
    script.created_at = datetime.now(timezone.utc)

    rss_xml = generate_rss_feed([script])
    print("RSS Feed Result:")
    print(rss_xml[:300].encode('utf-8', errors='replace').decode('utf-8') + "...\n")

    atom_xml = generate_atom_feed([script])
    print("Atom Feed Result:")
    print(atom_xml[:300].encode('utf-8', errors='replace').decode('utf-8') + "...\n")

    print("SUCCESS: Feeds generated without exceptions!")

if __name__ == "__main__":
    test_feeds()

import asyncio
from social.instagram_poster import InstagramPoster

def test_card():
    poster = InstagramPoster()
    # Mocking disabled API, just generating local card
    card_path = poster.generate_share_card(
        headline="AI Model Breaks Benchmarks, Researchers Puzzled Over Sudden Improvement",
        category="TECHNOLOGY",
        script_id="test-card-123"
    )
    print(f"Card successfully generated at: {card_path}")

if __name__ == "__main__":
    test_card()

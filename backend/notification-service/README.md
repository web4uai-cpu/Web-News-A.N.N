# Notification Service

Manages all outbound notifications and social media publishing.

## Responsibilities
- Social media auto-posting (Twitter/X, Facebook, Instagram)
- Telegram and WhatsApp channel distribution
- Push notifications (web + mobile)
- Email alerts for B2B clients
- Webhook delivery for enterprise integrations

## Tech
- FastAPI
- Celery + Redis for async delivery
- Platform-specific SDKs (Tweepy, Facebook Graph API, etc.)

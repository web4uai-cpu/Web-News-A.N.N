# Video Service

Handles all media production: TTS audio generation and avatar video generation.

## Responsibilities
- ElevenLabs TTS voice synthesis (EN + HI)
- HeyGen avatar video generation
- Thumbnail generation
- Media asset storage and CDN URLs
- Generation job queue and status tracking

## Tech
- FastAPI
- Celery + Redis for async generation
- ElevenLabs API, HeyGen API

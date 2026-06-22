# Article Service

Manages the article lifecycle: ingestion, storage, retrieval, and CRUD operations.

## Responsibilities
- Article CRUD (create, read, update, delete)
- Script storage and versioning (EN + HI)
- Category tagging and metadata
- Full-text search indexing
- RSS/Atom feed generation

## Tech
- FastAPI
- Supabase (Postgres) + SQLAlchemy
- Alembic migrations

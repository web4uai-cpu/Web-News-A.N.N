# Backend service directories — status

The deployable application is the **modular monolith**: `backend/main.py` + `backend/routers/`.

The sibling service directories (`api-gateway/`, `auth-service/`, `article-service/`,
`video-service/`, `analytics-service/`, `search-service/`, `notification-service/`)
are **dormant future extraction targets**. Each is an independently coded FastAPI app
with its own Dockerfile, but they largely duplicate monolith logic and the monolith does
not call them. As of the enterprise-hardening pass they are **not deployed** — the
Railway project runs only `ann-backend` + Postgres + Redis. Do not add features there
first — implement in the monolith, and extract a service only when load or team
boundaries justify it.

The monolith's live connections are exactly three, all health-verified at
`/health` (liveness, always 200 with a per-dependency `services` map) and
`/health/ready` (readiness, 503 if Postgres is down): **Postgres** (Alembic-managed —
see below), **Redis** (fastapi-cache2 + Celery broker/backend + pub/sub → WebSocket),
and **external vendor APIs** (egress only).

## Schema is Alembic-managed (Postgres)

`models/b2b_database.py:init_db()` runs Alembic on startup for Postgres: it stamps a
pre-existing un-stamped schema to `head`, then `upgrade head`. Dev SQLite still uses
`create_all`. **Never hand-edit the schema or add ad-hoc `ALTER TABLE` — change a model,
then `alembic revision --autogenerate -m "..."` and commit the migration.**

Known gaps in the dormant services: duplicated demo seed data, duplicated
`ClientAPIKey` model, and the api-gateway WebSocket proxy is incomplete.

## Running the stacks

- **Default (monolith)**: `docker compose up` — ann-backend (:8080→8000) + redis +
  celery + prometheus + grafana. Security env passthrough: `ENV`, `ADMIN_SECRET`,
  `CORS_ORIGINS`, `FIREBASE_PROJECT_ID` (host env or `.env`).
- **Microservices (opt-in)**: `docker compose --profile services up` adds the
  gateway (:8000) and the 6 services.
- **Kubernetes**: `infrastructure/kubernetes/ann-backend.yaml` is the primary
  Deployment (+Service+HPA); `services.yaml` holds the extraction-target services.
  CI builds/pushes `ann-backend` alongside the service images and deploys all to staging.

## Extraction path (when a service graduates)

1. The service owns its data: give it real tables/migrations, delete the duplicated
   models, and stop reading the monolith's DB.
2. Point the monolith at it: swap the in-process import for an HTTP call, adding a
   `<name>_service_url` setting to `backend/config.py` (the old speculative
   `*_SERVICE_URL` settings were removed — add them back per-service as you extract).
3. Route it: deploy the service on Railway, enable the path prefix in
   `api-gateway/routes` so external traffic bypasses the monolith.
4. Delete the corresponding router from `backend/routers/` once traffic is fully cut over.
Extract only when load or team boundaries justify it — never speculatively.

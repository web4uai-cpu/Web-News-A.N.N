# Backend service directories — status

The deployable application is the **modular monolith**: `backend/main.py` + `backend/routers/`.

The sibling service directories (`api-gateway/`, `auth-service/`, `article-service/`,
`video-service/`, `analytics-service/`, `search-service/`, `notification-service/`)
are **future extraction targets**. Each is an independently coded FastAPI app with its
own Dockerfile, but they largely duplicate monolith logic and the monolith does not
call them. Do not add features there first — implement in the monolith, and extract a
service only when load or team boundaries justify it.

Known gaps in the parallel services: duplicated demo seed data, duplicated
`ClientAPIKey` model, and the api-gateway WebSocket proxy is incomplete.

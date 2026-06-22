# API Gateway

Central entry point for all client requests. Routes traffic to backend microservices.

## Responsibilities
- Request routing and load balancing
- Rate limiting and throttling
- Authentication token validation
- API versioning
- Request/response transformation
- CORS management

## Tech
- FastAPI / Kong / Traefik (TBD)
- Redis for rate limit state

## Ports
- `8000` — public API

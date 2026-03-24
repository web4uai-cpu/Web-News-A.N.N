# A.N.N. Enterprise Architecture Blueprint

This document outlines the target 4-Phase Enterprise Architecture for the AI News Network (A.N.N.) platform, ensuring high availability, peak performance, and infinite scalability.

## Current State overview
The application is built on:
- **FastAPI** (High-performance Python web framework)
- **SQLAlchemy / Alembic** (Database ORM and migrations)
- **Celery** (Distributed task queue)
- **FastAPI Cache** (In-memory / Redis caching)

Currently, the system is capable of running locally but needs robust infrastructure to achieve true enterprise scale.

---

## 🚀 Phase 1: Performance & Background Processing (Current Focus)

**Goal:** Offload heavy processing from the main web server and cache frequent requests.

1. **Redis Cache Layer:**
   - Deploy a Redis instance.
   - Configure `REDIS_URL` in the `.env` file.
   - FastAPI will automatically switch from `InMemoryBackend` to `RedisBackend` for caching API responses (e.g., `/feed/json`).

2. **Celery Task Queue:**
   - Run a dedicated Celery worker process.
   - Use Redis as the message broker.
   - Offload NewsAPI, AlphaVantage, and GDELT ingestion/processing pipelines, as well as B2B Studio generations, to the background worker.

---

## 📊 Phase 2: Observability & Health Monitoring

**Goal:** Real-time insights into system health.

1. **Prometheus Metrics:**
   - Instrument FastAPI with `prometheus-fastapi-instrumentator`.
   - Track request latency, error rates, and active database connections.

2. **Grafana Dashboards:**
   - Connect Grafana to Prometheus.
   - Create custom dashboards for:
     - API Gateway Health (Requests per second, latency)
     - Celery Queue Depth (How many articles are pending generation)
     - Stripe B2B Revenue metrics

---

## 🚢 Phase 3: Orchestration & Infinite Scale

**Goal:** Zero-downtime deployments and auto-scaling.

1. **Docker Containerization:**
   - Finalize `Dockerfile` for the FastAPI backend, Celery worker, and Frontend.

2. **Kubernetes (K8s) Cluster:**
   - Deploy the containers into a managed K8s cluster (e.g., EKS, GKE, or AKS).
   - Use a **Load Balancer** to route incoming traffic across multiple FastAPI pods.

---

## 💾 Phase 4: High-Availability Data Layer

**Goal:** Ensure the database is never the bottleneck.

1. **Clustered DBMS:**
   - Migrate from local/single-instance databases to a highly available cluster natively supporting replication (e.g., Postgres Multi-AZ or Supabase clustered).
   - Implement read-replicas so that dashboard queries and feed reads do not block transactional B2B API key operations.

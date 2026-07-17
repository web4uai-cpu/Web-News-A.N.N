---
name: security-audit
description: Run the A.N.N. security checklist against the backend. Use when asked to audit, review security, or before a release.
---

# Security audit checklist

Grep-driven checks (all should come back clean):

1. **No default admin secrets**: `grep -r "superadmin" backend/` → only docs may mention it historically.
2. **No CORS wildcard**: `grep -rn 'allow_origins=\["\*"\]' backend/` → zero hits; origins must come from `CORS_ORIGINS`.
3. **Admin gating**: every route under `/api/v1/admin/` depends on `require_admin` (`backend/core/security.py`).
4. **Cost-endpoint gating**: `/api/v1/ingest/*`, `/api/v1/pipeline/*` (run + orchestrator), `/api/v1/media/*`, `/api/v1/process_news` depend on `require_pipeline_access`.
5. **Key hashing**: `ClientAPIKey.api_key` rows are SHA-256 hashes; no endpoint returns full keys after creation; listings show `key_prefix` only.
6. **Demo key**: `ann_demo_key_777` seeded only when `ENV=development` (`backend/models/b2b_database.py`).
7. **No live secrets tracked**: `git ls-files | grep -i env` → only `.env.example` / `.env.railway` templates with placeholders.
8. **Frontend**: no API keys in client code; only `NEXT_PUBLIC_*` values; admin token entered by the user, never hardcoded.

Also run `pip audit` / `npm audit` for dependency CVEs and check `docs/SECURITY.md` is current.

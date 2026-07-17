---
name: run-frontend
description: Start the A.N.N. Next.js frontend locally or build it for production. Use when asked to run, build, or verify the web frontend.
---

# Run the frontend

```powershell
cd frontend/web
npm install                # first time only
npm run dev                # http://localhost:3000
npm run build              # production build check
```

Notes:
- Backend URL comes from `NEXT_PUBLIC_API_URL` (defaults to http://localhost:8000) — run the backend first for live data; components fall back to typed demo data when the API is offline.
- Auth is Firebase: `NEXT_PUBLIC_FIREBASE_*` vars in `frontend/web/.env.local` (gitignored).
- Pages: `/` home, `/dashboard`, `/news`, `/portal`.

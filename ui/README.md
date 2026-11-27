# UI — Factory Maintenance Assistant

React + Vite + TypeScript + Tailwind v4.

- **Technician:** chat with the assistant, send a work-order draft for approval, track own work orders.
- **Foreman:** approval queue (high priority first, then oldest), approve / reject with a reason.

```bash
# backend (repo root)
uv run uvicorn app.api.main:app --port 8000
# frontend
cd ui && npm install && npm run dev   # http://localhost:5173
```

Vite proxies `/api/*` requests to `localhost:8000` (no CORS needed).
Identity is fake in v1 (`X-User` / `X-Role` headers); a real deployment uses SSO.

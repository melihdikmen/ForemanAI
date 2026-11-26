# UI — Fabrika Bakım Asistanı

React + Vite + TypeScript + Tailwind v4.

- **Teknisyen:** asistanla sohbet, iş emri taslağını "Onaya gönder", kendi iş emirlerini takip.
- **Ustabaşı:** onay kuyruğu (önce yüksek öncelik, sonra en eski), onayla / gerekçeyle reddet.

```bash
# backend (repo kökünde)
uv run uvicorn app.api.main:app --port 8000
# frontend
cd ui && npm install && npm run dev   # http://localhost:5173
```

Vite, `/api/*` isteklerini `localhost:8000`'e proxy'ler (CORS gerekmez).
Kimlik v1'de sahtedir (`X-User` / `X-Role` başlıkları); gerçek kurulumda SSO.

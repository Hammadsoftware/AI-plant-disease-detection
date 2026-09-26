# PlantAI web

A standalone Next.js App Router frontend for the Plant Disease Evidence API. This project is intentionally separate from the existing `frontend/` and `backend/` directories.

## Run locally

```bash
npm install
npm run dev
```

Open `http://localhost:3000` for the landing page or `http://localhost:3000/dashboard` for diagnosis.

## Environment

Only the public API base URL is used in the browser:

```dotenv
NEXT_PUBLIC_API_URL=https://plant-disease-api-1-0-0.onrender.com
```

No backend credentials belong in this project.

## Checks

```bash
npm run lint
npm run build
```

The browser posts `multipart/form-data` to the same-origin `/plant-api/diagnose` rewrite only after the user presses **Analyze Leaf**. Next.js forwards that request to the configured backend `/api/v1/diagnose`, avoiding browser CORS restrictions without adding another API implementation. Scan history is stored only in browser `localStorage`.

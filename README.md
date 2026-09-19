# React + TypeScript + Vite

> **🟢 已上线（2026-09-19）**
> **前端**：https://superdspliuyun.github.io/studypal/
> **后端**：https://studypal-backend-ekcp.onrender.com
> 部署日志：[`evidence/studypal-live.txt`](evidence/studypal-live.txt)

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend enabling type-aware lint rules by installing `oxlint-tsgolint` and editing `.oxlintrc.json`:

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "typescript", "oxc"],
  "options": {
    "typeAware": true
  },
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }]
  }
}
```

See the [Oxlint rules documentation](https://oxc.rs/docs/guide/usage/linter/rules) for the full list of rules and categories.

## Backend (StudyPal API)

The `backend/` directory holds the FastAPI + SQLite service that owns user accounts, JWT auth, and the user-profile read/write API. The frontend in `src/` does not consume it yet — wire-up is deferred to a later change via `VITE_API_BASE`.

### One-time setup

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # then edit JWT_SECRET
```

### Database migration

```bash
cd backend
alembic upgrade head
```

### Run the API

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Interactive docs: <http://localhost:8000/docs>. Health probe: <http://localhost:8000/healthz>.

### Run the tests

```bash
cd backend
pytest
```

### Endpoints

| Method | Path                  | Auth   | Purpose                                  |
|--------|-----------------------|--------|------------------------------------------|
| POST   | /api/auth/register    | none   | Create account, return access+refresh    |
| POST   | /api/auth/login       | none   | Exchange credentials for tokens          |
| POST   | /api/auth/refresh     | none*  | Exchange refresh token for new access    |
| GET    | /api/users/me         | Bearer | Read own profile                         |
| PATCH  | /api/users/me         | Bearer | Update own avatar                        |
| GET    | /static/avatars/...   | none   | Default avatar asset                     |
| GET    | /api/chat/sessions    | Bearer | List my chat sessions                    |
| POST   | /api/chat/sessions    | Bearer | Create a chat session                    |
| GET    | /api/chat/sessions/{id}/messages | Bearer | List messages in a session  |
| POST   | /api/chat/sessions/{id}/messages | Bearer | Send a user message (SSE stream)|
| GET    | /api/analytics/calendar     | Bearer | Per-day learning minutes (30/60/90/180) |
| GET    | /api/analytics/achievements | Bearer | Five achievement badges                  |

\* the refresh endpoint accepts a refresh token in the body, not an Authorization header.

### Frontend integration

Set `VITE_API_BASE` (e.g. `http://localhost:8000` for dev, `https://studypal-backend.onrender.com` for prod) in the frontend's `.env.local` and consume it via `fetch(${import.meta.env.VITE_API_BASE}/api/...)`.

## Deployment (Render)

The backend is configured for one-click deploy via `render.yaml` Blueprint.

### One-time setup

1. Create a new Render Blueprint from this repo (Render dashboard → "New" → "Blueprint").
2. Render reads `render.yaml` and proposes a `studypal-backend` web service (Docker, `backend/` rootDir, `/healthz` health check).
3. In the service's Environment tab, set:
   - `DATABASE_URL` → e.g. `sqlite:////var/data/studypal.db` (with a persistent disk mounted at `/var/data` on Render)
   - `JWT_SECRET` → a random ≥32-char string (Render can `generate` it)
   - `DEEPSEEK_API_KEY` → your real DeepSeek key
   - `CORS_ALLOW_ORIGINS` → `https://<your-username>.github.io,http://localhost:5173`
4. Click "Apply". Render builds the Docker image, runs `alembic upgrade head`, then starts `uvicorn`.

### CI

GitHub Actions workflow `.github/workflows/backend-deploy.yml` triggers a Render deploy hook on every push to `main` that touches `backend/**` or `render.yaml`. Add `RENDER_DEPLOY_HOOK_URL` to repo secrets to enable it. Without that secret, the workflow still validates `render.yaml` but skips the deploy trigger.

### Frontend

The frontend stays on GitHub Pages as before. After backend is live, set `VITE_API_BASE` in the frontend repo settings (or `.env.local`) and `npm run build && npm run deploy`.

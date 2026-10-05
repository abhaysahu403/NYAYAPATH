# NyayaPath backend (Django + DRF + PostgreSQL/pgvector)

Legal *information* and case-navigation API. Not legal advice. See STATUS.md for what is verified.

## Run
```bash
cp .env.example .env            # set SECRET_KEY, DATABASE_URL
createdb nyayapath && psql nyayapath -c 'CREATE EXTENSION vector'   # or use docker compose up db
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data          # DEMO data + demo@nyayapath.local / DemoPass#12345
python manage.py createsuperuser
python manage.py runserver
```
Docker: `docker compose up --build`. OCR needs tesseract (+ `hin` language data).

## API (all under /api/v1/)
Docs: `/api/v1/docs/` (Swagger), `/api/v1/schema/`. Responses: `{success, data, meta}` / `{success:false, error:{code,message}}`.
- auth: `auth/register|login|logout|profile|change-password|token/refresh/` (JWT Bearer)
- `ai/chat/` (guests allowed, rate limited), `ai/conversations/`, `ai/similar-cases/`, `ai/judgments/<id>/explain/`
- `judgments/search/` (paginated), `judgments/`, `judgments/<id>/`
- `cases/`, `cases/search/`, `cases/<id>/(timeline|hearings|parties)/`
- `documents/upload/`, `documents/<id>/(analyze|ask|reprocess|download-link)/`
- `action-plans/generate/`, `action-plans/<id>/steps/<step>/complete/`
- `drafts/(case-summary|lawyer-brief|rti)/`, `drafts/<id>/`; `courts/`, `sources/`, `audit-logs/` (admin)

## Commands
`seed_demo_data`, `ingest_judgments file.json [--mark-verified]`, `ingest_cases file.json --user-email`,
`generate_embeddings [--rebuild]`, `index_documents [--all]`, `verify_sources [--promote]` (demo is never promoted).

## AI provider
`AI_PROVIDER=mock` (offline, default) or `gemini` (set GEMINI_API_KEY). Tests/dev never need an API key.

## Run with Docker (backend + frontend + DB)
```
git clone https://github.com/abhaysahu403/NYAYAPATH.git && cd NYAYAPATH
docker compose up -d --build
```
Open `http://<host>/` (Caddy serves `frontend/` and proxies `/api/` to Django). Demo login is auto-seeded.
For real use: set `.env` (copy `.env.example`), `AI_PROVIDER=gemini`, `GEMINI_API_KEY`, a strong `SECRET_KEY`, explicit `ALLOWED_HOSTS`.

### HTTPS
Set `SITE_ADDRESS` in `.env` to a hostname pointing at the server (ports 80+443 open), e.g. `SITE_ADDRESS=1-2-3-4.sslip.io`.
Caddy fetches and renews a Let's Encrypt certificate automatically. Leave unset for plain HTTP on :80.

## Free hosting (Render + Neon + Vercel)
1. **Neon**: create a free project, copy the connection string (keep `?sslmode=require`). pgvector is enabled by the first migration.
2. **Render**: New → Blueprint → this repo. Set `DATABASE_URL` (Neon) and `GEMINI_API_KEY`. Service name `nyayapath-api` (else edit `frontend/vercel.json`).
3. **Vercel**: import this repo, Root Directory `frontend`, framework "Other". `/api/*` is proxied to Render by `vercel.json`.
Free Render sleeps after ~15 min idle (first request ~50s) and its disk is not persistent (uploads are lost on restart).

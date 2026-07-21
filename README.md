# ShineGold Backend — local setup

## 1. Environment

```powershell
cd backend
copy .env.example .env
```

Fill `.env` from **Supabase → Project Settings → Database** (connection strings) and **API → service role key**.

Required variables:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Transaction pooler, port **6543** |
| `DATABASE_URL_DIRECT` | Direct `db.<ref>.supabase.co` for Alembic |
| `SUPABASE_URL` | `https://<ref>.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Storage uploads |
| `SUPABASE_STORAGE_BUCKET` | `shinegold-media` |
| `JWT_SECRET_KEY` | Random secret for tokens |
| `SUPABASE_DB_REGION` | e.g. `ap-south-1` |
| `SUPABASE_POOLER_PREFIX` | `aws-1` or `aws-0` from dashboard |

## 2. One-command setup

```powershell
cd backend
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
```

This runs: `uv sync` → `alembic upgrade head` → seed admin + executives.

## 3. Start API

Use port **8080** so the Flutter app (`AppConfig.baseUrl`) can reach the API.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1
```

Or manually:

```powershell
uv run fastapi dev --port 8080
```

Health check: http://127.0.0.1:8080/health

If requests return **404** for new routes, an older API process may still be bound to port 8080. Stop it and restart the dev server.

## 4. Flutter app

The app defaults to `http://127.0.0.1:8080` (web/desktop). Override at build time if needed:

- **Android emulator:** `http://10.0.2.2:8080`
- **Physical device (same Wi‑Fi):** `http://<your-pc-ip>:8080` via `--dart-define=API_BASE_URL=...`

Set `useMockData = false` for live API.

## Default logins (after seed)

| Role | Employee ID | Password |
|------|-------------|----------|
| Super admin | `ADMIN001` | `ChangeMe123!` |
| Executive | `EXEC001` | `ChangeMe123!` |

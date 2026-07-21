# ShineGold

Field executive & admin app (Flutter) + FastAPI backend on Supabase.

## Quick start (local)

See [README backend setup](#shinegold-backend--local-setup) below for `.env`, migrations, and `uv run fastapi dev`.

Flutter app: `cd shinegold && flutter run` (defaults to local API on port 8000).

## Production deploy & APK

**Full guide:** [docs/DEPLOY.md](docs/DEPLOY.md)

1. **Backend on Render** — connect repo, apply `render.yaml`, set Supabase env vars, deploy.
2. **Health cron** — ping `https://YOUR-SERVICE.onrender.com/health` every 10 min (free tier).
3. **APK** — set Render URL in `shinegold/dart_defines/production.json`, then:
   ```powershell
   cd shinegold
   powershell -ExecutionPolicy Bypass -File scripts\build_apk.ps1
   ```
4. Share `shinegold/build/app/outputs/flutter-apk/app-release.apk` with testers.

---

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

From the **repo root** (matches how you normally run it):

```powershell
uv run --directory backend fastapi dev
```

Or:

```powershell
fastapi run backend
```

From `backend/`:

```powershell
uv run fastapi dev
```

Default URL: **http://127.0.0.1:8000** (FastAPI CLI default — same as Flutter `AppConfig.apiPort`).

Health check: http://127.0.0.1:8000/health

**Single port:** use **8000** only. If an old API is still on 8080, stop it or Flutter will hit stale data.

## 4. Flutter app

The app defaults to `http://127.0.0.1:8000` (web/desktop). Override at build time if needed:

- **Android emulator:** `http://10.0.2.2:8000`
- **Physical device (same Wi‑Fi):** `http://<your-pc-ip>:8000` via `--dart-define=API_BASE_URL=...`

Set `useMockData = false` for live API.

**Production APK:** use `scripts/build_apk.ps1` with your Render URL — see [docs/DEPLOY.md](docs/DEPLOY.md).

## Default logins (after seed)

| Role | Employee ID | Password |
|------|-------------|----------|
| Super admin | `ADMIN001` | `shinegold2026` |
| Executive | `EXEC001` | `ChangeMe123!` |

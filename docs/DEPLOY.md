# ShineGold — Production deployment

This guide covers deploying the **FastAPI backend to Render** and building a **production Android APK** that talks to it.

---

## 1. Deploy backend to Render

### Option A — Blueprint (recommended)

1. Push this repo to GitHub.
2. In [Render](https://render.com) → **New** → **Blueprint**.
3. Connect the repo and apply `render.yaml` at the repo root.
4. When prompted, fill in the secret env vars:
   - `DATABASE_URL` — Supabase transaction pooler (port **6543**)
   - `DATABASE_URL_DIRECT` — Supabase session pooler (port **5432**)
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
5. Deploy. Render runs `alembic upgrade head` before each deploy.

### Option B — Manual Web Service

| Setting | Value |
|---------|-------|
| Root directory | `backend` |
| Runtime | Python 3.12 |
| Build command | `pip install uv && uv sync --frozen --no-dev` |
| Pre-deploy command | `uv run alembic upgrade head` |
| Start command | `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health check path | `/health` |

Set `ENVIRONMENT=production` and all variables from `backend/.env.example`.

### After first deploy

1. Open `https://YOUR-SERVICE.onrender.com/health` — should return `{"status":"ok"}`.
2. **Seed users once** (from your machine, with production `.env` or Render shell):
   ```bash
   cd backend
   uv run python scripts/seed_admin.py
   uv run python scripts/seed_executives.py
   ```
3. Copy your public API URL — you need it for the APK build.

### Keep Render awake (free tier)

Free Render services sleep after ~15 minutes of inactivity. Use an external cron to ping `/health` every 10 minutes:

- [cron-job.org](https://cron-job.org) (free)
- URL: `https://YOUR-SERVICE.onrender.com/health`
- Schedule: every 10 minutes

---

## 2. Build production Android APK

### Prerequisites

- [Android Studio](https://developer.android.com/studio) installed (for Android SDK)
- `flutter doctor` shows Android toolchain as OK

### Configure API URL

After Render deploy, set your API URL:

**Option 1 — config file (recommended)**

```powershell
cd shinegold
copy dart_defines\production.json.example dart_defines\production.json
```

Edit `dart_defines/production.json`:

```json
{
  "API_BASE_URL": "https://YOUR-SERVICE.onrender.com",
  "PRODUCTION": "true"
}
```

Use **HTTPS** (Render provides this automatically). No trailing slash.

**Option 2 — pass URL on the command line**

```powershell
.\scripts\build_apk.ps1 -ApiBaseUrl "https://YOUR-SERVICE.onrender.com"
```

### Build

```powershell
cd shinegold
powershell -ExecutionPolicy Bypass -File scripts\build_apk.ps1
```

Output APK:

`shinegold/build/app/outputs/flutter-apk/app-release.apk`

### Share with testers

1. Upload `app-release.apk` to Google Drive / Dropbox / WhatsApp.
2. Recipient enables **Install unknown apps** for that app, then installs.
3. Share login credentials (after seeding).

---

## 3. Environment variables reference

| Variable | Required | Notes |
|----------|----------|-------|
| `DATABASE_URL` | Yes | Port 6543 (transaction pooler) |
| `DATABASE_URL_DIRECT` | Yes | Port 5432 (migrations) |
| `SUPABASE_URL` | Yes | `https://<ref>.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Storage uploads |
| `JWT_SECRET_KEY` | Yes | Long random string |
| `ENVIRONMENT` | Yes | `production` on Render |
| `SUPABASE_STORAGE_BUCKET` | No | Default `shinegold-media` |
| `SUPABASE_DB_REGION` | No | e.g. `ap-south-1` |
| `SUPABASE_POOLER_PREFIX` | No | `aws-1` or `aws-0` |

---

## 4. Troubleshooting

| Problem | Fix |
|---------|-----|
| APK can't reach API | Rebuild with correct `API_BASE_URL` (HTTPS, no trailing slash) |
| 502 on Render after deploy | Check Render logs; verify `DATABASE_URL` and migrations |
| First request slow (~30s) | Free tier cold start — use health cron |
| Login fails | Run seed scripts against production DB |
| Upload / voice notes fail | Check `SUPABASE_SERVICE_ROLE_KEY` and bucket name |

---

## 5. Default logins (after seed)

| Role | Employee ID | Password |
|------|-------------|----------|
| Super admin | `ADMIN001` | See `scripts/seed_admin.py` |
| Executive | `EXEC001` | See `scripts/seed_executives.py` |

Change passwords before wider distribution.

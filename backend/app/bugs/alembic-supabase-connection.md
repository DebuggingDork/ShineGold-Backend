# Bug: Alembic failed to connect to Supabase (`getaddrinfo failed` / `psycopg2` missing)

**Date:** 2025-06-25  
**Area:** `migrations/env.py`, `app/core/config.py`, `.env`  
**Symptom:** `uv run alembic revision --autogenerate` crashed before generating migrations.

## What went wrong

Three separate issues stacked on top of each other:

### 1. Wrong PostgreSQL driver (`ModuleNotFoundError: psycopg2`)

`DATABASE_URL_DIRECT` used `postgresql://…` (no `+asyncpg`). SQLAlchemy picked the sync **psycopg2** driver, which is not installed. The app uses **asyncpg**.

### 2. Invalid Supabase pooler hostname (`getaddrinfo failed`)

`.env` used a hostname like:

```
<project-ref>.pooler.supabase.com
```

That host **does not exist in DNS**. Supabase pooler URLs use a regional host:

```
aws-1-<region>.pooler.supabase.com
```

(e.g. `aws-1-ap-south-1.pooler.supabase.com`)

The pooler username must also be `postgres.<project-ref>`, not plain `postgres`.

### 3. Direct DB host unreachable on Windows (same `getaddrinfo failed`)

The direct host `db.<project-ref>.supabase.co` often resolves to **IPv6 only**. On Windows, Python’s `socket.getaddrinfo` frequently fails even when `nslookup` works. The regional pooler host resolves over **IPv4** and is reliable for Alembic.

### 4. Password with special characters (`InvalidPasswordError`)

The DB password contained `$` and `&`. In `.env` it must be URL-encoded (`%24`, `%26`). URLs must be built with `SQLAlchemy URL.create()` so the password is encoded once — manual string concatenation caused auth failures.

## How we fixed it

| Change | File |
|--------|------|
| Normalize `postgresql://` → `postgresql+asyncpg://` | `app/core/config.py` |
| Rewrite bad hosts to `aws-1-{region}.pooler.supabase.com` | `app/core/config.py` |
| Use session pooler (port `5432`) for Alembic instead of `db.*.supabase.co` | `app/core/config.py`, `migrations/env.py` |
| Build connection URLs with `URL.create()` for safe password encoding | `app/core/config.py` |
| Add `SUPABASE_DB_REGION` and `SUPABASE_POOLER_PREFIX` settings | `app/core/config.py`, `.env.example` |
| Use `settings.database_url_async` / `database_url_direct_async` | `app/db/session.py`, `migrations/env.py` |
| Enable `ssl=require` for Supabase | `app/db/session.py`, `migrations/env.py` |
| Document correct connection string format | `.env.example` |

## Correct `.env` shape (example)

```env
SUPABASE_DB_REGION=ap-south-1
SUPABASE_POOLER_PREFIX=aws-1

# App runtime — transaction pooler, port 6543
DATABASE_URL=postgresql+asyncpg://postgres.<ref>:<url-encoded-password>@aws-1-ap-south-1.pooler.supabase.com:6543/postgres

# Migrations — direct host is OK here; config rewrites to session pooler port 5432
DATABASE_URL_DIRECT=postgresql+asyncpg://postgres:<url-encoded-password>@db.<ref>.supabase.co:5432/postgres
```

Copy exact values from **Supabase → Project Settings → Database → Connection string**.

## Verification

```powershell
uv run alembic revision --autogenerate -m "create users, farms, farmers, visits tables"
uv run alembic upgrade head
```

Both should complete without DNS or driver errors.

## Takeaway

Supabase connection strings from docs or templates are easy to get subtly wrong. Always use the **regional pooler host** from the dashboard, URL-encode passwords with special characters, and route Alembic through the **session pooler** on Windows when the direct host is IPv6-only.

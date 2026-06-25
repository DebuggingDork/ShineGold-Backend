# Bug: Login / API returns 500 — pgbouncer prepared statement error

**Date:** 2026-06-25  
**Area:** `app/db/session.py`, `app/core/config.py`, `migrations/env.py`  
**Symptom:** `POST /api/v1/auth/login` returns `500 Internal Server Error`. Server logs show:

```
asyncpg.exceptions.DuplicatePreparedStatementError: prepared statement "__asyncpg_stmt_1__" already exists
HINT: pgbouncer with pool_mode set to "transaction" or "statement" does not support prepared statements properly.
```

## What went wrong

The app runtime uses Supabase's **transaction pooler** (pgbouncer, port `6543`) via `DATABASE_URL`.  
`asyncpg` caches prepared statements by default. pgbouncer in transaction mode reassigns backend connections between transactions, so the same prepared-statement name can collide → `DuplicatePreparedStatementError` → unhandled 500 on any route that touches the DB (including login).

## How we fixed it

| Change | File |
|--------|------|
| Added `settings.asyncpg_connect_args` with `statement_cache_size: 0` | `app/core/config.py` |
| Pass `statement_cache_size: 0` via `settings.asyncpg_connect_args` on engine | `app/db/session.py` |
| Same connect args for Alembic online migrations | `migrations/env.py` |

## Verification

```powershell
cd backend
uv run fastapi dev
```

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"employee_id\": \"EXEC002\", \"password\": \"ChangeMe123!\"}"
```

Expect `200` with `access_token`, `refresh_token`, and `user` — or `401` if the user was not seeded (run `uv run python scripts/seed_executives.py`).

## Takeaway

When using **asyncpg + Supabase pooler (pgbouncer transaction mode)**, always disable prepared statement caching:

```python
connect_args={"ssl": "require", "statement_cache_size": 0}
```

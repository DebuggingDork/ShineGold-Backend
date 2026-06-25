# Bug: Tables not visible in Supabase after Alembic autogenerate

**Date:** 2025-06-25  
**Area:** Alembic workflow, Supabase Table Editor  
**Symptom:** Only `alembic_version` appeared in Supabase `public` schema. App tables (`users`, `farms`, `farmers`, `visits`, etc.) were missing.

## What went wrong

`alembic revision --autogenerate` was run, but **`alembic upgrade head` was not**.

| Command | What it does |
|---------|----------------|
| `alembic revision --autogenerate` | Compares models to DB and **writes a migration file** locally |
| `alembic upgrade head` | **Applies** that migration and **creates tables** in Supabase |

Autogenerate connects to the DB to diff schemas. That can leave an empty `alembic_version` table, but it does **not** create your application tables.

## Secondary confusion

In Supabase Table Editor, tables live under schema **`public`**. Supabase internal tables (`auth.*`, `storage.*`) are separate — easy to miss if you're only scanning the sidebar.

## Connection type used (for reference)

| Env var | Supabase type | Host | Port |
|---------|---------------|------|------|
| `DATABASE_URL` | Transaction pooler | `aws-1-ap-south-1.pooler.supabase.com` | `6543` |
| `DATABASE_URL_DIRECT` | Session pooler | `aws-1-ap-south-1.pooler.supabase.com` | `5432` |

Do **not** use Direct connection (`db.<ref>.supabase.co`) on Windows without IPv4 add-on.

## Fix

```powershell
cd backend
uv run alembic upgrade head
```

Then refresh Supabase → **Table Editor** → schema **`public`**.

## Verification

```powershell
uv run alembic current   # should show revision e.g. 514b4fe05bb3 (head)
```

## Takeaway

**Autogenerate = write migration file. Upgrade = create tables.** Always run both, in that order.

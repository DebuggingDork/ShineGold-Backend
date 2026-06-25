# Bug: `seed_admin` fails — passlib incompatible with bcrypt 5.x

**Date:** 2026-06-25  
**Area:** `app/core/security.py`, `pyproject.toml`, `scripts/seed_admin.py`  
**Symptom:** `uv run python scripts/seed_admin.py` crashes while hashing the default admin password.

## What went wrong

`passlib` 1.7.4 (last release: 2020) does not support modern `bcrypt` 4.1+ / 5.x. With `bcrypt==5.0.0` installed via `passlib[bcrypt]`, password hashing fails during backend initialization.

### Error 1 — version probe

```
(trapped) error reading bcrypt version
AttributeError: module 'bcrypt' has no attribute '__about__'
```

`passlib` reads `bcrypt.__about__.__version__`, which was removed in newer `bcrypt` releases.

### Error 2 — hash failure (follow-on)

```
ValueError: password cannot be longer than 72 bytes, truncate manually if necessary
```

This surfaces during passlib's internal `detect_wrap_bug` self-test, not because the seed password is too long (`ChangeMe123!` is 12 characters). The broken passlib ↔ bcrypt integration mis-handles the test hash and raises a misleading error.

## Root cause

| Package | Version | Status |
|---------|---------|--------|
| `passlib` | 1.7.4 | Unmaintained since 2020 |
| `bcrypt` | 5.0.0 | Current; API changed |

`passlib[bcrypt]` does not pin a compatible `bcrypt` version, so `uv` resolves to the latest `bcrypt`, which breaks passlib at runtime.

## How we fixed it

| Change | File |
|--------|------|
| Replaced `passlib` with direct `bcrypt` calls in `hash_password` / `verify_password` | `app/core/security.py` |
| Swapped `passlib[bcrypt]>=1.7.4` for `bcrypt>=4.2.0` | `pyproject.toml` |

`bcrypt` hashes remain standard `$2b$…` strings — existing hashes in the DB (if any) stay compatible with `bcrypt.checkpw`.

## Verification

```powershell
cd backend
uv sync
uv run python -c "from app.core.security import hash_password, verify_password; h = hash_password('ChangeMe123!'); assert verify_password('ChangeMe123!', h)"
uv run python scripts/seed_admin.py
```

All commands should complete without errors.

## Takeaway

Avoid `passlib` for new FastAPI projects. Use `bcrypt` directly (or `argon2-cffi`) so password hashing does not depend on an unmaintained wrapper that breaks whenever `bcrypt` ships a new major version.

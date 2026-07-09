# Backend vs Frontend API Gap Analysis

> Generated from comparing `shinegold/lib` (read-only reference) against the FastAPI backend.  
> **`docs/API_STATUS.md` is outdated** — most endpoints listed as “pending” there are already implemented.

---

## Executive summary

| Area | Verdict |
|------|---------|
| **Core backend** | ~95% done for what the Flutter app screens need |
| **Frontend API wiring** | ~85% — remote datasources exist for almost every screen |
| **Backend still to build** | 2 small gaps (now added below) |
| **Frontend still to build** | Several features use mock-only logic or wrong endpoints |
| **Backend ahead of frontend** | Assignment v2, bulk import, transfer farms, farm visit history |

**Run migration before testing assignment features:**

```bash
cd backend && uv run alembic upgrade head
```

---

## What the frontend already calls (and backend status)

### Auth — ✅ complete

| Frontend | Backend | Notes |
|----------|---------|-------|
| `POST /auth/login` | ✅ | |
| `POST /auth/refresh` | ✅ | |
| `POST /auth/logout` | ✅ | |
| `POST /auth/forgot-password` | ✅ | |
| `POST /auth/change-password` | ✅ | |
| `GET /users/me` | ✅ | Frontend uses this (not dead `authMe` constant) |
| `POST /users/me/setup-location` | ✅ | `home_lat`, `home_lng` |
| `GET /auth/password-reset-requests` | ✅ | **Not wired** in Flutter datasource |
| `POST /auth/password-reset-requests/{id}/approve` | ✅ | **Not wired** in Flutter datasource |
| `GET /auth/password-reset-requests/status?employee_id=` | ✅ **NEW** | For forgot-password polling — frontend still stubs `checkPasswordResetApproved` |

### Uploads — ✅ complete

| Frontend | Backend |
|----------|---------|
| `POST /uploads/presign` | ✅ Returns `upload_url`, `public_url` |

Contexts used: `farm_photo`, `visit_photo`, `visit_voice`, `profile_photo`.

### Dashboard — ✅ complete

| Frontend | Backend |
|----------|---------|
| `GET /dashboard/executive` | ✅ |
| `GET /dashboard/admin` | ✅ (frontend ignores optional `date_from`/`date_to`) |

### Users / executives — ✅ complete

| Frontend | Backend | Notes |
|----------|---------|-------|
| `GET /users` | ✅ | Executive list |
| `POST /users` | ✅ | Add executive |
| `GET /users/{id}` | ✅ | Detail + `assigned_farms` + summary `visit_history` |
| `PATCH /users/{id}/block` | ✅ | |
| `PATCH /users/me` | ✅ | **Not wired** in Flutter — profile screen is read-only |
| `GET /users/{id}/visits` | ✅ **NEW** | Admin executive profile should use this instead of `/visits/mine` |

### Farms — ✅ complete (+ extras backend-only)

| Frontend | Backend | Notes |
|----------|---------|-------|
| `GET /farms` | ✅ | Query: `lat`, `lng`, `sort`, `search`, `assigned_to`, `harvest_status` |
| `GET /farms/{id}` | ✅ | |
| `POST /farms` | ✅ | Body: `location_lat`, `location_lng`, `farmer`, … |
| `PATCH /farms/{id}/assign` | ✅ | **Constant exists, no datasource/UI** — now supports `executive_ids[]` + `mode` |
| `PATCH /farms/{id}` | ✅ | **Not used** by frontend |
| `POST /farms/admin` | ✅ | **Backend only** — admin create + multi-assign |
| `GET /farms/invitations` | ✅ | **Backend only** — proximity accept flow |
| `POST /farms/{id}/accept` | ✅ | **Backend only** |
| `GET /farms/{id}/visits` | ✅ | **Not used** by frontend |
| `GET /farms/{id}/visits/latest` | ✅ | **Not used** by frontend |

### Visits — ✅ complete

| Frontend | Backend | Notes |
|----------|---------|-------|
| `POST /visits/checkin` | ✅ | `checkin_lat`, `checkin_lng` |
| `PATCH /visits/{id}/form` | ✅ | Photos, voice, MCQs |
| `POST /visits/{id}/submit` | ✅ | `checkout_lat`, `checkout_lng` |
| `GET /visits/mine` | ✅ | **Current user only** |
| `GET /visits/{id}` | ✅ | |

### Farmers — ✅ complete

| Frontend | Backend |
|----------|---------|
| `GET /farmers` | ✅ |
| `GET /farmers/{id}` | ✅ |

### Harvests — ✅ complete

| Frontend | Backend |
|----------|---------|
| `GET /harvests/calendar` | ✅ | `month=YYYY-MM` |

### Infrastructure — ✅ complete

| Frontend | Backend |
|----------|---------|
| `GET /health` | ✅ |

### Backend-only (no frontend reference yet)

| Endpoint | Purpose |
|----------|---------|
| `GET /users/bulk-import/template` | Excel template for executive import |
| `POST /users/bulk-import` | Bulk create executives |
| `POST /users/{id}/transfer-farms` | Move all farms between executives |

---

## Frontend screens vs API coverage

| Screen | APIs used | Gap |
|--------|-----------|-----|
| Login | login | — |
| Forgot password | forgot-password | `checkPasswordResetApproved` stubbed; use new **status** endpoint |
| Executive home | dashboard/executive, farms | — |
| Farms list | farms + `lat`/`lng` | — |
| Farm detail | farms/{id} | — |
| Onboard farm | presign + POST farms | — |
| Check-in / visit submit | presign + checkin + form + submit | — |
| My visits | visits/mine | — |
| Executive profile | users/me (read) | No profile edit (`PATCH /users/me`) |
| Admin dashboard | dashboard/admin | — |
| Executives list | users GET/POST | — |
| Admin executive profile | **visits/mine** ❌ | Should use **`GET /users/{id}/visits`** |
| Admin farms | farms | No assign/create UI (`/assign`, `/farms/admin`) |
| Farmers | farmers | — |
| Harvests calendar | harvests/calendar | — |
| Password reset admin | — | **No admin screen**; backend ready |

---

## Lat/lng contract (already aligned)

| Use case | Frontend sends | Backend accepts |
|----------|----------------|-----------------|
| Farm list distance | Query `lat`, `lng` | ✅ |
| Onboard farm | `location_lat`, `location_lng` | ✅ (+ `latitude`/`longitude` aliases) |
| Check-in | `checkin_lat`, `checkin_lng` | ✅ |
| Submit visit | `checkout_lat`, `checkout_lng` | ✅ |
| Home location | `home_lat`, `home_lng` | ✅ |
| Invitations display | Query `lat`, `lng` (optional) | ✅ (coverage still uses home) |

Device GPS resolution: `resolveLocationCoords()` — device first, then `home_lat`/`home_lng`.

---

## What was incomplete on the backend (now fixed)

1. **`GET /api/v1/users/{user_id}/visits`** — Admin viewing another executive’s visits. The Flutter admin executive profile incorrectly calls `/visits/mine` (always returns the logged-in admin’s visits).

2. **`GET /api/v1/auth/password-reset-requests/status?employee_id=`** — Public poll for forgot-password approval. Flutter’s `checkPasswordResetApproved` always returns `false` in API mode.

---

## What the frontend developer still needs to do

See also [`FRONTEND_INTEGRATION.md`](./FRONTEND_INTEGRATION.md).

1. **Fix admin executive profile** — call `GET /users/{id}/visits` instead of `/visits/mine`.
2. **Wire forgot-password poll** — `GET /auth/password-reset-requests/status?employee_id=`.
3. **After admin approves reset** — executive logs in with **temp password**, then `POST /auth/change-password` (no separate `setNewPassword` API).
4. **Wire farm assignment** — `PATCH /farms/{id}/assign` with `{ "executive_ids": [...], "mode": "replace|add|remove" }`.
5. **Add proximity flow** — `GET /farms/invitations`, `POST /farms/{id}/accept`.
6. **Add admin farm create** — `POST /farms/admin` with optional `executive_ids`.
7. **Parse `assigned_executives[]`** on farm list/detail (multi-executive support).
8. **Optional:** admin UI for password reset list + approve.
9. **Optional:** profile edit via `PATCH /users/me` + presign for photo.
10. **Optional:** bulk import + farm transfer (backend ready, no UI).

---

## Is the entire backend done?

**For v1 app screens: yes**, with the two endpoints above added.

**Not in scope / future:**

- Visit cancel endpoint
- `GET /auth/me` alias (frontend dead constant; use `/users/me`)
- Real JWT refresh-token revocation on logout
- Push notifications for invitations

**Ops before go-live:**

1. `uv run alembic upgrade head` (multi-executive assignment migration)
2. Set `EXECUTIVE_ASSIGNMENT_RADIUS_KM=70` in `.env`
3. Configure Supabase storage + `DATABASE_URL` for presign uploads

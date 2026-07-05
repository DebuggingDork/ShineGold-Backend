# ShineGold API Status

Reference for which APIs are implemented and which are still pending. Organized by app screen so each screen maps to the endpoints it needs.

**Legend:** ✅ Done · ⬜ Not started · 🔶 Partial (logic/models exist, endpoint missing)

Full request/response shapes live in [`ShineGoldSpec.md`](../ShineGoldSpec.md).

---

## Executive App

### Login

| Status | Method | Endpoint | What it does |
|--------|--------|----------|--------------|
| ✅ | POST | `/api/v1/auth/login` | Authenticate with `employee_id` + password; returns access/refresh tokens and user profile. Blocks login if account is blocked. |
| ⬜ | POST | `/api/v1/auth/forgot-password` | Executive submits a password-reset request; creates a pending request for admin approval. |

---

### Executive Home

| Status | Method | Endpoint | What it does |
|--------|--------|----------|--------------|
| ⬜ | GET | `/api/v1/dashboard/executive` | Home summary: greeting, farms to visit today, upcoming harvests, visited/pending farm counts. |

---

### Farms List

| Status | Method | Endpoint | What it does |
|--------|--------|----------|--------------|
| ⬜ | GET | `/api/v1/farms` | Paginated farm list with filters: distance sort (`lat`/`lng`), harvest status, search by farm/farmer name. Returns distance, farmer summary, last visited, status. |

---

### Farm Detail (Card)

| Status | Method | Endpoint | What it does |
|--------|--------|----------|--------------|
| ⬜ | GET | `/api/v1/farms/{farm_id}` | Full farm card: location, boundary, crop, harvest info, farmer, photos, visit logs with reports/media. |

---

### Onboard Farm

| Status | Method | Endpoint | What it does |
|--------|--------|----------|--------------|
| 🔶 | POST | `/api/v1/uploads/presign` | Issue a pre-signed PUT URL for farm/farmer photos. Storage service exists; endpoint not wired. |
| ⬜ | POST | `/api/v1/farms` | Create a new farm with location, boundary, crop, harvest fields, photos, and linked farmer (1:1). Sets status to `pending_visit`. |

---

### Visit — Check-in

| Status | Method | Endpoint | What it does |
|--------|--------|----------|--------------|
| ⬜ | POST | `/api/v1/visits/checkin` | Start a visit at a farm; records GPS + timestamp. Returns `409` if executive already has an in-progress visit. |

---

### Visit — Form (Photos, Voice, Notes, MCQs)

| Status | Method | Endpoint | What it does |
|--------|--------|----------|--------------|
| 🔶 | POST | `/api/v1/uploads/presign` | Pre-signed URLs for visit photos and voice notes (`visit_photo`, `visit_voice` contexts). |
| ⬜ | PATCH | `/api/v1/visits/{visit_id}/form` | Save visit form data progressively (photos, voice note, text note, MCQ answers). Callable multiple times before submit. |

---

### Visit — Submit

| Status | Method | Endpoint | What it does |
|--------|--------|----------|--------------|
| ⬜ | POST | `/api/v1/visits/{visit_id}/submit` | Complete the visit with checkout GPS; computes duration and marks visit `completed`. |

---

### My Visits

| Status | Method | Endpoint | What it does |
|--------|--------|----------|--------------|
| ⬜ | GET | `/api/v1/visits/mine` | Executive's own visit history. Filter by status, date range, farm name. Paginated. |
| ⬜ | GET | `/api/v1/visits/{visit_id}` | Single visit detail: check-in/out times, duration, notes, photos, voice note, MCQ answers. |

---

### Profile

| Status | Method | Endpoint | What it does |
|--------|--------|----------|--------------|
| 🔶 | GET | `/api/v1/auth/me` | Returns current user profile. **Implemented here instead of spec's `/users/me`** — no stats yet. |
| ⬜ | GET | `/api/v1/users/me` | Current user profile with stats (`total_farms_visited`, `onboarding_farms_count`). |
| 🔶 | POST | `/api/v1/uploads/presign` | Pre-signed URL for profile photo (`profile_photo` context). |
| ⬜ | PATCH | `/api/v1/users/me` | Update name, address, mobile, profile photo. |
| ✅ | POST | `/api/v1/auth/change-password` | Change password (used after temp-password login too). Validates current password and confirmation match. |

---

## Super Admin App

### Admin Home (Dashboard)

| Status | Method | Endpoint | What it does |
|--------|--------|----------|--------------|
| ⬜ | GET | `/api/v1/dashboard/admin` | Aggregate stats: total farms, executives, visits, farmers onboarded. Optional date-range filter. |

---

### Executives List

| Status | Method | Endpoint | What it does |
|--------|--------|----------|--------------|
| ⬜ | GET | `/api/v1/users` | List executives with search, blocked filter, visit/assignment counts. Paginated. Super admin only. |

---

### Add Executive

| Status | Method | Endpoint | What it does |
|--------|--------|----------|--------------|
| ⬜ | POST | `/api/v1/users` | Create a new executive account. Super admin only. |

---

### Executive Detail

| Status | Method | Endpoint | What it does |
|--------|--------|----------|--------------|
| ⬜ | GET | `/api/v1/users/{user_id}` | Executive profile with visit history and currently assigned farms. Super admin only. |
| ⬜ | PATCH | `/api/v1/users/{user_id}/block` | Block or unblock an executive (`is_blocked`). Preserves historical visit data. Super admin only. |

---

### Password Reset Requests

| Status | Method | Endpoint | What it does |
|--------|--------|----------|--------------|
| ⬜ | GET | `/api/v1/auth/password-reset-requests` | List pending/approved/rejected reset requests. Super admin only. |
| ⬜ | POST | `/api/v1/auth/password-reset-requests/{request_id}/approve` | Approve a reset request and set a temporary password. Super admin only. |

---

### Farms (Admin View)

| Status | Method | Endpoint | What it does |
|--------|--------|----------|--------------|
| ⬜ | GET | `/api/v1/farms` | Same list endpoint as executive; admin uses `assigned_to` and other filters. |
| ⬜ | GET | `/api/v1/farms/{farm_id}` | Same detail endpoint as executive. |
| ⬜ | PATCH | `/api/v1/farms/{farm_id}` | Edit farm details or reassign executive. Super admin only. |
| ⬜ | PATCH | `/api/v1/farms/{farm_id}/assign` | Dedicated endpoint to reassign an executive to a farm. Super admin only. |

---

### Farmers List

| Status | Method | Endpoint | What it does |
|--------|--------|----------|--------------|
| ⬜ | GET | `/api/v1/farmers` | Paginated farmer list with search. Returns name, contact, photo, farms count. Super admin only. |

---

### Farmer Detail

| Status | Method | Endpoint | What it does |
|--------|--------|----------|--------------|
| ⬜ | GET | `/api/v1/farmers/{farmer_id}` | Farmer profile with linked farms (crop, status). Super admin only. |

---

### Harvests Calendar

| Status | Method | Endpoint | What it does |
|--------|--------|----------|--------------|
| ⬜ | GET | `/api/v1/harvests/calendar` | Farms grouped by `harvest_date` for a given month or date range. No separate harvest entity — reads from `Farm`. Super admin only. |

---

## Shared / Infrastructure

| Status | Method | Endpoint | What it does |
|--------|--------|----------|--------------|
| ✅ | POST | `/api/v1/auth/refresh` | Exchange a refresh token for a new access token. |
| ✅ | POST | `/api/v1/auth/logout` | Logout (stateless JWT — no server-side revoke yet). |
| ✅ | GET | `/health` | Health check. |

---

## Summary

| Module | Done | Partial | Pending |
|--------|------|---------|---------|
| Auth (core) | 4 | 1 | 3 |
| File Uploads | 0 | 1 | 0 |
| Users / Profile | 0 | 0 | 5 |
| Farms | 0 | 0 | 5 |
| Visits | 0 | 0 | 5 |
| Farmers | 0 | 0 | 2 |
| Harvests | 0 | 0 | 1 |
| Dashboard | 0 | 0 | 2 |
| **Total endpoints** | **5** | **2** | **23** |

### What's already in the codebase (no endpoint yet)

- **DB models:** `User`, `PasswordResetRequest`, `Farm`, `Farmer`, `Visit`, `VisitPhoto`, `VisitMcqAnswer`
- **Pydantic schemas:** auth, user, farm, visit
- **Services:** `AuthService`, `StorageService` (Supabase presign logic)
- **Migrations:** users, farms, farmers, visits tables

### Suggested next build order

1. `POST /api/v1/uploads/presign` — wire existing `StorageService`
2. Farms module — onboard, list, detail
3. Visits module — check-in → form → submit → mine
4. Users module — `/users/me`, admin CRUD, block
5. Forgot-password flow
6. Farmers list/detail
7. Harvests calendar
8. Dashboard aggregations

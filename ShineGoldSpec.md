# ShineGold App — Backend API Specification (FastAPI)

> Built for handoff to Cursor/agentic coding tools. Covers all endpoints, request/response bodies, and data model assumptions based on the screen spec doc.
> Stack assumption: FastAPI + PostgreSQL + SQLAlchemy (async) + Alembic + Pydantic v2 + JWT (access + refresh) + Supabase Storage / Cloudflare R2 for files.

---

## 0. Design Decisions & Assumptions (read this first)

1. **Roles**: `super_admin`, `executive`. Role is on the `User` model. Auth is identical for both; permissions differ at the route level.
2. **Visit forms are fixed structure** (not dynamic): every visit submission has `photos[]`, `voice_note` (optional), `text_note` (optional), `mcq_answers[]` (fixed set of MCQs defined in backend config/enum, not admin-editable).
3. **Farmer is 1:1 with Farm** at onboarding time (one farm has one primary farmer). Farmer is still independently listable (Farmers page) via a `farmers` table with FK from `farms`.
4. **Farm has one `assigned_executive_id`** at any time (current assignment). Historical "who visited" is tracked per-visit in the `visits` table regardless of current assignment.
5. **File uploads (photos, voice notes, profile photos, farmer photos)** use a **pre-signed URL pattern**: backend issues a signed PUT URL for Supabase Storage/R2, Flutter app uploads directly, then calls a "confirm" endpoint (or just includes the resulting public/object URL in the next request). This keeps large binary traffic off the FastAPI server.
6. **Harvest is NOT a separate root entity** — it's fields on `Farm` (`harvest_type`, `harvest_date`, `crop`). The "Harvests" admin page is just a calendar query over farms grouped by `harvest_date`.
7. **Forgot password flow**: executive requests reset → creates a `password_reset_request` row with status `pending` → super admin approves/sets temp password → executive logs in and is forced to set new password. No email/OTP assumed (since it's admin-mediated), but flagged as an open question below.
8. **Pagination**: all list endpoints use `page` + `page_size` query params, returning `{items, total, page, page_size}`.
9. **Soft delete / block**: executives are **blocked**, not deleted (`is_blocked: bool` on User), so historical visit data stays intact.

**⚠️ Open questions to confirm with your friend/client before Cursor builds this:**
- Does forgot-password need email/SMS OTP, or is "request → admin manually approves" truly the full flow?
- Can a farm have more than one executive assigned over its lifetime concurrently (e.g., shared coverage), or strictly one at a time?
- MCQ questions — are they truly fixed forever, or should they live in a config table even if not admin-editable in v1 (easier to change later without a migration)?

---

## 1. Data Models (core entities)

```
User
- id (PK, UUID)
- employee_id (unique, str)        # login identifier
- name
- password_hash
- role (enum: super_admin, executive)
- profile_photo_url (nullable)
- address (nullable)
- mobile_number (nullable)
- is_blocked (bool, default False)
- created_at, updated_at

PasswordResetRequest
- id (PK)
- user_id (FK -> User)
- status (enum: pending, approved, rejected)
- temp_password_hash (nullable, set on approval)
- requested_at, resolved_at

Farm
- id (PK, UUID)
- name
- location_lat, location_lng
- location_address (nullable)
- crop
- harvest_type
- harvest_date
- total_acres
- boundary_geojson (nullable, for boundary selection polygon)
- assigned_executive_id (FK -> User, nullable)
- onboarded_by (FK -> User)
- status (enum: pending_visit, visited, harvested)  # adjust as needed
- created_at, updated_at

Farmer
- id (PK, UUID)
- farm_id (FK -> Farm, unique = 1:1)
- name
- mobile_number
- gender (enum: male, female, other)
- age
- photo_url (nullable)
- created_at

Visit
- id (PK, UUID)
- farm_id (FK -> Farm)
- executive_id (FK -> User)
- status (enum: in_progress, completed, cancelled)
- checkin_lat, checkin_lng, checkin_time
- checkout_time (nullable)
- duration_seconds (computed at submit)
- text_note (nullable)
- created_at

VisitPhoto
- id (PK)
- visit_id (FK -> Visit)
- photo_url

VisitVoiceNote
- id (PK)
- visit_id (FK -> Visit)
- audio_url

VisitMcqAnswer
- id (PK)
- visit_id (FK -> Visit)
- question_key (str, fixed enum/config key)
- answer (str)
```

---

## 2. Auth Module

### POST `/api/v1/auth/login`
**Request**
```json
{
  "employee_id": "EMP1023",
  "password": "string"
}
```
**Response 200**
```json
{
  "access_token": "jwt...",
  "refresh_token": "jwt...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "employee_id": "EMP1023",
    "name": "Ravi Kumar",
    "role": "executive",
    "profile_photo_url": "https://..."
  }
}
```
**Errors**: `401` invalid credentials, `403` if `is_blocked`.

---

### POST `/api/v1/auth/refresh`
**Request**
```json
{ "refresh_token": "jwt..." }
```
**Response 200**
```json
{ "access_token": "jwt...", "token_type": "bearer" }
```

---

### POST `/api/v1/auth/logout`
**Request**: (auth header only, optionally pass refresh token to revoke it)
```json
{ "refresh_token": "jwt..." }
```
**Response 200**
```json
{ "message": "Logged out successfully" }
```

---

### POST `/api/v1/auth/forgot-password`
*Executive requests a reset.*
**Request**
```json
{ "employee_id": "EMP1023" }
```
**Response 200**
```json
{ "message": "Reset request submitted. Await admin approval.", "request_id": "uuid" }
```

---

### GET `/api/v1/auth/password-reset-requests` *(super admin only)*
**Query params**: `status=pending|approved|rejected`, `page`, `page_size`
**Response 200**
```json
{
  "items": [
    {
      "id": "uuid",
      "user": { "id": "uuid", "employee_id": "EMP1023", "name": "Ravi Kumar" },
      "status": "pending",
      "requested_at": "2026-06-20T10:00:00Z"
    }
  ],
  "total": 4, "page": 1, "page_size": 20
}
```

---

### POST `/api/v1/auth/password-reset-requests/{request_id}/approve` *(super admin only)*
**Request**
```json
{ "temp_password": "string" }
```
**Response 200**
```json
{ "message": "Password reset approved", "request_id": "uuid" }
```

---

### POST `/api/v1/auth/change-password`
*Used after temp-password login to set a real password.*
**Request**
```json
{ "current_password": "string", "new_password": "string", "confirm_password": "string" }
```
**Response 200**
```json
{ "message": "Password updated successfully" }
```

---

## 3. File Upload Module (Supabase/R2 pre-signed pattern)

### POST `/api/v1/uploads/presign`
**Request**
```json
{
  "file_type": "image/jpeg",
  "context": "farm_photo | farmer_photo | profile_photo | visit_photo | visit_voice"
}
```
**Response 200**
```json
{
  "upload_url": "https://...presigned-put-url...",
  "object_key": "visits/2026/06/uuid.jpg",
  "public_url": "https://cdn.../visits/2026/06/uuid.jpg",
  "expires_in": 300
}
```
*Flutter app PUTs the file directly to `upload_url`, then sends `public_url` (or `object_key`) in the relevant create/update endpoint below. No separate "confirm" call needed — the object simply won't be referenced by any record until used.*

---

## 4. User / Profile Module

### GET `/api/v1/users/me`
**Response 200**
```json
{
  "id": "uuid",
  "employee_id": "EMP1023",
  "name": "Ravi Kumar",
  "role": "executive",
  "profile_photo_url": "https://...",
  "address": "Hyderabad",
  "mobile_number": "9876543210",
  "stats": {
    "total_farms_visited": 12,
    "onboarding_farms_count": 3
  }
}
```

### PATCH `/api/v1/users/me`
**Request**
```json
{
  "name": "Ravi Kumar",
  "address": "Hyderabad",
  "mobile_number": "9876543210",
  "profile_photo_url": "https://cdn.../profile.jpg"
}
```
**Response 200**: same shape as GET `/users/me`

---

### POST `/api/v1/users` *(super admin only — add new executive)*
**Request**
```json
{
  "employee_id": "EMP1099",
  "name": "Sita Rao",
  "mobile_number": "9123456780",
  "password": "string",
  "role": "executive"
}
```
**Response 201**
```json
{ "id": "uuid", "employee_id": "EMP1099", "name": "Sita Rao", "role": "executive" }
```

### GET `/api/v1/users` *(super admin only — list executives)*
**Query params**: `role=executive`, `search`, `is_blocked`, `page`, `page_size`
**Response 200**
```json
{
  "items": [
    {
      "id": "uuid",
      "employee_id": "EMP1099",
      "name": "Sita Rao",
      "profile_photo_url": "https://...",
      "mobile_number": "9123456780",
      "is_blocked": false,
      "total_farms_visited": 8,
      "farms_assigned_count": 5
    }
  ],
  "total": 30, "page": 1, "page_size": 20
}
```

### GET `/api/v1/users/{user_id}` *(super admin only — executive detail)*
**Response 200**
```json
{
  "id": "uuid",
  "employee_id": "EMP1099",
  "name": "Sita Rao",
  "mobile_number": "9123456780",
  "profile_photo_url": "https://...",
  "is_blocked": false,
  "visit_history": [
    { "visit_id": "uuid", "farm_name": "Green Acres", "date": "2026-06-10", "status": "completed" }
  ],
  "assigned_farms": [
    { "farm_id": "uuid", "farm_name": "Green Acres", "status": "visited" }
  ]
}
```

### PATCH `/api/v1/users/{user_id}/block` *(super admin only)*
**Request**
```json
{ "is_blocked": true }
```
**Response 200**
```json
{ "id": "uuid", "is_blocked": true }
```

---

## 5. Farms Module

### POST `/api/v1/farms` *(executive — onboard farm)*
**Request**
```json
{
  "name": "Green Acres",
  "location_lat": 17.385,
  "location_lng": 78.4867,
  "location_address": "Shamshabad, Hyderabad",
  "crop": "Mango",
  "harvest_type": "Seasonal",
  "harvest_date": "2026-09-15",
  "total_acres": 4.5,
  "boundary_geojson": { "type": "Polygon", "coordinates": [[[78.48,17.38],[78.49,17.38],[78.49,17.39],[78.48,17.39],[78.48,17.38]]] },
  "photos": ["https://cdn.../farm1.jpg", "https://cdn.../farm2.jpg"],
  "farmer": {
    "name": "Lakshmi Devi",
    "mobile_number": "9988776655",
    "gender": "female",
    "age": 45,
    "photo_url": "https://cdn.../farmer1.jpg"
  }
}
```
**Response 201**
```json
{
  "id": "uuid",
  "name": "Green Acres",
  "status": "pending_visit",
  "farmer_id": "uuid",
  "created_at": "2026-06-25T09:00:00Z"
}
```

---

### GET `/api/v1/farms` *(list with filters — used by both Executive "Farms" screen and Admin dashboard)*
**Query params**:
- `lat`, `lng` — required if `sort=distance`
- `sort` = `distance | farthest`
- `harvest_status` = `pending_visit | visited | harvested`
- `assigned_to` = executive id
- `search` — farm name/farmer name
- `page`, `page_size`

**Response 200**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Green Acres",
      "location_address": "Shamshabad, Hyderabad",
      "distance_km": 3.2,
      "farmer": { "name": "Lakshmi Devi", "mobile_number": "9988776655", "photo_url": "https://..." },
      "last_visited": "2026-06-10T11:00:00Z",
      "status": "visited"
    }
  ],
  "total": 56, "page": 1, "page_size": 20
}
```

---

### GET `/api/v1/farms/{farm_id}` *(individual farm card detail)*
**Response 200**
```json
{
  "id": "uuid",
  "name": "Green Acres",
  "harvest_type": "Seasonal",
  "harvest_date": "2026-09-15",
  "crop": "Mango",
  "location": { "lat": 17.385, "lng": 78.4867, "address": "Shamshabad, Hyderabad" },
  "boundary_geojson": { "type": "Polygon", "coordinates": [["..."]] },
  "total_acres": 4.5,
  "assigned_executive": { "id": "uuid", "name": "Ravi Kumar" },
  "farmer": {
    "id": "uuid", "name": "Lakshmi Devi", "mobile_number": "9988776655",
    "gender": "female", "age": 45, "photo_url": "https://..."
  },
  "photos": ["https://cdn.../farm1.jpg"],
  "status": "visited",
  "visit_logs": [
    {
      "visit_id": "uuid",
      "date": "2026-06-10",
      "duration_seconds": 1820,
      "report": "Crop healthy, minor pest signs on 2 acres.",
      "photos": ["https://cdn.../v1.jpg"],
      "voice_note": "https://cdn.../v1.mp3",
      "visited_by": { "id": "uuid", "name": "Ravi Kumar" }
    }
  ]
}
```

### PATCH `/api/v1/farms/{farm_id}` *(super admin — e.g. reassign executive, edit details)*
**Request**
```json
{ "assigned_executive_id": "uuid", "harvest_date": "2026-09-20" }
```
**Response 200**: same shape as GET farm detail (or partial)

### PATCH `/api/v1/farms/{farm_id}/assign` *(super admin — dedicated reassign endpoint, alt. to above)*
**Request**
```json
{ "executive_id": "uuid" }
```
**Response 200**
```json
{ "farm_id": "uuid", "assigned_executive_id": "uuid" }
```

---

## 6. Visits Module

### POST `/api/v1/visits/checkin`
*Starts a visit — captures GPS + time.*
**Request**
```json
{
  "farm_id": "uuid",
  "checkin_lat": 17.3851,
  "checkin_lng": 78.4868
}
```
**Response 201**
```json
{
  "visit_id": "uuid",
  "farm_id": "uuid",
  "status": "in_progress",
  "checkin_time": "2026-06-25T09:15:00Z"
}
```
**Errors**: `409` if there's already an `in_progress` visit for this executive.

---

### PATCH `/api/v1/visits/{visit_id}/form`
*Saves form data progressively (photos/voice/text/MCQs) — can be called multiple times before submit, or once with everything.*
**Request**
```json
{
  "photos": ["https://cdn.../p1.jpg", "https://cdn.../p2.jpg"],
  "voice_note_url": "https://cdn.../note1.mp3",
  "text_note": "Crop healthy, minor pest signs on 2 acres.",
  "mcq_answers": [
    { "question_key": "irrigation_status", "answer": "adequate" },
    { "question_key": "pest_observed", "answer": "yes" }
  ]
}
```
**Response 200**
```json
{ "visit_id": "uuid", "status": "in_progress", "updated_fields": ["photos", "voice_note_url", "text_note", "mcq_answers"] }
```

---

### POST `/api/v1/visits/{visit_id}/submit`
*Review & submit — ends visit.*
**Request**
```json
{ "checkout_lat": 17.3852, "checkout_lng": 78.4869 }
```
**Response 200**
```json
{
  "visit_id": "uuid",
  "status": "completed",
  "checkout_time": "2026-06-25T09:45:00Z",
  "duration_seconds": 1800
}
```

---

### GET `/api/v1/visits/mine` *(My Visits screen)*
**Query params**: `status=in_progress|completed`, `date_from`, `date_to`, `farm_name`, `page`, `page_size`
**Response 200**
```json
{
  "items": [
    {
      "visit_id": "uuid",
      "farm": { "id": "uuid", "name": "Green Acres" },
      "status": "completed",
      "checkin_time": "2026-06-25T09:15:00Z",
      "duration_seconds": 1800
    }
  ],
  "total": 12, "page": 1, "page_size": 20
}
```

### GET `/api/v1/visits/{visit_id}`
**Response 200**
```json
{
  "visit_id": "uuid",
  "farm_id": "uuid",
  "status": "completed",
  "checkin_time": "2026-06-25T09:15:00Z",
  "checkout_time": "2026-06-25T09:45:00Z",
  "duration_seconds": 1800,
  "text_note": "Crop healthy, minor pest signs on 2 acres.",
  "photos": ["https://cdn.../p1.jpg"],
  "voice_note_url": "https://cdn.../note1.mp3",
  "mcq_answers": [{ "question_key": "irrigation_status", "answer": "adequate" }],
  "visited_by": { "id": "uuid", "name": "Ravi Kumar" }
}
```

---

## 7. Farmers Module *(super admin)*

### GET `/api/v1/farmers`
**Query params**: `search`, `page`, `page_size`
**Response 200**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Lakshmi Devi",
      "mobile_number": "9988776655",
      "photo_url": "https://...",
      "farms_count": 1
    }
  ],
  "total": 56, "page": 1, "page_size": 20
}
```

### GET `/api/v1/farmers/{farmer_id}`
**Response 200**
```json
{
  "id": "uuid",
  "name": "Lakshmi Devi",
  "mobile_number": "9988776655",
  "gender": "female",
  "age": 45,
  "photo_url": "https://...",
  "farms": [
    { "id": "uuid", "name": "Green Acres", "crop": "Mango", "status": "visited" }
  ]
}
```

---

## 8. Harvests Module *(super admin — calendar view)*

### GET `/api/v1/harvests/calendar`
**Query params**: `month` (e.g. `2026-09`), or `date_from`/`date_to`
**Response 200**
```json
{
  "harvests": [
    {
      "date": "2026-09-15",
      "farms": [
        { "id": "uuid", "name": "Green Acres", "crop": "Mango", "harvest_type": "Seasonal" }
      ]
    }
  ]
}
```

---

## 9. Dashboard Module *(super admin home + executive home)*

### GET `/api/v1/dashboard/admin`
**Query params**: optional `date_from`, `date_to` (for "filter based" stats)
**Response 200**
```json
{
  "total_farms": 120,
  "total_executives": 14,
  "total_visits": 340,
  "farmers_onboarded": 120
}
```

### GET `/api/v1/dashboard/executive`
**Response 200**
```json
{
  "greeting_name": "Ravi Kumar",
  "date": "2026-06-25",
  "total_farms_to_visit": 8,
  "upcoming_harvests": [
    { "farm_id": "uuid", "farm_name": "Green Acres", "harvest_date": "2026-09-15" }
  ],
  "farms_visited_count": 12,
  "pending_farms_count": 8
}
```

---

## 10. Suggested Build Order (for Cursor prompting)

1. Project scaffold: FastAPI app, SQLAlchemy async engine, Alembic, Pydantic settings, JWT utils
2. `User` model + Auth module (login, refresh, logout) — get JWT working end-to-end first
3. Forgot-password flow
4. File upload presign endpoint (Supabase/R2 client wrapper)
5. `Farm` + `Farmer` models, onboarding endpoint, farm list/detail/filters
6. `Visit` + related tables, check-in → form → submit flow
7. My Visits, Users (executive admin CRUD + block), Farmers list, Harvests calendar
8. Dashboard aggregation endpoints last (they just query everything above)

---

## 11. Suggested Cursor Prompt Opener

> "I'm building the backend for ShineGold, a farm-visit tracking app (FastAPI + PostgreSQL async + SQLAlchemy + Alembic + Pydantic v2 + JWT access/refresh + Supabase Storage for files). I have a full API spec with all endpoints and request/response bodies below. Start by scaffolding the project structure (app/, models/, schemas/, routers/, core/), then implement Section 2 (Auth) completely with working JWT, then move to Section 5 (Farms) and Section 6 (Visits). Follow the request/response shapes exactly as given — don't invent extra fields. Ask me before changing any schema shape." + [paste this doc]
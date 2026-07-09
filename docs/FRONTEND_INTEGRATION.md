# Shine Gold Frontend — Backend Integration Guide

> **For the Flutter developer.** This backend repo does **not** include the frontend. The `shinegold/` folder may exist locally for reference only and is gitignored. All API changes below are implemented in the FastAPI backend; the Flutter app needs to be updated separately in [shinegold](https://github.com/Charanreddy2408/shinegold).

---

## 1. Base URL & auth

- Set `AppConfig.useMockData = false` and point `AppConfig.baseUrl` at this API.
- Auth is unchanged: `POST /api/v1/auth/login` with `employee_id` + `password`.
- Send `Authorization: Bearer <access_token>` on protected routes.

---

## 2. Latitude / longitude — what the backend expects

The backend is aligned with how the Flutter app **already sends** coordinates. No renames required on the frontend for existing flows.

| Feature | HTTP | Field names (preferred) | Also accepted |
|--------|------|-------------------------|---------------|
| Farm list (distance sort) | `GET /api/v1/farms` | Query: `lat`, `lng` | — |
| Onboard farm | `POST /api/v1/farms` | Body: `location_lat`, `location_lng`, `location_address` | `latitude`, `longitude` |
| Visit check-in | `POST /api/v1/visits/checkin` | Body: `checkin_lat`, `checkin_lng` | `latitude`, `longitude` |
| Visit submit | `POST /api/v1/visits/{id}/submit` | Body: `checkout_lat`, `checkout_lng` | `latitude`, `longitude` |
| Executive home location | `POST /api/v1/users/me/setup-location` | Body: `home_lat`, `home_lng`, optional `address` | `latitude`, `longitude` |
| Farm invitations (display distance) | `GET /api/v1/farms/invitations` | Query: optional `lat`, `lng` (device GPS for **display** only) | — |

### How the app should resolve coordinates

Current Flutter logic (`resolveLocationCoords`) is correct:

1. **Device GPS first** (`geolocator` position)
2. **Fallback to profile** `home_lat` / `home_lng` from `GET /api/v1/users/me`

Use that for:

- `GET /api/v1/farms` → pass as query `lat` / `lng` when sorting by distance
- `GET /api/v1/farms/invitations` → pass as query `lat` / `lng` for distance shown in the UI

**Important:** Proximity **assignment rules** use the executive’s **pinned home location** (`home_lat` / `home_lng`), not live GPS. The executive must call `POST /api/v1/users/me/setup-location` before invitations work. Coverage radius defaults to **70 km** (`EXECUTIVE_ASSIGNMENT_RADIUS_KM` on the server).

---

## 3. Executive assignment (three paths)

A farm can have **multiple executives** assigned at the same time.

| Path | Who | How |
|------|-----|-----|
| **Onboard** | Executive | `POST /api/v1/farms` — onboarder is auto-assigned |
| **Proximity accept** | Executive | `GET /api/v1/farms/invitations` → `POST /api/v1/farms/{id}/accept` |
| **Admin assign** | Super admin | `POST /api/v1/farms/admin` and/or `PATCH /api/v1/farms/{id}/assign` |

### Rules

- Only **assigned** executives can open farm detail or check in (`403` otherwise).
- Executives listing farms: backend auto-filters to **their** assignments (no need to pass `assigned_to` unless admin).
- Proximity invitations only show farms with **no** executives yet, within 70 km of home.
- Accepting adds the executive; admin can add more via assign `mode: "add"`.

---

## 4. New / updated API endpoints

### `POST /api/v1/farms/admin` — super admin creates farm

Same body as executive onboard, plus optional assignments.

```json
{
  "name": "Farm A",
  "location_lat": 17.385,
  "location_lng": 78.486,
  "location_address": "Hyderabad",
  "crop": "Turmeric",
  "harvest_type": "Organic",
  "harvest_date": "2026-09-20",
  "total_acres": 5,
  "farmer": {
    "name": "Ravi",
    "mobile_number": "9876543210",
    "gender": "male",
    "age": 45
  },
  "executive_ids": ["uuid-1", "uuid-2"]
}
```

- `executive_ids` is optional. Omit to leave the farm unassigned (shows in nearby executives’ invitations).

**Response `201`:**

```json
{
  "id": "uuid",
  "name": "Farm A",
  "status": "pending_visit",
  "farmer_id": "uuid",
  "assigned_executive_ids": ["uuid-1", "uuid-2"],
  "created_at": "2026-07-09T12:00:00Z"
}
```

---

### `GET /api/v1/farms/invitations` — executive only

Unassigned farms within 70 km of executive **home**.

**Query:** `page`, `page_size`, optional `lat`, `lng` (device coords for `distance_km` display)

**Response:** paginated `items[]`:

```json
{
  "id": "uuid",
  "name": "Farm A",
  "location_address": "...",
  "location_lat": 17.385,
  "location_lng": 78.486,
  "location": { "lat": 17.385, "lng": 78.486, "address": "..." },
  "distance_km": 12.4,
  "farmer": { "name": "...", "mobile_number": "...", "photo_url": null },
  "status": "pending_visit",
  "assignment_radius_km": 70
}
```

---

### `POST /api/v1/farms/{farm_id}/accept` — executive only

Accepts proximity assignment if farm is unassigned and within home coverage.

**Response:**

```json
{
  "farm_id": "uuid",
  "assigned_executive_ids": ["executive-uuid"],
  "distance_km": 12.4
}
```

---

### `PATCH /api/v1/farms/{farm_id}/assign` — super admin only

Assign one or more executives.

```json
{
  "executive_ids": ["uuid-1", "uuid-2"],
  "mode": "replace"
}
```

| `mode` | Behavior |
|--------|----------|
| `replace` (default) | Set exactly these executives (empty list clears all) |
| `add` | Add without removing existing |
| `remove` | Remove only listed executives |

**Legacy single assign** still works:

```json
{ "executive_id": "uuid-1", "mode": "replace" }
```

**Response:**

```json
{
  "farm_id": "uuid",
  "assigned_executive_ids": ["uuid-1", "uuid-2"]
}
```

---

## 5. Response shape changes (parse on frontend)

### Farm list — `GET /api/v1/farms`

Each item now includes location and assignment summary:

```json
{
  "id": "uuid",
  "name": "Farm A",
  "location_address": "...",
  "location_lat": 17.385,
  "location_lng": 78.486,
  "location": { "lat": 17.385, "lng": 78.486, "address": "..." },
  "distance_km": 3.2,
  "farmer": { "name": "...", "mobile_number": "...", "photo_url": null },
  "last_visited": null,
  "status": "pending_visit",
  "assigned_executive_id": "uuid",
  "assigned_executive_name": "Ravi Kumar",
  "assigned_executives": [
    { "id": "uuid", "name": "Ravi Kumar" },
    { "id": "uuid-2", "name": "Second Exec" }
  ]
}
```

`Farm.fromJson` already handles `location: { lat, lng, address }` and singular `assigned_executive` / `assigned_executive_id`. **Add parsing for `assigned_executives[]`** if the UI should show multiple assignees.

### Farm detail — `GET /api/v1/farms/{id}`

```json
{
  "assigned_executives": [
    { "id": "uuid", "name": "Ravi Kumar" }
  ],
  "assigned_executive_id": "uuid",
  "assigned_executive_name": "Ravi Kumar",
  "assigned_executive": { "id": "uuid", "name": "Ravi Kumar" },
  "location": { "lat": 17.385, "lng": 78.486, "address": "..." }
}
```

Singular fields are **computed from the first** executive for backward compatibility.

---

## 6. Flutter changes checklist

Add to `lib/core/network/api_endpoints.dart`:

```dart
static const farmsAdmin = '$_v1/farms/admin';
static const farmInvitations = '$_v1/farms/invitations';
static String acceptFarm(String id) => '$_v1/farms/$id/accept';
```

Wire in `api_farm_datasource.dart` (or equivalent):

- [ ] `getFarmInvitations({ lat, lng, page, pageSize })` → `GET /farms/invitations`
- [ ] `acceptFarmInvitation(farmId)` → `POST /farms/{id}/accept`
- [ ] `createFarmAsAdmin(request, executiveIds)` → `POST /farms/admin`
- [ ] `assignFarmExecutives(farmId, executiveIds, mode)` → `PATCH /farms/{id}/assign` with `executive_ids` + `mode`

Model updates:

- [ ] Parse `assigned_executives` array on farm list/detail
- [ ] Optional UI: invitations screen for executives (nearby unassigned farms)
- [ ] Optional UI: admin create farm + multi-select executives
- [ ] Optional UI: admin assign/add/remove executives on farm detail

Existing flows **no change** needed for field names:

- Farm list still sends `lat` / `lng` query params ✓
- Onboard still sends `location_lat` / `location_lng` ✓
- Check-in still sends `checkin_lat` / `checkin_lng` ✓
- Setup location still sends `home_lat` / `home_lng` ✓

---

## 9. Visit report form (dynamic)

See **[VISIT_FORM.md](./VISIT_FORM.md)** for the full Jackfruit field visit form API.

- `GET /api/v1/visit-forms/active` — active template
- `GET /api/v1/visit-forms/visits/{visit_id}/context` — template + auto-prefill
- `PATCH /api/v1/visits/{id}/form` — add `form_answers[]` alongside `photos` / `voice_note_url`
- Admin CRUD under `/api/v1/visit-forms/templates/...`

---

## 10. Database migration (backend ops)

Run on the API server before testing new assignment features:

```bash
cd backend
uv run alembic upgrade head
```

This creates `farm_executive_assignments`, migrates old `assigned_executive_id` data, and drops the single-assign column.

---

## 8. Error cases to handle in UI

| Status | When |
|--------|------|
| `400` | Accept outside 70 km, farm already assigned, blocked executive, missing home location |
| `403` | Executive opens or checks in to a farm they are not assigned to |
| `404` | Farm / visit not found |

Typical `400` messages:

- `"Set your home location before viewing or accepting farm invitations"`
- `"Farm is outside your coverage area (70 km radius from home)"`
- `"You are not assigned to this farm. Onboard it or accept a nearby invitation first."`

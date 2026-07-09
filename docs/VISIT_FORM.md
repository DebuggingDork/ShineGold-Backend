# Visit Report Form — API Guide

Configurable field visit report form (default: **Jackfruit Farmer Field Visit Report**).  
Photos and voice notes continue to use the existing visit upload flow (`PATCH /visits/{id}/form`).

Run migration:

```bash
cd backend && uv run alembic upgrade head
```

---

## Default questions (seeded)

| Key | Type | Required | Maps from Google Form |
|-----|------|----------|------------------------|
| `visit_metadata` | section_header | No | Employee name, date, location (auto-prefilled) |
| `tree_health` | single_choice | Yes | General Health Assessment |
| `pests_diseases` | multi_choice | Yes | Observed Pest or Disease |
| `infrastructure_matrix` | matrix | Yes | Farm Infrastructure (4 rows × 4 columns) |
| `agronomic_adoption` | rating_scale 1–5 | Yes | Farmer adoption rating |
| `assistance_needed` | single_choice | Yes | Immediate assistance / training |
| `harvest_schedule_expectations` | textarea | No | Harvest schedule & yield expectations |
| `action_plan` | textarea | No | Action plan (also copied to `text_note`) |

**Auto-prefilled** (not stored as answers — returned in `prefill`):

- Executive name
- Visit date
- Farm location (village/district)
- Farmer contact name
- Check-in time

**Geotagged photos** — use existing `photos[]` on `PATCH /visits/{id}/form` (up to 5 via app logic).

---

## Executive endpoints

### Get active form template

`GET /api/v1/visit-forms/active`

Returns full template with questions and options.

### Get form context for a visit

`GET /api/v1/visit-forms/visits/{visit_id}/context`

Returns `{ template, prefill }` for rendering the in-progress visit form.

### Save form answers (partial save)

`PATCH /api/v1/visits/{visit_id}/form`

```json
{
  "form_answers": [
    { "question_key": "tree_health", "answer": "good" },
    {
      "question_key": "pests_diseases",
      "answer_json": ["aphids", "no_major_issues"]
    },
    {
      "question_key": "infrastructure_matrix",
      "answer_json": {
        "irrigation_system": "good",
        "field_fencing": "fair",
        "weed_management": "good",
        "fertigation_system": "poor"
      }
    },
    { "question_key": "agronomic_adoption", "answer": "4" },
    { "question_key": "assistance_needed", "answer": "follow_up_training" },
    {
      "question_key": "harvest_schedule_expectations",
      "answer": "Harvest expected in September, ~2 tons."
    },
    {
      "question_key": "action_plan",
      "answer": "Schedule pest spray next week."
    }
  ],
  "photos": [
    {
      "photo_url": "https://...",
      "captured_lat": 17.38,
      "captured_lng": 78.48,
      "captured_at": "2026-07-09T12:00:00Z"
    }
  ],
  "voice_note_url": "https://..."
}
```

### Submit visit

`POST /api/v1/visits/{visit_id}/submit` — validates **required** questions before completing.

### Visit detail response

`GET /api/v1/visits/{id}` now includes:

```json
{
  "form_answers": [
    {
      "question_key": "tree_health",
      "question_label": "General Health Assessment...",
      "question_type": "single_choice",
      "answer": "good",
      "answer_json": null
    }
  ]
}
```

Legacy `mcq_answers` is still supported for backward compatibility.

---

## Admin endpoints (super admin)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/visit-forms/templates` | List templates |
| POST | `/api/v1/visit-forms/templates` | Create template `{ name, description, activate? }` |
| GET | `/api/v1/visit-forms/templates/{id}` | Full template |
| PATCH | `/api/v1/visit-forms/templates/{id}` | Update name/description |
| POST | `/api/v1/visit-forms/templates/{id}/activate` | Set as active form |
| POST | `/api/v1/visit-forms/templates/{id}/questions` | Add question |
| PATCH | `/api/v1/visit-forms/questions/{id}` | Edit question |
| DELETE | `/api/v1/visit-forms/questions/{id}` | Remove question |
| POST | `/api/v1/visit-forms/questions/{id}/options` | Add option (choice questions) |
| PATCH | `/api/v1/visit-forms/options/{id}` | Edit option |
| DELETE | `/api/v1/visit-forms/options/{id}` | Remove option |

### Add a new single-choice question (example)

`POST /api/v1/visit-forms/templates/{template_id}/questions`

```json
{
  "question_key": "irrigation_source",
  "label": "Primary irrigation source",
  "question_type": "single_choice",
  "sort_order": 35,
  "is_required": false,
  "options": [
    { "value": "borewell", "label": "Borewell", "sort_order": 1 },
    { "value": "canal", "label": "Canal", "sort_order": 2 }
  ]
}
```

### Question types

- `single_choice` — `answer` string (option value)
- `multi_choice` — `answer_json` string array
- `rating_scale` — `answer` string number; `config: { min, max, min_label?, max_label? }`
- `matrix` — `answer_json` object `{ row_key: column_key }`; `config: { rows[], columns[] }`
- `text` / `textarea` — `answer` string
- `section_header` — display only, no answer

---

## Frontend checklist

- [ ] On check-in, fetch `GET /visit-forms/visits/{visit_id}/context`
- [ ] Render dynamic form from `template.questions` (skip `section_header` for input)
- [ ] Show `prefill` fields at top (read-only)
- [ ] Save progressively via `PATCH /visits/{id}/form` with `form_answers`
- [ ] Keep photo upload via presign + `photos[]`
- [ ] Keep voice note via presign + `voice_note_url`
- [ ] Submit via `POST /visits/{id}/submit` after required fields filled
- [ ] Admin: form builder UI using admin endpoints above

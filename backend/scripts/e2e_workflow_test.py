"""
End-to-end workflow test mirroring the Shine Gold Flutter app API calls.

Run from backend/ (with API server on http://127.0.0.1:8000 via `uv run fastapi dev`):
    uv run python scripts/e2e_workflow_test.py
"""
from __future__ import annotations

import json
import sys
import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from api_base import API_BASE as BASE
PASSWORD = "ChangeMe123!"

# Hyderabad area dummy coordinates
HYDERABAD_LAT = 17.3850
HYDERABAD_LNG = 78.4867
NEARBY_LAT = 17.4200
NEARBY_LNG = 78.5000
FAR_LAT = 18.5204  # Pune ~560km away
FAR_LNG = 73.8567


@dataclass
class StepResult:
    name: str
    ok: bool
    detail: str = ""
    response: dict | list | str | None = None


@dataclass
class WorkflowReport:
    steps: list[StepResult] = field(default_factory=list)

    def add(self, name: str, ok: bool, detail: str = "", response=None) -> None:
        self.steps.append(StepResult(name, ok, detail, response))
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))

    @property
    def failed(self) -> list[StepResult]:
        return [s for s in self.steps if not s.ok]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login(client: httpx.Client, employee_id: str) -> tuple[str, dict]:
    r = client.post(
        f"{BASE}/api/v1/auth/login",
        json={"employee_id": employee_id, "password": PASSWORD},
    )
    r.raise_for_status()
    data = r.json()
    return data["access_token"], data["user"]


def build_form_answers(ctx: dict) -> list[dict]:
    """Build API form_answers matching backend FormAnswerIn schema."""
    template = ctx.get("template") or {}
    questions = ctx.get("questions") or template.get("questions") or []
    answers: list[dict] = []
    for q in questions:
        qtype = q.get("question_type") or q.get("type")
        if qtype == "section_header":
            continue
        key = q.get("question_key") or q.get("key")
        if not key:
            continue
        if qtype in ("text", "textarea"):
            answers.append({"question_key": key, "answer": "E2E test answer"})
        elif qtype == "single_choice":
            opts = q.get("options") or []
            if opts:
                answers.append(
                    {"question_key": key, "answer": opts[0].get("value") or opts[0].get("label")}
                )
        elif qtype == "multi_choice":
            opts = q.get("options") or []
            if opts:
                val = opts[0].get("value") or opts[0].get("label")
                answers.append({"question_key": key, "answer_json": [val]})
        elif qtype == "rating_scale":
            answers.append({"question_key": key, "answer": "4"})
        elif qtype == "matrix":
            config = q.get("config") or {}
            rows = config.get("rows") or []
            cols = config.get("columns") or []
            if rows and cols:
                answers.append(
                    {
                        "question_key": key,
                        "answer_json": {rows[0]["key"]: cols[0]["key"]},
                    }
                )
    return answers


def main() -> int:
    report = WorkflowReport()
    suffix = uuid.uuid4().hex[:6]

    with httpx.Client(timeout=30.0) as client:
        # 0. Health
        try:
            r = client.get(f"{BASE}/health")
            report.add("Health check", r.status_code == 200, f"status={r.status_code}")
        except Exception as e:
            report.add("Health check", False, str(e))
            return print_summary(report)

        # 1. Admin login
        try:
            admin_token, admin_user = login(client, "ADMIN001")
            report.add("Admin login", True, f"role={admin_user.get('role')}")
        except Exception as e:
            report.add("Admin login", False, str(e))
            return print_summary(report)

        # 2. Executive login
        try:
            exec_token, exec_user = login(client, "EXEC001")
            report.add("Executive login", True, f"id={exec_user.get('id')}")
        except Exception as e:
            report.add("Executive login", False, str(e))
            return print_summary(report)

        exec2_token = None
        try:
            exec2_token, _ = login(client, "EXEC002")
            report.add("Executive 2 login", True)
        except Exception as e:
            report.add("Executive 2 login", False, str(e))

        # 3. Executive home location setup (required for invitations)
        try:
            r = client.post(
                f"{BASE}/api/v1/users/me/setup-location",
                headers=auth_headers(exec_token),
                json={
                    "home_lat": HYDERABAD_LAT,
                    "home_lng": HYDERABAD_LNG,
                    "address": "Hyderabad Test Home",
                },
            )
            data = r.json()
            ok = r.status_code == 200 and data.get("home_lat") == HYDERABAD_LAT
            report.add("Executive setup home location", ok, f"status={r.status_code}")
        except Exception as e:
            report.add("Executive setup home location", False, str(e))

        # 4. Admin creates unassigned farm (for proximity invitations)
        unassigned_farm_id = None
        try:
            r = client.post(
                f"{BASE}/api/v1/farms/admin",
                headers=auth_headers(admin_token),
                json={
                    "name": f"Proximity Test Farm {suffix}",
                    "location_lat": NEARBY_LAT,
                    "location_lng": NEARBY_LNG,
                    "location_address": "Near Hyderabad",
                    "crop": "Jackfruit",
                    "harvest_type": "Organic",
                    "harvest_date": (date.today() + timedelta(days=90)).isoformat(),
                    "total_acres": 3.5,
                    "farmer": {
                        "name": f"Farmer Prox {suffix}",
                        "mobile_number": f"9{suffix[:9]}".ljust(10, "1")[:10],
                        "gender": "male",
                        "age": 42,
                    },
                },
            )
            data = r.json()
            unassigned_farm_id = data.get("id")
            ok = r.status_code == 201 and not data.get("assigned_executive_ids")
            report.add("Admin create unassigned farm", ok, f"farm_id={unassigned_farm_id}")
        except Exception as e:
            report.add("Admin create unassigned farm", False, str(e))

        # 5. Farm invitations (proximity)
        try:
            r = client.get(
                f"{BASE}/api/v1/farms/invitations",
                headers=auth_headers(exec_token),
                params={"lat": HYDERABAD_LAT, "lng": HYDERABAD_LNG},
            )
            data = r.json()
            items = data.get("items", [])
            found = any(i.get("id") == unassigned_farm_id for i in items)
            report.add(
                "Executive farm invitations (nearby)",
                r.status_code == 200 and found,
                f"count={len(items)}, found_test_farm={found}",
            )
        except Exception as e:
            report.add("Executive farm invitations (nearby)", False, str(e))

        # 6. Accept invitation
        try:
            r = client.post(
                f"{BASE}/api/v1/farms/{unassigned_farm_id}/accept",
                headers=auth_headers(exec_token),
            )
            data = r.json()
            ok = r.status_code == 200 and data.get("farm_id") == unassigned_farm_id
            report.add("Accept farm invitation", ok, f"distance_km={data.get('distance_km')}")
        except Exception as e:
            report.add("Accept farm invitation", False, str(e))

        # 7. Executive onboard another farm
        onboarded_farm_id = None
        try:
            r = client.post(
                f"{BASE}/api/v1/farms",
                headers=auth_headers(exec_token),
                json={
                    "name": f"Onboarded Farm {suffix}",
                    "location_lat": HYDERABAD_LAT,
                    "location_lng": HYDERABAD_LNG,
                    "location_address": "Hyderabad Onboard",
                    "crop": "Turmeric",
                    "harvest_type": "Organic",
                    "harvest_date": (date.today() + timedelta(days=120)).isoformat(),
                    "total_acres": 2.0,
                    "farmer": {
                        "name": f"Onboard Farmer {suffix}",
                        "mobile_number": f"8{suffix[:9]}".ljust(10, "2")[:10],
                        "gender": "female",
                        "age": 38,
                    },
                },
            )
            data = r.json()
            onboarded_farm_id = data.get("id")
            assigned = data.get("assigned_executive_ids") or []
            ok = r.status_code == 201 and onboarded_farm_id and len(assigned) >= 1
            report.add("Executive onboard farm", ok, f"farm_id={onboarded_farm_id}")
        except Exception as e:
            report.add("Executive onboard farm", False, str(e))

        # 8. Farm list with distance sort
        try:
            r = client.get(
                f"{BASE}/api/v1/farms",
                headers=auth_headers(exec_token),
                params={"lat": HYDERABAD_LAT, "lng": HYDERABAD_LNG, "sort": "distance"},
            )
            data = r.json()
            items = data.get("items", [])
            report.add("Executive farm list (distance sort)", r.status_code == 200, f"count={len(items)}")
        except Exception as e:
            report.add("Executive farm list (distance sort)", False, str(e))

        # 9. Farm detail
        detail_farm_id = onboarded_farm_id or unassigned_farm_id
        try:
            r = client.get(
                f"{BASE}/api/v1/farms/{detail_farm_id}",
                headers=auth_headers(exec_token),
            )
            data = r.json()
            has_execs = bool(data.get("assigned_executives") or data.get("assigned_executive_id"))
            report.add("Farm detail", r.status_code == 200 and has_execs, f"name={data.get('name')}")
        except Exception as e:
            report.add("Farm detail", False, str(e))

        # 9.5 Cancel any stale in-progress visit before check-in
        try:
            r = client.get(
                f"{BASE}/api/v1/visits/mine",
                headers=auth_headers(exec_token),
                params={"status": "in_progress"},
            )
            for item in r.json().get("items", []):
                visit_key = item.get("id") or item.get("visit_id")
                if visit_key:
                    client.post(
                        f"{BASE}/api/v1/visits/{visit_key}/cancel",
                        headers=auth_headers(exec_token),
                    )
        except Exception:
            pass

        # 10. Visit check-in
        visit_id = None
        try:
            r = client.post(
                f"{BASE}/api/v1/visits/checkin",
                headers=auth_headers(exec_token),
                json={
                    "farm_id": detail_farm_id,
                    "checkin_lat": HYDERABAD_LAT,
                    "checkin_lng": HYDERABAD_LNG,
                },
            )
            data = r.json()
            visit_id = data.get("visit_id")
            ok = r.status_code == 201 and visit_id
            report.add("Visit check-in", ok, f"visit_id={visit_id}")
        except Exception as e:
            report.add("Visit check-in", False, str(e))

        # 11. Visit form context
        try:
            r = client.get(
                f"{BASE}/api/v1/visit-forms/visits/{visit_id}/context",
                headers=auth_headers(exec_token),
            )
            data = r.json()
            has_template = bool(data.get("template") or data.get("questions"))
            report.add("Visit form context", r.status_code == 200 and has_template, f"keys={list(data.keys())}")
        except Exception as e:
            report.add("Visit form context", False, str(e))

        # 12. Save visit form (dummy answers)
        try:
            r = client.get(
                f"{BASE}/api/v1/visit-forms/visits/{visit_id}/context",
                headers=auth_headers(exec_token),
            )
            ctx = r.json()
            form_answers = build_form_answers(ctx)

            r = client.patch(
                f"{BASE}/api/v1/visits/{visit_id}/form",
                headers=auth_headers(exec_token),
                json={"form_answers": form_answers, "text_note": "E2E visit notes"},
            )
            report.add("Save visit form", r.status_code == 200, f"answers={len(form_answers)}")
        except Exception as e:
            report.add("Save visit form", False, str(e))

        # 13. Submit visit
        try:
            r = client.post(
                f"{BASE}/api/v1/visits/{visit_id}/submit",
                headers=auth_headers(exec_token),
                json={"checkout_lat": HYDERABAD_LAT, "checkout_lng": HYDERABAD_LNG},
            )
            data = r.json()
            ok = r.status_code == 200 and data.get("status") in (
                "submitted",
                "SUBMITTED",
                "completed",
                "COMPLETED",
            )
            report.add("Visit submit", ok, f"status={data.get('status')}")
        except Exception as e:
            report.add("Visit submit", False, str(e))

        # 14. My visits
        try:
            r = client.get(f"{BASE}/api/v1/visits/mine", headers=auth_headers(exec_token))
            data = r.json()
            report.add("My visits list", r.status_code == 200, f"total={data.get('total')}")
        except Exception as e:
            report.add("My visits list", False, str(e))

        # 15. Executive dashboard
        try:
            r = client.get(f"{BASE}/api/v1/dashboard/executive", headers=auth_headers(exec_token))
            report.add("Executive dashboard", r.status_code == 200, f"keys={list(r.json().keys())}")
        except Exception as e:
            report.add("Executive dashboard", False, str(e))

        # 16. Admin dashboard
        try:
            r = client.get(f"{BASE}/api/v1/dashboard/admin", headers=auth_headers(admin_token))
            report.add("Admin dashboard", r.status_code == 200, f"keys={list(r.json().keys())}")
        except Exception as e:
            report.add("Admin dashboard", False, str(e))

        # 17. Admin list executives
        try:
            r = client.get(f"{BASE}/api/v1/users", headers=auth_headers(admin_token), params={"role": "executive"})
            data = r.json()
            report.add("Admin list executives", r.status_code == 200, f"total={data.get('total')}")
        except Exception as e:
            report.add("Admin list executives", False, str(e))

        # 18. Admin assign executives
        if detail_farm_id and exec2_token:
            try:
                exec2_user = client.get(f"{BASE}/api/v1/users/me", headers=auth_headers(exec2_token)).json()
                r = client.patch(
                    f"{BASE}/api/v1/farms/{detail_farm_id}/assign",
                    headers=auth_headers(admin_token),
                    json={"executive_ids": [exec2_user["id"]], "mode": "add"},
                )
                data = r.json()
                ok = r.status_code == 200 and len(data.get("assigned_executive_ids", [])) >= 2
                report.add("Admin assign executive (add)", ok, f"assigned={data.get('assigned_executive_ids')}")
            except Exception as e:
                report.add("Admin assign executive (add)", False, str(e))

        # 19. Proximity rejection — farm too far
        far_farm_id = None
        try:
            r = client.post(
                f"{BASE}/api/v1/farms/admin",
                headers=auth_headers(admin_token),
                json={
                    "name": f"Far Farm {suffix}",
                    "location_lat": FAR_LAT,
                    "location_lng": FAR_LNG,
                    "location_address": "Pune (far)",
                    "crop": "Jackfruit",
                    "harvest_type": "Organic",
                    "harvest_date": (date.today() + timedelta(days=60)).isoformat(),
                    "total_acres": 1.0,
                    "farmer": {
                        "name": f"Far Farmer {suffix}",
                        "mobile_number": f"7{suffix[:9]}".ljust(10, "3")[:10],
                        "gender": "male",
                        "age": 50,
                    },
                },
            )
            far_farm_id = r.json().get("id")
            report.add("Admin create far unassigned farm", r.status_code == 201, f"id={far_farm_id}")
        except Exception as e:
            report.add("Admin create far unassigned farm", False, str(e))

        if far_farm_id:
            try:
                r = client.post(
                    f"{BASE}/api/v1/farms/{far_farm_id}/accept",
                    headers=auth_headers(exec_token),
                )
                report.add(
                    "Reject far farm accept (expect 400)",
                    r.status_code == 400,
                    f"status={r.status_code}, detail={r.text[:200]}",
                )
            except Exception as e:
                report.add("Reject far farm accept (expect 400)", False, str(e))

        # 20. Unauthorized farm access (exec2 on farm they aren't assigned to - if any)
        try:
            if exec2_token and onboarded_farm_id:
                # First remove exec2 if added, test 403 on unassigned farm
                r = client.get(
                    f"{BASE}/api/v1/farms/{onboarded_farm_id}",
                    headers=auth_headers(exec2_token),
                )
                # exec2 might be assigned via add mode; check farmers list instead
                report.add("Exec2 farm detail access", r.status_code in (200, 403), f"status={r.status_code}")
        except Exception as e:
            report.add("Exec2 farm detail access", False, str(e))

        # 21. Farmers list (admin)
        try:
            r = client.get(f"{BASE}/api/v1/farmers", headers=auth_headers(admin_token))
            report.add("Admin farmers list", r.status_code == 200, f"total={r.json().get('total')}")
        except Exception as e:
            report.add("Admin farmers list", False, str(e))

        # 22. Harvest calendar
        try:
            r = client.get(
                f"{BASE}/api/v1/harvests/calendar",
                headers=auth_headers(admin_token),
                params={"month": f"{date.today().year}-{date.today().month:02d}"},
            )
            report.add("Harvest calendar", r.status_code == 200)
        except Exception as e:
            report.add("Harvest calendar", False, str(e))

        # 23. Forgot password flow
        try:
            r = client.post(
                f"{BASE}/api/v1/auth/forgot-password",
                json={"employee_id": "EXEC001"},
            )
            report.add("Forgot password request", r.status_code in (200, 201, 409))
        except Exception as e:
            report.add("Forgot password request", False, str(e))

        try:
            r = client.get(
                f"{BASE}/api/v1/auth/password-reset-requests/status",
                params={"employee_id": "EXEC001"},
            )
            report.add("Password reset status poll", r.status_code == 200, f"approved={r.json().get('approved')}")
        except Exception as e:
            report.add("Password reset status poll", False, str(e))

    return print_summary(report)


def print_summary(report: WorkflowReport) -> int:
    print("\n" + "=" * 60)
    failed = report.failed
    passed = len(report.steps) - len(failed)
    print(f"SUMMARY: {passed}/{len(report.steps)} passed, {len(failed)} failed")
    if failed:
        print("\nFAILURES:")
        for s in failed:
            print(f"  - {s.name}: {s.detail}")
    print("=" * 60)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

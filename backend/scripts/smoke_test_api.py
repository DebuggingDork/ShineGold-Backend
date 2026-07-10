"""Smoke-test Shine Gold API endpoints used by the Flutter app."""
from __future__ import annotations

import sys
from dataclasses import dataclass

import httpx

BASE = "http://127.0.0.1:8011"
EXEC_ID = "EXEC001"
ADMIN_ID = "ADMIN001"
PASSWORD = "ChangeMe123!"


@dataclass
class Result:
    method: str
    path: str
    status: int
    ok: bool
    note: str = ""


results: list[Result] = []


def record(method: str, path: str, status: int, ok: bool, note: str = "") -> None:
    results.append(Result(method, path, status, ok, note))
    mark = "OK" if ok else "FAIL"
    print(f"[{mark}] {method} {path} -> {status} {note}")


def login(client: httpx.Client, employee_id: str) -> str:
    r = client.post(
        f"{BASE}/api/v1/auth/login",
        json={"employee_id": employee_id, "password": PASSWORD},
    )
    record("POST", "/api/v1/auth/login", r.status_code, r.status_code == 200, employee_id)
    r.raise_for_status()
    return r.json()["access_token"]


def parse_items(data) -> list:
    if isinstance(data, dict):
        return data.get("items") or []
    if isinstance(data, list):
        return data
    return []


def main() -> int:
    with httpx.Client(timeout=30.0) as client:
        r = client.get(f"{BASE}/health")
        record("GET", "/health", r.status_code, r.status_code == 200)

        exec_token = login(client, EXEC_ID)
        admin_token = login(client, ADMIN_ID)
        exec_headers = {"Authorization": f"Bearer {exec_token}"}
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        def get(path: str, headers: dict, ok_codes: set[int] | None = None) -> httpx.Response:
            ok_codes = ok_codes or {200}
            r = client.get(f"{BASE}{path}", headers=headers)
            record("GET", path, r.status_code, r.status_code in ok_codes)
            return r

        get("/api/v1/users/me", exec_headers)
        get("/api/v1/dashboard/executive", exec_headers)
        get("/api/v1/dashboard/admin", admin_headers)
        get("/api/v1/users", admin_headers)

        farms_r = get("/api/v1/farms", exec_headers)
        farms = parse_items(farms_r.json()) if farms_r.status_code == 200 else []
        get("/api/v1/farms/invitations", exec_headers)

        farm_id = farms[0]["id"] if farms else None
        if farm_id:
            get(f"/api/v1/farms/{farm_id}", exec_headers)

        visits_r = get("/api/v1/visits/mine", exec_headers)
        visits = parse_items(visits_r.json()) if visits_r.status_code == 200 else []

        get("/api/v1/visit-forms/active", admin_headers)

        visit_id = (
            visits[0].get("visit_id") or visits[0].get("id") if visits else None
        )
        if visit_id:
            get(f"/api/v1/visit-forms/visits/{visit_id}/context", exec_headers)
            get(f"/api/v1/visits/{visit_id}", exec_headers)

        get("/api/v1/farmers", admin_headers)
        from datetime import date

        today = date.today()
        start = today.replace(day=1)
        end = date(today.year + 1, today.month, today.day)
        r = client.get(
            f"{BASE}/api/v1/harvests/calendar",
            headers=admin_headers,
            params={"date_from": str(start), "date_to": str(end)},
        )
        record("GET", "/api/v1/harvests/calendar", r.status_code, r.status_code == 200)

        users_r = get("/api/v1/users", admin_headers)
        users = parse_items(users_r.json()) if users_r.status_code == 200 else []
        if not users and users_r.status_code == 200:
            raw = users_r.json()
            users = raw if isinstance(raw, list) else []
        exec_user = next((u for u in users if u.get("role") == "executive"), None)
        if exec_user:
            get(f"/api/v1/users/{exec_user['id']}/visits", admin_headers)

        r = client.get(
            f"{BASE}/api/v1/auth/password-reset-requests/status",
            params={"employee_id": "UNKNOWN"},
        )
        record("GET", "/api/v1/auth/password-reset-requests/status", r.status_code, r.status_code in {200, 404})

    failed = [x for x in results if not x.ok]
    print(f"\n--- {len(results) - len(failed)}/{len(results)} passed ---")
    if failed:
        for f in failed:
            print(f"  FAILED: {f.method} {f.path} ({f.status}) {f.note}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

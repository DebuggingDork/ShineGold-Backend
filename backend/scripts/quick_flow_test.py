"""Quick manual flow test for proximity + visit form."""
import sys
import uuid
from datetime import date, timedelta
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from api_base import API_BASE as BASE
PWD = "ChangeMe123!"


def main() -> None:
    c = httpx.Client(timeout=30)
    admin = c.post(
        f"{BASE}/api/v1/auth/login",
        json={"employee_id": "ADMIN001", "password": PWD},
    ).json()["access_token"]
    exec_t = c.post(
        f"{BASE}/api/v1/auth/login",
        json={"employee_id": "EXEC001", "password": PWD},
    ).json()["access_token"]
    ah = {"Authorization": f"Bearer {admin}"}
    eh = {"Authorization": f"Bearer {exec_t}"}
    suffix = uuid.uuid4().hex[:6]

    body = {
        "name": f"Prox {suffix}",
        "location_lat": 17.42,
        "location_lng": 78.5,
        "location_address": "near",
        "crop": "Jackfruit",
        "harvest_type": "Organic",
        "harvest_date": (date.today() + timedelta(days=90)).isoformat(),
        "total_acres": 2,
        "farmer": {
            "name": "F",
            "mobile_number": "9123456789",
            "gender": "male",
            "age": 40,
        },
    }
    r = c.post(f"{BASE}/api/v1/farms/admin", headers=ah, json=body)
    print("admin farm", r.status_code, r.text[:200])
    farm_id = r.json().get("id")

    r = c.get(
        f"{BASE}/api/v1/farms/invitations",
        headers=eh,
        params={"lat": 17.385, "lng": 78.4867},
    )
    items = r.json().get("items", [])
    print("invitations", len(items), "found", any(i["id"] == farm_id for i in items))

    r = c.post(f"{BASE}/api/v1/farms/{farm_id}/accept", headers=eh)
    print("accept", r.status_code, r.text[:200])

    r = c.get(
        f"{BASE}/api/v1/visits/mine",
        headers=eh,
        params={"status": "in_progress"},
    )
    for v in r.json().get("items", []):
        vid = v["id"]
        c.post(f"{BASE}/api/v1/visits/{vid}/cancel", headers=eh)
        print("cancelled", vid)

    r = c.post(
        f"{BASE}/api/v1/visits/checkin",
        headers=eh,
        json={"farm_id": farm_id, "checkin_lat": 17.42, "checkin_lng": 78.5},
    )
    print("checkin", r.status_code, r.text[:200])
    visit_id = r.json().get("visit_id")

    r = c.get(f"{BASE}/api/v1/visit-forms/visits/{visit_id}/context", headers=eh)
    print("form context", r.status_code)
    if r.status_code == 200:
        data = r.json()
        qs = data.get("questions") or data.get("template", {}).get("questions", [])
        print("questions", len(qs))

    r = c.post(
        f"{BASE}/api/v1/visits/{visit_id}/submit",
        headers=eh,
        json={"checkout_lat": 17.42, "checkout_lng": 78.5},
    )
    print("submit", r.status_code, r.text[:300])


if __name__ == "__main__":
    main()

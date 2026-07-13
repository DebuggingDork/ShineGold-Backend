"""Check visit history returned by farm detail API for recently visited farms."""
from __future__ import annotations

import httpx

BASE = "http://127.0.0.1:8080"


def main() -> None:
    c = httpx.Client(timeout=30)
    r = c.post(
        f"{BASE}/api/v1/auth/login",
        json={"employee_id": "EXEC001", "password": "ChangeMe123!"},
    )
    tok = r.json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}

    r = c.get(f"{BASE}/api/v1/visits/mine", headers=h, params={"page_size": 50})
    data = r.json()
    visits = data if isinstance(data, list) else data.get("items", data.get("visits", []))
    print(f"my-visits: {r.status_code}, count={len(visits)}")
    if visits:
        print("item keys:", sorted(visits[0].keys()))
    farm_ids: dict[str, str] = {}
    for v in visits:
        farm = v.get("farm") or {}
        fid = v.get("farm_id") or farm.get("id") or farm.get("farm_id")
        fname = v.get("farm_name") or farm.get("name") or farm.get("farm_name")
        print(
            f"  visit {str(v.get('id') or v.get('visit_id'))[:8]} | farm={fname}"
            f" | status={v.get('status')} | checkin={str(v.get('checkin_time'))[:16]}"
        )
        if fid:
            farm_ids[str(fid)] = str(fname)

    print("\n--- farm detail visit_logs ---")
    for fid, fname in farm_ids.items():
        r = c.get(f"{BASE}/api/v1/farms/{fid}", headers=h)
        if r.status_code != 200:
            print(f"{fname}: HTTP {r.status_code}: {r.text[:200]}")
            continue
        fd = r.json()
        logs = fd.get("visit_logs", [])
        print(f"{fname}: {len(logs)} logs | farm photos: {len(fd.get('photos') or [])}")
        for l in logs:
            print(
                f"    log visit_id={str(l.get('visit_id'))[:8]} date={l.get('date')}"
                f" photos={len(l.get('photos', []))} voice={bool(l.get('voice_note'))}"
            )


if __name__ == "__main__":
    main()

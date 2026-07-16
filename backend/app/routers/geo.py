"""Address search / geocode helpers (Nominatim proxy for mobile clients).

Android emulators often cannot reach the public internet, while they can reach
this API via adb reverse. Proxying Nominatim through the backend keeps address
autocomplete working in that environment.
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/v1/geo", tags=["geo"])

_NOMINATIM = "https://nominatim.openstreetmap.org"
_HEADERS = {
    "User-Agent": "ShineGoldBackend/1.0 (executive-home-location)",
    "Accept": "application/json",
}


@router.get("/search")
async def search_address(
    q: str = Query(min_length=2, max_length=200),
    limit: int = Query(default=8, ge=1, le=15),
    _current_user: User = Depends(get_current_user),
):
    query = q.strip()
    if len(query) < 2:
        return {"items": []}

    params = {
        "q": query,
        "format": "json",
        "limit": limit,
        "countrycodes": "in",
        "addressdetails": 1,
    }

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.get(
                f"{_NOMINATIM}/search",
                params=params,
                headers=_HEADERS,
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Address search unavailable: {exc}",
        ) from exc

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Address search provider returned an error",
        )

    items: list[dict] = []
    for row in response.json():
        if not isinstance(row, dict):
            continue
        try:
            lat = float(row["lat"])
            lng = float(row["lon"])
        except (KeyError, TypeError, ValueError):
            continue
        name = row.get("display_name")
        if not name:
            continue
        items.append(
            {
                "display_name": name,
                "lat": lat,
                "lng": lng,
            }
        )

    return {"items": items}

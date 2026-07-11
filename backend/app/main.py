from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, dashboard, farmers, farms, harvests, uploads, users, visit_forms, visits

app = FastAPI(title="ShineGold API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(uploads.router)
app.include_router(farms.router)
app.include_router(visits.router)
app.include_router(visit_forms.router)
app.include_router(farmers.router)
app.include_router(harvests.router)
app.include_router(dashboard.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
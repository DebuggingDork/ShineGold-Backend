from fastapi import FastAPI

from app.routers import auth, farms, uploads, users, visits

app = FastAPI(title="ShineGold API", version="0.1.0")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(uploads.router)
app.include_router(farms.router)
app.include_router(visits.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
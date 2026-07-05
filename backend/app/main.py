from fastapi import FastAPI

from app.routers import auth, uploads, users

app = FastAPI(title="ShineGold API", version="0.1.0")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(uploads.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
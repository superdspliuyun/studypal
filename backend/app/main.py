"""FastAPI application entrypoint.

Mounts CORS, /static, and the two feature routers. CORS origins come from
settings so dev and prod can override without code changes.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import analytics as analytics_router
from app.routers import auth as auth_router
from app.routers import chat as chat_router
from app.routers import profile as profile_router


app = FastAPI(title="StudyPal Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth_router.router)
app.include_router(profile_router.router)
app.include_router(chat_router.router)
app.include_router(analytics_router.router)


@app.get("/healthz", include_in_schema=False)
def healthz() -> dict[str, str]:
    return {"status": "ok"}
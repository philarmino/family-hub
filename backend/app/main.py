from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .database import SessionLocal, init_db
from .routers import bring, meals, members, weeks
from .services.seed import seed_example_meals

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    settings = get_settings()
    async with SessionLocal() as db:
        try:
            n = await seed_example_meals(db, settings)
            if n:
                logger.info("Seeded %s example meals", n)
        except Exception:  # noqa: BLE001
            logger.exception("Seeding example meals failed")
    yield


app = FastAPI(title="Family Hub", lifespan=lifespan)


@app.middleware("http")
async def ensure_utf8_json(request, call_next):
    response = await call_next(request)
    content_type = response.headers.get("content-type", "")
    if content_type.startswith("application/json") and "charset" not in content_type:
        response.headers["content-type"] = "application/json; charset=utf-8"
    elif content_type.startswith("text/html") and "charset" not in content_type:
        response.headers["content-type"] = "text/html; charset=utf-8"
    return response


app.include_router(meals.router)
app.include_router(members.router)
app.include_router(weeks.router)
app.include_router(bring.router)

settings = get_settings()
photos_dir = settings.data_dir / "photos"
photos_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media/photos", StaticFiles(directory=str(photos_dir)), name="photos")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@app.get("/api/health")
async def health():
    return {"ok": True, "service": "family-hub"}


if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        candidate = STATIC_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        index = STATIC_DIR / "index.html"
        if index.exists():
            return FileResponse(index)
        return {"detail": "Frontend nicht gebaut"}

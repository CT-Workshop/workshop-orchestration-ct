from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.database import init_db
from app.routers import admin, closings, debug, webhooks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting %s (%s)", settings.app_name, settings.environment)
    await init_db()
    yield
    logger.info("Shutdown %s", settings.app_name)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/healthz", tags=["health"])
    async def healthz():
        return {"status": "ok", "service": settings.app_name}

    app.include_router(closings.router)
    app.include_router(webhooks.router)
    app.include_router(admin.router)
    app.include_router(debug.router)
    return app


app = create_app()

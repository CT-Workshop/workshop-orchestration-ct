from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import get_settings
from app.database import engine
from app.routers import admin, closings, debug, webhooks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEALTH_TIMEOUT_SECONDS = 2.0


async def check_postgres() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning("healthz postgres check failed: %s", type(exc).__name__)
        return False


async def check_redis() -> bool:
    import redis.asyncio as redis

    client = None
    try:
        client = redis.from_url(
            get_settings().celery_broker_url,
            socket_connect_timeout=HEALTH_TIMEOUT_SECONDS,
            socket_timeout=HEALTH_TIMEOUT_SECONDS,
        )
        await client.ping()
        return True
    except Exception as exc:
        logger.warning("healthz redis check failed: %s", type(exc).__name__)
        return False
    finally:
        if client is not None:
            await client.aclose()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting %s (%s)", settings.app_name, settings.environment)
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
        postgres_ok = await check_postgres()
        redis_ok = await check_redis()
        healthy = postgres_ok and redis_ok
        payload = {
            "status": "ok" if healthy else "unhealthy",
            "service": settings.app_name,
            "checks": {
                "postgres": "ok" if postgres_ok else "down",
                "redis": "ok" if redis_ok else "down",
            },
        }
        if not healthy:
            return JSONResponse(status_code=503, content=payload)
        return payload

    app.include_router(closings.router)
    app.include_router(webhooks.router)
    app.include_router(admin.router)
    app.include_router(debug.router)
    return app


app = create_app()

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app


def test_healthz_ok_when_dependencies_up() -> None:
    with (
        patch("app.main.check_postgres", new_callable=AsyncMock, return_value=True),
        patch("app.main.check_redis", new_callable=AsyncMock, return_value=True),
        TestClient(app) as client,
    ):
        response = client.get("/healthz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["postgres"] == "ok"
    assert body["checks"]["redis"] == "ok"


def test_healthz_503_when_postgres_down() -> None:
    with (
        patch("app.main.check_postgres", new_callable=AsyncMock, return_value=False),
        patch("app.main.check_redis", new_callable=AsyncMock, return_value=True),
        TestClient(app) as client,
    ):
        response = client.get("/healthz")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unhealthy"
    assert body["checks"]["postgres"] == "down"
    assert body["checks"]["redis"] == "ok"


def test_healthz_503_when_redis_down() -> None:
    with (
        patch("app.main.check_postgres", new_callable=AsyncMock, return_value=True),
        patch("app.main.check_redis", new_callable=AsyncMock, return_value=False),
        TestClient(app) as client,
    ):
        response = client.get("/healthz")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unhealthy"
    assert body["checks"]["postgres"] == "ok"
    assert body["checks"]["redis"] == "down"

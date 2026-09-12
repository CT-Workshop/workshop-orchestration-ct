import asyncio
import uuid

from fastapi import HTTPException

from app.deps import (
    ClosingActor,
    parse_closing_tenant_keys,
    require_closing_actor,
    resolve_closing_actor,
)
from app.routers.closings import _closing_for_tenant


def test_parse_closing_tenant_keys() -> None:
    assert parse_closing_tenant_keys("") == {}
    assert parse_closing_tenant_keys("lender-north:secret-north,lender-south:secret-south") == {
        "lender-north": "secret-north",
        "lender-south": "secret-south",
    }


def test_resolve_closing_actor_maps_secret_to_org() -> None:
    keys = {"lender-north": "secret-north", "lender-south": "secret-south"}
    actor = resolve_closing_actor("secret-north", keys)
    assert actor == ClosingActor(lender_org_id="lender-north")
    assert resolve_closing_actor("wrong", keys) is None
    assert resolve_closing_actor("secret-north", {}) is None


def test_require_closing_actor_rejects_missing_and_unknown_tokens() -> None:
    missing = None
    try:
        asyncio.run(require_closing_actor(authorization=None, x_api_key=None))
    except HTTPException as exc:
        missing = exc
    assert missing is not None and missing.status_code == 401

    unknown = None
    try:
        asyncio.run(
            require_closing_actor(authorization="Bearer not-a-configured-key", x_api_key=None)
        )
    except HTTPException as exc:
        unknown = exc
    assert unknown is not None and unknown.status_code == 401


class _FakeResult:
    def __init__(self, row):
        self._row = row

    def scalar_one_or_none(self):
        return self._row


class _FakeSession:
    def __init__(self, row):
        self._row = row

    async def execute(self, _stmt):
        return _FakeResult(self._row)


class _FakeClosing:
    def __init__(self, lender_org_id: str):
        self.lender_org_id = lender_org_id


def test_closing_for_tenant_hides_cross_tenant_and_missing() -> None:
    actor = ClosingActor(lender_org_id="lender-north")
    closing_id = uuid.UUID("00000000-0000-4000-8000-000000000001")

    missing = None
    try:
        asyncio.run(_closing_for_tenant(_FakeSession(None), closing_id, actor))
    except HTTPException as exc:
        missing = exc
    assert missing is not None and missing.status_code == 404

    cross = None
    try:
        asyncio.run(_closing_for_tenant(_FakeSession(_FakeClosing("lender-south")), closing_id, actor))
    except HTTPException as exc:
        cross = exc
    assert cross is not None and cross.status_code == 404

    owned = _FakeClosing("lender-north")
    assert asyncio.run(_closing_for_tenant(_FakeSession(owned), closing_id, actor)) is owned

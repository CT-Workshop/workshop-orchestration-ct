from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.wire import WireHoldReleaseRequest, WireWindowResponse
from app.services import funding_service, wire_cutoff

router = APIRouter(prefix="/closings", tags=["funding"])


@router.get("/{closing_id}/wire-window", response_model=WireWindowResponse)
async def get_wire_window(
    closing_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> WireWindowResponse:
    try:
        payload = await wire_cutoff.wire_window_payload(db, closing_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Closing not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return WireWindowResponse(**payload)


@router.post("/{closing_id}/wire-hold/release")
async def release_wire_hold(
    closing_id: uuid.UUID,
    body: WireHoldReleaseRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        hold = await wire_cutoff.release_hold(
            db, closing_id, released_by=body.released_by
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await db.commit()
    return {
        "hold_id": str(hold.id),
        "active": hold.active,
        "released_by": hold.released_by,
        "note": body.note,
    }


@router.post("/{closing_id}/funding/evaluate")
async def evaluate_funding(
    closing_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    try:
        chk = await funding_service.evaluate_funding_readiness(db, closing_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Closing not found") from None
    await db.commit()
    window = await wire_cutoff.wire_window_payload(db, closing_id)
    return {
        "all_cleared": chk.all_cleared,
        "evaluated_by": chk.evaluated_by,
        "wire": window,
    }

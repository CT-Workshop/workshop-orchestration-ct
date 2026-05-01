from __future__ import annotations

import logging
import uuid

from sqlalchemy import select

from app.services.callback_client import fetch_callback_preview
from app.tasks.celery_app import celery_app
from app.worker_db import sync_session

logger = logging.getLogger(__name__)


@celery_app.task(name="cos.send_reminder")
def send_reminder_task(closing_id: str, channel: str, template: str) -> dict:
    """
    Placeholder delivery — real stack would render templates and hit SNS / SendGrid.
    """
    logger.info(
        "reminder dispatched closing=%s channel=%s template=%s",
        closing_id,
        channel,
        template,
    )
    return {"ok": True, "closing_id": closing_id, "channel": channel, "template": template}


@celery_app.task(name="cos.sync_los_callback")
def sync_los_callback_task(closing_id: str, callback_url: str) -> dict:
    """
    SSRF-prone outbound GET issued from worker network context.
    """
    logger.info("los callback sync closing=%s url=%s", closing_id, callback_url)
    preview = fetch_callback_preview(callback_url)
    return {"closing_id": closing_id, "preview": preview}


@celery_app.task(name="cos.evaluate_funding")
def evaluate_funding_task(closing_id: str) -> dict:
    """
    Sync ORM path for worker-side funding evaluation.
    """
    try:
        cid = uuid.UUID(closing_id)
    except ValueError:
        return {"ok": False, "error": "invalid closing_id"}

    from app.models import ClosingCase, FundingChecklist, WorkflowState
    from app.models.enums import ActorType
    from app.services.workflow_engine import can_transition

    session = sync_session()
    try:
        closing = session.get(ClosingCase, cid)
        if closing is None:
            return {"ok": False, "error": "not_found"}

        chk = session.execute(
            select(FundingChecklist).where(FundingChecklist.closing_id == cid)
        ).scalar_one_or_none()
        if chk is None:
            from app.services.funding_service import DEFAULT_ITEMS

            chk = FundingChecklist(closing_id=cid, items=list(DEFAULT_ITEMS), all_cleared=False)
            session.add(chk)
            session.flush()

        items = list(chk.items or [])
        all_cleared = bool(items) and all(bool(i.get("done")) for i in items)
        chk.all_cleared = all_cleared

        moved = False
        if all_cleared and closing.state == WorkflowState.SIGNED.value:
            if can_transition(closing.state, WorkflowState.FUNDING_READY.value):
                _apply_transition_sync(
                    session,
                    closing,
                    WorkflowState.FUNDING_READY.value,
                    ActorType.SYSTEM,
                    "funding_worker",
                    {"checklist_id": str(chk.id)},
                )
                moved = True
        elif all_cleared and closing.state == WorkflowState.FUNDING_READY.value:
            if can_transition(closing.state, WorkflowState.CLOSED.value):
                _apply_transition_sync(
                    session,
                    closing,
                    WorkflowState.CLOSED.value,
                    ActorType.SYSTEM,
                    "funding_worker",
                    {"checklist_id": str(chk.id)},
                )
                moved = True

        session.commit()
        return {"ok": True, "closing_id": closing_id, "all_cleared": all_cleared, "moved": moved}
    except Exception as exc:  # noqa: BLE001
        logger.exception("funding evaluation failed")
        session.rollback()
        return {"ok": False, "error": str(exc)}
    finally:
        session.close()


def _apply_transition_sync(session, closing, to_state: str, actor_type, actor_id: str, payload: dict):
    from app.models import WorkflowEvent

    prev = closing.state
    closing.state = to_state
    session.add(
        WorkflowEvent(
            closing_id=closing.id,
            from_state=prev,
            to_state=to_state,
            actor_type=actor_type.value,
            actor_id=actor_id,
            payload=payload,
        )
    )

"""Enqueue Celery work after a successful commit without failing the request."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def enqueue_after_commit(task: Any, *args: Any, **kwargs: Any) -> bool:
    """
    Publish a task after the DB transaction has committed.

    Broker/connection failures must not turn a persisted write into an HTTP error;
    callers retrying that error would otherwise insert duplicate rows.
    """
    try:
        task.delay(*args, **kwargs)
        return True
    except Exception:
        logger.exception("celery enqueue failed after commit task=%s", getattr(task, "name", task))
        return False

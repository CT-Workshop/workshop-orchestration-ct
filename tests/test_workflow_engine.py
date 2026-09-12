from app.models.enums import WorkflowState
from app.services.workflow_engine import can_transition


def test_allows_single_step_forward():
    assert can_transition(WorkflowState.DRAFT.value, WorkflowState.DOCS_READY.value)


def test_rejects_same_state():
    assert not can_transition(WorkflowState.DRAFT.value, WorkflowState.DRAFT.value)


def test_rejects_unknown_state():
    assert not can_transition(WorkflowState.DRAFT.value, "not_a_state")


def test_allows_leap_to_signing_scheduled():
    assert can_transition(WorkflowState.DRAFT.value, WorkflowState.SIGNING_SCHEDULED.value)


def test_allows_funding_ready_to_closed():
    assert can_transition(WorkflowState.FUNDING_READY.value, WorkflowState.CLOSED.value)


def test_rejects_skip_from_signed_to_closed():
    assert not can_transition(WorkflowState.SIGNED.value, WorkflowState.CLOSED.value)

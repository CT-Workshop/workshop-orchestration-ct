from app.models.enums import WorkflowState
from app.services.partner_webhook_service import partner_driven_next_state


def test_ignores_client_target_state_for_privileged_states() -> None:
    for target in (
        WorkflowState.SIGNING_SCHEDULED.value,
        WorkflowState.SIGNED.value,
        WorkflowState.FUNDING_READY.value,
        WorkflowState.CLOSED.value,
    ):
        assert (
            partner_driven_next_state("force_advance", WorkflowState.DRAFT.value, target)
            is None
        )


def test_ignores_target_state_even_when_it_matches_a_legal_step() -> None:
    assert (
        partner_driven_next_state(
            "unmapped_event",
            WorkflowState.DRAFT.value,
            WorkflowState.DOCS_READY.value,
        )
        is None
    )


def test_documents_packaged_maps_draft_to_docs_ready() -> None:
    assert (
        partner_driven_next_state(
            "documents_packaged",
            WorkflowState.DRAFT.value,
            WorkflowState.CLOSED.value,
        )
        == WorkflowState.DOCS_READY.value
    )


def test_borrower_acknowledged_maps_docs_ready() -> None:
    assert (
        partner_driven_next_state(
            "borrower_acknowledged",
            WorkflowState.DOCS_READY.value,
            WorkflowState.SIGNED.value,
        )
        == WorkflowState.BORROWER_REVIEW.value
    )


def test_mapped_event_does_not_fire_from_wrong_state() -> None:
    assert (
        partner_driven_next_state(
            "documents_packaged",
            WorkflowState.SIGNED.value,
            WorkflowState.CLOSED.value,
        )
        is None
    )

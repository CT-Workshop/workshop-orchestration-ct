# Decision record — partner webhook idempotency

## Title

Reject duplicate partner deliveries; do not apply the workflow transition twice.

## Summary

LOS retries were creating a second `partner_webhook_events` row and a second
state change. We now key deliveries on `(partner_id, idempotency_key)` and
return the original event on replay.

## Rationale

Idempotency is a delivery contract. HMAC is an authenticity contract. Mixing
them would block this fix behind partner onboarding. Title needs the replay
stop today.

## Alternatives

1. HMAC-gate all `/webhooks/partner` traffic — rejected (partners not ready).
2. Unique `(partner_id, idempotency_key)` + replay response — accepted.
3. Continue inserting every retry — rejected (double `docs_ready`).

## Drivers

- Retries are normal on LOS HTTP 502 / timeout.
- Workflow `_ORDER` is single-step; a replayed `target_state` is not harmless.
- Ops needs a stable `stored_event_id` for the first delivery.

## Topic

`partner-webhook-idempotency`

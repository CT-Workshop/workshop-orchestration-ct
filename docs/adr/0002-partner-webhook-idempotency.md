# ADR 0002 — Enforce partner webhook idempotency, defer HMAC

**Status:** Accepted  
**Date:** 2026-09-11  
**Deciders:** ClosingDesk Team 1 (orchestration)  
**Change:** stop replayed LOS callbacks from applying a second workflow transition

## Context

`PartnerWebhookEvent.idempotency_key` is stored today and then ignored. A retried
`documents_packaged` or `target_state` callback creates a new row and can walk
the closing forward twice. Title has already seen files jump `draft → docs_ready`
on a single LOS retry.

HMAC is still missing. That is a separate trust problem. Replay mutation is the
bug we can close without asking every partner to rotate secrets this week.

## Decision

Treat `(partner_id, idempotency_key)` as a unique delivery:

- Missing key is rejected when `PARTNER_IDEMPOTENCY_REQUIRED=true` (default).
- First delivery processes the transition and stores the row.
- Later deliveries with the same pair return HTTP 200, `replayed=true`, and the
  original `stored_event_id`. They do **not** call `apply_transition` again.
- HMAC verification stays out of this PR.

## Alternatives considered

| Option | Pros | Cons | Outcome |
|---|---|---|---|
| A. Require HMAC now | Stops spoofed partners | Every LOS must ship a secret this sprint | Rejected |
| B. Enforce idempotency only (chosen) | Stops double state changes immediately | Unsigned bodies can still be forged once | **Accepted** |
| C. Keep storing replays as new rows | Zero partner change | Duplicate transitions in production | Rejected |

## Implications accepted

- Partners that omit `idempotency_key` get 400 until they send one.
- Ops can tell a retry from a new event via `replayed` without reading logs.
- HMAC remains an intentional follow-up, not silently implied by this PR.

## Why B won

The live miss is **replay**, not first-delivery authenticity. Closing the replay
hole does not wait on partner secret distribution.

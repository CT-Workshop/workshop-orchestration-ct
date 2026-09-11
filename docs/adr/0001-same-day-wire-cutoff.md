# ADR 0001 — Same-day wire cutoff is an overlay hold, not a workflow state

**Status:** Accepted  
**Date:** 2026-09-11  
**Deciders:** ClosingDesk Team 1 (orchestration)  
**Change:** same-day ACH / wire window for `funding_ready` closings

## Context

Title companies lose same-day wires if funding is marked closed after the bank cutoff
(typically 15:00 America/New_York). The current engine treats “checklist complete” as
permission to jump `funding_ready → closed`. That is wrong after cutoff: the money
cannot move until the next banking day.

## Decision

Keep the workflow states unchanged. Add a **parallel wire-hold overlay**:

- Evaluate cutoff in the configured IANA timezone (default `America/New_York`).
- If local time is on or after `WIRE_CUTOFF_HOUR` (default 15), do **not** close.
- Persist a `wire_holds` row with reason `past_same_day_cutoff`.
- Ops can release the hold explicitly; the next evaluate may then close.

## Alternatives considered

| Option | Pros | Cons | Outcome |
|---|---|---|---|
| A. New `funding_held` workflow state | Visible in status machine | Breaks single-step `_ORDER`, partner webhooks, and LOS callbacks | Rejected |
| B. Overlay hold (chosen) | No state-machine rewrite; hold is reversible | Status payload must grow a `wire` block | **Accepted** |
| C. Warn-only, still close | Zero workflow risk | Funds show closed when the wire cannot leave | Rejected — lies to lender and title |

## Implications accepted

- Checklist `all_cleared` no longer implies “wire left the bank today”.
- Celery reminder templates must mention the cutoff, not only “docs missing”.
- Title-company local time, not UTC, is the source of truth for the window.

## Why B won

Partner webhooks already send `target_state` with loose coupling. Inserting
`funding_held` would invalidate those contracts in one release. An overlay can
ship without asking every LOS to learn a new state.

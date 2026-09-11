# Decision record — same-day wire cutoff

## Title

Do not auto-close a closing after the same-day wire cutoff.

## Summary

Funding readiness and wire dispatch are different events. After 15:00
America/New_York we hold the close, persist why, and wait for the next
banking day or an explicit ops release.

## Rationale

Closing `funding_ready` after cutoff caused title desks to tell borrowers
“funded” while the bank rejected the wire. That is an operational miss, not
a checklist miss. The hold is therefore **not** another checklist item.

## Alternatives

1. Add `funding_held` to `WorkflowState` — rejected (breaks partner target_state).
2. Overlay `wire_holds` table — accepted.
3. Close anyway and emit a warning — rejected (false closed state).

## Drivers

- Bank cutoff is a clock rule, not a document rule.
- LOS partners must keep sending the same `target_state` values.
- Ops needs a reversible override without rewriting history.

## Topic

`same-day-wire-cutoff-overlay`

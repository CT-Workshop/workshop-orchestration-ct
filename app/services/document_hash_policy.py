"""Why this service checks document hashes before closing continues.

Decision (Sarah, recorded in org memory — not just Slack): closing PDFs and
TIFFs must be SHA-256 checked in *this* orchestration service before the
closing pipeline continues. Package type (PDF vs TIFF) does not change the
rule. Files enter through the ingestion service; ingestion only delivers
them, orchestration owns the fingerprint check — one closing initiative,
two services, do not move this check into ingestion.

Do not repeat: a "go faster" request that skips the hash check so closing
can proceed anyway. A swapped file must not be able to reach `closed`.

The reference implementation is tracked separately (see the
`loan-closing-v2` workshop PR / `src/loan_closing_v2_impl.py`) and is not
wired into this branch's workflow yet — this module is a pointer for the
next engineer, not the enforcement point itself.
"""

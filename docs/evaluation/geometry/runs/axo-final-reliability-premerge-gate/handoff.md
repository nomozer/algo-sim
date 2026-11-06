# Handoff

Status: **READY_FOR_OWNER_REVIEW** with declared conditions (report §9–§10). Read `report.md` first.

- Branch `integration/axo-hybrid4-reliability`; start `c5cef563`; commits `38cb181d` (fixture: no `StaticPool`) → `43e8fb8c`
  (usage ledger, migration `e437149641fa`) → `4bcc1368` (test password generated at run time) → `4a05ccff` (candidate freeze
  `5a7f4eba…`, template rebind) → docs-only evidence commit(s). Not merged, not pushed. 0 provider calls.
- T3: one run at `4a05ccff`, clean detached worktree — PASS; node harness 0 fail.
- Usage ledger owner: `backend/app/accounts/router.py` (`reserve_analysis_usage`, `finalize_analysis_usage`); wired in
  `backend/app/main.py::_analyze_counted`. Telemetry is observational only. Deploying needs `alembic upgrade head`.
- Re-run the mathematical classification: `tools/classify_corpus.py <fresh.json>` (from `backend/`), then the frontend replay in
  `tools/classified_audit.vitest.ts.txt` (copy into `frontend/src`, run with `--maxWorkers=1`, remove). Expected on this HEAD:
  436 certified / 156 construction / 985 contract refusals; frontend 1 577/1 577 consistent.
- Concurrency stress used 4 CPU-burner processes (bounded `timeout`); never run it next to T3.
- Owner decisions: publication (blob `23109136` created by this task in local history; 97 pending + `28be1ef6`), PostgreSQL
  environment, one live prism call, policy for session-less requests, merge/push.

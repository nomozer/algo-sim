# Handoff — axo-hybrid4-final-premerge-hardening

Branch `integration/axo-hybrid4-reliability` (worktree `.superpowers/worktrees/axo-hybrid4-integration`), wave base
`01cfda03`, main `bb61a804` fully contained. Not merged, not pushed. 0 provider calls. Authoritative text: `report.md`.

## Commits

`ce676a17` Case C test · `8248eae0` idempotency · `6d0796d4` history order · `c8e4bb17` telemetry middleware ·
`4e5a7af7` one localStorage key per record + two-tab check · `b98a470b` registry quadrilateral right angle + restored Axo
engine regressions on /4 · `09634f92` seal frozen at `b98a470b` (103 files `a0cb684e…`) + template rebind ·
`2330b675` evidence (tested tree: T3 FULL_PRODUCT_GATE_PASS) · then one docs-only commit with the gate results. Status: **READY_FOR_OWNER_REVIEW**.

Product code (`backend/app`, `frontend/src`) is unchanged after `b98a470b`: the seal holds for every later commit.

## Owner decisions

1. Publication exception for `6533b586` / `backend/tests/test_auth_api.py` blob `28be1ef6…` (`HARDCODED_PASSWORD`, test
   fixture, already removed from the tree by `cb564b1e`) — `OWNER_DECISION_REQUIRED`; plus the 98 pre-existing pending entries.
2. TypedFactNext /2 has no "plane through three named points" (Case C section refused on /4).
3. Merge/push — not done; needs explicit permission for that task.

## Scratch left on disk (reproducible, untracked)

`frontend/dist-perf`, `frontend/dist-twotab`, `frontend/dist-int` (builds) in this worktree; in the run folder the raw
`perf/perf-*/receipt.json` (13 MB each; committed gzipped) and the traces/screenshots of `perf-3-C`, `perf-3r-C`,
`perf-4-B` and the two-tab failure screenshots beyond `failure-1-*` are local only. The baseline and T3 worktrees were
removed (junction `rmdir` first).

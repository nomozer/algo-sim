# Claude to Codex takeover — 2026-10-26

## Preservation before implementation

Source branch `research/scene3d-to-hybrid-v2-replacement`, HEAD `3dcd6d9fbdc5627197537dc79c1e609ac3e03bea`, no upstream.
Six tracked modifications, no staged changes, 102 untracked files. Exact paths and SHA-256: `preservation.json`.
Backup: `.superpowers/backups/claude-to-codex-20261026-133857/uncommitted.zip` (repository root).
Archive SHA-256: `8db6107d6096e62b374b0c11ee982beade0f0d4da6a2d712206aca2f2401ca01`.
All 112 archive entries with file hashes verified. Source hashes checked again after capture: no changes.
Four ignored files retained: database, built frontend and offline log (see manifest); reproducible dependencies/caches excluded explicitly.
The first backup attempt failed on Git's Windows NUL exclude handling; its partial archive is retained separately, not used for recovery.

A Claude VS Code process and its Vite server remained present. Writer inactivity could not be established; no process was stopped.
No source worktree file was modified. Work continues in a separate branch/worktree `research/scene3d-hybrid-v2-codex` / `.superpowers/worktrees/s3d-hybrid-v2-codex`, forked at the exact source HEAD. This is continuation, not a restart from main.
All 108 nonignored changed/new files were restored from the archive and verified byte-for-byte. Ignored evidence remains in the backup; source database/dist are not used for testing.

## What Claude completed (observed history, not independent certification)

- `f3ae506c`: backend plane naming and producer witnesses, frontend witness gate and anchored right angles; inherited camera/layout kept.
- `1beb3d0f`, `542420c0`: CACHE_VERSION 130 and adapter /2 fixture export.
- `06906545`, `9de6e222`: RED right-angle probe, 60-frame P0 evidence, 204-frame visual matrix and role-aware F2 fault probe.
- `3dcd6d9f`: frozen candidate identity. Latest uncommitted official receipt reports the eight-family run; exact score is re-read during verification. Existing reports describe the locked F2 conflict (7/8), not an Owner approval.

## What was unfinished

- `backend/app/ai/hybrid_offline.py`: local replay corpus route.
- `backend/app/main.py`: loopback-only opt-in /api/analyze before cache, no fallback.
- `backend/app/simulation/geometry_functions/typed_fact_next_bridge.py`: angle mapping onto existing planner.
- `backend/app/simulation/geometry_functions/engine.py`: exact coplanarity refusal when a distance question calls lines skew. `unicodedata` IS USED to NFC-normalize quote matching; labels and provenance are not rewritten.
- `backend/tests/geometry/test_structured_geometry_relations.py`: declared lazy import boundary.
- `frontend/src/llm/client.ts`: existing /4 reader wired into analyze.
- New angle/HTTP/frontend tests, corpus exporter/evaluator and official browser artifacts (full inventory in manifest).

No test failure is asserted before running tests. Skew-claim code has no new accompanying regression test in the captured tree. Its quote scope, non-orthonormal-frame invariance and refusal classification require checking. Existing architecture-diff text saying the engine is unchanged is stale relative to this uncommitted diff.

## Pre-flight

Active branch: research/scene3d-hybrid-v2-codex. HEAD: 3dcd6d9f. Working tree: restored Claude snapshot plus this report.
Current milestone: frozen Scene3D visual candidate, Hybrid V2 unfinished local slices.
Classification: CORE (geometry correctness and local Hybrid route), SUPPORTING (preservation/evidence).
Thesis relevance: verified spatial-geometry simulation, fail-closed source-to-scene pipeline.
Reuse: typed_fact_next_bridge._distance_question/_refs, planner ask_angle_*, exact engine/interpreter, ReplayExtractor, /4 reader, Scene3DExplorer.
Source of truth: owner takeover directive, docs/RULES.md, code/tests and immutable machine receipts.
Expected changes: captured six product/test files, focused skew/angle/route regressions, run-local reports/evidence and indexes as needed.
Contract/cache/history impact: preserve public schemas, LLM_ONLY default and cache130; no history rewrite. New refusal needs taxonomy/version review.
Duplicate risk: use existing planner/engine/reader, no second implementation. Dependency-cycle risk: preserve lazy route gate.
Scope-creep risk: 18 families and provider extraction are not all verified; report gaps explicitly.
Smallest implementation: reproduce unfinished slice failures, fix exact cause, targeted tests then related browser tests; freeze before Full T3.
Excluded: root checkout/UI/theme/layout/camera changes, live provider calls, merging/pushing, old receipt edits, locked oracle edits.
Stop conditions: concurrent-source mutation (isolated snapshot only), unverified math (refuse), irreversible unapproved action.

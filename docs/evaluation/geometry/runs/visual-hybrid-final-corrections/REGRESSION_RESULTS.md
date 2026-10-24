# Regression results (final corrections)

**Candidate:** product `af670aa6`, freeze `a636a0e5` (118 files, tree `8be63267…`, cache 128).

**Authoritative runs:** in the clean detached worktree `t3-b1b2`, with `git status --porcelain` empty before and after.

## Full T3 (`frontend/scripts/full-gate.mjs`) on the final candidate

**`FULL_PRODUCT_GATE_PASS`**: target `a084c180` (candidate `a636a0e5`, product `af670aa6`), 570 s, exit 0, receipt `verification/full-t3/execution.json` (sha256 `ece374b1…`).

| Stage | Result |
|---|---|
| pytest (whole backend) | 11856 passed, 1 skipped, 2 deselected, 15 xfailed, 0 failed |
| Vitest | 79 files, 1343 tests passed |
| typecheck + production build | pass |
| thesis demo replay | pass |
| demo crash surface | pass (six refusal boundaries refuse with the right kind) |
| `freeze_evaluation_candidate.py --verify` after T3 | "Candidate khớp bản đã đóng băng (118 file, 8be63267…)" |
| Source tree before / after | empty / empty |

The earlier Full T3 at `b99afd32` covered a different product (`a9d05dda`). It is **not** reused as certification here.

## Targeted and suite runs

| Check | Result |
|---|---|
| P3 tests (`final-quality`, `hybrid-preview-contract`, `ui-hygiene`) | RED 10 failures on old code → GREEN 83/83 |
| P2 tests (`test_display_identity_source_names.py`) | RED 7 failures on old code → GREEN 14/14 |
| Adapter /4 naming check, fault-injected | flags `MI1I2I3`, `S(MI1I2I3)`, `V(S.MI1I2I3)` on the Adapter /3 demo; 9 served /4 scenes with unnamed points, 0 leaks |
| Adapter /4 offline export (47 cases) | byte-identical to the integrated export (`1abad7c5…`): 22 served, 25 refused, 0 wrong-served, 0 false-refused |
| Cache migration (`test_cache_display_identity_invalidation.py`, `test_cache_segment_witness_invalidation.py`, `test_api.py`, `test_cache_identity.py`) | pass; genuine v127 row MISSES under 128, fresh envelope = v127 bytes with `(AB′D′)` → `(P)`, control byte-identical |
| Whole backend suite on the working tree, before freeze | 11839 passed, 17 failed. All 17 traced: stale candidate / cache identity / chain layer before the freeze, a dirty-tree readiness test. All resolved by the re-lock, the freeze `a636a0e5` and the chain layer `7c296be1` (178/178 re-run) |
| Vitest (working tree, after the samples regeneration) | 79 files, 1343 tests pass |
| Node harness `node --test "scripts/*.node-test.mjs"` | 115 tests: 113 pass, 2 skipped, 0 fail |
| `freeze_evaluation_candidate.py --verify` (before T3) | MATCH, 118 files, `8be63267…` |

## Owner regression areas

| Area | Evidence | Status |
|---|---|---|
| Default LLM_ONLY route | `CHE_DO_MAC_DINH` unchanged; no change in `app/ai/skills`, `ai/pipeline.py` routing or `geometry_compiler/routing.py`; prompts / grammar / schema hashes unchanged (`cache_identity.lock.json`: semantic environment `b1714b56…` same, only the version moved) | PASS |
| Backend display identity | DISPLAY_IDENTITY_FIX.md | PASS |
| Adapter /4 | byte-identical export, browser 94 rows | PASS |
| Learner diagnostics | DIAGNOSTICS_UI.md; refusal surface 21/21; owner refusal screens: no code, no drawer | PASS |
| Geometry, provenance, DAG, construction order, certificates | cache probe envelope equality and 7 byte-identical controls; whole backend suite | PASS |
| Scene3D rendering / orbit | orbit gate ĐẠT; official suite rendering assertions (formation, section fill, orbit, CSS) pass in all 8 families | PASS |
| Official Visual suite | FAIL with 2 product findings (OFFICIAL_SUITE_RESULTS.md F1, F2) | OPEN (owner decision) |

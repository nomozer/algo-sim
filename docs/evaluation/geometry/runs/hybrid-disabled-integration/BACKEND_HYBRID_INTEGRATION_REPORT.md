# Backend Hybrid integration report — coherent disabled integration

Date 2026-10-23. Branch `research/hybrid-session4b-integration` (worktree `.superpowers/worktrees/hybrid-session4b-integration`).
Status: **BACKEND_HYBRID_INTEGRATION_CANDIDATE_READY_FOR_OWNER_GO_MAIN** — with `PRODUCTION_REPLACEMENT = NO-GO`,
`LIVE_PROVIDER_EVALUATION = NOT_AUTHORIZED`, `MAIN_MERGE_PUSH = NOT_AUTHORIZED`, and `FRONTEND_CONSUMER_ACCEPTANCE_OPEN`
for Adapter `/4` (it has no caller; see §5). 0 provider calls in this run.

## 1. Identities

| Role | SHA |
|---|---|
| Base: local `main` | `f10e6283dd3fd2cfdef189e1bef0ffdecf2be942` (1 docs commit ahead of `origin/main`) |
| `origin/main` (local ref and `git ls-remote` at session start) | `43247c9e9375a3dbf2b5223324a58e6f932ca596` — remote fresh at that time |
| Session 3 product / T3 candidate / docs | `69bd2fe4…` / `84c729e0…` / `0f7b3a69…` |
| Session 4A | `ef6829d3e1784b661427839b7df9583ca643dde5` |
| Merge of Session 3 (contains S1, S2) | `561958fc` |
| Merge of Session 4A | `14cdc25a` |
| Gateway docs sync | `84cd09e3` |
| Verification receipts | `b99f6420` (independent review round 1 target) |
| Review remediation = **frozen candidate = Full T3 target** | `2bbad1f2715c367736b4a5d783551b94b45fbb79` (review round 2 target) |
| Product commit (`product-paths-excluding-test-only/1`) | `69bd2fe48be1fd3afa6ce4112ccddda92a07d850` |
| Measured system (LF-normalized SHA-256, freeze helper algorithm) | `413ee525d20874aa346b13df7e51019266f7d4701af56719c2a2ee736266b5df`, 116 entries — **recomputed** on the integrated tree at `14cdc25a`, `2bbad1f2` and post-T3 |
| Git trees `backend/app` · `backend/tests` · `backend/scripts` · `frontend/src` · `frontend/scripts` | `357afcfa` · `942634c3` · `5d593734` · `0d4b2088` · `635b314c` — equal to `84c729e0` |

The measured hash and product commit equal Session 3's because the product bytes are identical, not because a Session 3
receipt was reused: `freeze_evaluation_candidate.py --verify` recomputes from disk and resolves the product commit with
`git log` (the merge is TREESAME to its Session 3 parent).

## 2. What was integrated

`git merge --no-ff` of the whole Session 3 branch (Sessions 1→2→3 ancestry kept; no cherry-pick), then of Session 4A.
The product diff versus `main` is exactly the ten files Session 4A predicted: `adapter3_simulation.py`, new
`adapter4_route.py`, `fact_extraction.py`, `function_route.py`, `hybrid_preview.py`, and geometry-functions
`engine.py`, `planner.py`, `registry.py`, `typed_fact_next.py`, new `typed_fact_next_bridge.py`, with their tests,
fixtures exporter and benchmark. That is the coherent stack: TypedFacts V2 schema/validation, route-labelled `/1 → /2`
conversion, bridge `/1` + `/2`, Registry and `PlanningContract`s, Source Gate (`registry.kiem_nguon`, G1–G7), goal-directed
planner with section-vertex orchestration, exact engine with section/closure/volume certificates, Adapter `/3` + `/4`,
operator-only preview, refusal taxonomy, Scene3D. `main` had no product change after the Session 3 fork point
(`43247c9e`), so the merge had no code conflict. Two index files conflicted with Session 4A and were resolved by keeping
both sides (line-preservation checked by the reviewer: 0 lines lost).

**One Registry / Planner / Engine.** Adapter `/4`, the fact route, the preview and Adapter `/3`'s gate all call the same
`registry.py` / `planner.py` / `engine.py`. Adapter `/4` → `bridge_v2` → `function_route.chay_sau_cau_noi` →
`run_fact_route` → engine `dung_tu_loi_goi`, which calls `kiem_nguon` unconditionally; `/4` has no legacy branch.
Adapter `/3` keeps a labelled legacy authority only where the bridge cannot express its payload.

Not integrated (separate sources, out of this scope): `research/hybrid-semantic-extraction-v2`,
`integration/extraction-v2-safety`, `research/nl-to-scene3d-e2e-readiness`, the scene3d/visual-UX branches and the
other unmerged branches listed by `git branch --no-merged main`. None is needed for the Session 1–3 stack.

## 3. Verification (in order run)

| Step | Command / receipt | Result |
|---|---|---|
| Docs gate | `tests/geometry/test_docs_information_architecture.py`, `tests/test_current_state_identity.py` | 45 passed (after merge, after docs sync, before final commit) |
| Focused backend: hybrid, contract, source gate, planner, engine, preview, cache, default route | `results/focused-backend-pytest.log` (at `14cdc25a`, same product trees) | 1968 passed, 13 xfailed, 0 failed |
| Candidate lock | `freeze_evaluation_candidate.py --verify`; `tests/semantic_program/test_evaluation_candidate.py` | MATCH; 26 passed |
| Session 4A replay harness | `SESSION4A_SOURCE_ROOT=<integrated> pytest …/hybrid-session4a-readiness/test_offline_replay.py` | 12 passed. A first run without that env var failed 2 tests with `KeyError` (harness input, not product) |
| Seam replay | `python …/hybrid-session4a-readiness/offline_replay.py --source-root <integrated> --archive-root <integrated> --output results/seam-replay-integrated.json` (from `backend/`) | Identical to 4A except `offline_seconds` and input paths (same input SHA-256): 47 authored → 22 `VERIFIED_SCENE` / 25 refused; 44 archived flat outputs → `EXTRACTION_FAILURE` |
| Locked planner diagnostics | `replay_planner_diagnostics.py` → `results/planner-diagnostics-integrated/` | Row-for-row identical to 4A: 12/12 exact, 12 valid scenes; route-B 38 correct served / 18 correct refusals / 4 false refusals = B27 `OUT_OF_SCOPE`, B28 `PREDICATE_NOT_IN_QUOTE`, each in both arms |
| Invariants + default isolation | `verify_integration_invariants.py` → `results/invariants-default-isolation-2bbad1f2.json` | 127 / LLM_ONLY / flat / 32 / ALLOW_LIVE_AI 0 (inherited); default policy fingerprint `None`; 47 startup modules, 0 differ from `main` |
| Provider surface | `surface_fingerprint('flat')` on `git archive main` and on the integrated tree | both `485d3834…` |
| Adapter `/4` consumer boundary | `check_adapter4_consumer.py` → `results/adapter4-consumer-after-review/` | 22/22 served, 25/25 refused with code, 0 wrong serves; 15 numeric oracles all match, 7 construct-only; 22/22 scene gate, metric, envelope; 0 internal-ID leaks; 21/22 closure certificates (DEV10 plane-only has none) |
| Frontend consumer | `npx vitest run --maxWorkers=1 src/simulations/domains/geometry/ src/components/hybrid-preview-contract.test.tsx` → `results/focused-frontend-vitest.log` | 37 files, 788 passed |
| Independent review | `INDEPENDENT_REVIEW.md` | Round 1 PASS (0 blocker, 4 important fixed in `2bbad1f2`), round 2 PASS |
| **Full T3** | `run_full_t3.py` → `verification/full-t3/execution.json` (+ raw `stdout.log`, `stderr.log`) | **FULL_PRODUCT_GATE_PASS**, exit 0, clean before/after, 554.42 s, UTC 03:39:14–03:48:28; pytest 11572 passed / 1 skipped / 2 deselected / 15 xfailed; vitest 72 files / 1156 passed; build PASS (chunk-size warning only); demo 5/5; crash surface 6/6 |
| Post-T3 lock | `verification/full-t3/post-t3-freeze-verify.log` | MATCH, head `2bbad1f2`, clean |

Single T3 attempt, one worker, BLAS/OpenMP threads 1, clean detached worktree; no retry was needed. Raw streams are
committed (Session 4A noted Session 3's were not).

## 4. Answers to the owner's questions

1. **Integrated exactly:** the ten product files and tests of Sessions 1–3 as one merge, plus the Session 4A
   correction layer; plus a docs sync of gateway contract versions.
2. **Still separate / blocked:** provider extraction work (extraction-v2 branches), any `/4` product caller,
   default switch, live evaluation, independent holdout.
3. **Shared Registry/Planner/Engine:** yes — one implementation behind `/3` gate, `/4`, fact route and preview.
4. **Recombination quality:** bounded generic goal composition (typed needs, depth 3, ≤ 64 calls) reproduced on 6
   changed-centroid probes with effect-chain certificates; section work is handwritten orchestration. All measured
   sets are implementer-authored development sets, not blind. No general-planner claim.
5. **Regressions vs old backend:** none observed. The default route modules, prompts, schema, route policy and provider
   surface are byte-identical to `main`; Full T3 counts equal Session 3's.
6. **Scene3D / frontend:** backend-boundary checks above plus existing frontend tests. No browser run on a `/4` scene.
7. **SHAs:** §1. **8. Full T3:** PASS on `2bbad1f2`. **9. Worktrees:** `SAFE_WORKTREE_CLEANUP_REPORT.md`.
10. **Conditions for GO main:** `FINAL_HANDOFF.md`.

## 5. Limits that stay open

`FRONTEND_CONSUMER_ACCEPTANCE_OPEN` for `/4`: no caller exists, so nothing in the product consumes it; merging does
not expose it. The fixtures in `results/adapter4-consumer/` are for a separate frontend session. Scene-schema PASS is
not browser PASS. All other gaps are classified in `BACKEND_HYBRID_REMAINING_GAPS.md`. Counting rules kept from
Session 4A: Session 3's "562" is not a count of independent problems, and its 46,436 fuzz executions are mutations,
not problems.

Post-flight: reused the freeze helper, Session 3 evaluator (`load_lock`, `square_of`), Session 4A replay and
diagnostics, `hybrid_preview._validate_scene`, `compile_semantic_program_to_envelope`,
`validate_semantic_envelope_config`, existing pytest/vitest suites and `full-gate.mjs`. Created only run-local
scripts (invariants, diagnostics wrapper, `/4` boundary check, T3 runner). No product module, dependency or
abstraction added.

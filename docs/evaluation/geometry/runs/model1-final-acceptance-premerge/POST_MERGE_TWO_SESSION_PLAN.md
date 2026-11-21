# Post-merge plan: two backend sessions

Run `model1-final-acceptance-premerge` (AXO HYBRID /18), 2026-11-21. Audience: the owner and the two future sessions.
**Draft only.** It takes effect after Model 1 is merged into `main` *and* the owner approves parallel work. No branch or
worktree was created for it in /18.

## 1. Ownership

One file has one owner. A change outside your column goes through the shared-contract procedure (§3).

| Session A — Dynamic Construction Planner /2 + Model 2 | Session B — Model 1 architecture & performance |
|---|---|
| `backend/experimental/construction_planner/**` (frozen /2 prototype; integration starts from its `integration_adapter.py`, `scene3d_bridge.py`, `verified_input_bridge.py`, `model2_interface.py`) | `backend/app/ai/local_geometry_parser.py` |
| `backend/app/simulation/geometry_functions/construction_continuity.py` | `backend/app/ai/slm_verified_normalizer.py` |
| `backend/app/simulation/geometry_functions/step_editor.py` | `backend/app/ai/local_slm_extractor.py` |
| new Model 2 modules (to be created under a Session-A-owned path agreed before work) | `backend/app/ai/local_slm_runtime.py` (llama.cpp process, queue, timeouts, Linux runtime pin) |
| construction evaluation tooling and runs (`docs/evaluation/geometry/runs/<construction-run>/`) | `backend/app/ai/adaptive_input_router.py`, `compositional_clause_analysis.py`, `local_failure_diagnostics.py` |
| | `backend/app/ai/hybrid_offline.py` (local-mode runners) |
| | local-route caching, latency, concurrency, profiling, Rust feasibility (only if profiling shows the need) |

Session A does not edit Model 1 files; Session B does not edit Construction /2 files.

## 2. Shared contracts (locked; neither session owns them alone)

| contract | files | lock / check |
|---|---|---|
| Typed Facts | `geometry_functions/typed_fact_next.py`, `typed_fact_next_bridge.py` | additive-only changes; `test_parser_routing_integrity.py`, TypedFactNext surface hash in `cache_identity.lock.json` |
| Source Gate | `geometry_functions/registry.py` (`kiem_nguon`) | Source Gate suites (6 files), never loosened to raise completion |
| Planner / Registry interfaces | `planner.py`, `registry.py` function library | planner + registry suites; Construction /2 imports `engine, planner, registry` |
| Exact Kernel | `geometry_functions/engine.py`, `certificates.py`, `simulation/geometry/**`, `semantic_program/interpreter.py` | kernel suites; independent oracle `docs/evaluation/geometry/custodian/geometry_oracle.py` |
| Scene3D adapter schema | `backend/app/ai/adapter4_route.py`, envelope `hybrid-route-d-simulation/4`, frontend `domains/geometry/**` | adapter + vitest geometry domain; Construction /2 imports `adapter4_route` |
| Cache identity | `backend/app/main.py` (`CACHE_VERSION`, route modes), `cache_identity.lock.json` | **serialized**: one bump at a time, the later session rebases its bump |
| Evaluation harness | `docs/evaluation/geometry/harness/live-acceptance/**` | byte-locked by `test_shared_live_harness.py` |

Shared-contract change procedure: written proposal in the requesting session's run folder → owner approval → one
commit that touches only the contract and its tests → the other session rebases onto `main` and re-runs its suite.

## 3. Git isolation (proposal)

- Two branches from the merged `main`: `feat/construction-planner-v2-integration` (A) and
  `feat/model1-performance` (B), each in its own worktree — this needs the owner's approval of parallel worktrees
  (today's policy is one shared worktree).
- Each branch rebases (or merges `main`) before review; neither merges the other.
- Integration order: B's first deliverable is a measurement-only baseline (no product change) so that A's later scene
  changes are not confused with B's latency changes; then the session that touches a shared contract first lands it
  alone; the other follows.
- Candidate freeze and `CACHE_VERSION` are per merge into `main`, not per session.

## 4. Regression every merge into `main` must pass

1. Full T3 (`npm run test:full`) on the merge commit, in the location D3 approves.
2. Shared-contract suites listed in §2.
3. Negative safety on the exposed regression sets (0 served negatives, 0 invalid scenes, 0 numeric mismatch) with the
   shared `scene_oracle.py`.
4. For B: routing ablation tools of `/17` (`model1-integration-readiness/tools/`) to show correctness unchanged and
   latency/capacity deltas on the same host.
5. For A: construction evaluation of its own run plus the Construction /2 freeze suites.
6. Publication gate on the range.

## 5. First items already known

- **B:** fingerprint gap (`ISSUE-ARCH-PARSER-NOT-IN-SEMANTIC-FINGERPRINT`), Linux runtime + GGUF hosting
  (`ISSUE-OPS-LOCAL-SLM-LINUX-RUNTIME-AND-GGUF-PROVISIONING`), deadline/queue/idempotency
  (`ISSUE-OPS-LOCAL-ROUTE-CAPACITY-AND-DEADLINE`), clarification wording for capability gaps
  (`ISSUE-ARCH-CAPABILITY-GAP-WORDED-AS-CLARIFICATION`).
- **A:** the Construction /2 handoff patch `frontend_scene3d_multiplan_switcher.patch` is listed in
  `HANDOFF_REBASE_REQUIRED` (`backend/tests/geometry/test_axo_construction_v2_integrity_and_integration.py:379`) since `/13`;
  rebase it onto the merged `main` before any integration.

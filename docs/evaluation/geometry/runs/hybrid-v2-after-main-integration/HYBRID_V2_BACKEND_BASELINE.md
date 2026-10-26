# Hybrid V2 backend baseline

Status: NOT_STARTED_AWAITING_VERIFIED_MAIN_MERGE_AND_SAFE_CLEANUP.

No backend development branch was created. The requested branch is `research/hybrid-v2-backend-generalization`, to start from verified integrated main after the required gates. Product remains LLM_ONLY / CACHE_VERSION 130, Hybrid opt-in, provider calls zero.

The 18-family checkpoint (0 FULL / 9 PARTIAL / 7 RENDER_ONLY / 2 UNSUPPORTED) is inherited, not newly measured by watchdog recovery. P7 must audit actual TypedFacts, Source Gate, Registry, Planner, Engine and adapter code before choosing a single vertical slice. No readiness or live NL extraction claim is made.

## Baseline audit at `main` `a9889031` (Claude, 2026-10-26)

Branch `research/hybrid-v2-backend-generalization` was created from verified `main` `a9889031` in its own worktree
`.superpowers/worktrees/hybrid-v2-backend-generalization` (not the root, not an old agent branch).

Read from source, not from earlier reports:

| Layer | Where | State at `a9889031` |
|---|---|---|
| TypedFacts V2 | `geometry_functions/typed_fact_next.py` | `typed-fact-next/2`; premise plane args `refs3` = **three or more** labels |
| V2 → planner bridge | `typed_fact_next_bridge.py` (`typed-fact-next-bridge/2`) | distance (B3, `3524bec8`) and angle (`f9e86972`) goals bridged; **every plane operand of a math goal forced to exactly three labels** (`INVALID_MATH_GOAL` otherwise) |
| Source Gate | `registry.kiem_nguon`, `_cung_mat` | the question quote must name the plane; quoted and called label sets share ≥ 3 labels and one contains the other |
| Registry | `registry.py` (`geometry-functions/13`) | `AskDistancePointPlaneArgs.plane` exactly 3 (part of the function-calling surface `7ea511a6…`); angle planes `Poly` (≥ 3) |
| Planner | `planner.py` (`geometry-fact-planner/13`) | point–plane distance call cut to `b[:3]` (also for described points) |
| Engine | `engine.py` (`geometry-function-engine/12`) | `kiem_mat_viet` checks exact coplanarity of every plane group in the problem text and in the calls; all measurements use the first three labels |
| Route D / Adapter /4 | `ai/function_route.run_fact_route`, `ai/adapter4_route` | one planner/Source Gate/engine for route B and `/4`; not wired to `/api/analyze` |
| Verified witnesses | engine + `kernel.common_perpendicular_feet` | skew-line common perpendicular witness since `1faee1db` (route D only) |
| Default product | `main.py`, `ai/pipeline.py` | `LLM_ONLY`, `CACHE_VERSION = "130"`, Hybrid opt-in |

Gap chosen (prompt priority "four-label plane and coplanarity"): route B already serves `góc giữa SA và mặt đáy` with
plane `[A, B, C, D]`, but the canonical V2 `/4` path refused any math goal that named a plane by more than three labels —
`góc giữa SC và (ABCD)`, `khoảng cách từ A đến (BCC'B')`, the most common wording in families #3, #4, #11, #12, #13.
The B3 slice had made that refusal deliberate (review I-1) because the planner truncated the distance plane.

18-family matrix: inherited **0 FULL_E2E_VERIFIED / 9 PARTIAL / 7 RENDER_ONLY / 2 UNSUPPORTED**
(`../claude-to-codex-takeover/families.md`), not re-measured here. See `HYBRID_V2_VERTICAL_SLICE_REPORT.md` for the
delta.

# Owner decision — CIC-D1 locked V2 contract recovery

Owner GO `HYBRID_V2_W3_F2_CIC_D1_LOCKED_CONTRACT_RECOVERY`, 2026-10-30: option **(a)
`PRESERVE_LOCKED_V2_DISTANCE_TARGET_CONTRACT`**. Option (b) is rejected, and the target grammar is not widened.

- Locked test `test_typed_fact_next_v2_distance_bridge.py::test_malformed_distance_target_is_refused[target8]` and its
  expected `REFUSED / INVALID_MATH_GOAL` are not edited.
- CIC-D1-A: `solid`/`solid_id` may not appear beside geometric operands in a target. Ownership is declared through
  `MathGoalSpec.solid_id`. CIC-D1-B: such a key is refused, never silently removed. CIC-D1-C: `/1` keeps another
  grammar only if an active `/1` contract really allows one (see `contract-analysis.md`).
- A versioned amendment is allowed for the supplementary N2 tests only (`n2-amendment.md`).
- Product edits are allowed in `typed_fact_next.py`, `typed_fact_next_bridge.py`, `adapter3_simulation.py` only. No
  Registry, Planner, Engine, radical kernel, Adapter /4 product code or frontend change. No hard-coded case ids.
- Continue in order: Gates A–D → independent pre-freeze review → Wave 3 replay → T0/T1/T2 → freeze → Full T3 → final
  review. Stop at any BLOCKER/MAJOR. No merge, push or cleanup. `LLM_ONLY`, `CACHE_VERSION` 130, `ALLOW_LIVE_AI=0`.

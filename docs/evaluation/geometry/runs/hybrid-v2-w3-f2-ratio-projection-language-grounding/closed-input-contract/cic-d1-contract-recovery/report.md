# CIC-D1 locked V2 contract recovery: NOT_READY (pre-freeze review: 2 MAJOR)

Owner GO `HYBRID_V2_W3_F2_CIC_D1_LOCKED_CONTRACT_RECOVERY`, option (a), 2026-10-30. Branch
`research/hybrid-v2-w3-f2-ratio-projection-language-grounding`. Main/origin `996f114b` were not touched. 0 provider calls.
`LLM_ONLY`, `CACHE_VERSION` 130 (no bump; the cache lock matches), Hybrid opt-in, `ALLOW_LIVE_AI=0`.

1. **Final research HEAD:** the commit that contains this file (`git log -1`). Earlier commits: `007063cc` preregistration +
   RED, `717f8b2b` product fix, `6a208e13` GREEN/Gates A–C, `6b4a9752` Gate D.
2. **Product commits:** `4b361c47` (closed input contract, verbatim checkpoint) and `717f8b2b` (CIC-D1). Both touch only
   `typed_fact_next.py` and `typed_fact_next_bridge.py` (`4b361c47` also `adapter3_simulation.py`).
3. **CIC-D1 root cause:** two parts.
   - `_validate_goal_target` admitted `solid`/`solid_id` beside geometric operands.
   - The Bridge stripped those keys with `measurement_operands`, so the locked exact-key check never saw them (`contract-analysis.md`).
4. **Locked V2 contract preserved:**
   - `target8` and all 16 locked params pass. The test file is unchanged versus main (the reviewer confirmed).
   - A scope key beside operands is now `INVALID_MATH_GOAL` at the schema on /1 and /2. The Bridge reads `g.target` again.
5. **N2 amended evidence:**
   - `n2-amendment.md` (v2 inputs, plus the `oracle_shape` amendment and the post-registration `s8_preflight` addendum).
   - The original inputs are kept verbatim in `cases.json#N2v1.*`. After the fix all four are `INVALID_MATH_GOAL` (`green.json`).
6. **S8 ownership proof:** `n2-ownership-proof.json`.
   - The three valid-shape violations are refused with `SOURCE_OBJECT_MISMATCH` on a3, pl and a4.
   - S8 runs first and refuses on its own, before any capability check, with no fallback and no global resolution.
   - The own-point control is served (√5/2)·a.
7. **Gates:**
   - A PASS: acceptance 748/0; 5 CIC-D1 and 9 mandatory mutants killed; 203 probes, 0 negatives served, 0 internal. 11 in-target transitions, one of them the reclassified POS probe, which the reviewer judged legitimate. The 4 source-grammar diagnostics are still `PENDING`.
   - B PASS.
   - C 96/96.
   - D `PRE_FREEZE_COMPATIBILITY_PASS`: full backend 13427 passed; the 11 failures are stale freeze identity (`PENDING_NEW_FREEZE`); fixtures 41/41; cache MATCH. Publication **BLOCKED**: raw traceback logs committed in `1490e3cd`; proposal `publication-exception-proposal.json`; this cycle 0 violations. Gate D is **not** an overall PASS.
8. **Independent pre-freeze review: NOT_READY** (`pre-freeze-review.md`):
   - **F1 MAJOR:** the target grammar was widened by `4b361c47`. `{solid_id}` is accepted for radius/lateral_area/area, and curved radius/lateral_area/volume `{solid_id}` are served on /1. Main and `5e44d5da` refuse those.
   - **F2 MAJOR:** the /1 and /2 grammars differ. `{segment: [A, pr::A]}` is served 0 on /1 and refused on /2. This was already the case on main.
   - Plus 5 MINOR and 4 NOTE (corrections in `corrections.md`).
9.–13. **Wave 3 replay, T0/T1/T2, freeze, Full T3, final review: NOT_RUN** (STOP per Owner GO §8). No candidate frozen.
14. **Historical evidence integrity:** no earlier receipt was edited. Corrections are a new layer, and every earlier report/log is unchanged.
15. **Limitations:**
    - F1 and F2 are open.
    - Publication needs an Owner exception.
    - Freeze identity is pending.
    - F3 mutants survive.
    - F7 pre-existing internal error on prism radius/lateral_area.
    - Provider null behaviour is unmeasured (F8).
16. **Next steps (Owner decisions needed):**
    - (i) F1: restrict scope-only targets to the registered alternatives, or register `solid_id` as an alias for those kinds.
    - (ii) F2: compare canonical identities (namespace-resolved) in the schema distinctness check, so the /1 and /2 grammars match. The product edit stays inside `typed_fact_next.py`.
    - (iii) Approve or decline the two publication exceptions.
    - Then rerun Gates A–D, the pre-freeze review, replay, T0–T2, the freeze, Full T3 and the final review.

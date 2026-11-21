# Test infrastructure consolidation (/13)

Run `axo-hybrid-local-model1-finalization-test-consolidation`, branch `feat/local-model1-finalization-test-consolidation`.
Baseline for every count below: `ba8db5612`, the merge of `main` into the branch, before any /13 test change.

## 1. Counts

| measure | before (`ba8db5612`) | after (`b3173a02e` + P2) | delta |
|---|---|---|---|
| backend `test_*.py` files | 448 | 426 | −23 removed, +1 added (`test_shared_live_harness.py`) |
| backend collected tests | 15 320 | 15 007 | −313 |
| backend result (Full T3) | 15 302 passed, 1 failed (stale Construction /2 handoff patch, fixed in `883467c9a`) | 14 983 passed at `47f4d9632`, 0 failed; +4 harness tests since | — |
| frontend vitest files | 203 | 203 | 0 (`semantic.test.ts` rewritten in place) |
| frontend vitest tests | 2 357 | 2 343 | −14 (2D container renderer cases) |
| `frontend/scripts/*.node-test.mjs` | 8 | 8 | 0 |

Sources: `pytest --collect-only -q` at each commit (the node-ID lists were diffed by file), and the Full T3 logs on `71336847b` (the baseline T3 ran after the CACHE pin and section fixes, so its backend total differs from the collection by skips and deselects) and `47f4d9632`.

## 2. What the 313 removed test IDs were

All 313 are informatics-domain cases. The node-ID diff, grouped by file:

- **23 deleted files (informatics only):** `semantic_program/test_learner_surface.py` (59), `test_scalar_obligations` (32), `test_predicate_verdict` (29), `test_witness_derivation` (23), `test_container_ref_canonicalization` (20), `test_trace_certification` (18), `test_cross_domain_matrix` (18), `test_interpreter_and_adapter` (13), `test_postconditions` (10), `test_coverage_gate_c1a` (10), `test_map_view` (9), `test_vacuous_obligation_diagnosis` (8), `test_contract_coverage` (8), `test_unseen_live_smoke` (7), `test_graph_view` (7), `test_derived_sequence_vacuous` (7), `test_c2_fail_closed` (7), `test_generation_equivalence` (5), `test_coverage_gate_c1b` (5), `test_narration_certification` (4), `test_primitive_set_frozen` (3), `test_binding_fail_closed` (3), `test_primitive_coverage` (2). Also removed: their helper modules `fixtures_coverage_18.py`, `unseen_smoke_fixtures.py`, `execution_oracles.py`, and `backend/scripts/cross_domain_matrix.py`.
- **Kept files that lost informatics parametrizations only:** `geometry/test_model_assumption_boundary.py` (−13: `array`/`map` MemoryTypes and the 11 informatics obligations), `geometry/test_dev_failure_regressions.py` (−13, +2), `semantic_program/test_interpreter_fail_closed.py` (−11 container-operation cases, +5 generic validator cases), `test_frame_state_invariant.py` (−5 informatics programs, +2 on a geometry spec), `test_grammar_card.py` (−3 full-card cases), `test_coercion_stats.py` (−3 container refs), `test_condition_canonicalization.py` (−2 array forms), `geometry/test_symbol_namespace.py` (−3, +1), `test_taxonomy_frozen.py` (−1, +1 invalidation), and single renamed cases in `test_simulation_state`, `test_scene3d_integration`, `test_scale_normalization`, `test_coordinate_grounding`, `test_measure_contract` and `test_learner_surface_3d`. In each renamed case the informatics fixture became an out-of-scope or non-geometry fixture, and the guard itself stayed.

**Guards ported, not lost.** Domain-neutral rules that informatics fixtures used to exercise now run on geometry fixtures:

| rule | new home |
|---|---|
| C1a/C1b coverage-gate rules | `geometry/test_geometry_coverage_gate.py` (+6) |
| learner-surface leak/policy rules (`NaN`, `undefined`, `[object Object]`, …) | `geometry/test_learner_surface_3d.py` (+26) |
| frame k ⇔ trace[k] (invariant #31) | `semantic_program/test_frame_state_invariant.py` |
| validator / fail-closed / checker registry | `semantic_program/test_interpreter_fail_closed.py` |
| grounding gate | `test_grounding_gate.py` (scalar facts) |
| transport boundary | `test_transport_boundary.py` (`transport_pair`) |

No geometry test was removed. Measured invariants of the prune (commit `c8868964a`):
- the geometry grammar card is byte-identical (sha `85b4534c`, 6 976 B);
- the geometry and advanced samples regenerate byte-identically;
- 0 served programs are affected.

## 3. Shared helpers replacing per-file / per-run copies

| before | after | commit |
|---|---|---|
| 27 test files pinning the current `CACHE_VERSION` literal (each bump edited all 27) | `tests/cache_policy.py::assert_cache_policy_at_least(<introduced>)` | `1c6659dea` |
| an inline fake DB session per invalidation test | `tests/cache_policy.py::assert_route_d_row_misses(<old policy>)` | `26d6f456e` |
| 24 per-run copies of `tools/refresh_pending_templates.py` | `backend/scripts/refresh_pending_templates.py` (refuses an existing receipt and approved or paid templates) | `c634c0fe2` |
| per-run copies of the live-acceptance browser, UI, oracle and aggregate tools, which wrote into their own run directory by default | `docs/evaluation/geometry/harness/live-acceptance/` (`axo-live-acceptance-harness/1`, no default output) | `b3173a02e` |
| two browser/backend contracts bound to one checkout (hard-coded venv / foreign path) | portable via `ALGO_SIM_PYTHON` / repo-relative paths | `7615d6bca` |
| `zero_measure_audit` pasted by hand into the advanced samples | derived in the builder | `9ee417171` |

**Frozen copies stay.** Per-run copies under `runs/*/tools/` are frozen evidence, so none were edited or deleted. New runs use the shared tools.

## 4. Equivalence evidence

- **Live harness:** replaying the oracle and the aggregator on the frozen /12 inputs reproduces the /12 deliverables exactly (`SHARED_LIVE_HARNESS_VALIDATION.json`; `test_shared_live_harness.py`). A mutation of the SLM provenance rule turns the self-test red.
- **Template refresh:** the shared tool's test re-binds PENDING templates only and never writes an approval (`test_s2_student_language_pilot_runner.py::test_shared_template_refresh_rebinds_pending_templates_only_and_never_approves`).
- **Cache pins:** the identity lock (`test_cache_identity.py`) is still the single source of truth for the value. The shared premise check fails if `CACHE_VERSION` drops below the version that introduced a test.
- **Whole product:** Full T3 PASS on `47f4d9632` (backend 14 983, vitest 203 files / 2 343, build, demo 5/5, crash 6/6).

## 5. Informatics shell residue (`ISSUE-ARCH-SHELL-INFORMATICS-RESIDUE`)

No learner-visible informatics icon or label remains.
- `KIND_BY_SIM_ID` no longer exists: every preview resolves to a geometry illustration.
- The zero-reader `DOMAIN_COLOR`, `DOMAIN_LABEL` and `FOCUS_SIM_IDS` were deleted.
- The informatics rows of `transport-policy.ts` and the `Domain` members are a recorded, not learner-visible, historical exception. Details are in the issue entry in `docs/OPEN_ISSUES.md`.

`TEST_CONSOLIDATION_VERIFIED = true`: every removed test is informatics-only or was ported, the shared helpers carry their own tests, and the full gate is green.

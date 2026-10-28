# Implementation Plan — Hybrid V2 W2-M5 Adapter `/4` Category A Identity Repair

- **Task ID**: `HYBRID_V2_W2_M5_ADAPTER4_CATEGORY_A_IDENTITY_REPAIR`
- **Run Directory**: `docs/evaluation/geometry/runs/hybrid-v2-w2-m5-adapter4-category-a-identity-repair/`
- **Research Branch**: `research/hybrid-v2-w2-m5-adapter4-category-a-identity-repair`
- **Authoritative Baseline (`main`)**: `eb661971847c034500862299c5091f1f3d2a2998`
- **Baseline Product Freeze Hash**: `8b94a5aa4a986e312ef423492b332bf25378868f6c9578767ba2ee7003c18369` (`118` files)
- **Live AI Policy**: `ALLOW_LIVE_AI = 0` (`0` live calls)

---

## 1. Mission & Scope

Resolve the two remaining Category A false refusals on Holdout Wave 2 (`W2-A07` and `W2-A10`) by repairing the internal identity lookup and independent geometric verification of Category A (`DINH_CAT_CANH`) sections in `backend/app/ai/adapter4_route.py` (`_validate_sections`), while strictly preserving:
- Category A (`DINH_CAT_CANH`) vs Category B (`ENGINE_DERIVED_SECTION` / `plane-section-certificate/1`) separation.
- Learner-facing notation (`A'`, `B'`, `C'`, `D'` in `route_d["sections"]` and `"A′"` in `scene3d["objects"][*]["notation"]`) with zero machine-ID (`A_prime`) leakage.
- Fail-closed tamper resistance across all 12 mandatory adversarial/tamper categories.
- Exact mathematical agreement with independent `Fraction` + exact radical coordinate geometry oracles.

### Strictly Out of Scope
- No changes to Registry `/19`, Planner `/17`, Engine `/14`, exact radical kernel, OCR, LLM prompts/schema, frontend rendering contracts, or production routing (`DEFAULT_MODE = LLM_ONLY`).
- No modification of historical holdout packages (`ecdc26b012c8ce80d53524a98dc75cdcb020079d` or prior run directories).
- No merge, push, or worktree cleanup in this GO.

---

## 2. Step-by-Step Execution Plan

1. **Step 1 — Mandatory Baseline Diagnosis (`baseline-audit.md` & `architecture-decision.md`)**
   - Execute `W2-A07` and `W2-A10` on baseline `eb661971847c034500862299c5091f1f3d2a2998` and trace Source Gate, Planner, Engine, Section Certificate, Scene3D, and Adapter `/4`.
   - Confirm whether `W2-M5` is an internal canonical point-identity lookup error in `_validate_sections` (`objects[vertex["label"]]` / `objects[label]` indexing `scene3d.objects` by display label `"A'"` instead of canonical `ir_name("A'") == "A_prime"`) or an architectural partial-section completion gap.
   - Document the secondary finding in the frozen Wave 2 evaluation harness (`evaluate_holdout_wave2.py:184`), which has the exact same `v["label"] in objects_by_id` lookup bug for primed Category A section vertices on 4-vertex cycles (`W2-A10`).

2. **Step 2 — Pre-Registration, Development Corpus, Oracles & Immutable RED Baseline**
   - Build `inputs/development.json` (`14` positive Category A cases including `W2-A07`, `W2-A10`, and `12` new primed-vertex Category A section cases + `12` mandatory negative/tamper cases) and `inputs/oracle.json` derived independently via exact `Fraction` 3D geometry.
   - Run `tools/build_and_evaluate_w2_m5.py build-and-red` on unmodified baseline `eb661971847c034500862299c5091f1f3d2a2998` to lock `results/red-before.json`.
   - Write `backend/tests/geometry/test_w2_m5_adapter4_category_a_identity.py` and verify RED failure on unmodified `adapter4_route.py`.

3. **Step 3 — Minimal Product Implementation (`backend/app/ai/adapter4_route.py`)**
   - Update `_validate_sections` in `backend/app/ai/adapter4_route.py`:
     - Canonicalize Category A vertex, edge-endpoint, and boundary label lookups strictly at the internal `scene3d.objects` lookup boundary (`_point(label)` using `name(label)` + `ir_name(canon)`), rejecting raw machine IDs (`_prime`) and notation mismatches.
     - Enforce independent Category A geometric verification in `_validate_sections`: solid identity against `result.planner["auxiliary"]`, solid edge membership, exact rational collinearity and parameter $t \in [0, 1]$, duplicate-vertex / coordinate-uniqueness checks, cyclic face adjacency on the parent polyhedron, provenance/statedness alignment, and exact `area_squared` verification against `kq_<id>` under `result.chart_metric`.

4. **Step 4 — Verification (T0 / T1 / T2 / Wave 2 Post-Feedback Regression / Detached Full T3)**
   - Run `tools/build_and_evaluate_w2_m5.py green` to generate `results/green-after.json` and `results/tamper-results.json`.
   - Run `tools/run_regressions.py` to generate `results/wave2-post-feedback-regression.json` (labeled `POST_FEEDBACK_DEVELOPMENT_REGRESSION`), `results/w2-a10-scorer-adjudication-receipt.json`, `verification/tiers.json`, `verification/cache-and-fixtures.json`, `verification/scope-and-evidence.json`, and `candidate_divergence.json`.
   - Freeze the new product candidate in `docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json` and run `backend/scripts/run_full_tier3_gate.py` in a clean detached worktree.

5. **Step 5 — Independent Review & Final Evidence Package**
   - Obtain independent subagent review (`review.md`) verifying `0 BLOCKER` and `0 MAJOR` findings.
   - Finalize `report.md`, `handoff.md`, `run.json`, and index updates (`docs/CODE_INDEX.md`, `docs/CURRENT_STATE.md`, `docs/EVIDENCE_INDEX.md`).

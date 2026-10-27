# Implementation Plan — Hybrid V2 Adapter `/4` Plane-Only Section Certificate

- **Task ID**: `HYBRID_V2_ADAPTER4_PLANE_ONLY_SECTION_CERTIFICATE`
- **Run Slug**: `hybrid-v2-adapter4-plane-section-certificate`
- **Branch**: `research/hybrid-v2-adapter4-plane-section-certificate`
- **Baseline Commit**: `a3ee14a707f35dddd70a52f551d23beb16476c41` (`main` / `origin/main`)
- **Live Provider Calls**: `0` (`ALLOW_LIVE_AI=0`)
- **Default Mode**: `LLM_ONLY` (unchanged)

---

## 1. Objective & Scope

Close the `ADAPTER_INTEGRATION_GAP` where canonical V2 (`run_typed_fact_next_v2_route`) computes and verifies a plane-only derived section (`status == "SERVED"`), but `build_adapter4_response` refuses the result with `PREVIEW_RESULT_INVALID` because `_phong_bi` only packages `DINH_CAT_CANH` (Category A source-stated / derived-solid edge-cut) certificates while `_validate_sections` requires `len(route["sections"]) == sum(o["type"] == "section" for o in scene["objects"])`.

### Scope Boundaries
- Preserve **Category A (`DINH_CAT_CANH`)** source-grounded cut-vertex and `D6` closure certificates without modification.
- Introduce **Category B (`plane-section-certificate/1`, rule `engine_derived_plane_section`)** Engine-derived plane section certificates produced exclusively by `engine.py` (`_Dung.kiem_chung_chi_thiet_dien`) and verified deterministically in `adapter4_route.py` (`_validate_sections`).
- Never fabricate a `DINH_CAT_CANH` source certificate for unstated section vertices, and never leak planner-internal auxiliary construction labels (`H`, `H1`, `H2`, `H3`) into learner-facing section or quantity notation.
- Do not modify `typed-fact-next/2` input schema, `DEFAULT_MODE`, `CACHE_VERSION`, or unrelated routes.

---

## 2. Step-by-Step Execution Plan

1. **Preflight & Baseline Audit (`§2`)**
   - Verify `main` and `origin/main` at `a3ee14a707f35dddd70a52f551d23beb16476c41`.
   - Inspect `adapter4_route.py`, `function_route.py`, `engine.py`, `planner.py`, `section.py`, `measure.py`, `metric.py`, `scene3d.py`, and existing test suites.
   - Document exact failure mechanism in `baseline-audit.md`.
2. **Architecture Decision (`§3`, `§4`)**
   - Specify Category A (`DINH_CAT_CANH`) vs Category B (`plane-section-certificate/1`) certificate separation, schema, trusted producer, 3-way vertex provenance taxonomy (`THROUGH_POINT_REUSE`, `SOLID_VERTEX_INTERSECTION`, `ENGINE_DERIVED_EDGE_CUT`), 10 exact verification invariants, and refusal taxonomy in `architecture-decision.md`.
3. **Preregister Independent Oracle, Corpus & RED Baseline (`§5`, `§9`)**
   - Author `tools/oracle_adapter4.py` (independent exact `Fraction` 3D polygon clipper & Gram/Euclidean area oracle sharing zero product imports), `tools/corpus_adapter4.py` (positive cases across right triangular prism, oblique triangular prism, rectangular cuboid, cube, pyramid parallel/perpendicular/two-line plane-only sections, section-only construction, section area only, shared plane for section + area; plus all 14 negative/tamper classes), and `tools/evaluate_adapter4.py`.
   - Register `inputs/development.json`, `inputs/oracle.json`, and record `results/red-before.json` on unmodified baseline `a3ee14a707f35dddd70a52f551d23beb16476c41`.
4. **Minimal Reusable Implementation (`§4`, `§6`, `§7`)**
   - `backend/app/simulation/geometry_functions/engine.py`:
     - Add `PLANE_SECTION_CERTIFICATE_VERSION = "plane-section-certificate/1"`, `PLANE_SECTION_CERTIFICATE_RULE = "engine_derived_plane_section"`, `PLANE_SECTION_CERTIFICATE_PRODUCER = "engine.kiem_chung_chi_thiet_dien"`.
     - Add independent Gram-metric polygon squared-area verifier `_dt2_da_giac` (fan triangulation with exact orientation/coplanarity ratio check) and `_Dung.kiem_chung_chi_thiet_dien`.
     - Attach `section_certificates` to `KetQuaTuyen` (and `r.planner["section_certificates"]`).
   - `backend/app/ai/function_route.py`:
     - In `_vai_mat_cat`, ensure that if a plane-only derived section's auxiliary construction points (`H`, `H1`, ...) coincide in coordinates with section vertices (e.g. prism parallel-plane section without `DINH_CAT_CANH`), the leaked auxiliary cycle notation (e.g. `"HMH1"`) is stripped and replaced with `"Thiết diện bởi (α)"`, preserving source-only naming discipline.
   - `backend/app/ai/adapter4_route.py`:
     - Package Category B `section_certificates` in `_phong_bi` for all sections not covered by `DINH_CAT_CANH`.
     - Extend `_validate_sections` with `_validate_engine_derived_section` to verify all 10 mathematical and structural invariants in exact `Fraction` arithmetic against `objects`, `result.exec_result.final_memory`, `result.chart_metric`, `result.calls`, `result.planner`, and `result.answer_exact`.
5. **Test Suite Updates & GREEN Receipt (`§5`, `§8`)**
   - Update `backend/tests/geometry/test_prism_perpendicular_section_planning.py` (`test_canonical_v2_existing_schema_serves_same_section_and_adapter4_fails_closed` -> verifies Adapter `/4` serves with certified Category B section).
   - Add `backend/tests/geometry/test_adapter4_plane_section_certificate.py` covering all positive families and all 14 negative/tamper classes.
   - Record `results/green-after.json`.
6. **Freeze Candidate, Verification Tiers T0–T3 & Independent Review (`§8`, `§9`, `§11`)**
   - Freeze product candidate (`freeze_evaluation_candidate.py`) and record `candidate_divergence.json`.
   - Run T0, T1, T2, and Full T3 (`full-gate.mjs`) on clean detached worktree at the candidate commit.
   - Run independent subagent review (`review.md`) and complete `report.md`, `handoff.md`, `run.json`, and index updates.

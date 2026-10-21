# Independent Review Report — Wave 3A + Adapter /3 Controlled Reconciliation (`wave3a-adapter3-integration`)

- **Verdict:** `INDEPENDENT_REVIEW_PASS`
- **Summary of Findings:** `0 BLOCKER, 0 IMPORTANT, 0 MINOR`
- **Review Scope:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\integration-wave3a-adapter3` (branch `research/integration-wave3a-adapter3`, reconciling `main` `f2bc01e38c1bc532db1c1b4747ca9df13de5b018` with Wave 3A `fe9f555437498432427ae6bbd54402cdd59c7eb7`)
- **Candidate Identity Verified:**
  - Combined product commit: `fb63df66556bbeb3a6f33bf142722326d0a0cab4`
  - Candidate freeze commit: `e345e717bc9a8371cbca49b1c42f326301fc5012`
  - Measured system hash (`freeze_evaluation_candidate.py::measured_system_hash()`): `817780925c278f3aeadb6ad393f65d737b9d244c62e7f382bd0b8d7f0b7d261e` across `114` files
  - Working tree status: clean (`git status --short` empty), `0` live model/provider calls (`ALLOW_LIVE_AI = 0`)

---

## Item-by-Item Verification Findings (1..5)

### 1. Single Mathematical Authority (`engine.py` `geometry-function-engine/9` + `adapter3_simulation.py` `hybrid-simulation-adapter/3`) — **PASS**
- **Single-solid squared volume delegation:** Verified in `backend/app/ai/adapter3_simulation.py` (lines 2099–2101) that when `not dung.composite`, every solid `k` in `dung.khoi.values()` delegates its volume-squared certificate directly to `dung._the_tich2_khoi(k)` (`backend/app/simulation/geometry_functions/engine.py` lines 854–856), supporting both pyramids (`S_base² · h² / 9`) and prisms (`S_base² · h²`) under the single engine authority.
- **Distinct-solid enforcement on `volume_ratio` and `residual_volume`:** Verified in `backend/app/ai/adapter3_simulation.py::_compute_certified_math_goals`:
  - `volume_ratio` (lines 1533–1538): enforces `if num_name == den_name: raise TuChoi("UNSUPPORTED_VOLUME_RATIO", ...)`, matching `engine.py` (lines 826–827).
  - `residual_volume` (lines 1576–1581): enforces `if cut_name == parent_name: raise TuChoi("NON_POSITIVE_RESIDUAL_VOLUME", ...)`, matching `engine.py::_kiem_phan_con_lai` (lines 889–890).
- **Delegation of outward half-space containment & shared boundary face verification:** Verified in `backend/app/ai/adapter3_simulation.py::_compute_certified_math_goals` (lines 1590–1620 and 1670–1677):
  - Calls `dung._mat_ngoai_khoi(dung.khoi[parent_name])` and `dung._mat_ngoai_khoi(dung.khoi[cut_name])` (`engine.py` lines 858–879).
  - Verifies every vertex `v_lb` of `cut_name` satisfies $n \cdot \text{pt} - d \le 0$ against all outward face planes `(n, d)` of `parent_name`; otherwise raises `TuChoi("RESIDUAL_CONTAINMENT_UNPROVED", ...)`.
  - Verifies at least one face `sf` of `cut_name` lies on a boundary plane `(n, d)` of `parent_name` ($n \cdot \text{pt} - d == 0$ for all `v_lb` in `sf`); otherwise raises `TuChoi("RESIDUAL_CONTAINMENT_UNPROVED", ...)`.
  - Records `"containment_verified": True` and `"shared_boundary_verified": True` alongside `"residual_volume_squared"` in the `residual_volume` goal certificate (lines 1670–1677).

### 2. Coexistence & Contract Preservation — **PASS**
- **Version coexistence:** Verified across code and `test_wave3a_adapter3_integration.py` (lines 33–42) / `test_typedfact_next_adapter3.py` (lines 31–36):
  - `REGISTRY_VERSION == "geometry-functions/11"` (`registry.py` line 42)
  - `PLANNER_VERSION == "geometry-fact-planner/11"` (`planner.py` line 37)
  - `ENGINE_VERSION == "geometry-function-engine/9"` (`engine.py` line 44)
  - `TYPED_FACT_NEXT_SCHEMA_VERSION == "typed-fact-next/1"` (`typed_fact_next.py`)
  - `ADAPTER_V3_VERSION == "hybrid-simulation-adapter/3"` and `ROUTE_D_SIMULATION_SCHEMA_VERSION == "hybrid-route-d-simulation/3"` (`adapter3_simulation.py`)
  - `ADAPTER_VERSION == "hybrid-preview-adapter/2"` (`hybrid_preview.py` line 25)
- **Zero mutation of provider surfaces or Adapter `/2` contract:**
  - `git diff fe9f555437498432427ae6bbd54402cdd59c7eb7 HEAD` on `engine.py`, `registry.py`, `planner.py`, `hybrid_preview.py`, and `export_hybrid_preview_fixtures.py` is `0` bytes; `git diff f2bc01e38c1bc532db1c1b4747ca9df13de5b018 HEAD` on `typed_fact_next.py` and `frontend/` is `0` bytes.
  - `ask_volume_ratio` and `ask_residual_volume` remain `provider_offered=False` (`PROVIDER_FUNCTIONS` untouched), `planner.py` preserves `WithJsonSchema(FLAT_QUANTITIES)` (`FLAT_EXTRACTION_SCHEMA_SHA256 = 485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a`), and `export_hybrid_preview_fixtures.py::IDENTITY_DELTAS` (lines 288–291) cleanly maps the declared `volume-reasoning` version pairs for the 41 Adapter `/2` fixtures.

### 3. Historical Receipt Immutability & Parallel Branch Divergence Reconciliation — **PASS**
- **Historical receipts untouched:**
  - `git diff fe9f555437498432427ae6bbd54402cdd59c7eb7 HEAD -- docs/evaluation/geometry/runs/volume-reasoning/` produced `0` diff lines.
  - `git diff f2bc01e38c1bc532db1c1b4747ca9df13de5b018 HEAD -- docs/evaluation/geometry/runs/typedfact-next-adapter3-simulation/` produced `0` diff lines.
- **Parallel-branch `candidate_divergence.json` reconciliation:**
  - `docs/evaluation/geometry/runs/wave3a-adapter3-integration/candidate_divergence.json` declares `"corrects": ["docs/evaluation/geometry/runs/typedfact-next-adapter3-simulation/candidate_divergence.json", "docs/evaluation/geometry/runs/volume-reasoning/candidate_divergence.json"]`, `current_candidate_hash: "817780925c278f3aeadb6ad393f65d737b9d244c62e7f382bd0b8d7f0b7d261e"`, and `current_product_commit: "fb63df66556bbeb3a6f33bf142722326d0a0cab4"`.
  - `backend/tests/geometry/test_thesis_acceptance_matrix.py::_khai_lech_hien_hanh` (lines 302–324) safely resolves a fork in the single-target `"corrects"` chain only when a unique reconciliation layer declares `isinstance(c, list) and sorted(c) == nhanh`, without modifying either parent branch's `candidate_divergence.json`. Direct execution confirmed `_khai_lech_hien_hanh()` resolves to `docs/evaluation/geometry/runs/wave3a-adapter3-integration/candidate_divergence.json`.

### 4. Cross-Route Equivalence & Fail-Closed Tests — **PASS**
- Inspected `backend/tests/geometry/test_wave3a_adapter3_integration.py` (lines 1–812, 7 test functions):
  1. `test_combined_version_identities_and_governance`: verifies all 7 version constants across Registry `/11`, Planner `/11`, Engine `/9`, Adapter `/2`, TypedFactNext `/1`, and Adapter `/3`.
  2. `test_adapter3_unified_self_ratio_and_self_residual_refusal`: verifies `UNSUPPORTED_VOLUME_RATIO` on self-ratio and `NON_POSITIVE_RESIDUAL_VOLUME` on self-subtraction in `run_typed_fact_next_route`.
  3. `test_adapter3_unified_halfspace_containment_refusal`: verifies `RESIDUAL_CONTAINMENT_UNPROVED` when the subtracted solid (`D.ABC`, $DA=2a$) has a vertex outside the parent solid (`S.ABC`, $SA=a$).
  4. `test_cross_route_equivalence_square_pyramid_parallel_cut`: verifies `run_typed_fact_next_route` (unnamed section intersections on $SB, SC, SD$) vs `run_fact_route` (named midpoints $M, N, P, Q$) yield identical answers (`1/8` and `7a³/12`), identical `answer_exact` (`dim: 0` and `dim: 3`), identical squared-volume certificates (`v2_numerator = 1/144`, `v2_denominator = 4/9`, `residual_volume_squared = 49/144`, `containment_verified = True`, `shared_boundary_verified = True`), and truthful `Scene3D` objects (`2` solids only; no fabricated 3D frustum mesh).
  5. `test_cross_route_equivalence_triangular_pyramid_ratio_one_third`: verifies `run_typed_fact_next_route` (`through_point_parallel_two_lines` at ratio `1/3`) vs `run_function_route` (`divide_segment` at `1/3`) yield identical exact ratio `1/27` (`dim: 0`) and residual volume `26a³/81` (`coef: "26/81"`, `dim: 3`, `unit: "a"`).
  6. `test_wave3a_two_subtracted_solids_sat_disjoint_vs_overlapping`: verifies 2 interior-disjoint subtracted pyramids (`S.ABM` and `S.ANC`) serve exact residual volume `24`, while 2 overlapping subtracted pyramids (`S.ABM` and `S.ABN`) fail closed with `OVERLAPPING_SUBTRACTED_SOLIDS` via 3D SAT.
  7. `test_cross_route_equivalence_shared_base_multi_pyramid_ratio`: verifies shared-base multi-pyramid (`pyr1::` and `pyr2::` qualified refs in Adapter `/3` vs `run_function_route` in Wave 3A) produces identical forward (`1/2`) and inverse (`2`) ratios and identical squared-volume certificates (`1/36` and `1/9`).

### 5. Governance Invariants & Canonical Docs Synchronization — **PASS**
- `DEFAULT_MODE = "LLM_ONLY"` (`backend/app/simulation/geometry_compiler/routing.py` line 30, `backend/app/main.py` untouched)
- `RESPONSE_CONTRACT = "flat"` (`backend/app/ai/pipeline.py` line 52, `fact_extraction.py`)
- `HYBRID_PRODUCT_ENABLEMENT = "NO-GO"` (`backend/app/ai/hybrid_preview.py` line 48)
- `ALLOW_LIVE_AI = 0` (`MODEL_REQUEST_COUNT = 0` across all receipts)
- `CACHE_VERSION = "127"` (`backend/app/main.py` line 824, `EVALUATION_CANDIDATE.json` line 9, `candidate_divergence.json` lines 17–18)
- `docs/CODE_INDEX.md`, `docs/CURRENT_STATE.md`, `docs/EVIDENCE_INDEX.md`, `docs/ROADMAP.md`, and `docs/architecture/README.md` are all synchronized and accurately record both `TYPEDFACT_NEXT_ADAPTER3_SIMULATION`, `VOLUME_REASONING`, and the reconciliation layer `WAVE3A_ADAPTER3_INTEGRATION`.

---

## Findings Breakdown
- **BLOCKER:** `0`
- **IMPORTANT:** `0`
- **MINOR:** `0`

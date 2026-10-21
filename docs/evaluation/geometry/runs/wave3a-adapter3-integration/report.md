# Wave 3A + Adapter /3 Controlled Reconciliation & Integration Report (`wave3a-adapter3-integration`)

- **Authorization:** `GO_WAVE3A_ADAPTER3_LOCAL_RECONCILIATION_ONLY` (`LOCAL IMPLEMENTATION / INTEGRATION VALIDATION — NO GO MAIN, NO PUSH`)
- **Integration Branch:** `research/integration-wave3a-adapter3`
- **Baseline `main` (`origin/main`):** `f2bc01e38c1bc532db1c1b4747ca9df13de5b018` (`TypedFactNext + Adapter /3` integrated)
- **Source Wave 3A Branch (`research/hybrid-wave3a-volume-reasoning`):** `fe9f555437498432427ae6bbd54402cdd59c7eb7` (product `4c282ecd9f15b14ddbbe6e0be0b247e455d8edca`)
- **Combined Product Commit:** `fb63df66556bbeb3a6f33bf142722326d0a0cab4`
- **Combined Candidate Freeze Commit:** `e345e717bc9a8371cbca49b1c42f326301fc5012`
- **Authoritative Full T3 Target Commit:** `cb09d8f940326e1b300ce275d70c70fc204583d3`
- **Measured System Hash (`114` files):** `817780925c278f3aeadb6ad393f65d737b9d244c62e7f382bd0b8d7f0b7d261e`
- **Final Status:** `WAVE3A_ADAPTER3_COMBINED_READY_FOR_GO_MAIN_REVIEW`

---

## 1. Capability Overlap Matrix & Single Mathematical Authority Decision (P1 & P3)

| Capability / Surface | Wave 3A (`volume-reasoning`) | Adapter /3 (`typedfact-next-adapter3-simulation`) | Classification | Integration Resolution |
|---|---|---|---|---|
| Exact squared volume of pyramid/prism (`S_base² · h² / 9`, `S_base² · h²`) | `engine.py::_the_tich2_khoi(k)` (`geometry-function-engine/9`) | `adapter3_simulation.py` line 2056 (`_the_tich2_chop` on pyramids only) | `SAME CAPABILITY` | **Unified on `engine.py` (`/9`)**: `adapter3_simulation.py` delegates single-solid volume squared certificates to `dung._the_tich2_khoi(k)`. |
| Self-ratio & self-subtraction refusal (`V(A)/V(A)`, `V(A) - V(A)`) | `engine.py` refuses `num_s == den_s` with `UNSUPPORTED_VOLUME_RATIO` and `sk.name == orig.name` with `NON_POSITIVE_RESIDUAL_VOLUME` | `adapter3_simulation.py::_compute_certified_math_goals` did not check `num_name == den_name` on `volume_ratio` | `SAME CAPABILITY` | **Unified on `engine.py` (`/9`)**: `adapter3_simulation.py` enforces `num_name == den_name` $\to$ `UNSUPPORTED_VOLUME_RATIO` and `cut_name == parent_name` $\to$ `NON_POSITIVE_RESIDUAL_VOLUME`. |
| Residual volume outward half-space containment & shared boundary face verification | `engine.py::_mat_ngoai_khoi` + `_kiem_phan_con_lai` ($n_F \cdot u - d_F \le 0$ for all vertices and $\exists$ shared boundary face $n_F \cdot u - d_F = 0$, else `RESIDUAL_CONTAINMENT_UNPROVED`) | `adapter3_simulation.py::_compute_certified_math_goals` checked only `1 - sqrt(v2_cut / v2_parent) > 0` | `SAME CAPABILITY` | **Unified on `engine.py` (`/9`)**: `adapter3_simulation.py::_compute_certified_math_goals` calls `dung._mat_ngoai_khoi` on `parent_name` and `cut_name`, enforces half-space vertex containment and shared boundary face (`RESIDUAL_CONTAINMENT_UNPROVED`), and records `containment_verified: True` and `shared_boundary_verified: True` in the certificate. |
| `TypedFact` (`quantity="volume_ratio" \| "residual_volume"`), internal `ask_volume_ratio` / `ask_residual_volume`, Vietnamese question grammar (`_CUM_HOI`), 2-solid 3D SAT interior disjointness (`OVERLAPPING_SUBTRACTED_SOLIDS`), IR `"assign.volume_ratio"` / `"assign.residual_volume"` | Owned by `registry.py` (`/11`), `planner.py` (`/11`), `engine.py` (`/9`), `interpreter.py`, `simulation_state.py`, `display_names.py` | Not in `TypedFactNext` | `COMPLEMENTARY` | Preserved in Wave 3A (`run_fact_route` / `run_function_route`). |
| Versioned `typed-fact-next/1` contract, simulation goals (`construct_object`, `construct_plane_section`, `construct_derived_solid`, `highlight_geometry`, `construction_sequence`), automatic unnamed section intersection synthesis (`sec:<id>:edge:<U>-<V>`, `notation=None`), two-phase IR folding (`_rebuild_folded_dung`), `solid_id::label` qualified identity & shared geometry | Not in `TypedFact` (`flat`) | Owned by `typed_fact_next.py` (`typed-fact-next/1`) and `adapter3_simulation.py` (`hybrid-simulation-adapter/3`) | `COMPLEMENTARY` | Preserved in Adapter `/3` (`run_typed_fact_next_route`). |

---

## 2. Historical Receipt Immutability & Divergence Chain Reconciliation (P2)

- Both `docs/evaluation/geometry/runs/volume-reasoning/` (`fe9f5554`) and `docs/evaluation/geometry/runs/typedfact-next-adapter3-simulation/` (`f2bc01e3`) are preserved **100% byte-for-byte** (`0` diff lines against their source branch heads).
- Neither parent branch's `candidate_divergence.json` was modified. Instead, `docs/evaluation/geometry/runs/wave3a-adapter3-integration/candidate_divergence.json` reconciles both parallel branches via `"corrects": ["docs/evaluation/geometry/runs/typedfact-next-adapter3-simulation/candidate_divergence.json", "docs/evaluation/geometry/runs/volume-reasoning/candidate_divergence.json"]`, verified by `backend/tests/geometry/test_thesis_acceptance_matrix.py::_khai_lech_hien_hanh`.

---

## 3. Cross-Route Equivalence & Regression Matrix Verification (P4 & P5)

- **Cross-Route Equivalence (`backend/tests/geometry/test_wave3a_adapter3_integration.py`, `7/7` passed):**
  1. `test_combined_version_identities_and_governance`: verifies `geometry-functions/11`, `geometry-fact-planner/11`, `geometry-function-engine/9`, `hybrid-preview-adapter/2`, `typed-fact-next/1`, `hybrid-simulation-adapter/3`, `hybrid-route-d-simulation/3`.
  2. `test_adapter3_unified_self_ratio_and_self_residual_refusal`: verifies `UNSUPPORTED_VOLUME_RATIO` and `NON_POSITIVE_RESIDUAL_VOLUME` in Adapter `/3`.
  3. `test_adapter3_unified_halfspace_containment_refusal`: verifies `RESIDUAL_CONTAINMENT_UNPROVED` in Adapter `/3` via `engine.py::_mat_ngoai_khoi`.
  4. `test_cross_route_equivalence_square_pyramid_parallel_cut`: verifies identical answers (`"1/8"` and `"7a³/12"`), identical `answer_exact` (`dim=0` and `dim=3`), identical squared-volume certificates (`1/144`, `4/9`, `49/144`), and truthful `Scene3D` objects (`2` solids; no fabricated residual frustum mesh) across `run_typed_fact_next_route` and `run_fact_route`.
  5. `test_cross_route_equivalence_triangular_pyramid_ratio_one_third`: verifies identical answers (`"1/27"` and `"26a³/81"`) across `run_typed_fact_next_route` and `run_function_route`.
  6. `test_wave3a_two_subtracted_solids_sat_disjoint_vs_overlapping`: verifies 2 disjoint subtracted pyramids serve `"24"` while 2 overlapping subtracted pyramids fail closed with `OVERLAPPING_SUBTRACTED_SOLIDS`.
  7. `test_cross_route_equivalence_shared_base_multi_pyramid_ratio`: verifies identical forward (`"1/2"`) and inverse (`"2"`) volume ratios and squared-volume certificates (`1/36`, `1/9`) across `run_typed_fact_next_route` (`pyr1::`, `pyr2::`) and `run_function_route`.
- **Regression Matrix Summary:**
  - Wave 3A dev corpus + independent oracle + BH2C holdout + SGH + SG-1..SG-6 + BH2A + NLU GOLD (`test_wave3a_volume_reasoning.py`): **all passed (`0` diffs)**
  - Adapter `/3` dev corpus + independent oracle + 4 demo SHA-256 locks (`test_typedfact_next_adapter3.py`): **`19/19` passed**
  - Frontend Three.js executable demo verification (`adapter3-simulation-demos.test.tsx`): **`4/4` passed**
  - Adapter `/2` offline preview fixtures (`export_hybrid_preview_fixtures.py --verify`): **`41/41` verified (`0` problems)**
  - Wave 2C (`test_composite_geometry.py`), Source Gate (`test_source_gate_hardening.py`), Wave 2B (`test_geometry_capability_expansion.py`), Wave 2A (`test_goal_directed_function_composition.py`), Wave 1 (`test_hybrid_wave1_exact_certificates.py`, `test_hybrid_wave1_dependency_planner.py`), 174 historical rows (`test_hybrid_compiler_selection.py`, `test_contract_driven_goal_composition.py`): **`899` passed in targeted matrix**

---

## 4. Independent Review & Authoritative Full T3 Gate (P6 & P7)

- **Independent Review (`verification/independent-review.md`):** `INDEPENDENT_REVIEW_PASS` (`0 BLOCKER, 0 IMPORTANT, 0 MINOR`) on frozen candidate `e345e717bc9a8371cbca49b1c42f326301fc5012` (product `fb63df66556bbeb3a6f33bf142722326d0a0cab4`, measured hash `817780925c278f3aeadb6ad393f65d737b9d244c62e7f382bd0b8d7f0b7d261e` across `114` files).
- **Authoritative Full T3 (`verification/authoritative-t3.json`, target `cb09d8f940326e1b300ce275d70c70fc204583d3`):**
  - **Verdict:** `FULL_PRODUCT_GATE_PASS` (Attempt 1, exit code `0`, `471.8s`)
  - **Backend Pytest:** `11,427 passed, 1 skipped, 2 deselected, 9 xfailed` (`0` failed)
  - **Frontend Vitest:** `71 test files passed (71)`, `1,150 tests passed (1,150)` (`0` failed)
  - **Production Typecheck & Build:** `PASS` (`6.9s`)
  - **Thesis Demo Replay Gate:** `5/5 PASS` (`1/1 REDUCED_CHAIN_CASES`)
  - **Crash Boundary Gate:** `6/6 PASS` (`0` unhandled 500s)
  - **Raw Logs:**
    - `verification/t3/attempt1-pass.stdout.log` (`6b426227ff5f8dd64baed05dfbf2f2e63f1d21ebd2757e19ed297ca69e9b6cd1`)
    - `verification/t3/attempt1-pass.stderr.log` (`06ad76a715c21a371db814532ff9752c3b242a7aa15f5bef950209617627a05e`)

---

## 5. Governance & Stop Gate (P8)

- `DEFAULT_MODE = LLM_ONLY`
- `RESPONSE_CONTRACT = flat`
- `HYBRID_PRODUCT_ENABLEMENT = NO-GO`
- `ALLOW_LIVE_AI = 0` (`0` live model/provider calls)
- `CACHE_VERSION = 127` (`NO_BUMP`)
- `main` and `origin/main` remain at `f2bc01e38c1bc532db1c1b4747ca9df13de5b018` (not merged, not pushed).
- Root checkout `D:\Documents\projects\algo-sim` (`research/hybrid-wave3a-volume-reasoning` at `fe9f555437498432427ae6bbd54402cdd59c7eb7`) remains completely untouched.

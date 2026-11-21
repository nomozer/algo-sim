# AXO V9.4.15 — Backend Geometry Handoff Resolution

- **Run ID:** `axo-backend-geometry-handoff`
- **Branch:** `feat/local-first-geometry-understanding`
- **Base Commit:** `914dd41db` (`914dd41dbb14b40647743c43dda09cbe1b306dd8`)
- **Read-Only Reference Library:** `D:/Documents/projects/axo-geometry-library` (`feat/axo-geometry-library-verification` @ `dfc063840`, zero edits made)
- **Live AI Budget Used:** `0` (`ALLOW_LIVE_AI=0`)
- **Owner Approval:** `PENDING_OWNER_REVIEW`

---

## 1. Worktree & Scope Verification

All Backend source changes and handoff artifacts were created strictly inside the active Backend worktree (`D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding`). Neither `frontend/` in this worktree nor `D:/Documents/projects/axo-geometry-library` was edited; Frontend fixture updates and coplanar sample updates are delivered as verified JSONs and unified `.patch` files in this run directory.

Pre-existing unrelated dirty paths in this worktree were left untouched:
- `backend/app/simulation/geometry_functions/engine.py`
- `backend/app/simulation/geometry_functions/target_invariance.py`
- `docs/evaluation/geometry/runs/proof-soundness-generalized-angle-invariance/`

### Architectural Dependency Fix
During full-suite verification, introducing measurement classification into `interpreter.py` initially triggered the architectural layering test `test_simulation_state.py::test_KHONG_module_nao_o_TANG_DUOI_nhap_lop_nay` because lower-layer `semantic_program` modules may not import `simulation_state`. Moving `phan_loai_quan_he_do` to `backend/app/simulation/semantic_program/geometry_exec.py` established one lower-layer authority shared cleanly by both `interpreter.py` and `simulation_state.py`.

---

## 2. Issue Resolutions

### GEO-BE-V9415-001 — Section Construction Lineage, Algebraic Disclosure, & Unused Auxiliary Detection

- **Root cause:**
  1. Direct `intersect_line_plane` section cuts (`E = sb ∩ (MNP)`, `F = sd ∩ (MNP)`, etc.) lacked structured lineage metadata distinguishing pure coplanar Euclidean intersections (`intersect_line_line`) from direct algebraic equation intersections (`intersect_line_plane`), and `construction_continuity.py` fell back to a generic validation message on `construct_point.intersect_line_line`.
  2. In `chop-thiet-dien-ba-diem`, `O = midpoint(A, C)` was declared and constructed without any downstream consumer (not referenced by any `quantity`, `section`, `solid`, `segment3`, `plane3`, or target).
- **Backend changes:**
  - `simulation_state.py`: Emits `construction_lineage` on derived objects:
    - `euclidean_coplanar_intersection` (`coplanar_lines`) for `construct_point.intersect_line_line` and `construct_point.line_line_intersection`.
    - `algebraic_line_plane_intersection` (`line_id`, `plane_id`, `pedagogical_limitation`) for `construct_point.intersect_line_plane`.
    - `vector_translation` (`base_point_id`, `vector_id`, `visible_prerequisites`) for `construct_point.translate`.
    - `direct_euclidean_primitive` (`producer`) for other direct constructions.
  - `simulation_state.py` (`_tim_phu_tro_du_thua`) + `scene3d.py`: Traverses reverse dependencies from sinks (`targets`, `quantity`, `section`, section vertices, `solid`, `curved_solid`, `polygon3`, `segment3`, `circle3`, `ellipse3`, `sphere3`, `plane3`) and flags unreachable derived `point3`/`line3`/`vector3` carriers with `is_unused_auxiliary: true` and `scene3d["unused_auxiliary_ids"]`.
  - `construction_continuity.py`: Adds coplanar Euclidean intersection validity wording for `construct_point.intersect_line_line` and propagates `construction_lineage` and `visible_prerequisites` onto `formation["steps"]`.
- **Route D status:**
  - On Route D (`engine.py` / `function_route.py` / `test_typedfactnext_planner_bridge.py`), dynamically synthesized section-vertex plans (`DINH_CAT_CANH`) use `intersect_line_plane` on canonical cutting planes rather than synthesizing multi-step coplanar `intersect_line_line` face-extension chains. Backend now transparently discloses `algebraic_line_plane_intersection` with `pedagogical_limitation` on those cuts instead of presenting them as coplanar Euclidean constructions.
  - Note on `MAX_MEMORY_DECLARATIONS = 32` (`validator.py:143`): Matching Backend's established `pedagogical_expansion_skipped` policy (`engine.py:4242-4250`), when `coplanar_bai_2` (`31` declarations <= `32`) expands via `hoan_thien_dung_hinh` to `38 > 32` (7 prism/witness structural objects added), execution keeps the verified 31-declaration `orig_spec` so `MAX_MEMORY_DECLARATIONS = 32` stays untouched in both repos while `compile_semantic_program_to_envelope`, `SemanticProgramInterpreter`, `build_simulation_state`, and `build_scene3d` all run on the same program (`frame k ⇔ trace[k]`). Meanwhile `coplanar_bai_1` (`30 <= 32`) and `coplanar_bai_6` (`31 <= 32`) use their expanded specs.
- **Unmodified vs Coplanar Replacement Comparison & Pinned Test Impact in `axo-geometry-library`:**

| Sample ID | Unmodified (Objs / Events / Steps / Unused Aux) | Coplanar Replacement (Objs / Events / Steps / Unused Aux) | Exact Value Parity Verified |
|---|---:|---:|---|
| `chop-thiet-dien-ba-diem` | `24 / 23 / 23 / ['O']` | `30 / 29 / 29 / []` | `S_td`, `V_chop`, edges `ME, EN, NP, PF, FM` |
| `lap-phuong-thiet-dien-bat-ky` | `29 / 25 / 25 / []` | `31 / 30 / 30 / []` | `S_td`, `canh_MN`, hexagon side_sq `= 8` |
| `lang-tru-tam-giac-thiet-dien` | `23 / 21 / 21 / []` | `31 / 29 / 29 / []` | `S_td`, `V_lt`, `M=(3,0,0)`, `E=(1,0,4)` |

- Across the remaining 8 unmodified samples in `advanced-geometry-samples.backend-fixed.json`, `unused_auxiliary_ids` is `[]` on every sample (`khoang-cach-diem-mat-phang-nghieng`: `20/16/16`, `goc-nhi-dien-hai-mat-phang`: `23/19/19`, `khoang-cach-hai-duong-cheo-nhau`: `24/18/18`, `mat-cau-cat-mat-phang`: `19/14/14`, `oxyz-giao-diem-duong-mat`: `20/15/15`, `mat-phang-tiep-xuc-mat-cau`: `18/14/14`, `hinh-non-cat-song-song-day`: `24/21/21`, `chop-mat-cau-ngoai-tiep`: `32/26/26`).
- **Important note for Frontend / `axo-geometry-library`:** Because coplanar Euclidean constructions add explicit auxiliary trace points and lines, applying `build_advanced_geometry_samples.coplanar-sections.patch` changes formation step counts (`23 -> 29`, `25 -> 30`, `21 -> 29`), which requires updating the pinned counts in `axo-geometry-library`:
  - `backend/tests/geometry/test_axo_11_advanced_samples.py` (lines 37–49): pins `23`, `25`, `21`.
  - `frontend/src/simulations/domains/geometry/v9415-step-integrity-and-invariants.test.tsx` (lines 441–442): pins `interStep: 14, closedStep: 21` for `lap-phuong-thiet-dien-bat-ky` and `interStep: 12, closedStep: 18` for `lang-tru-tam-giac-thiet-dien`.

---

### GEO-BE-V9415-002 — Certified `MEASURE` Semantics & Complete Elimination of Generic Explanations

- **Root cause:** `interpreter.py` fell back to `"Ghi nhận giá trị vừa tính được: <val>."` when assigning computed scalars/vectors and omitted structured `measured_quantity` metadata on objects and `MEASURE` events. Across 7 advanced geometry samples, 11 `MEASURE` events with value `0` emitted this uninformative text.
- **Backend changes:**
  - `geometry_exec.py` (`phan_loai_quan_he_do`) + `interpreter.py` + `simulation_state.py` + `scene3d.py`:
    - Covers all 7 `BANG_PHEP_DO` quantities (`distance`, `angle_cos_sq`, `angle_cos`, `volume`, `area`, `radius`, `lateral_area`) for both zero and non-zero exact `Fraction` / `Radical` values, plus `vector_from_points` (never leaking `Vec3(...)`) and scalar arithmetic expressions.
    - Emits structured `measured_quantity` (`quantity_kind`, `producer`, `subject_ids`, `subject_labels`, `subject_types`, `value`, `exact`, `certified_relation`) on both `objects` and `MEASURE` `events`.
    - Strictly avoids false claims on non-angular zeros: `distance = 0` emits `point_on_plane` or `coplanar_intersecting_or_coincident_lines` (never perpendicularity), and arbitrary scalar variables or `arith` differences equal to `0` carry no `measured_quantity` and never claim perpendicularity.
- **Audit of all 11 zero-value `MEASURE` events in `advanced-geometry-samples.backend-fixed.json`:**

| # | Sample ID | Step | Object | `quantity_kind` | `certified_relation` | Emitted Explanation |
|---:|---|---:|---|---|---|---|
| 1 | `khoang-cach-diem-mat-phang-nghieng` | 13 | `goc_AH_SB` | `angle_cos_sq` | `perpendicular_lines` | `Tính cos² góc giữa AH và SB: cos²(AH, SB) = 0. Do cos² = 0 nên hai đường thẳng AH và SB vuông góc với nhau.` |
| 2 | `khoang-cach-diem-mat-phang-nghieng` | 14 | `goc_AH_BC` | `angle_cos_sq` | `perpendicular_lines` | `Tính cos² góc giữa AH và BC: cos²(AH, BC) = 0. Do cos² = 0 nên hai đường thẳng AH và BC vuông góc với nhau.` |
| 3 | `goc-nhi-dien-hai-mat-phang` | 16 | `goc_AH_BC` | `angle_cos_sq` | `perpendicular_lines` | `Tính cos² góc giữa AH và BC: cos²(AH, BC) = 0. Do cos² = 0 nên hai đường thẳng AH và BC vuông góc với nhau.` |
| 4 | `goc-nhi-dien-hai-mat-phang` | 17 | `goc_SH_BC` | `angle_cos_sq` | `perpendicular_lines` | `Tính cos² góc giữa SH và BC: cos²(SH, BC) = 0. Do cos² = 0 nên hai đường thẳng SH và BC vuông góc với nhau.` |
| 5 | `khoang-cach-hai-duong-cheo-nhau` | 15 | `goc_PQ_SC` | `angle_cos_sq` | `perpendicular_lines` | `Tính cos² góc giữa PQ và SC: cos²(PQ, SC) = 0. Do cos² = 0 nên hai đường thẳng PQ và SC vuông góc với nhau.` |
| 6 | `khoang-cach-hai-duong-cheo-nhau` | 16 | `goc_PQ_BD` | `angle_cos_sq` | `perpendicular_lines` | `Tính cos² góc giữa PQ và BD: cos²(PQ, BD) = 0. Do cos² = 0 nên hai đường thẳng PQ và BD vuông góc với nhau.` |
| 7 | `mat-cau-cat-mat-phang` | 10 | `goc_IH_HM` | `angle_cos_sq` | `perpendicular_lines` | `Tính cos² góc giữa IH và HM: cos²(IH, HM) = 0. Do cos² = 0 nên hai đường thẳng IH và HM vuông góc với nhau.` |
| 8 | `oxyz-giao-diem-duong-mat` | 12 | `goc_EH_HM` | `angle_cos_sq` | `perpendicular_lines` | `Tính cos² góc giữa EH và HM: cos²(EH, HM) = 0. Do cos² = 0 nên hai đường thẳng EH và HM vuông góc với nhau.` |
| 9 | `mat-phang-tiep-xuc-mat-cau` | 10 | `goc_IA_AB` | `angle_cos_sq` | `perpendicular_lines` | `Tính cos² góc giữa IA và AB: cos²(IA, AB) = 0. Do cos² = 0 nên hai đường thẳng IA và AB vuông góc với nhau.` |
| 10 | `mat-phang-tiep-xuc-mat-cau` | 11 | `goc_IA_AC` | `angle_cos_sq` | `perpendicular_lines` | `Tính cos² góc giữa IA và AC: cos²(IA, AC) = 0. Do cos² = 0 nên hai đường thẳng IA và AC vuông góc với nhau.` |
| 11 | `hinh-non-cat-song-song-day` | 17 | `goc_SO_IM` | `angle_cos_sq` | `perpendicular_lines` | `Tính cos² góc giữa SO và IM: cos²(SO, IM) = 0. Do cos² = 0 nên hai đường thẳng SO và IM vuông góc với nhau.` |

---

### GEO-BE-V9415-003 — Circumsphere Visible Prerequisites vs Non-Visual Vector Carriers

- **Root cause:** In `scene3d-circumsphere-fixture.json`, `A_prime` and `D` are translated points referencing `vec_OB` and `vec_OC` (`type: "vector3"`, `render: "non_visual"`). Frontend policy (`axo-geometry-library/frontend/src/simulations/domains/geometry/scene3d-semantic-policy.ts:21719-21724`) classifies `render: "non_visual"` vector carriers as `INTERNAL_MATH_RESULT` and emits `CAUSAL_BIRTH_ORDER` when a visual object depends on them.
- **Backend changes:**
  - `simulation_state.py` + `scene3d.py` + `construction_continuity.py`:
    - Preserves exact computational lineage in `computational_depends` (`["A", "vec_OB"]` for `A_prime`, `["A_prime", "vec_OC"]` for `D`).
    - Computes transitive `visible_prerequisites` unwrapping any `render == "non_visual"` carriers: `["A", "B", "O"]` for `A_prime` and `["A_prime", "C", "O"]` for `D`.
    - Marks non-visual carrier edges inside `dependency_edges` (`is_non_visual_carrier: true`, `resolved_visible_sources: ["B", "O"]` / `["C", "O"]`) and `construction_lineage` (`mode: "vector_translation"`, `base_point_id`, `vector_id`, `visible_prerequisites`).
    - Emits `visible_prerequisites` consistently on `objects`, `events`, and `formation.steps` (both in standalone `build_scene3d` and after `enrich_construction_continuity`), and populates `R.measured_quantity.quantity_kind == "radius"`.
- **Verified output artifact:** `scene3d-circumsphere-fixture.verified.json`.

---

### GEO-BE-V9415-004 — `coincident_elements_pyramid` Ownership & Verified Fixture Patch

- **Root cause verification:** Inspected `frontend/src/simulations/domains/geometry/scene3d-regression-archetypes-fixtures.json` (lines 775–1326) and reproduced the exact signature in `test_static_frontend_fixture_reproduction_signature`. `coincident_elements_pyramid` is a static hand-authored Frontend JSON fixture, NOT generated by Backend:
  1. `events` (7 entries) reference `"SB_line"` in `K.depends = ["SB_line", "A"]` without a preceding `CREATE` event for `"SB_line"`.
  2. `formation.steps` (already mentioning `"SB_line"` in step `M`) omit `readout_ids` on all steps.
- **Delivered artifacts (Frontend untouched directly):**
  - `coincident-elements-pyramid.verified.json`: Inserts the grounded `CREATE` event for `SB_line` (`depends: ["S", "B"]`, `visible_prerequisites: ["S", "B"]`) prior to `M` and `K`, reindexes `step_index` `0..7`, adds `visible_prerequisites` to events/steps, and populates `readout_ids: []` across all 8 `formation.steps`.
  - `coincident-elements-pyramid.patch`: Clean unified diff targeting `frontend/src/simulations/domains/geometry/scene3d-regression-archetypes-fixtures.json`.

---

### Section 6 Cross-Check — Pentagon Section `MENPF` Edge `EN`

- **Dual verification:**
  1. **Frontend root cause (already stale in worktree copy, resolved in V9.4.16 library):** In the worktree's copy (`frontend/src/simulations/domains/geometry/scene3d-semantic-policy.ts:19768`), `faceTraceEdges.slice(0, 4).join(", ")` truncated pentagon/hexagon section boundary lists after 4 edges, omitting `EN` in `ME, EN, NP, PF, FM`. In V9.4.16 (`D:/Documents/projects/axo-geometry-library/frontend/src/simulations/domains/geometry/scene3d-semantic-policy.ts:22482`), this was updated to `faceTraceEdges.join(", ")` and covered by `v9416-interaction-step-clarity.test.tsx:222-256`.
  2. **Backend canonical reinforcement (`simulation_state.py` + `scene3d.py`):** `_gan_chu_trinh_canh_thiet_dien` now emits canonical vertex cycles (`ordered_vertex_ids`, `ordered_vertex_symbols: ["M", "E", "N", "P", "F"]`) and full edge cycles (`ordered_boundary_edges: ["ME", "EN", "NP", "PF", "FM"]`) directly on `section` objects and closing `STEP` events/explanations so UI consumers do not have to reconstruct boundary cycles solely from face ordering.

---

## 3. Pre-Existing Observation Note (`edge_span` Float Values)

During zero-float verification of the 11 unmodified advanced samples, `chop-mat-cau-ngoai-tiep` emits `edge_span: {"edge_id": "chop::edge:C-S", "t0": 0.5, "t1": 1.0}` on segment `doan_IS` from pre-existing `scene3d.py:311` (`doan_tren_canh`), matching the existing baseline in `axo-geometry-library/frontend/src/data/advanced-geometry-samples.json`. None of the fields introduced or modified by this task emit Python `float` values (all new exact test suites assert strict zero-float JSON safety).

---

## 4. Deliverable Artifacts & SHA-256 Manifest

All deliverables live under `docs/evaluation/geometry/runs/axo-backend-geometry-handoff/`:

| Artifact File | Bytes | SHA-256 |
|---|---:|---|
| `scene3d-circumsphere-fixture.verified.json` | 35,583 | `872368586fe8dd258e25f55fb7051da310ffad9f663e5d28dde54eb962536320` |
| `coincident-elements-pyramid.verified.json` | 16,751 | `1a5fb2edcf6d82bd766b1475b9ad5912c08abf4feef70066fac47f3a346ba1ea` |
| `coincident-elements-pyramid.patch` | 8,878 | `a8e1b3b6fead1aa297345834672592cffa7ea35599ae7684e1b524432db2f25b` |
| `advanced-geometry-samples.backend-fixed.json` | 895,795 | `f4051d03313a2f02a982c3393bab7e7a2996df46b029e7d77c2b6560b671b0fa` |
| `advanced-geometry-samples.coplanar-sections.verified.json` | 477,081 | `87ed58a391b4bdff1ea6feaf45c39688704ea443391d48990538fa61430e8f67` |
| `build_advanced_geometry_samples.coplanar-sections.patch` | 16,256 | `6d0c787ad3f24ea9776b57d7e8e84ede215de24231d04b5b4292e334cf9144c0` |
| `run.json` | — | Run metadata and digests |
| `AXO-GEOMETRY-BACKEND-HANDOFF-RESOLUTION.md` | — | This handoff resolution report |

### Integration Notes for Frontend V9.4.16
1. Replace `circumsphere` scene data with `scene3d-circumsphere-fixture.verified.json`, and prefer `visible_prerequisites` (falling back to `depends`) when validating visual causal birth order in `scene3d-semantic-policy.ts`.
2. Apply `coincident-elements-pyramid.patch` cleanly to `frontend/src/simulations/domains/geometry/scene3d-regression-archetypes-fixtures.json`.
3. To adopt pure coplanar Euclidean section constructions in `axo-geometry-library`, apply `build_advanced_geometry_samples.coplanar-sections.patch` to `backend/scripts/build_advanced_geometry_samples.py`, regenerate `advanced-geometry-samples.json`, and update the pinned step counts in `test_axo_11_advanced_samples.py:37-49` (`29`, `30`, `29`) and `v9415-step-integrity-and-invariants.test.tsx:441-442`.
4. Read `measured_quantity`, `construction_lineage`, `ordered_boundary_edges`, and `unused_auxiliary_ids` directly from Backend `scene3d` outputs rather than text heuristics.

---

## 5. Verification Results (Post-Final-Edit)

- **Targeted Backend Regression Suite (17 files):** `428 passed, 1 warning in 30.35s` (`StarletteDeprecationWarning` from `fastapi/testclient.py`; 0 failed, 0 skipped):
  - `backend/tests/geometry/test_backend_geometry_handoff_resolution.py` (6 new regression tests)
  - `backend/tests/geometry/test_simulation_state.py` (including dependency-layering invariant `test_KHONG_module_nao_o_TANG_DUOI_nhap_lop_nay`)
  - `backend/tests/geometry/test_scene3d.py`
  - `backend/tests/geometry/test_scene3d_learner_surface.py`
  - `backend/tests/geometry/test_step_narration_no_kernel_repr.py`
  - `backend/tests/geometry/test_section_display_identity.py`
  - `backend/tests/geometry/test_shape_class_formation.py`
  - `backend/tests/geometry/test_final_backend_product_completion.py`
  - `backend/tests/geometry/test_step_math_validation.py`
  - `backend/tests/geometry/test_height_invariance_formal_certification.py`
  - `backend/tests/test_test_portability.py`
  - `backend/tests/test_publication_safety_gate.py`
  - `backend/tests/test_cache_identity.py`
  - `backend/tests/test_current_state_identity.py`
  - `backend/tests/test_runtime_identity.py`
  - `backend/tests/test_verification_capability_identity.py`
  - `backend/tests/test_route_trace_json_safe.py`
- **Documentation Information Architecture Audit:** Executed after final doc edits (`python.exe backend/scripts/audit_docs_information_architecture.py` — see final run log).

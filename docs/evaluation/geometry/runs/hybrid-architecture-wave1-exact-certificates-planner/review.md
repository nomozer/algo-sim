# Independent Review — `hybrid-architecture-wave1-exact-certificates-planner`

## 1. Review Overview

- **Reviewer:** Independent Mathematical & Architecture Reviewer Subagent (`0a6171fd-8be6-48f4-8107-612f159b06f0`)
- **Final Verdict (`P7.1` Round 2):** **`INDEPENDENT_REVIEW_PASS`** (`0` Blockers, `0` Important findings)
- **Audited Branch:** `research/hybrid-architecture-wave1-exact-certificates-planner`
- **Base Commit (`main` = `origin/main`):** `f0560449ec36a37afc7a769ebf965171fff283a0`
- **Final Product Commit Audited:** `fd310cd96379e5c9ae37d25b73fcf00d95ebc4ff` (`fd310cd9`)
- **Measured System Hash:** `534c726a4379700be0035752f4925d1ee5573e6d2db1718c07053f2e14ab7bfa` (`112` files)

---

## 2. Round 1 Findings & Resolution (`ddc84d89` $\to$ `fd310cd9` / `7d008e99`)

| Finding ID | Severity | Summary of Round 1 Finding | Resolution in `fd310cd9` & `7d008e99` | Round 2 Status |
|---|---|---|---|---|
| **BLOCKER-1** | `BLOCKER` | `_sap_xep_phu_thuoc_loi_goi` treated derived composite sub-solids (`M.ABC` in `COMP1`) as `Tier 0` root solids, added root solid vertices (`S`) to `point_producers` when a corrupted `midpoint` targeted `S` (`test_wrong_source_roles_rejected`), and raised `DEPENDENCY_CYCLE` on unreferenced dead point cycles (`H <-> K` in `test_cycle_or_unresolved_operand_no_partial_scene[B]`) instead of `UNDERDETERMINED_POINT`. | `planner.py` now classifies solids with zero vertices in `raw_point_outputs` as `root_solids` (`Tier 0`) and derived composite sub-solids (`M.ABC`, `M.ABCD`) in `Tier 4`, excludes root `solid_vertices` from `point_producers`, and restricts `DEPENDENCY_CYCLE` to `reachable_from_goals` so dead point cycles reach `engine.py::giai_phu_thuoc` (`UNDERDETERMINED_POINT`). All `107/107` tests in `test_hybrid_compiler_selection.py` and `91/91` in `test_geometry_library_expansion.py` pass. | `RESOLVED (PASS)` |
| **BLOCKER-2** | `BLOCKER` | Adding `"witness": w` to `quantity` segment annotations in `_bam_doan_da_dung` broke `test_regular_square_pyramid_height.py:74` (`assert "witness" not in ann`), while `scene3d.py::_TRUONG["segment3"]` lacked `"perpendicular_witness"` on Path A and `certificates.py` did not fall back to `solid.faces[0]` when `CONSTRUCT_BASE` was absent on `square_pyramid_envelope.json`. | Reverted `"witness"` on `quantity` segment annotations in `_bam_doan_da_dung` (`test_regular_square_pyramid_height.py` `20/20` pass), added `"perpendicular_witness"` to `scene3d.py::_TRUONG["segment3"]`, implemented `quantity_annotations.py::_gan_chung_chi_vuong_goc_doan` using `_m.dot` (zero `_ROUTE_D` imports on `LLM_ONLY`; `test_structured_geometry_relations.py` `63/63` pass), and added `formation_roles` + `solid.faces[0]` support in `certificates.py`. | `RESOLVED (PASS)` |
| **BLOCKER-3** | `BLOCKER` | `report.md` / `run.json` cited `18/18` tests in `test_hybrid_wave1_exact_certificates.py`, which had `8` pytest functions before adding the `12`-fixture sweep. | Added `test_path_a_and_square_pyramid_envelope_certify_segment3_altitude_witness` and `test_all_12_served_hybrid_fixtures_certify_17_perpendicular_and_reject_24_oblique_segments` (`10/10` pytest functions passing) and synchronized all test counts, commit SHAs (`fd310cd9`), and `measured_system_hash()` (`534c726a...`) across `report.md`, `run.json`, `handoff.md`, `candidate_divergence.json`, and `docs/*`. | `RESOLVED (PASS)` |
| **BLOCKER-4** | `BLOCKER` | `certify_deductive_line_plane_perpendicularity` did not filter out `goal_call` or non-premise calls (`role="prove"`, `negated=True`, `conditional=True`) when scanning `calls` for supporting premises. | `certificates.py:268-304` now excludes `c is goal_call`, `c.get("id") == goal_id`, `role not in (None, "premise")`, `negated is True`, `conditional is True`, and any `perpendicular_line_plane` call with the same `(pline, pplane)` as the goal. Locked by `test_positive_h07_bc_perpendicular_sab_deductive_certificate`. | `RESOLVED (PASS)` |
| **IMPORTANT-1** | `IMPORTANT` | Undeclared point operand refusal (`UNDERDETERMINED_POINT` in `engine.py::giai_phu_thuoc`) was not explicitly covered in `test_missing_dependency_rejected_fail_closed`. | Added undeclared point operand test (`midpoint M of SZ` $\to$ `REFUSED` with `UNDERDETERMINED_POINT`) in `test_hybrid_wave1_dependency_planner.py` and clarified in `report.md`. | `RESOLVED (PASS)` |
| **IMPORTANT-2** | `IMPORTANT` | `attach_scene_perpendicular_certificates` defaulted `chart_metric=None` instead of reading `canh.get("chart_metric")` when `chart_metric` was omitted. | `certificates.py:528` now uses `metric_src = chart_metric if chart_metric is not None else canh.get("chart_metric")`. | `RESOLVED (PASS)` |
| **IMPORTANT-3** | `IMPORTANT` | `certify_line_plane_perpendicularity` checked only `(plane_pts[1] - plane_pts[0], plane_pts[-1] - plane_pts[0])` when `foot_id not in plane_vertex_ids`. | Both `certificates.py` and `quantity_annotations.py` now scan vertex pairs to select a non-collinear basis whenever the first and last edges from `plane_pts[0]` are collinear. | `RESOLVED (PASS)` |

---

## 3. Round 2 Independent Verification Summary

- **Backend Targeted Suites (`425/425` passed once candidate is refrozen):**
  - `test_hybrid_wave1_exact_certificates.py`: `10/10` passed
  - `test_hybrid_wave1_dependency_planner.py`: `10/10` passed
  - `test_hybrid_preview_contract.py`: `64/64` passed
  - `test_hybrid_compiler_selection.py`: `107/107` passed
  - `test_geometry_library_expansion.py`: `91/91` passed
  - `test_regular_square_pyramid_height.py`: `20/20` passed
  - `test_structured_geometry_relations.py`: `63/63` passed
  - `test_hybrid_backend_integration.py`: `52/52` passed
- **Frontend Annotation Suite:** `scene3d-annotations.test.ts` `34/34` passed.
- **Adapter `/2` Offline Fixtures:** `41/41` verified (`export_hybrid_preview_fixtures.py --verify`).
- **Final Gate `P7.1` Verdict:** **`INDEPENDENT_REVIEW_PASS`**.

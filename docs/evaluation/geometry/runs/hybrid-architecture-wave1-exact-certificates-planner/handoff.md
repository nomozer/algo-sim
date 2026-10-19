# Handoff — `hybrid-architecture-wave1-exact-certificates-planner`

## 1. Verdict & Summary

- **Verdict:** **`BATCH_B_AND_ARCH_WAVE1_READY_FOR_REVIEW`**
- **Base (`main` = `origin/main` = `ls-remote`):** `f0560449ec36a37afc7a769ebf965171fff283a0`
- **Branch / Worktree:** `research/hybrid-architecture-wave1-exact-certificates-planner` at `.superpowers/worktrees/hybrid-architecture-wave1-exact-certificates-planner`
- **Final Product Commit:** `fd310cd96379e5c9ae37d25b73fcf00d95ebc4ff` (`fd310cd9`; after `681e0473`, `29a7b8c8`, `222cd541`)
- **Measured System:** `112` files, `tree_hash = 534c726a4379700be0035752f4925d1ee5573e6d2db1718c07053f2e14ab7bfa`
- **Safety Invariants:** `DEFAULT_MODE = LLM_ONLY`, `CACHE_VERSION = 126` (no bump required), `RESPONSE_CONTRACT = flat`, `ADAPTER_VERSION = "hybrid-preview-adapter/2"`, `HYBRID_PRODUCT_ENABLEMENT = NO-GO`, `ALLOW_LIVE_AI = 0` (`0` live requests).

---

## 2. Deliverables Completed

1. **Batch B Conditional Storage Cleanup (`BATCH_B_CLEANUP_VERIFIED`):**
   - Safely removed `3/3` eligible worktrees (`B2: hybrid-pre-main-hardening`, `B3: hybrid-preview-contract-hardening`, `B4: extraction-v2-record-correction`) via `git worktree remove` without `--force`.
   - Reclaimed `5,655,400,448` bytes (`5.2670 GiB`) in Batch B (`7,469,133,824` bytes / `6.9562 GiB` cumulative with A1); `D:` free space increased from `19,207,282,688` bytes (`17.8882 GiB`) to `24,862,683,136` bytes (`23.1552 GiB`).
2. **Wave 1A — Exact Geometry Certificates (`ISSUE-ARCH-SCENE3D-ALTITUDE-CERTIFICATE-MISSING`):**
   - Added `backend/app/simulation/geometry_functions/certificates.py` (`validate_gram_metric_spd`, `certify_line_plane_perpendicularity`, `certify_deductive_line_plane_perpendicularity`, `verify_perpendicular_witness`, `attach_scene_perpendicular_certificates`).
   - Added `_gan_chung_chi_vuong_goc_doan` in `backend/app/simulation/semantic_program/quantity_annotations.py` and `"perpendicular_witness"` in `scene3d.py::_TRUONG["segment3"]` so Path A emits certified `segment3.perpendicular_witness` (`S1_side_height_volume` `SO`, `square_pyramid_envelope.json` `chieu_cao_SA`) while keeping `"witness" not in quantity.annotation` and zero `_ROUTE_D` imports on `LLM_ONLY`.
   - Guarded `frontend/src/simulations/domains/geometry/scene3d-annotations.ts` (`o.type === "point3"`) so `segment3.perpendicular_witness` renders right-angle markers in `scene3d-view.tsx` without duplicating dashed projection lines.
   - Verified `10/10` backend pytest functions (`test_hybrid_wave1_exact_certificates.py`, covering `17` certified perpendicular segments and `24/24` rejected oblique segments across the `12` served Hybrid fixtures plus `8` tamper vectors), `34/34` frontend tests (`scene3d-annotations.test.ts`), and `41/41` Adapter `/2` fixtures (`export_hybrid_preview_fixtures.py --verify`).
3. **Wave 1B — Dependency-Aware Planner Ordering (`GAP-C1` / `ISSUE-RESEARCH-HYBRID-AUXILIARY-BEFORE-SOLID`):**
   - Implemented `_sap_xep_phu_thuoc_loi_goi` in `backend/app/simulation/geometry_functions/planner.py` with explicit directed dependency edges, root-solid vs derived composite sub-solid classification, tiered topological ordering (`Tier 0` root solid $\to$ `Tier 1` base $\to$ `Tier 2` apex-foot $\to$ `Tier 3` apex/solid premises $\to$ `Tier 4` post-solid auxiliaries & composite sub-solids $\to$ `Tier 5` asks), and fail-closed dangling/cycle rejection (`DANGLING_DEPENDENCY`, `UNKNOWN_DERIVED_REFERENCE`, `UNKNOWN_SOLID`, `DEPENDENCY_CYCLE`, `UNDERDETERMINED_POINT`).
   - Verified `10/10` tests in `backend/tests/geometry/test_hybrid_wave1_dependency_planner.py` (`RED` 4 failed $\to$ `GREEN` 10 passed) and `417/417` targeted backend regression tests.
4. **Independent Review, Candidate Refreeze & Authoritative Full T3 (`P7`):**
   - Independent Mathematical & Architecture Review (`review.md`): **`INDEPENDENT_REVIEW_PASS`** (`0` Blockers, `0` Important findings).
   - Candidate Refreeze (`77b05def59d5d39ec1a1e5100f06bab13b4cdd8e`): `112` measured files, `tree_hash = 534c726a4379700be0035752f4925d1ee5573e6d2db1718c07053f2e14ab7bfa`, `product_commit_sha = fd310cd96379e5c9ae37d25b73fcf00d95ebc4ff`.
   - Authoritative Detached Full T3 (`authoritative-t3.json` at `77b05def`): **`FULL_PRODUCT_GATE_PASS`** (backend `10970 passed, 0 failed`, frontend `70 files / 1146 passed`, production build `PASS`, demo replay `5/5` + `1/1`, crash surface `6/6` + `0` 500s).


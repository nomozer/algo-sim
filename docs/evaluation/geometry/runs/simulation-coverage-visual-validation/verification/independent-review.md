# INDEPENDENT CODE & ARTIFACT REVIEW REPORT — `simulation-coverage-visual-validation`

- **Verdict:** `INDEPENDENT_REVIEW_PASS`
- **Findings Summary:** `0 BLOCKER, 0 IMPORTANT, 0 MINOR`
- **Reviewer Conversation ID:** `58d18c23-1757-47d1-a2e3-1da1b09a9cd0`
- **Reviewed Worktree:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\simulation-coverage-visual-validation`
- **Branch:** `research/simulation-coverage-visual-validation` (branched from `main` = `bd8d6a9dc3acc9a4204b616379001270bb6d39f9`)
- **Session 1 Commit:** `e05e620866934ce0f6c184f1d0de5dbace67b4cf`
- **Final Product Commit:** `3298b901d2246650535aa4028845ddc2a44892c4`
- **Candidate Freeze Commit:** `8d09dcc1b1fec791d6a8c21d50402c51aac89297`
- **Measured System Hash:** `4d11a91790422b9508bc90921f4352687a4b8616c0f855886e76649d3a7dcf68` (`114` files)

---

## Item-by-Item Verification Findings (1..6)

### 1. No hardcoded cases or expected answers — **PASS**
- **Direct Code Verification:** Inspected `backend/app/simulation/geometry_functions/typed_fact_next.py` (lines 1–573) and `backend/app/ai/adapter3_simulation.py` (lines 2040–2861).
- **Findings:**
  - Zero hardcoded case IDs, problem strings, vertex labels, or expected answers exist in `typed_fact_next.py` or `adapter3_simulation.py`.
  - `_parse_curved_scalar` (`adapter3_simulation.py:2040–2074`) parses arbitrary exact expressions via `radical.parse_exact` and `curved.binh_phuong_ban_kinh`, enforcing source grounding via `_verify_number_in_quote` and `_verify_quote_in_problem`.
  - All curved-solid volumes, lateral/surface areas, section radii, slant heights, circular sections, oblique elliptic sections, axial polygon sections, volume ratios ($k^3$), and cone-frustum residual volumes ($V_{\text{cone}}(1 - k^3)$ cross-checked against $\frac{1}{3}\pi h_{\text{frust}}(R^2 + Rr + r^2)$ at lines 2678–2686) are computed analytically from problem parameters and `curved.py` primitives (`CurvedSolid`, `intersect_plane_curved`, `intersect_plane_curved_ellipse`, `the_tich`, `dien_tich_mat_cong`).

### 2. No fake Scene3D objects or hidden fallback math — **PASS**
- **Direct Code Verification:** Inspected `_run_curved_route` in `backend/app/ai/adapter3_simulation.py` (lines 2076–2860), `demos/demo7-invalid-geometry-safe-refusal.json`, `test_simulation_coverage_curved.py` (lines 368–584), and `oracle_eval.py` (lines 868–1397).
- **Findings:**
  - `_run_curved_route` compiles a real `SemanticProgram` (`program_id="adapter3_curved_simulation"`, lines 2577–2583), validates it with `validate_semantic_program(program)` (line 2584), executes it through `SemanticProgramInterpreter().execute(vr.spec)` (line 2591), projects state via `build_simulation_state(vr.spec, ket, None)` (line 2710), and builds the 3D scene via `build_scene3d(state)` (line 2712). All 10 positive corpus cases pass `validate_geometry_v2(res.scene3d)` (`eval-summary.json:14`).
  - On invalid or unsupported geometry (`demo7-invalid-geometry-safe-refusal.json`, `neg_02..neg_05`, and 6 parametrized refusal tests in `test_simulation_coverage_curved.py`), execution fails closed with `status: "REFUSED"`, `scene3d: null`, and explicit refusal codes (`CURVED_PLANE_DOES_NOT_CUT`, `CURVED_PLANE_TANGENT`, `CURVED_CONE_SECTION_PARABOLIC`, `CURVED_PRIMITIVE_BLOCKED_BY_KERNEL`, `AMBIGUOUS_REFERENCE`, `CURVED_SECTION_OUTSIDE_V1_CLOSURE`, `CURVED_RADIUS_OUTSIDE_DOMAIN`).

### 3. No second mathematical authority — **PASS**
- **Direct Code Verification:** Inspected `backend/app/ai/adapter3_simulation.py` (lines 1590–1625, 2137–2189, 2299–2305, 2332, 2469–2474, 2931–2934) and `backend/app/simulation/geometry/curved.py` (lines 158–287, 606–1095).
- **Findings:**
  - `_run_curved_route` delegates curved solid kind metadata (`co_truc`, `vai_dinh`, `danh_tu`) exclusively to `CV.KHOI_CONG[curved_kind]` (`adapter3_simulation.py:2137–2141, 2169–2173, 2300, 2332, 2469–2474`) without branching on `"ball"`, `"cylinder"`, or `"cone"` strings outside `curved.py` and the renderer.
  - Curved plane intersections delegate to `CV.intersect_plane_curved` and `CV.intersect_plane_curved_ellipse` via IR statements (`adapter3_simulation.py:2210, 2237, 2439–2441`).
  - Polyhedral volume certification in `adapter3_simulation.py` continues to delegate single-solid volume squared (`dung._the_tich2_khoi(k)` at line 2933) and outward half-space containment & shared boundary face verification (`dung._mat_ngoai_khoi(...)` at lines 1591–1592) to `backend/app/simulation/geometry_functions/engine.py`.

### 4. No silent approximation where exact verification is required — **PASS**
- **Direct Code Verification:** Inspected `backend/app/simulation/geometry/curved.py` (lines 126–155, 291–548, 808–858), `backend/app/simulation/semantic_program/simulation_state.py` (lines 538–576), `frontend/src/simulations/domains/geometry/scene3d-view.tsx` (lines 1478–1531), and `frontend/src/simulations/domains/geometry/scene3d-model.ts` (lines 842–865).
- **Findings:**
  - Exact rational squared values ($R^2, h^2, l^2 = R^2+h^2, d^2, r^2 = R^2-d^2, a^2, b^2$) are stored as `Fraction` in `CurvedSolid`, `Circle3`, and `Ellipse3` and serialized as exact fraction strings (`radius_sq`, `height_sq`, `semi_major_sq`, `semi_minor_sq`).
  - Exact symbolic $\pi$ and radical values (`Radical(he, can, mu)`) are preserved in `final_memory`, `answers`, `answer_exact`, and `math_goals` certificates.
  - Three.js display meshes (`SphereGeometry`, `CylinderGeometry`, `ConeGeometry` in `scene3d-view.tsx:1505–1511`) and bounding-box extents (`diemHuuHan` in `scene3d-model.ts:842–865`) take square roots only at the client presentation layer, with no path back into mathematical checks.

### 5. Browser visual receipt matches actual code and demo fixtures — **PASS**
- **Direct Artifact & Code Verification:** Inspected `visual-acceptance-receipt.json`, `eval-summary.json`, `corpus-dev.json`, `demos/demo1..demo7*.json`, `screenshots/` (`49` PNG files), `frontend/src/simulations/domains/geometry/simulation-coverage-fixes.test.tsx`, and `backend/tests/geometry/test_simulation_coverage_fixes.py`.
- **Findings:**
  - `scene3d.py` (lines 504, 869–871) maps `construct_curved_solid` to `CREATE` and `circle3`/`ellipse3` events to `action="CREATE"`, `semantic_kind="GEOMETRY_CONSTRUCTION"`, with clean Vietnamese learner narration (`Dựng ...`).
  - `simulation_state.py` (lines 427–429) classifies `curved_solid`, `circle3`, and `ellipse3` dependency edges as `"structural"`.
  - `interaction-state.ts` (lines 336, 342–345, 392) classifies `segment3`, `circle3`, `ellipse3`, and `curved_solid` into proper Vietnamese tree categories (`Cạnh`, `Thiết diện`, `Khối`) with zero `"Khác"` fallback nodes.
  - `visual-acceptance-receipt.json` confirms across all 9 demos (`8` served + `1` refused): `totalConsoleErrors = 0`, `totalPageErrors = 0`, `inkPixels > 519,000` on all 8 positive scenes, `ownPixels > 0` for every primary object in `ownPixelMap`, `orbitDiffPixels > 0`, `zoomDiffPixels > 0`, `panDiffPixels > 0`, `selectionDiffPixels > 0`, `step0DiffPixels > 0`, `labelCollisions = 0`, `labelsNotCollapsed = true`, and `depViolations = []`.
  - `eval-summary.json` and `corpus-dev.json` (`evaluation_scope: "DEVELOPMENT_EVALUATION_NOT_BLIND"`) confirm `15` cases (`10/10` positive served, `5/5` negative refused, `0` wrong serves, `all_passed = true`, `10/10` across all 8 simulation criteria).

### 6. All earlier tests and governance invariants remain intact — **PASS**
- **Direct Code & Metadata Verification:** Inspected `backend/app/simulation/geometry_compiler/routing.py`, `backend/app/ai/pipeline.py`, `backend/app/main.py`, `docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json`, `docs/evaluation/geometry/runs/simulation-coverage-visual-validation/candidate_divergence.json`, `run.json`, and `docs/CURRENT_STATE.md`.
- **Findings:**
  - `DEFAULT_MODE = LLM_ONLY` (`routing.py:30` `CHE_DO_MAC_DINH = "LLM_ONLY"`)
  - `RESPONSE_CONTRACT = flat` (`pipeline.py:52, 92`)
  - `HYBRID_PRODUCT_ENABLEMENT = NO-GO` (`run.json:35`, `CURRENT_STATE.md:7`)
  - `ALLOW_LIVE_AI = 0` / `live_provider_calls = 0` (`candidate_divergence.json:18`, `run.json:38`)
  - `CACHE_VERSION = 127` (`main.py:824`, `EVALUATION_CANDIDATE.json:9`, `candidate_divergence.json:13–14`)
  - `EVALUATION_CANDIDATE.json` matches `product_commit_sha = "3298b901d2246650535aa4028845ddc2a44892c4"`, `so_file = 114`, and `tree_hash = "4d11a91790422b9508bc90921f4352687a4b8616c0f855886e76649d3a7dcf68"`.

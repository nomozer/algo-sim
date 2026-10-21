# Candidate Measured-Hash Scope & Browser Inventory Reconciliation (`simulation-demo6b-renderer-fix`)

- **Run ID**: `simulation-demo6b-renderer-fix`
- **Wave ID**: `simulation-demo6b-renderer-fix-w01`
- **Authorization**: `GO_MAIN_SIMULATION_RENDERER_FIX_CONDITIONAL`
- **Machine Receipt**: [`candidate-and-browser-inventory-reconciliation.json`](candidate-and-browser-inventory-reconciliation.json)

---

## 1. P1 — Measured-System Hash Coverage & Frontend Source Identity

### Inspection of `backend/scripts/freeze_evaluation_candidate.py` & `EVALUATION_CANDIDATE.json`
- **`MEASURED_SYSTEM_PATHS` (lines 52–57)**:
  ```python
  MEASURED_SYSTEM_PATHS = (
      "backend/app",
      "frontend/src/simulations/domains/semantic",
      "frontend/src/simulations/domains/semantic/semantic_program.schema.json",
  )
  ```
- **Actual Composition of the `114` Measured Entries (`4d11a91790422b9508bc90921f4352687a4b8616c0f855886e76649d3a7dcf68`)**:
  - `108` Python source files under `backend/app/`.
  - `6` entries from `frontend/src/simulations/domains/semantic/` (`index.ts`, `model.ts`, `semantic.test.ts`, `semantic_program.schema.json` [included once via directory walk and once via explicit path entry], and `ui.tsx`).
- **Answers to P1 Questions (A–D)**:
  - **A. Are frontend geometry renderer files intentionally excluded from `measured_system.tree_hash`?**
    **Yes.** `frontend/src/simulations/domains/geometry/*` (including `scene3d-view.tsx`) is intentionally outside `MEASURED_SYSTEM_PATHS`.
  - **B. Does `product_commit_sha` fully identify the changed frontend sources?**
    **Yes.** `freeze_evaluation_candidate.py` (lines 61–84) defines `PRODUCT_PATHS = ("backend/app", "frontend/src")` and `PRODUCT_COMMIT_RULE = "product-paths-excluding-test-only/1"` (`TEST_ONLY_GLOBS` excludes `frontend/src/**/*.test.ts`, `frontend/src/**/*.test.tsx`, `*fixture*.json`, `test-setup.ts`, `test-source.ts`). As explicitly documented at lines 61–62: *"commit cuối chạm mã sản phẩm, KỂ CẢ renderer ngoài `MEASURED_SYSTEM_PATHS`: sửa renderer không đổi `tree_hash` nhưng phải làm `--verify` đỏ (sự cố W12)."*
  - **C. Does governance require the freeze to cover frontend changes?**
    **Yes, via `product_commit_sha` in `EVALUATION_CANDIDATE.json` (`1ca20f4f51457f3457802bca042af76accd13698`) and `candidate_divergence.json`.** Before refreezing at `d2e6037b12580eed1503e911999d4bf981f2c0e4`, `freeze_evaluation_candidate.py --verify` failed on `product_commit_sha` (`3298b901...` vs `1ca20f4f...`).
  - **D. Scientific Labeling**:
    `measured_system.tree_hash` (`4d11a91790422b9508bc90921f4352687a4b8616c0f855886e76649d3a7dcf68`, `114` entries) covers `backend/app` (`108` files) + `frontend/src/simulations/domains/semantic` (`6` entries) only; it is **neither** a full-system hash **nor** a strictly backend-only hash. Frontend 3D renderer identity is governed by `product_commit_sha = 1ca20f4f51457f3457802bca042af76accd13698` and the exact Git blob identities below.

### Exact Git Blob Identities & SHA256 Digests of Changed Frontend Files (`3298b901` $\to$ `1ca20f4f` / `d2e6037b`)

| Path | Role | Commit | Git Blob OID | Blob Bytes (LF) | Git Blob SHA256 (LF) | Worktree Bytes (CRLF) | Worktree Raw SHA256 |
|---|---|---|---|---:|---|---:|---|
| `frontend/src/simulations/domains/geometry/scene3d-view.tsx` | Product renderer (`in_product_paths = true`) | `3298b901` (Old) | `c1ae8e0426276f249356b95c8a182f59229e7605` | `141,643` | `41a46ad97e2a5b597b9acafabb8855eab754123bc24f205eacf7b71d92c3940b` | `144,513` | `—` |
| `frontend/src/simulations/domains/geometry/scene3d-view.tsx` | Product renderer (`in_product_paths = true`) | `1ca20f4f` / `d2e6037b` (New & T3) | `382ca0ef525eb21dbe9789962a6faf3841642dba` | `142,638` | `ccb09f86ce4910b0aad25797be8cf99d004d19d494cb3a475a9fcd4ce5c6e63e` | `145,539` | `9893e6df94ea44f52ac0fec475240b6e3c19b399a384b8f0de8421a0153cee92` |
| `frontend/src/simulations/domains/geometry/simulation-coverage-fixes.test.tsx` | Unit regression test (`TEST_ONLY_GLOBS`) | `3298b901` (Old) | `0ae3646758dae7755b327f92432ac5ea8bd90f1d` | `11,056` | `fecc37028c542c7eeccb92fdbef4bb7b0b61ead5999dc756eded4e8faeacd853` | `11,056` | `fecc37028c542c7eeccb92fdbef4bb7b0b61ead5999dc756eded4e8faeacd853` |
| `frontend/src/simulations/domains/geometry/simulation-coverage-fixes.test.tsx` | Unit regression test (`TEST_ONLY_GLOBS`) | `1ca20f4f` / `d2e6037b` (New & T3) | `7948f458f9682ddae8bf81810bfbefdc72cd3eed` | `16,478` | `308424c44a2c9edb06b3e425435a0df49592043a3836bf2db6ca11cd2856121a` | `16,478` | `308424c44a2c9edb06b3e425435a0df49592043a3836bf2db6ca11cd2856121a` |

- **Proof of Execution in Authoritative Full T3 (`d2e6037b12580eed1503e911999d4bf981f2c0e4`)**:
  - `t3/execution.json` verified `HEAD == d2e6037b12580eed1503e911999d4bf981f2c0e4` and clean working tree before and after (`snapshot_dirty_after: []`).
  - At `d2e6037b`, `git rev-parse d2e6037b:frontend/src/simulations/domains/geometry/scene3d-view.tsx` is `382ca0ef525eb21dbe9789962a6faf3841642dba` and `git rev-parse d2e6037b:frontend/src/simulations/domains/geometry/simulation-coverage-fixes.test.tsx` is `7948f458f9682ddae8bf81810bfbefdc72cd3eed`.
  - `t3/stdout.log` (line 209) records `✓ src/simulations/domains/geometry/simulation-coverage-fixes.test.tsx (6 tests) 147ms` (up from `4 tests` at `3298b901`) and `1156 passed` across `72` test files (up from `1154 passed` at `3298b901`), followed by `tsc -b && vite build` (`PASS`).

---

## 2. P2 — Reconciliation of Old and New Browser Inventories

### Cause of Apparent Scenario Difference in `report.md`
- **Classification**: `PROSE_TABLE_TRANSCRIPTION_ERROR_IN_REPORT_MD_SECTION_3_ONLY`
- **Finding**:
  1. The actual browser input file [`browser/input-scenes.json`](browser/input-scenes.json) has raw SHA256 `c3203838fc0eefb916d98212674f89e07d1e37706e6dce9daf8779e0cd7466de` (`593,526` bytes), which is **100% byte-for-byte identical** to [`docs/evaluation/geometry/runs/simulation-evidence-repair/browser/input-scenes.json`](../simulation-evidence-repair/browser/input-scenes.json) and contains the **exact 9 original demo scenarios** from [`docs/evaluation/geometry/runs/simulation-coverage-visual-validation/demos/demo1..demo7*.json`](../simulation-coverage-visual-validation/demos/).
  2. In [`browser/visual-receipt.json`](browser/visual-receipt.json) (`0cb8c28e...`) and [`browser/screenshots/`](browser/screenshots/), all 9 scenes executed are those exact 9 original scenarios (`demo1-pyramid-derived-section`, `demo2-unnamed-section-intersections`, `demo3-multi-solid-shared-geometry`, `demo4-step-by-step-construction`, `demo5-selection-and-highlighting`, `demo6a-curved-cylinder-sections`, `demo6b-curved-cone-frustum-cut`, `demo6c-curved-sphere-plane-cut`, `demo7-invalid-geometry-safe-refusal`).
  3. Only the prose Markdown summary table in the earlier draft of `report.md` Section 3 had miswritten demo IDs/object names from memory (`demo1-regular-pyramid-named-section`, `tru_T`, `non_S`, etc.). `report.md` Section 3 has been updated to match the exact machine receipts.

### Separate Provenance: Original Unaltered Runner (`browser-original-runner/`) vs Extended Axial-Section Runner (`browser/`)
To preserve complete, separate provenance on the new renderer (`1ca20f4f` / `d2e6037b`), both runners were executed in the clean detached worktree `verify-simulation-demo6b-renderer-fix` against the exact original 9-demo input `browser/input-scenes.json` (`c3203838fc0eefb916d98212674f89e07d1e37706e6dce9daf8779e0cd7466de`):
1. **Original Unaltered Runner ([`browser-original-runner/`](browser-original-runner/))**:
   - Script: `docs/evaluation/geometry/runs/simulation-coverage-visual-validation/run_browser_audit.mjs` (SHA256 `274ab853cd74fe12b35bd9f982a79c92c5bfcaa7bd6996375209274bd4af486d`)
   - Environment ([`browser-original-runner/environment.json`](browser-original-runner/environment.json)): Headless Chromium `151.0.7922.34` (`Playwright 1.62.1`, `Node v24.13.0`), `ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device (Subzero) (0x0000C0DE)), SwiftShader driver)`, viewport `1280x860`
   - Raw streams ([`browser-original-runner/execution.json`](browser-original-runner/execution.json)): `stdout.log` `226` bytes (`434eec4afa560e1de9f5985269b0a0458dd08bfd97dff5be3075e88cada0cd40`), `stderr.log` `0` bytes (`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`), exit code `0`
   - Receipt ([`browser-original-runner/visual-receipt.json`](browser-original-runner/visual-receipt.json), SHA256 `74d2ad48f0b1cfc0b5af923435c7a916f0f42a5eca9eb756cfcf0e6f5882d549`) & Validation ([`browser-original-runner/validation.json`](browser-original-runner/validation.json)): `8` positive served, `1` negative refused, `49` PNG screenshots, `0` console errors, `0` page errors, `all_primary_objects_own_pixels_positive = true`, `all_camera_resets_exact_zero_diff = true`.
2. **Extended Axial-Section Regression Runner ([`browser/`](browser/))**:
   - Script: `docs/evaluation/geometry/runs/simulation-demo6b-renderer-fix/run_browser_regression_audit.mjs` (adds `axialSectionChecks` for `orbitOwnPixels`, `selectAxialDiffPixels`, `isolateAxialInkPixels`, `isolateAxialSectionHuePixels`, `isolateAxialDiffPixels`, and 4 additional `_selected_td_sec_axial.png` / `_isolated_td_sec_axial.png` screenshots)
   - Raw streams ([`browser/execution.json`](browser/execution.json)): `stdout.log` `210` bytes (`8461c3762fd0db7457799b6929c804e26c5adbdd6d0a52fefad5d920a3d75184`), `stderr.log` `0` bytes (`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`), exit code `0`
   - Receipt ([`browser/visual-receipt.json`](browser/visual-receipt.json), SHA256 `0cb8c28e396b3590cf5f1a9c97cb3b220479b57a8c5a787f6515bb7cc61cec9a`) & Validation ([`browser/validation.json`](browser/validation.json)): `8` positive served, `1` negative refused, `53` PNG screenshots, `0` console errors, `0` page errors.

### Side-by-Side Comparison Across All 9 Authoritative Original Demos

| # | Demo ID & Category | Demo File Git Blob SHA256 (`5f4ee58c`) | Original Campaign (`3298b901`) `ownPixelMap` | Repair Repro (`3298b901`) `ownPixelMap` / Reset Diff | New Renderer Original Runner (`1ca20f4f`) `ownPixelMap` / Reset Diff | New Renderer Extended Runner (`1ca20f4f`) `ownPixelMap` & Axial Checks |
|---:|---|---|---|---|---|---|
| 1 | `demo1-pyramid-derived-section`<br/>*(Pyramid + Derived Plane Section)* | `47c4dfa7575beb60...` | `khoi_S_ABCD`: `52,372`<br/>`khoi_S_MI1I2I3`: `9,438` | `khoi_S_ABCD`: `52,372`<br/>`khoi_S_MI1I2I3`: `9,438`<br/>resetDiff: `0` | `khoi_S_ABCD`: `52,372`<br/>`khoi_S_MI1I2I3`: `9,438`<br/>resetDiff: `0` | `khoi_S_ABCD`: `52,372`<br/>`khoi_S_MI1I2I3`: `9,438`<br/>resetDiff: `0` |
| 2 | `demo2-unnamed-section-intersections`<br/>*(Unnamed Section Intersections I1..I3)* | `052e37205a6c4c85...` | `khoi_S_ABCD`: `43,147`<br/>`khoi_S_MI1I2I3`: `3,970` | `khoi_S_ABCD`: `43,147`<br/>`khoi_S_MI1I2I3`: `3,970`<br/>resetDiff: `0` | `khoi_S_ABCD`: `43,147`<br/>`khoi_S_MI1I2I3`: `3,970`<br/>resetDiff: `0` | `khoi_S_ABCD`: `43,147`<br/>`khoi_S_MI1I2I3`: `3,970`<br/>resetDiff: `0` |
| 3 | `demo3-multi-solid-shared-geometry`<br/>*(Multi-Solid Shared Geometry)* | `7c453812de25f42a...` | `khoi_D1_ABC`: `544`<br/>`khoi_S_ABC`: `16,135`<br/>`day_ABC`: `423` | `khoi_D1_ABC`: `544`<br/>`khoi_S_ABC`: `16,135`<br/>`day_ABC`: `423`<br/>resetDiff: `0` | `khoi_D1_ABC`: `544`<br/>`khoi_S_ABC`: `16,135`<br/>`day_ABC`: `423`<br/>resetDiff: `0` | `khoi_D1_ABC`: `544`<br/>`khoi_S_ABC`: `16,135`<br/>`day_ABC`: `423`<br/>resetDiff: `0` |
| 4 | `demo4-step-by-step-construction`<br/>*(Step-by-Step Construction Timeline)* | `8615ae838be11693...` | `khoi_S_ABC`: `60,520` | `khoi_S_ABC`: `60,520`<br/>resetDiff: `0` | `khoi_S_ABC`: `60,520`<br/>resetDiff: `0` | `khoi_S_ABC`: `60,520`<br/>resetDiff: `0` |
| 5 | `demo5-selection-and-highlighting`<br/>*(Selection & Highlighting)* | `dc8c780abd19325c...` | `khoi_S_ABCD`: `3,831`<br/>`khoi_T_ABCD`: `18,339`<br/>`day_ABCD`: `652` | `khoi_S_ABCD`: `3,831`<br/>`khoi_T_ABCD`: `18,339`<br/>`day_ABCD`: `652`<br/>resetDiff: `0` | `khoi_S_ABCD`: `3,831`<br/>`khoi_T_ABCD`: `18,339`<br/>`day_ABCD`: `652`<br/>resetDiff: `0` | `khoi_S_ABCD`: `3,831`<br/>`khoi_T_ABCD`: `18,339`<br/>`day_ABCD`: `652`<br/>resetDiff: `0` |
| 6 | `demo6a-curved-cylinder-sections`<br/>*(Curved Cylinder + Parallel Circle & Axial Section)* | `89bded678b1fb758...` | `khoi_cyl`: `36,691`<br/>`duong_tron_day_cyl`: `31,106`<br/>`duong_tron_day_tren_cyl`: `31,813`<br/>`td_sec_parallel`: `31,333`<br/>`td_sec_axial`: `358` | `khoi_cyl`: `36,691`<br/>`duong_tron_day_cyl`: `31,106`<br/>`duong_tron_day_tren_cyl`: `31,813`<br/>`td_sec_parallel`: `31,333`<br/>`td_sec_axial`: `358`<br/>resetDiff: `0` | `khoi_cyl`: `36,685`<br/>`duong_tron_day_cyl`: `27,322`<br/>`duong_tron_day_tren_cyl`: `27,674`<br/>`td_sec_parallel`: `26,013`<br/>**`td_sec_axial`: `7,468`**<br/>resetDiff: `0` | `khoi_cyl`: `36,685`<br/>`duong_tron_day_cyl`: `27,322`<br/>`duong_tron_day_tren_cyl`: `27,674`<br/>`td_sec_parallel`: `26,098`<br/>**`td_sec_axial`: `7,468`** (orbit `4,981`, selectDiff `39,801`, isolateInk `520,548`, resetDiff `0`) |
| 7 | `demo6b-curved-cone-frustum-cut`<br/>*(Curved Cone + Parallel Cut + Cone Frustum)* | `fda86ad1799e2b8a...` | `khoi_cone_main`: `19,195`<br/>`duong_tron_day_cone_main`: `32,620`<br/>`td_sec_cut`: `4,017`<br/>`td_sec_axial`: `41`<br/>`khoi_cone_upper`: `4,711` | `khoi_cone_main`: `19,195`<br/>`duong_tron_day_cone_main`: `32,620`<br/>`td_sec_cut`: `4,017`<br/>**`td_sec_axial`: `0`**<br/>`khoi_cone_upper`: `4,711`<br/>**resetDiff: `239`** | `khoi_cone_main`: `19,181`<br/>`duong_tron_day_cone_main`: `31,979`<br/>`td_sec_cut`: `4,005`<br/>**`td_sec_axial`: `3,105`**<br/>`khoi_cone_upper`: `4,669`<br/>**resetDiff: `0`** | `khoi_cone_main`: `19,185`<br/>`duong_tron_day_cone_main`: `31,960`<br/>`td_sec_cut`: `4,063`<br/>**`td_sec_axial`: `3,105`** (orbit `2,041`, selectDiff `20,557`, isolateInk `520,548`, **resetDiff `0`**)<br/>`khoi_cone_upper`: `4,669` |
| 8 | `demo6c-curved-sphere-plane-cut`<br/>*(Curved Sphere + Plane Cut Circle)* | `ea06b12896c62913...` | `khoi_sph`: `25,665`<br/>`td_sec_sph`: `29,346` | `khoi_sph`: `25,665`<br/>`td_sec_sph`: `29,346`<br/>resetDiff: `0` | `khoi_sph`: `25,665`<br/>`td_sec_sph`: `29,346`<br/>resetDiff: `0` | `khoi_sph`: `25,665`<br/>`td_sec_sph`: `29,346`<br/>resetDiff: `0` |
| 9 | `demo7-invalid-geometry-safe-refusal`<br/>*(Invalid Geometry Safe Refusal)* | `bb462747338c7e0a...` | `served: false`<br/>`CURVED_PLANE_DOES_NOT_CUT` | `served: false`<br/>`CURVED_PLANE_DOES_NOT_CUT` | `served: false`<br/>`CURVED_PLANE_DOES_NOT_CUT` | `served: false`<br/>`CURVED_PLANE_DOES_NOT_CUT` |

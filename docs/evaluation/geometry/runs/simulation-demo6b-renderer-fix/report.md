# Final Simulation Renderer Repair & Raw-Log Metadata Reconciliation Report (`simulation-demo6b-renderer-fix`)

- **Run ID**: `simulation-demo6b-renderer-fix`
- **Wave ID**: `simulation-demo6b-renderer-fix-w01`
- **Owner Authorization**: `GO_SIMULATION_DEMO6B_RENDERER_FIX_LOCAL_ONLY` / `GO_MAIN_SIMULATION_RENDERER_FIX_CONDITIONAL`
- **Branch**: `research/simulation-demo6b-renderer-fix` (from `research/simulation-evidence-repair` @ `609cb877d9e0177e8408f31c7d3cc0c9cd5f89fc`)
- **Baseline `main` / `origin/main`**: `bd8d6a9dc3acc9a4204b616379001270bb6d39f9`
- **Original Campaign Commit**: `d86c72031d8fc85cd4eef62d9379cd1690ba1417`
- **Original Product Commit / Candidate**: `3298b901d2246650535aa4028845ddc2a44892c4` / `5f4ee58c48011e9e5d38d3209f7c97250032a976`
- **New Product Commit (`NEW_PRODUCT_COMMIT`)**: `1ca20f4f51457f3457802bca042af76accd13698`
- **New Frozen Candidate (`NEW_RENDERER_FIXED_CANDIDATE`)**: `d2e6037b12580eed1503e911999d4bf981f2c0e4`
- **Measured System Subset (`MEASURED_SYSTEM_PATHS`)**: `4d11a91790422b9508bc90921f4352687a4b8616c0f855886e76649d3a7dcf68` (`114` entries: `108` `backend/app` files + `6` `frontend/src/simulations/domains/semantic` entries; `frontend/src/simulations/domains/geometry/*` is outside `MEASURED_SYSTEM_PATHS` and locked by `product_commit_sha = 1ca20f4f51457f3457802bca042af76accd13698`)
- **Final Verdict**: `SIMULATION_RENDERER_FIX_READY_FOR_GO_MAIN_REVIEW`

---

## 1. P0 — Raw-Log Byte-Size & SHA256 Reconciliation

Full details and machine receipts: [`RAW_LOG_SIZE_RECONCILIATION.md`](RAW_LOG_SIZE_RECONCILIATION.md) and [`raw-log-size-reconciliation.json`](raw-log-size-reconciliation.json).

- **Cause Classification**: `PROSE_REPORTING_METADATA_ERROR_ONLY`
- **4-Way Binary Identity of the 4 Original Full T3 Logs (`raw/original-t3/*`)**:
  Direct binary `Path.read_bytes()` and `git show` inspection proves exact byte-length and SHA256 equality across all 4 locations (`original_runtime_source_worktree`, `corrective_archive_worktree`, `git_blob_609cb877`, and `clean_checkout_archive`):

| File | Original Runtime Bytes | Corrective Archive Bytes | Git Blob Bytes (`609cb877`) | Clean Checkout Bytes | Exact Raw SHA256 | Historical LF Blob (`d86c7203`) | `simulation-evidence-repair/report.md` Prose Table |
|---|---:|---:|---:|---:|---|---|---:|
| `attempt1-fail.stdout.log` | `31,647` | `31,647` | `31,647` | `31,647` | `e2074c0897550bda185a6f55ea4113e3a8324263fc7a0cf1e2743228207c03f6` | `31,390` B (`2620186c...`) | `17,843` (prose error) |
| `attempt1-fail.stderr.log` | `121,261` | `121,261` | `121,261` | `121,261` | `bfd6d2ca0bf9c3f05bf6010dd12a9c949656172434d9579ba24fdc3701be54a5` | `121,261` B (`bfd6d2ca...`) | `1,303` (prose error) |
| `attempt2-pass.stdout.log` | `28,606` | `28,606` | `28,606` | `28,606` | `013f2e784e9fa828a055320468afe7137f080d2447615aec3c3d3970a2138e06` | `28,399` B (`8274c4c2...`) | `18,243` (prose error) |
| `attempt2-pass.stderr.log` | `121,261` | `121,261` | `121,261` | `121,261` | `47de58275e7e069019a5f60938442317568919cd55fcaf2c0cd567fee13589c0` | `121,261` B (`47de5827...`) | `332` (prose error) |

- **3-Way Binary Identity of `simulation-evidence-repair` New T3 Logs (`t3/*`)**:
  - `t3/stdout.log`: `18,257` bytes across worktree, Git blob at `609cb877`, and clean checkout (`d2446b46ba4aba9fae7203cc6be401e820248087430b63b0d7cbe358af0edd33`).
  - `t3/stderr.log`: `332` bytes across worktree, Git blob at `609cb877`, and clean checkout (`ccb6bf354a0674eeb1e49df9a880a000b75240079fdb849282bb899d81eeb58c`).
- **Explanation**: Both machine receipts (`simulation-evidence-reconciliation/evidence.json` and `simulation-evidence-repair/original-raw-manifest.json` + `archive-integrity.json`) agree on `31,647`, `121,261`, `28,606`, `121,261` bytes. Only the prose summary table in `simulation-evidence-repair/report.md` mistakenly paired the new T3 run's byte lengths (`332` B stderr, `~18.2` KB stdout) with the original T3 logs' SHA256 digests. All historical files remain untouched; this wave registers an additive `CORRECTED_BY` link in `docs/EVIDENCE_INDEX.md`.

---

## 2. P2 & P3 — Root Cause, Scoped Renderer Fix & Frontend Blob Identities

Full measured-hash scope and frontend identity receipt: [`CANDIDATE_AND_BROWSER_INVENTORY_RECONCILIATION.md`](CANDIDATE_AND_BROWSER_INVENTORY_RECONCILIATION.md) and [`candidate-and-browser-inventory-reconciliation.json`](candidate-and-browser-inventory-reconciliation.json).

### Root Cause
1. **Interior Fill Occlusion**: In `frontend/src/simulations/domains/geometry/scene3d-view.tsx`, `curved_solid` objects (`khoi_cone_main` in `demo6b-curved-cone-frustum-cut`, `khoi_cyl` in `demo6a-curved-cylinder-sections`) render an opaque depth-only prepass mesh `lopChieuSau` (`colorWrite: false, depthWrite: true, side: THREE.FrontSide`) at `renderOrder = THU_TU_LOT_CHIEU_SAU = 5` so back-facing curves/lines test `GreaterDepth` and dash properly. However, in `buildObject3D` (`o.render === "polygon"`), `thietDien` was defined as `o.type === "section"`, whereas axial section polygons emitted by `SemanticProgramInterpreter` (`construct_polygon`) have `o.type === "polygon3"` and `o.surface_role === "AUXILIARY_SURFACE"`. Consequently, `polygon_fill:td_sec_axial` rendered at `renderOrder = 0` with `depthTest: true` and `depthWrite: false`, and its interior fill was overwritten/occluded by the cone's front-surface depth prepass (`renderOrder = 5`).
2. **Boundary Line Pass inside Curved Solids**: In `updateCanonicalEdgeVisibility`, `occluders` only collects polyhedral `solid` meshes (`c.name.startsWith("solid:")`), so in curved-solid scenes `occluders.length === 0` and `updateNonCanonicalVisibility` returns early without building CPU-classified `section_border` spans. Meanwhile, `buildObject3D` only created a single `LessEqualDepth` solid border line (`polygon_border:${o.id}`) without a `GreaterDepth` dashed pass for segments behind the curved solid's front surface.
3. **Camera Reset Render Lag**: `vuaKhungRef.current` updated `cam` and `dieuKhien` via `datKhungNhin(cam, dieuKhien, kn)` without synchronously invoking `veRef.current?.()` and `chieuNhan()`, leaving a 1-frame stale render/label projection (`resetDiffFromDefault = 239`).

### Scoped Role-Based Fix (`1ca20f4f51457f3457802bca042af76accd13698`)
In `frontend/src/simulations/domains/geometry/scene3d-view.tsx`:
- Defined `daGiacPhu = o.type === "polygon3" && o.surface_role === "AUXILIARY_SURFACE" && !(o.formation_roles ?? []).includes("CONSTRUCT_BASE")` and `toXuyenKhoi = thietDien || daGiacPhu` (excluding `CONSTRUCT_BASE` so shared polyhedral base polygons such as `day_ABC` in `demo3` and `day_ABCD` in `demo5` retain `depthTest: true` and `renderOrder: 0`).
- Set interior fill mesh for `toXuyenKhoi` to `renderOrder = THU_TU_TO_THIET_DIEN` (`7`), `...LECH_THIET_DIEN`, `depthTest: false`, `depthWrite: false`, and opacity `noiBat ? 0.42 : 0.28` for `daGiacPhu`.
- Emitted two GPU depth passes for `ownsBoundary` (`polygon_border:${o.id}:thay` with `LessEqualDepth` solid + `polygonOffset`, and `polygon_border:${o.id}:khuat` with `GreaterDepth` dashed + `computeLineDistances()`), both tagged `userData.nonCanonicalBorderLine = true` so polyhedral scenes (`occluders.length > 0`) still replace them with CPU-classified `section_border` spans while curved-solid scenes (`occluders.length === 0`) retain GPU two-pass visibility against `lopChieuSau`.
- Called `veRef.current?.(); chieuNhan();` synchronously at the end of `vuaKhungRef.current`.

### Measured-Hash Coverage & Changed Frontend File Identities
- `MEASURED_SYSTEM_PATHS` in `backend/scripts/freeze_evaluation_candidate.py` (lines 52–57) intentionally covers `backend/app` (`108` files) + `frontend/src/simulations/domains/semantic` (`6` entries = `114` total entries, `tree_hash = 4d11a91790422b9508bc90921f4352687a4b8616c0f855886e76649d3a7dcf68`); it is neither a full-system hash nor a strictly backend-only hash.
- `frontend/src/simulations/domains/geometry/*` is locked by `product_commit_sha = 1ca20f4f51457f3457802bca042af76accd13698` under `PRODUCT_PATHS = ("backend/app", "frontend/src")` and `PRODUCT_COMMIT_RULE = "product-paths-excluding-test-only/1"`:
  - `frontend/src/simulations/domains/geometry/scene3d-view.tsx`: Git blob `c1ae8e0426276f249356b95c8a182f59229e7605` (`141,643` LF B, SHA256 `41a46ad97e2a5b597b9acafabb8855eab754123bc24f205eacf7b71d92c3940b`) at `3298b901` $\to$ Git blob `382ca0ef525eb21dbe9789962a6faf3841642dba` (`142,638` LF B, SHA256 `ccb09f86ce4910b0aad25797be8cf99d004d19d494cb3a475a9fcd4ce5c6e63e`) at `1ca20f4f` and Full T3 target `d2e6037b`.
  - `frontend/src/simulations/domains/geometry/simulation-coverage-fixes.test.tsx`: Git blob `0ae3646758dae7755b327f92432ac5ea8bd90f1d` (`11,056` LF B, SHA256 `fecc37028c542c7eeccb92fdbef4bb7b0b61ead5999dc756eded4e8faeacd853`) at `3298b901` $\to$ Git blob `7948f458f9682ddae8bf81810bfbefdc72cd3eed` (`16,478` LF B, SHA256 `308424c44a2c9edb06b3e425435a0df49592043a3836bf2db6ca11cd2856121a`) at `1ca20f4f` and Full T3 target `d2e6037b`.

---

## 3. P4 — Unit & Real-Browser WebGL Regression Verification (Original & Extended Runners)

Receipts:
- Extended axial-section runner (`53` PNGs): [`browser/invocation.json`](browser/invocation.json), [`browser/execution.json`](browser/execution.json), [`browser/validation.json`](browser/validation.json), [`browser/visual-receipt.json`](browser/visual-receipt.json), [`browser/screenshots/`](browser/screenshots/).
- Original unaltered runner (`49` PNGs): [`browser-original-runner/invocation.json`](browser-original-runner/invocation.json), [`browser-original-runner/environment.json`](browser-original-runner/environment.json), [`browser-original-runner/execution.json`](browser-original-runner/execution.json), [`browser-original-runner/validation.json`](browser-original-runner/validation.json), [`browser-original-runner/visual-receipt.json`](browser-original-runner/visual-receipt.json), [`browser-original-runner/screenshots/`](browser-original-runner/screenshots/).
- Both runners executed the exact 9 original demo scenarios in [`browser/input-scenes.json`](browser/input-scenes.json) (SHA256 `c3203838fc0eefb916d98212674f89e07d1e37706e6dce9daf8779e0cd7466de`, byte-identical to `simulation-evidence-repair/browser/input-scenes.json` and `simulation-coverage-visual-validation/demos/demo1..demo7*.json`).

### `demo6b-curved-cone-frustum-cut` Before vs After (`td_sec_axial`)

| Metric | Before Fix (`simulation-evidence-repair`) | After Fix — Original Runner (`browser-original-runner/`) | After Fix — Extended Runner (`browser/`) | Status |
|---|---:|---:|---:|---|
| `td_sec_axial` `defaultOwnPixels` | `0` (historical `41`) | `3,105` | `3,105` | **PASS (`> 0`)** |
| `td_sec_axial` `orbitOwnPixels` | `0` | `—` | `2,041` | **PASS (`> 0`)** |
| `td_sec_axial` `selectAxialDiffPixels` | `—` | `—` | `20,557` | **PASS (`> 0`)** |
| `td_sec_axial` `isolateAxialInkPixels` | `—` | `—` | `520,548` (`546` section-hue px) | **PASS (`> 0`)** |
| `td_sec_axial` `isolateAxialDiffPixels` | `—` | `—` | `20,876` | **PASS (`> 0`)** |
| `khoi_cone_main` `defaultOwnPixels` | `19,195` | `19,181` | `19,185` | **PASS (`> 0`)** |
| `duong_tron_day_cone_main` `defaultOwnPixels` | `32,620` | `31,979` | `31,960` | **PASS (`> 0`)** |
| `td_sec_cut` / `khoi_cone_upper` `defaultOwnPixels` | `4,017` / `4,711` | `4,005` / `4,669` | `4,063` / `4,669` | **PASS (`> 0`)** |
| `cameraChecks.resetDiffFromDefault` | `239` | `0` | `0` | **PASS (`=== 0`)** |

### Full 9-Demo Authoritative Browser Regression Summary (`browser-original-runner/` `49` PNGs & `browser/` `53` PNGs, `0` Errors)

| Demo ID | Category | Served | Default Ink Pixels | Primary Object `ownPixelMap` (`browser/`) | Orbit / Zoom / Pan Diff (`browser/`) | Reset Diff | Selection / Explode / Step0 Diff (`browser/`) | Labels / Collisions | Console / Page Errors |
|---|---|---|---:|---|---|---|---|---|---|
| `demo1-pyramid-derived-section` | Pyramid + Derived Plane Section | Yes | `520,010` | `khoi_S_ABCD`: `52,372`, `khoi_S_MI1I2I3`: `9,438` | `45,633` / `22,298` / `57,402` | `0` | `14,020` / `53,270` / `53,065` | `6` / `0` | `0` |
| `demo2-unnamed-section-intersections` | Unnamed Section Intersections (`I1..I3`) | Yes | `519,978` | `khoi_S_ABCD`: `43,147`, `khoi_S_MI1I2I3`: `3,970` | `26,406` / `13,224` / `42,418` | `0` | `8,281` / `40,892` / `43,672` | `6` / `0` | `0` |
| `demo3-multi-solid-shared-geometry` | Multi-Solid Shared Geometry (Prism + Pyramid) | Yes | `519,237` | `khoi_D1_ABC`: `544`, `khoi_S_ABC`: `16,135`, `day_ABC`: `423` | `20,787` / `6,297` / `19,658` | `0` | `23,128` / `33,171` / `23,155` | `6` / `0` | `0` |
| `demo4-step-by-step-construction` | Step-by-Step Construction Timeline | Yes | `520,019` | `khoi_S_ABC`: `60,520` | `61,037` / `21,310` / `38,843` | `0` | `8,706` / `75,420` / `60,934` | `5` / `0` | `0` |
| `demo5-selection-and-highlighting` | Selection & Highlighting | Yes | `519,690` | `khoi_S_ABCD`: `3,831`, `khoi_T_ABCD`: `18,339`, `day_ABCD`: `652` | `36,483` / `17,445` / `59,917` | `0` | `30,842` / `38,012` / `32,810` | `7` / `0` | `0` |
| `demo6a-curved-cylinder-sections` | Curved Cylinder + Parallel Circle & Axial Section | Yes | `519,543` | `khoi_cyl`: `36,685`, `duong_tron_day_cyl`: `27,322`, `duong_tron_day_tren_cyl`: `27,674`, `td_sec_parallel`: `26,098` (`26,013` orig runner), `td_sec_axial`: `7,468` (orbit `4,981`) | `19,345` / `22,831` / `62,911` | `0` | `38,211` (axial `39,801`) / `14,609` / `38,644` | `4` / `0` | `0` |
| `demo6b-curved-cone-frustum-cut` | Curved Cone + Parallel Cut + Cone Frustum | Yes | `519,887` | `khoi_cone_main`: `19,185` (`19,181` orig runner), `duong_tron_day_cone_main`: `31,960` (`31,979` orig runner), `td_sec_cut`: `4,063` (`4,005` orig runner), `td_sec_axial`: `3,105` (orbit `2,041`), `khoi_cone_upper`: `4,669` | `14,520` / `12,319` / `40,203` | `0` | `20,296` (axial `20,557`) / `7,057` / `20,725` | `4` / `0` | `0` |
| `demo6c-curved-sphere-plane-cut` | Curved Sphere + Plane Cut Circle | Yes | `520,329` | `khoi_sph`: `25,665`, `td_sec_sph`: `29,346` | `3,031` / `10,944` / `41,139` | `0` | `25,111` / `0` / `25,214` | `1` / `0` | `0` |
| `demo7-invalid-geometry-safe-refusal` | Invalid Geometry Safe Refusal (Non-cutting Plane) | No (`REFUSED`) | `—` | Safe refusal (`CURVED_PLANE_DOES_NOT_CUT`, `scene3d: null`) | `—` | `—` | `—` | `—` | `0` |

---

## 4. P5, P6 & P7 — Candidate Governance, Independent Review & Authoritative Full T3

- **Historical Preservation**: `0` modified files across `simulation-coverage-visual-validation/`, `simulation-evidence-reconciliation/`, and `simulation-evidence-repair/`.
- **Candidate Freeze**: `EVALUATION_CANDIDATE.json` frozen at `NEW_RENDERER_FIXED_CANDIDATE = d2e6037b12580eed1503e911999d4bf981f2c0e4` (`NEW_PRODUCT_COMMIT = 1ca20f4f51457f3457802bca042af76accd13698`, `114` measured entries in `MEASURED_SYSTEM_PATHS`, SHA256 `4d11a91790422b9508bc90921f4352687a4b8616c0f855886e76649d3a7dcf68`); [`candidate_divergence.json`](candidate_divergence.json) records both `original_product_commit` (`3298b901...`) / `original_frozen_candidate` (`5f4ee58c...`) and `current_product_commit` (`1ca20f4f...`).
- **Independent Review**: [`independent-review.md`](independent-review.md) — **`INDEPENDENT_REVIEW_PASS`** (`0 BLOCKER, 0 IMPORTANT, 0 MINOR`).
- **Authoritative Full T3 (`t3/validation.json`)**: Executed in clean detached worktree `verify-simulation-demo6b-renderer-fix` at `d2e6037b12580eed1503e911999d4bf981f2c0e4` via binary-safe [`capture.py`](capture.py):
  - Verdict: **`FULL_PRODUCT_GATE_PASS`** (`527.6s`, exit code `0`, attempt `1/1`).
  - `pytest`: `11,439 passed, 1 skipped, 2 deselected, 9 xfailed` (`511.3s`).
  - `vitest`: `72` test files / `1,156 passed` (`8.7s`, including `6 tests` in `simulation-coverage-fixes.test.tsx`).
  - `tsc -b && vite build`: `PASS` (`6.4s`).
  - Thesis demo replay: `5/5 PASS`, `1/1` reduced chain (`0.7s`).
  - Demo crash surface: `6/6 PASS`, `0` escaped `500`s (`0.5s`).
  - Raw stream digests: `t3/stdout.log` (`28,349` bytes, SHA256 `0d252ca18f66b1d8927b3e322ccc8ee3609fa5524ab2a5a260dfed4f4958d53d`), `t3/stderr.log` (`127,372` bytes, SHA256 `71e892d5f24a39e2342a0d6cb4a91808607490bdfe64836ef4ef761a0d18b93b`).
  - Post-T3 freeze verification: `MATCH` (`t3/freeze/stdout.log`: `93` bytes, SHA256 `06f3c429768e8b03408400299290363b271fac389b56ec3e780dc7b1a92e9abf`; `t3/freeze/stderr.log`: `0` bytes, SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`).

---

## 5. Scope Boundaries & Governance Invariants

- Residual polyhedral/frustum mesh `E` remains `NOT_IMPLEMENTED` (no `DerivedSubSolidSpec` or `frustum_like` in `backend/app`); scalar residual volume certification is distinct from rendering a residual 3D solid mesh.
- Standalone `cone_frustum` remains `BLOCKED_BY_KERNEL`.
- Oblique cylinder/cone ellipse section coverage remains `BACKEND_ONLY` for browser validation.
- Offline prepared-input execution does not claim live natural-language product E2E.
- `DEFAULT_MODE = LLM_ONLY`, `RESPONSE_CONTRACT = flat`, `HYBRID_PRODUCT_ENABLEMENT = NO-GO`, `ALLOW_LIVE_AI = 0`, `CACHE_VERSION = 127` (`0` live provider calls).

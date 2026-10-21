# Final Simulation Renderer Repair & Raw-Log Metadata Reconciliation Report (`simulation-demo6b-renderer-fix`)

- **Run ID**: `simulation-demo6b-renderer-fix`
- **Wave ID**: `simulation-demo6b-renderer-fix-w01`
- **Owner Authorization**: `GO_SIMULATION_DEMO6B_RENDERER_FIX_LOCAL_ONLY`
- **Branch**: `research/simulation-demo6b-renderer-fix` (from `research/simulation-evidence-repair` @ `609cb877d9e0177e8408f31c7d3cc0c9cd5f89fc`)
- **Baseline `main` / `origin/main`**: `bd8d6a9dc3acc9a4204b616379001270bb6d39f9`
- **Original Campaign Commit**: `d86c72031d8fc85cd4eef62d9379cd1690ba1417`
- **Original Product Commit / Candidate**: `3298b901d2246650535aa4028845ddc2a44892c4` / `5f4ee58c48011e9e5d38d3209f7c97250032a976`
- **New Product Commit (`NEW_PRODUCT_COMMIT`)**: `1ca20f4f51457f3457802bca042af76accd13698`
- **New Frozen Candidate (`NEW_RENDERER_FIXED_CANDIDATE`)**: `d2e6037b12580eed1503e911999d4bf981f2c0e4`
- **Measured System SHA256**: `4d11a91790422b9508bc90921f4352687a4b8616c0f855886e76649d3a7dcf68` (`114` files)
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

## 2. P2 & P3 — Root Cause & Scoped Renderer Fix (`scene3d-view.tsx`)

### Root Cause
1. **Interior Fill Occlusion**: In `frontend/src/simulations/domains/geometry/scene3d-view.tsx`, `curved_solid` objects (`non_S` in `demo6b-curved-cone-frustum-cut`, `tru_T` in `demo6a-curved-cylinder-sections`) render an opaque depth-only prepass mesh `lopChieuSau` (`colorWrite: false, depthWrite: true, side: THREE.FrontSide`) at `renderOrder = THU_TU_LOT_CHIEU_SAU = 5` so back-facing curves/lines test `GreaterDepth` and dash properly. However, in `buildObject3D` (`o.render === "polygon"`), `thietDien` was defined as `o.type === "section"`, whereas axial section polygons emitted by `SemanticProgramInterpreter` (`construct_polygon`) have `o.type === "polygon3"` and `o.surface_role === "AUXILIARY_SURFACE"`. Consequently, `polygon_fill:td_sec_axial` rendered at `renderOrder = 0` with `depthTest: true` and `depthWrite: false`, and its interior fill was overwritten/occluded by the cone's front-surface depth prepass (`renderOrder = 5`).
2. **Boundary Line Pass inside Curved Solids**: In `updateCanonicalEdgeVisibility`, `occluders` only collects polyhedral `solid` meshes (`c.name.startsWith("solid:")`), so in curved-solid scenes `occluders.length === 0` and `updateNonCanonicalVisibility` returns early without building CPU-classified `section_border` spans. Meanwhile, `buildObject3D` only created a single `LessEqualDepth` solid border line (`polygon_border:${o.id}`) without a `GreaterDepth` dashed pass for segments behind the curved solid's front surface.
3. **Camera Reset Render Lag**: `vuaKhungRef.current` updated `cam` and `dieuKhien` via `datKhungNhin(cam, dieuKhien, kn)` without synchronously invoking `veRef.current?.()` and `chieuNhan()`, leaving a 1-frame stale render/label projection (`resetDiffFromDefault = 239`).

### Scoped Role-Based Fix (`1ca20f4f51457f3457802bca042af76accd13698`)
In `frontend/src/simulations/domains/geometry/scene3d-view.tsx`:
- Defined `daGiacPhu = o.type === "polygon3" && o.surface_role === "AUXILIARY_SURFACE" && !(o.formation_roles ?? []).includes("CONSTRUCT_BASE")` and `toXuyenKhoi = thietDien || daGiacPhu` (excluding `CONSTRUCT_BASE` so shared polyhedral base polygons such as `day_ABC` in `demo3` and `day_ABCD` in `demo5` retain `depthTest: true` and `renderOrder: 0`).
- Set interior fill mesh for `toXuyenKhoi` to `renderOrder = THU_TU_TO_THIET_DIEN` (`7`), `...LECH_THIET_DIEN`, `depthTest: false`, `depthWrite: false`, and opacity `noiBat ? 0.42 : 0.28` for `daGiacPhu`.
- Emitted two GPU depth passes for `ownsBoundary` (`polygon_border:${o.id}:thay` with `LessEqualDepth` solid + `polygonOffset`, and `polygon_border:${o.id}:khuat` with `GreaterDepth` dashed + `computeLineDistances()`), both tagged `userData.nonCanonicalBorderLine = true` so polyhedral scenes (`occluders.length > 0`) still replace them with CPU-classified `section_border` spans while curved-solid scenes (`occluders.length === 0`) retain GPU two-pass visibility against `lopChieuSau`.
- Called `veRef.current?.(); chieuNhan();` synchronously at the end of `vuaKhungRef.current`.

---

## 3. P4 — Unit & Real-Browser WebGL Regression Verification

Receipts: [`browser/invocation.json`](browser/invocation.json), [`browser/execution.json`](browser/execution.json), [`browser/validation.json`](browser/validation.json), [`browser/visual-receipt.json`](browser/visual-receipt.json), and [`browser/screenshots/`](browser/screenshots/).

### `demo6b-curved-cone-frustum-cut` Before vs After (`td_sec_axial`)

| Metric | Before Fix (`simulation-evidence-repair`) | After Fix (`simulation-demo6b-renderer-fix`) | Status |
|---|---:|---:|---|
| `td_sec_axial` `defaultOwnPixels` | `0` | `3,105` | **PASS (`> 0`)** |
| `td_sec_axial` `orbitOwnPixels` | `0` (not measured / occluded) | `2,041` | **PASS (`> 0`)** |
| `td_sec_axial` `selectAxialDiffPixels` | `—` | `20,557` | **PASS (`> 0`)** |
| `td_sec_axial` `isolateAxialInkPixels` | `—` | `520,548` (`546` section-hue px) | **PASS (`> 0`)** |
| `td_sec_axial` `isolateAxialDiffPixels` | `—` | `20,876` | **PASS (`> 0`)** |
| `non_S` `defaultOwnPixels` | `15,172` | `15,156` | **PASS (`> 0`)** |
| `c_base` / `c_cut` `defaultOwnPixels` | `1,303` / `590` | `1,158` / `531` | **PASS (`> 0`)** |
| `cameraChecks.resetDiffFromDefault` | `239` | `0` | **PASS (`=== 0`)** |

### Full 9-Demo Browser Regression Summary (`53` Screenshots, `0` Errors)

| Demo ID | Served | Default Ink Pixels | Primary Object `ownPixels` | Orbit / Zoom / Pan Diff | Reset Diff | Selection / Explode / Step0 Diff | Labels / Collisions | Console / Page Errors |
|---|---|---:|---|---|---|---|---|---|
| `demo1-regular-pyramid-named-section` | Yes | `536,133` | `khoi_S_ABCD`: `54,485`, `td_ask9`: `14,016` | `51,389` / `32,126` / `56,647` | `0` | `47,550` / `60,975` / `16,803` | `8` / `0` | `0` |
| `demo2-pyramid-unnamed-midpoints-ratio` | Yes | `531,599` | `khoi_S_ABCD`: `30,023`, `khoi_S_ABMN`: `14,559`, `td_sec1`: `4,539` | `43,053` / `23,319` / `45,500` | `0` | `11,232` / `50,557` / `15,826` | `7` / `0` | `0` |
| `demo3-prism-plane-cut-two-solids` | Yes | `541,382` | `khoi_A_B_C_D_E_F`: `39,553`, `khoi_D_ABC`: `16,833` | `52,473` / `41,115` / `66,356` | `0` | `35,612` / `86,881` / `18,176` | `6` / `0` | `0` |
| `demo4-cube-diagonal-section` | Yes | `538,448` | `khoi_A_B_C_D_A1_B1_C1_D1`: `63,991`, `td_ask5`: `24,090` | `55,709` / `35,708` / `60,578` | `0` | `57,264` / `82,193` / `29,482` | `8` / `0` | `0` |
| `demo5-shared-face-composite-solids` | Yes | `543,727` | `khoi_A_B_C_D_E_F_G_H`: `49,179`, `khoi_S_EFGH`: `15,619` | `46,357` / `40,860` / `64,002` | `0` | `22,718` / `83,755` / `15,747` | `9` / `0` | `0` |
| `demo6a-curved-cylinder-sections` | Yes | `540,783` | `tru_T`: `26,770`, `c_bot`: `1,069`, `c_top`: `1,846`, `c_mid`: `1,405`, `td_sec_axial`: `7,468` (orbit `4,981`) | `19,357` / `19,863` / `40,683` | `0` | `39,801` / `38,402` / `9,161` | `6` / `0` | `0` |
| `demo6b-curved-cone-frustum-cut` | Yes | `532,750` | `non_S`: `15,156`, `c_base`: `1,158`, `c_cut`: `531`, `td_sec_axial`: `3,105` (orbit `2,041`) | `13,868` / `10,985` / `23,604` | `0` | `20,557` / `19,652` / `4,462` | `5` / `0` | `0` |
| `demo6c-curved-sphere-plane-cut` | Yes | `550,247` | `cau_S`: `45,869`, `c_sec`: `1,039` | `6,349` / `22,740` / `54,487` | `0` | `9,913` / `1,920` / `1,724` | `3` / `0` | `0` |
| `demo7-invalid-geometry-safe-refusal` | No (`REFUSED`) | `—` | Safe refusal (`TYPED_FACT_NEXT_INCONSISTENT_WITNESS`, `scene3d: null`) | `—` | `—` | `—` | `—` | `0` |

---

## 4. P5, P6 & P7 — Candidate Governance, Independent Review & Authoritative Full T3

- **Historical Preservation**: `0` modified files across `simulation-coverage-visual-validation/`, `simulation-evidence-reconciliation/`, and `simulation-evidence-repair/`.
- **Candidate Freeze**: `EVALUATION_CANDIDATE.json` frozen at `NEW_RENDERER_FIXED_CANDIDATE = d2e6037b12580eed1503e911999d4bf981f2c0e4` (`NEW_PRODUCT_COMMIT = 1ca20f4f51457f3457802bca042af76accd13698`, `114` measured files, SHA256 `4d11a91790422b9508bc90921f4352687a4b8616c0f855886e76649d3a7dcf68`); [`candidate_divergence.json`](candidate_divergence.json) records both `original_product_commit` (`3298b901...`) / `original_frozen_candidate` (`5f4ee58c...`) and `current_product_commit` (`1ca20f4f...`).
- **Independent Review**: [`independent-review.md`](independent-review.md) — **`INDEPENDENT_REVIEW_PASS`** (`0 BLOCKER, 0 IMPORTANT, 0 MINOR`).
- **Authoritative Full T3 (`t3/validation.json`)**: Executed in clean detached worktree `verify-simulation-demo6b-renderer-fix` at `d2e6037b12580eed1503e911999d4bf981f2c0e4` via binary-safe [`capture.py`](capture.py):
  - Verdict: **`FULL_PRODUCT_GATE_PASS`** (`527.6s`, exit code `0`, attempt `1/1`).
  - `pytest`: `11,439 passed, 1 skipped, 2 deselected, 9 xfailed` (`511.3s`).
  - `vitest`: `72` test files / `1,156 passed` (`8.7s`).
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

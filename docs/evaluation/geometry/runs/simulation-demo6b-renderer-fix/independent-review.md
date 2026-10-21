# Independent Review Report — `simulation-demo6b-renderer-fix`

- **Verdict**: `INDEPENDENT_REVIEW_PASS`
- **Severity Summary**: `0 BLOCKER, 0 IMPORTANT, 0 MINOR`
- **Reviewer Conversation ID**: `0920a218-54e8-46dd-a3fc-a0d3f599c9e1`
- **Reviewed Worktree**: `D:\Documents\projects\algo-sim\.superpowers\worktrees\simulation-demo6b-renderer-fix` (`research/simulation-demo6b-renderer-fix`)
- **Product Commit**: `1ca20f4f51457f3457802bca042af76accd13698`
- **Candidate Freeze Commit**: `d2e6037b12580eed1503e911999d4bf981f2c0e4`
- **Measured System Hash**: `4d11a91790422b9508bc90921f4352687a4b8616c0f855886e76649d3a7dcf68` (`114` files)

---

## Item-by-Item Verification Findings

### 1. P0 Raw-Log Byte-Size Reconciliation — **PASS**
- Direct inspection of `docs/evaluation/geometry/runs/simulation-demo6b-renderer-fix/RAW_LOG_SIZE_RECONCILIATION.md` and `raw-log-size-reconciliation.json` confirms exact 4-way binary byte-length and SHA256 identity across `original_runtime_source_worktree`, `corrective_archive_worktree`, `git_blob_609cb877`, and `clean_checkout_archive`:
  - `attempt1-fail.stdout.log`: `31,647` bytes, SHA256 `e2074c0897550bda185a6f55ea4113e3a8324263fc7a0cf1e2743228207c03f6` (`257` CRLF / `126` lone LF; historical LF-normalized blob at `d86c7203`: `31,390` bytes, `2620186c...`).
  - `attempt1-fail.stderr.log`: `121,261` bytes, SHA256 `bfd6d2ca0bf9c3f05bf6010dd12a9c949656172434d9579ba24fdc3701be54a5` (`0` CRLF / `733` lone LF).
  - `attempt2-pass.stdout.log`: `28,606` bytes, SHA256 `013f2e784e9fa828a055320468afe7137f080d2447615aec3c3d3970a2138e06` (`207` CRLF / `126` lone LF; historical LF-normalized blob at `d86c7203`: `28,399` bytes, `8274c4c2...`).
  - `attempt2-pass.stderr.log`: `121,261` bytes, SHA256 `47de58275e7e069019a5f60938442317568919cd55fcaf2c0cd567fee13589c0` (`0` CRLF / `733` lone LF).
- The discrepancy in `simulation-evidence-repair/report.md` (`17,843`, `1,303`, `18,243`, `332` bytes) is accurately classified as `PROSE_REPORTING_METADATA_ERROR_ONLY` (conflating byte counts from the new `simulation-evidence-repair/t3` run where `t3/stdout.log` = `18,257` B and `t3/stderr.log` = `332` B with the true SHA256 digests of the original T3 logs), with zero mutation of any historical files.

### 2. P3 Scoped Renderer Fix (`frontend/src/simulations/domains/geometry/scene3d-view.tsx`) — **PASS**
- **Role-based interior auxiliary section polygon rendering (lines 1640–1718)**:
  - `daGiacPhu = o.type === "polygon3" && o.surface_role === "AUXILIARY_SURFACE" && !(o.formation_roles ?? []).includes("CONSTRUCT_BASE")` and `toXuyenKhoi = thietDien || daGiacPhu` classify interior auxiliary section polygons generally by semantic role, with zero hardcoded demo IDs or vertex labels.
  - Interior fill mesh applies `renderOrder = THU_TU_TO_THIET_DIEN` (`7`), `...LECH_THIET_DIEN` (`polygonOffset: true, polygonOffsetFactor: 0, polygonOffsetUnits: -1`), `depthTest: false`, `depthWrite: false`, and opacity `noiBat ? 0.42 : 0.28`, preventing complete rejection behind `curved_solid` `lopChieuSau` opaque depth prepasses while preserving `depthTest: true` and `renderOrder: 0` for `BASE_REGION` and `CONSTRUCT_BASE` polygons.
  - Boundary loop lines emit two GPU depth passes (`polygon_border:${o.id}:thay` using `THREE.LineBasicMaterial` with `depthFunc: THREE.LessEqualDepth` and `polygonOffset`, plus `polygon_border:${o.id}:khuat` using `THREE.LineDashedMaterial` with `depthFunc: THREE.GreaterDepth`, `depthWrite: false`, and `computeLineDistances()`), both tagged `userData.nonCanonicalBorderLine = true`.
  - In polyhedral scenes (`occluders.length > 0`), `updateNonCanonicalVisibility` (lines 712–770) removes children with `userData.nonCanonicalBorderLine === true` and replaces them with CPU-classified `section_border` spans as before; in curved-solid scenes (`occluders.length === 0`), both GPU passes remain active so visible and hidden boundary segments render properly against `lopChieuSau`.
- **Synchronous camera reset render & label re-projection (lines 2517–2520)**:
  - `vuaKhungRef.current` invokes `veRef.current?.(); chieuNhan();` immediately after `datKhungNhin(cam, dieuKhien, kn)`, eliminating the 1-frame stale render/label projection lag on camera reset.

### 3. P4 Unit & Real-Browser WebGL Regression Evidence — **PASS**
- **Unit tests (`frontend/src/simulations/domains/geometry/simulation-coverage-fixes.test.tsx`, lines 251–358)**:
  - Verifies `td_sec_axial` in `demo6b` builds `polygon_fill:td_sec_axial` with `renderOrder === THU_TU_TO_THIET_DIEN (7)`, `depthTest === false`, `depthWrite === false`, `polygonOffset === true`, `opacity >= 0.28`, and retains both `LessEqualDepth` solid and `GreaterDepth` dashed border passes when `occluders.length === 0`.
  - Verifies `day_ABCD` (`BASE_REGION` in `demo1`) and `day_ABC` (`CONSTRUCT_BASE` in `demo3`) preserve `depthTest === true` and `renderOrder === 0`, and polyhedral `td_ask9` in `demo1` replaces initial `polygon_border` lines with CPU `section_border:td_ask9:*` spans.
- **Real-browser Playwright + SwiftShader WebGL regression (`browser/invocation.json`, `browser/execution.json`, `browser/validation.json`, `browser/visual-receipt.json`, `browser/screenshots/*.png`)**:
  - `demo6b-curved-cone-frustum-cut` axial section (`td_sec_axial`) metrics:
    - Default view: `ownPixels = 3105` (`> 0`)
    - Orbited view: `orbitOwnPixels = 2041` (`> 0`)
    - Selection (`select: "td_sec_axial"`): `selectAxialDiffPixels = 20557` (`> 0`)
    - Isolation (`isolate: "td_sec_axial"`): `isolateAxialInkPixels = 520548` (`> 0`), `isolateAxialSectionHuePixels = 546`, `isolateAxialDiffPixels = 20876`
  - Visual inspection of `demo6b-curved-cone-frustum-cut_default.png`, `demo6b-curved-cone-frustum-cut_orbit.png`, `demo6b-curved-cone-frustum-cut_selected_td_sec_axial.png`, and `demo6b-curved-cone-frustum-cut_isolated_td_sec_axial.png` confirms the interior triangle `SAB` is clearly visible, properly shaded/outlined in default and orbited views, highlighted in blue with readout `S(SAB) = 12` when selected, and rendered cleanly in isolation.
  - `demo6a-curved-cylinder-sections` axial section (`td_sec_axial`) also improved (`defaultOwnPixels = 7468`, `orbitOwnPixels = 4981`, `selectAxialDiffPixels = 39801`, `isolateAxialInkPixels = 520548`).
  - Across all 8 positive demos (`demo1..demo6c`): `all_primary_objects_own_pixels_positive = true` (every primary solid, curved_solid, circle3, and polygon3 has `ownPixels > 0`), `all_camera_resets_exact_zero_diff = true` (`resetDiffFromDefault = 0` for all 8 positive demos), `0` dependency violations, `0` label collisions, `1` clean refusal (`demo7`), and `0` console/page errors (`totalConsoleErrors = 0`, `totalPageErrors = 0`).

### 4. P5 Historical Evidence Preservation & Candidate Governance — **PASS**
- `git diff --name-only 609cb877d9e0177e8408f31c7d3cc0c9cd5f89fc -- docs/evaluation/geometry/runs/simulation-coverage-visual-validation docs/evaluation/geometry/runs/simulation-evidence-reconciliation docs/evaluation/geometry/runs/simulation-evidence-repair` is empty (`0` modified files).
- `docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json` and `docs/evaluation/geometry/runs/simulation-demo6b-renderer-fix/candidate_divergence.json` record both `original_product_commit` (`3298b901d2246650535aa4028845ddc2a44892c4`) / `original_frozen_candidate` (`5f4ee58c48011e9e5d38d3209f7c97250032a976`) and `current_product_commit` (`1ca20f4f51457f3457802bca042af76accd13698`) / `d2e6037b12580eed1503e911999d4bf981f2c0e4`, with `measured_system.tree_hash = 4d11a91790422b9508bc90921f4352687a4b8616c0f855886e76649d3a7dcf68` across `114` entries (`108` `backend/app` files + `6` `frontend/src/simulations/domains/semantic` entries), while preserving `DEFAULT_MODE = LLM_ONLY`, `RESPONSE_CONTRACT = flat`, `HYBRID_PRODUCT_ENABLEMENT = NO-GO`, `ALLOW_LIVE_AI = 0`, and `CACHE_VERSION = 127`.

---

## Final Integration Gate Review Addendum (P1–P3 Bounded Audit)

- **Reviewer Conversation ID**: `0920a218-54e8-46dd-a3fc-a0d3f599c9e1`
- **Review Rounds**:
  - **Round 1**: Found `0 BLOCKER, 1 IMPORTANT, 0 MINOR` — six prose SHA256/byte strings in `CANDIDATE_AND_BROWSER_INVENTORY_RECONCILIATION.md` (Section 1.2 worktree SHA256s for `scene3d-view.tsx` and `simulation-coverage-fixes.test.tsx`, and Section 2.3 byte sizes/SHA256s for `browser-original-runner/validation.json`, `browser-original-runner/visual-acceptance-receipt.json`, and `browser/input-scenes.json`) did not match the authoritative values in `candidate-and-browser-inventory-reconciliation.json` and on disk. All six strings were corrected in `CANDIDATE_AND_BROWSER_INVENTORY_RECONCILIATION.md`.
  - **Round 2 (Final)**: Verified all six corrected strings in `CANDIDATE_AND_BROWSER_INVENTORY_RECONCILIATION.md` match `candidate-and-browser-inventory-reconciliation.json` and actual on-disk bytes/SHA256 digests (`0 BLOCKER, 0 IMPORTANT, 0 MINOR`, `INDEPENDENT_REVIEW_PASS`).
- **Bounded Audit Findings (P1–P3)**:
  1. **P1 Measured Hash Coverage**: `backend/scripts/freeze_evaluation_candidate.py` defines `MEASURED_SYSTEM_PATHS = ("backend/app", "frontend/src/simulations/domains/semantic", "frontend/src/simulations/domains/semantic/semantic_program.schema.json")` (`108` `backend/app` files + `6` `frontend/src/simulations/domains/semantic` entries = `114` entries; `4d11a91790422b9508bc90921f4352687a4b8616c0f855886e76649d3a7dcf68`). `frontend/src/simulations/domains/geometry/*` is intentionally outside `MEASURED_SYSTEM_PATHS` and is locked by `product_commit_sha = 1ca20f4f51457f3457802bca042af76accd13698` (`PRODUCT_PATHS = ("backend/app", "frontend/src")`). Exact Git blob OIDs and SHA256 digests for `scene3d-view.tsx` (`c1ae8e04...` $\to$ `382ca0ef...`) and `simulation-coverage-fixes.test.tsx` (`0ae36467...` $\to$ `7948f458...`) are verified in `candidate-and-browser-inventory-reconciliation.json`, and Full T3 at `d2e6037b` (`t3/stdout.log` line 209) executed those exact blobs (`6 tests` in `simulation-coverage-fixes.test.tsx`, `1,156` frontend vitest passed).
  2. **P2 Browser Inventory Reconciliation & Original Runner Execution**: `browser/input-scenes.json` (`c3203838fc0eefb916d98212674f89e07d1e37706e6dce9daf8779e0cd7466de`, `593,526` bytes) is 100% byte-identical to `simulation-evidence-repair/browser/input-scenes.json` and contains the exact 9 original demo scenarios (`demo1..demo7`); only the prose Markdown table in the earlier draft of `report.md` Section 3 had miswritten demo/object names, which is now corrected in `report.md`. Executing the original unaltered `docs/evaluation/geometry/runs/simulation-coverage-visual-validation/run_browser_audit.mjs` on the new renderer (`browser-original-runner/`) produced `49` PNG screenshots, `0` console/page errors, `all_primary_objects_own_pixels_positive = true`, `all_camera_resets_exact_zero_diff = true`, `demo6b` `td_sec_axial` `ownPixels = 3,105` (up from `0`), `demo6a` `td_sec_axial` `ownPixels = 7,468` (up from `341`), 100% identical `ownPixelMap`s on `demo1..demo5` and `demo6c`, and clean refusal on `demo7`.
  3. **P3 Historical Preservation & Governance**: Zero historical files modified (`git diff --name-only 609cb877d9e0177e8408f31c7d3cc0c9cd5f89fc -- docs/evaluation/geometry/runs/simulation-coverage-visual-validation docs/evaluation/geometry/runs/simulation-evidence-reconciliation docs/evaluation/geometry/runs/simulation-evidence-repair` is empty), and all governance invariants (`DEFAULT_MODE = LLM_ONLY`, `RESPONSE_CONTRACT = flat`, `HYBRID_PRODUCT_ENABLEMENT = NO-GO`, `ALLOW_LIVE_AI = 0`, `CACHE_VERSION = 127`) remain intact.


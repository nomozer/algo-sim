# Independent Review Report — `simulation-visual-consistency-learning-ux`

- **Verdict:** `INDEPENDENT_REVIEW_PASS`
- **Severity Summary:** `0 BLOCKER, 0 IMPORTANT, 0 MINOR`
- **Reviewer Conversation ID:** `4683a88d-cbb7-40f1-a0e5-9b07575c1851`
- **Reviewed Worktree:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\simulation-visual-consistency-learning-ux`
- **Branch / Commits Verified:**
  - Branch: `research/simulation-visual-consistency-learning-ux`
  - Base `main`: `43247c9e9375a3dbf2b5223324a58e6f932ca596`
  - Session 1 commit: `9341a85771dba79376b46e69ac531c413f507b55`
  - Final product commit: `ec92c8ad81e52dcbf958f25184bea2958fd6be58`
  - Frozen candidate commit: `59d417a84b755d553b6dcf2085d66bb52fb100df`
  - Measured system hash: `91ac973ebc2d42041809d957c55e2829f875c05e649e35b7eee9ebeac1e5d26d` (`114` entries)

---

## Item-by-Item Verification Findings (`1..6`)

### 1. No hardcoded cases (`PASS`)
- **`backend/app/ai/adapter3_simulation.py` (`L2347-L2348`, `L2484-L2485`, `L2711-L2735`):**
  - Assigns canonical prime symbols (`A'`, `B'`, `O'`) and radius symbol (`r`) only when undeclared in `declared_names`, based on general curved-solid / sphere construction rules.
  - Attaches `notation`, `label`, and `reference` to undeclared `quantity` objects matching general symbolic identifiers (`^[a-zA-Z][a-zA-Z0-9₀-₉'’]*$`).
  - Tags `circle3` and `ellipse3` with `surface_role = "BASE_REGION"` when `"CONSTRUCT_BASE" in formation_roles or oid.startswith("duong_tron_day")` else `"SECTION_REGION"`.
- **`frontend/src/simulations/domains/geometry/pick-target.ts` (`L125-L132`):**
  - `HANG_CU_THE` orders raycast pick specificity strictly by general `Scene3D` object type (`point3: 0`, `edge: 1`, `segment3: 1`, `face: 2`, `polygon3: 3`, `circle3: 3`, `ellipse3: 3`, `line3: 3`, `plane3: 3`, `section: 3`, `quantity: 4`, `solid: 5`, `curved_solid: 5`, `cylinder: 5`, `cone: 5`, `sphere: 5`).
- **`frontend/src/simulations/domains/geometry/scene3d-model.ts` (`L826-L894`, `L1764-L1811`, `L1875-L1897`, `L1904-L2159`) & `scene3d-view.tsx` (`L2547-L2579`):**
  - `diemHuuHan`, `tapKetQuaCuoi`, `phanLoaiVat`, `phanTichToanHocCuaCanh`, and camera auto-framing (`vuaKhungRef`) operate strictly on general `Scene3D` object types, `surface_role`, `formation_roles`, `origin`, `annotation`, `perpendicular_witness`, and `RouteDSimulationSummary` with zero problem-ID, vertex-name, or expected-answer branches.

### 2. No fake Scene3D or fake answers (`PASS`)
- **`frontend/src/simulations/domains/geometry/scene3d-model.ts` (`L1904-L2159`) & `Scene3DExplorer.tsx` (`L234-L237`, `L469-L479`):**
  - `phanTichToanHocCuaCanh` extracts only verified `Scene3D` objects (`quantity`, `section`, `polygon3`, `circle3`, `ellipse3`, `perpendicular_witness`), optional `HybridPreviewView`, and optional `RouteDSimulationSummary` (`math_goals`, `verified_relations`). It never fabricates placeholder answers or synthetic 3D frustum meshes.
  - When a scene has no results, measurements, or certificates, `coPhanTichToan` evaluates to `false` and the `"Phân tích toán học"` button is not rendered (`simulation-learning-ux-session2.test.tsx` `L96-L140`).
- **Fail-closed unsupported geometry (`visual_ux_acceptance_receipt.json` `L4237-L4244`, `simulation-learning-ux-session2.test.tsx` `L211-L229`):**
  - `family13_invalid_geometry_refusal` fails closed with `served: false`, `scene3d: null` (`CURVED_PLANE_DOES_NOT_CUT`) and renders a structured `<UnsupportedNotice>` without fabricating a partial or approximate 3D scene.

### 3. No answer leakage in default simulation mode (Mode A) (`PASS`)
- **`frontend/src/simulations/domains/geometry/Scene3DExplorer.tsx` (`L242-L246`, `L309-L313`, `L698-L784`):**
  - `moBang` initializes to `new Set()` and resets to `new Set()` on every `scene` change (`useEffect` at `L244-L246`), ensuring Mode A (`!moBang.has("phan-tich")`) is always the default entry state.
  - In Mode A, `dapAnAn` is populated via `tapKetQuaCuoi(day, hybrid)`, which suppresses final answer badges on the 3D canvas (`scene3d-view.tsx` `L2031`, `L2057`), suppresses result readouts in `solutionAt(scene, step)` (`Scene3DExplorer.tsx` `L312-L313`), and hides numeric/exact final answers in the object list (`Scene3DExplorer.tsx` `L645-L647`).
- **`frontend/src/simulations/domains/geometry/scene3d-model.ts` (`L1764-L1811`):**
  - `tapKetQuaCuoi` collects `hybrid.answers`, `solutionAt(scene, cuoi).results` (`FINAL_RESULT` events and leaf `MEASURE` readouts), `annotation.role === "result"`, `annotation.category === "result"`, `formation_roles` containing `"FINAL_RESULT"`, `display_group` containing `"target"`, and `kq_vcert*` volume certificate quantities, and propagates bidirectionally across `same_as` and `alias_of`.
- **Browser & Unit Evidence (`visual_ux_acceptance_receipt.json`, `eval-summary.json`, `simulation-learning-ux-session2.test.tsx` `L74-L94`):**
  - Across all 13 served scenes in `visual_ux_acceptance_receipt.json`, `defaultPanelOpen` is `false` and `visibleReadoutBadgesDefault` is `[]` (`D8_default_simulation_mode_compliance = 1.0`).

### 4. No mathematical authority moved to frontend (`PASS`)
- **`frontend/src/simulations/domains/geometry/scene3d-model.ts` (`L1904-L2159`), `Scene3DExplorer.tsx` (`L698-L784`), & `scene3d-view.tsx` (`L1364`, `L1437-L1438`, `L1547-L1548`):**
  - All answers, formulas, exact expressions, and relation witnesses displayed in Mode B (`"Phân tích toán học"`) are formatted directly from backend-supplied `Scene3D` (`value`, `exact`, `formula`, `perpendicular_witness`) and `route_d` (`math_goals`, `verified_relations`, `certificate`) fields.
  - `toNumber` and `Math.sqrt` in `scene3d-view.tsx` and `scene3d-model.ts` (`diemHuuHan` `L843-L887`) are used exclusively for 3D mesh/bounding-box presentation of backend-supplied `radius_sq`, `height_sq`, `semi_major_sq`, and `semi_minor_sq`.

### 5. Unified visual semantics across polyhedra and curved solids (`PASS`)
- **Unified solid body shell (`scene3d-view.tsx` `L1554-L1560`, `L1610-L1616`):**
  - `curved_solid` (`cylinder`, `cone`, `ball`) and polyhedral `mesh` solids both use `color: nen(MAU.mesh)` (`0x647a96`) and default `opacity: 0.22` (`0.36` when highlighted for curved solids), reserving `MAU.surface` (`0x7c3aed`) exclusively for cutting planes (`plane3`, `L1233`).
- **Base vs. cutting section visual separation (`scene3d-view.tsx` `L1367-L1406`, `L1497-L1515`; `interaction-state.ts` `L354-L364`; `scene3d-model.ts` `L1875-L1897`):**
  - Structural base circles (`BASE_REGION` / `CONSTRUCT_BASE` / `duong_tron_day*`) render with dark slate ring `net(MAU.canh)` (`0x1e293b`), subtle slate cap fill (`polygon_fill:${o.id}`, `nen(MAU.mesh)`, `opacity: 0.12`, `0.24` highlighted), and categorize under `"Đa giác"`.
  - Cutting circular and elliptical sections (`SECTION_REGION`) render with warm amber ring `net(MAU.polygon)` (`0xf59e0b`), warm amber translucent disk (`section_fill:${o.id}`, `nen(MAU.polygon)`, `opacity: 0.28`, `0.42` highlighted, `renderOrder = THU_TU_TO_THIET_DIEN = 7`, `depthFunc: THREE.AlwaysDepth`, `depthWrite: false`, `LECH_THIET_DIEN`), and categorize under `"Thiết diện"`.
- **Real-Browser Chromium WebGL Verification (`visual_ux_acceptance_receipt.json`, `eval-summary.json`):**
  - All 14 benchmark families (13 served 3D scenes + 1 fail-closed refusal) passed real Chromium WebGL audit: `D1..D4 = 1.0`, `D5 collision_rate = 0.0` (`0` label overlaps across all steps and views), `D6..D10 = 1.0`, `totalConsoleErrors = 0`, `totalPageErrors = 0`, and `resetDiffFromDefault = 0` across all 13 served scenes.

### 6. Preserved governance invariants (`PASS`)
- **`CHE_DO_MAC_DINH = "LLM_ONLY"`:** Verified in `backend/app/simulation/geometry_compiler/routing.py` (`L30`).
- **`response_contract = "flat"` & `hybrid_preview_enabled = False`:** Verified in `backend/app/ai/pipeline.py` (`L51-L52`).
- **`HYBRID_PRODUCT_ENABLEMENT = NO-GO` & `ALLOW_LIVE_AI = 0`:** Verified across `eval-summary.json`, `corpus-dev.json`, `candidate_divergence.json` (`live_provider_calls = 0`), and `SIMULATION_VISUAL_UX_EVALUATION_REPORT.md`.
- **`CACHE_VERSION = "127"`:** Verified in `backend/app/main.py` (`L824`).
- **Frozen candidate consistency:** `docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json` matches `commit = product_commit_sha = "ec92c8ad81e52dcbf958f25184bea2958fd6be58"` and `measured_system.tree_hash = "91ac973ebc2d42041809d957c55e2829f875c05e649e35b7eee9ebeac1e5d26d"` (`so_file = 114`), with `candidate_divergence.json` confirming zero unrecorded divergence.

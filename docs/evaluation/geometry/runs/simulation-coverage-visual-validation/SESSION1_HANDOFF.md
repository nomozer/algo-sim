# Session 1 Handoff — Simulation Coverage & Visual Validation

## 1. Repository, Branch & Baseline Identity
- **Repository:** `D:\Documents\projects\algo-sim`
- **Campaign Worktree:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\simulation-coverage-visual-validation`
- **Campaign Branch:** `research/simulation-coverage-visual-validation`
- **Verified Baseline `main` / `origin/main`:** `bd8d6a9dc3acc9a4204b616379001270bb6d39f9`
- **Session 1 Checkpoint Commit (`HEAD`):** `e05e620866934ce0f6c184f1d0de5dbace67b4cf`
- **Owner Authorization:** `GO_SIMULATION_COVERAGE_VISUAL_VALIDATION_LOCAL_RESEARCH`
- **Live AI Calls:** `0` (`ALLOW_LIVE_AI = 0`)

## 2. Capability Matrix & Real-Browser Audit Artifacts (P1–P2)
- **Simulation Capability Matrix:** `docs/evaluation/geometry/runs/simulation-coverage-visual-validation/SIMULATION_CAPABILITY_MATRIX.md`
  - Inventories all 15 geometric shape/feature categories across all 7 architectural levels (`L1` Input Contract through `L7` Interactive Frontend).
- **Real-Browser Baseline vs Post-P3 Audit:**
  - Exporter: `docs/evaluation/geometry/runs/simulation-coverage-visual-validation/export_baseline_audit.py`
  - Playwright Headless Chromium Runner: `docs/evaluation/geometry/runs/simulation-coverage-visual-validation/run_browser_audit.mjs`
  - Baseline Receipt: `docs/evaluation/geometry/runs/simulation-coverage-visual-validation/browser-audit/baseline_audit_receipt.json` (`browser-audit/screenshots-baseline/`)
  - Post-P3 Receipt: `docs/evaluation/geometry/runs/simulation-coverage-visual-validation/browser-audit/post_p3_audit_receipt.json` (`browser-audit/screenshots-post-p3/`)

## 3. Fixed Simulation Breakages (`RED -> GREEN`, P3)
1. **Curved solid scalar-radius & scalar-height 3D rendering (`frontend/src/simulations/domains/geometry/scene3d-view.tsx`):**
   - Changed `o.rim_point` guard to `(o.rim_point || o.radius_sq)` so scalar-radius `ball`, `cylinder`, and `cone` solids construct their Three.js meshes (`ownPixels`: `0 -> 39,784` on cylinder, `0 -> 20,956` on cone, `0 -> 25,665` on sphere).
   - Added canonical Z-axis apex/top positioning `(tam.x, tam.y, tam.z + h)` when `o.apex_or_top` is `null` and `h > 0`.
2. **Curved solid scalar-height bounding box (`frontend/src/simulations/domains/geometry/scene3d-model.ts`):**
   - Included `[c[0], c[1], c[2] + h]` in `diemHuuHan` when `o.apex_or_top` is `null` and `o.curved_kind !== "ball" && h > 0` (`bbox`: `[-2,-2,0]->[2,2,0]` fixed to `[-2,-2,0]->[2,2,3]`).
3. **Component tree classification & explode anchor (`frontend/src/simulations/domains/geometry/interaction-state.ts`):**
   - Added `segment3: "Cạnh"`, `circle3: "Thiết diện"`, `ellipse3: "Thiết diện"`, `curved_solid: "Khối"` to `HANG_MUC`, included `o.type === "curved_solid"` in `laKhoi` for `semanticTree` (`0` `"Khác"` categories across all 9 audited scenes), and added `o.center` and `o.anchor` to `_tam(o)` for explode.
4. **Timeline event classification & learner narration (`backend/app/simulation/semantic_program/scene3d.py` & `simulation_state.py`):**
   - Added `"construct_curved_solid": "CREATE"` to `_HANH_DONG`.
   - Formatted `circle3` and `ellipse3` construction events with `action="CREATE"`, `semantic_kind="GEOMETRY_CONSTRUCTION"`, and `"Dựng <label>."` instead of leaking raw `Circle3(...)`/`Ellipse3(...)` repr strings.
   - Added `"curved_solid": "structural"`, `"circle3": "structural"`, `"ellipse3": "structural"` to `typed_dependency_graph`.

## 4. Curved Solid Expansion (P4)
- Extended `SolidSpec`, `DerivedPlaneSectionSpec`, `MathGoalSpec`, and `DerivedObjectIdentity` in `backend/app/simulation/geometry_functions/typed_fact_next.py` (`typed-fact-next/1`) and `_Adapter3Compiler` in `backend/app/ai/adapter3_simulation.py` (`hybrid-simulation-adapter/3`):
  - **Right circular cylinder (`cylinder`):** base & top circles (`circle3`), axis segment (`segment3`), parallel plane circle cut (`circle3`), axial section rectangle (`polygon3`), oblique ellipse cut (`ellipse3`), exact `volume`, `lateral_area`, `radius`, `area`.
  - **Right circular cone (`cone`) + Cone frustum / cut cone:** base circle (`circle3`), apex & slant generator (`segment3`), parallel plane cut (`circle3`), derived upper cone (`curved_solid`), axial section triangle (`polygon3`), exact `volume`, `lateral_area`, `volume_ratio`, and `residual_volume` (cone frustum cross-checked against $\frac{1}{3}\pi h_{\text{frustum}}(R^2 + R r + r^2)$).
  - **Sphere (`sphere`):** center, radius $R$, plane cut circle (`circle3`) when $d < R$, exact `volume` ($\frac{4}{3}\pi R^3$), surface area ($4\pi R^2$), section radius and area.
  - **Fail-closed refusals:** `CURVED_PLANE_DOES_NOT_CUT` ($d > R$), `CURVED_PLANE_TANGENT` ($d = R$), `CURVED_SECTION_OUTSIDE_V1_CLOSURE`, `CURVED_CONE_SECTION_PARABOLIC`, `CURVED_PRIMITIVE_BLOCKED_BY_KERNEL` (standalone `cone_frustum`), `CURVED_RADIUS_OUTSIDE_DOMAIN`.

## 5. Remaining Work for Session 2 (P6–P13)
- **P6:** Generate interactive demonstration suite (`demos/demo1..demo7.json`) covering all 7 required scenarios.
- **P7:** Execute real-browser Playwright visual acceptance (`run_browser_audit.mjs`) on the demo suite, producing screenshots and `visual-acceptance-receipt.json`.
- **P8:** Build and run simulation-centered development evaluation (`corpus-dev.json`, `oracle_eval.py`, `eval-summary.json`, labeled `DEVELOPMENT_EVALUATION_NOT_BLIND`).
- **P9:** Run full historical regression suite (`174` rows, `41` Adapter `/2` fixtures, Wave 1–3A, SGH, BH2A, BH2C, NLU GOLD).
- **P10–P13:** Candidate freeze, independent subagent review, authoritative Full T3 on a clean worktree snapshot, and final report.

## 6. Exact Commands to Resume in Session 2
```powershell
Set-Location "D:\Documents\projects\algo-sim\.superpowers\worktrees\simulation-coverage-visual-validation"
git status --short
git log -n 2 --oneline
```

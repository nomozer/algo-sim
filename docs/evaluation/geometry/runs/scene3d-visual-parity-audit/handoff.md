# Handoff — `scene3d-visual-parity-audit` (W0 Baseline Audit)

- **Status:** `SCENE3D_W0_BASELINE_AUDIT_COMPLETE`
- **Issue:** `ISSUE-ARCH-SCENE3D-CONSTRUCTION-READABILITY`
- **Baseline Commit:** `f83b4ed14995c89d6cf00a643cd14c814c78004c`
- **Product Commit:** `55c657b8be715cda0edcc9e6e2ec1b3a204bdb65`
- **Candidate Tree Hash:** `30808cb002b377e4ad68f224363ef58ab6e51e0facba7e2d4c501419f58d91dc` (110 files, unmodified)

## 1. What Was Accomplished in W0

1. **Separated Mathematical Correctness from Frontend Visual Mapping & Readability:**
   - Verified via `results/math_and_readability_oracle.json` (`sha256=9cda8f5ad7f30988f5147a2f998a6eddcbd0ec54627765f72449053e007e3cca`) that backend Scene IR coordinates, directions, plane equations, intersection lines, projection feet `H`, `perpendicular_witness` coordinates, and exact symbolic distances are **100% mathematically exact** in chart space under `chart_metric` $G$.
2. **Identified 2 CRITICAL and 5 IMPORTANT Frontend / Parity Root Causes (`results/findings.json`):**
   - **`FINDING-B1` (`CRITICAL` — `scene3d-chart.ts:53-70`):** `veKhongGian(scene)` transforms `o.xyz` and `o.annotation.witness` by the Cholesky factor $T$ ($T^T T = G$), **but omits `o.perpendicular_witness.{foot, marker.{u,v}}`**. This causes the purple/green dashed perpendicular segment (`perpendicular:H`) and right-angle symbol to terminate in raw chart coordinates (`0.668` to `1.000` world units away from the rendered point `H`!).
   - **`FINDING-B2` (`CRITICAL` — `scene3d-auxiliary.ts:36-63` & `scene3d-timeline.ts:110-128`):** `auxiliaryObjects` classifies target carrier lines (`gt_g`, `derived_H_line`) as disposable (`loai: "dung"`) with `xongTai` equal to `H`'s raw step, while `geometryTimeline` folds the `FINAL_RESULT` step (`xongTai + 1`) into `H`'s learner step anchor. Thus, in Product (`auxiliaryShown = false`), **`gt_g` and `derived_H_line` disappear at the final step (and on `H`'s own learner step!)**, while `projectionWitnessesAt` still draws `perpendicular:H` pointing to an invisible line. Conversely, temporary off-solid translated `point3` (`H, H1` in `two-line-*`) are ignored by `auxiliaryObjects` and remain permanently floating outside the solid.
   - **`FINDING-D1` (`IMPORTANT` — `Scene3DExplorer.tsx:210` vs `hybrid-section-visual.tsx:32`):** Product wraps the scene with `withSubEntities(veKhongGian(scene))` (adding `solid::face:i` amber tint meshes, premature `td::face:0` fill on the first section edge step, and duplicate `td::vertex:i` markers), whereas Harness omits `withSubEntities`.
   - **`FINDING-D2` (`IMPORTANT`):** Product starts at `step = 0` and steps through `geometryTimeline` learner anchors; Harness starts at `step = stepCount - 1` and steps through raw event indices.
   - **`FINDING-D3` (`IMPORTANT`):** `result-binding-visual-check.mjs:31` forced `&aux=1`, masking `FINDING-B2` during T3 visual checks.
   - **`FINDING-C2` (`IMPORTANT`):** Full-solid `plane_patch` rectangles (`mp1_gt_g`, `mp2_gt_g`, `mp_td_q`) span all solid vertices with `0.22 * span` padding at `0.26–0.42` opacity, obscuring internal geometry.
   - **`FINDING-E1` (`IMPORTANT`):** Coincident point labels (`H` occluding `B` at `[2, 0, 0]` in `derived-line-cuboid`/`prism`) and raw compiler IDs (`gt_g`, `mp1_gt_g`, `derived_H_line`).
3. **Captured Complete Browser Visual Parity Package (`results/parity_telemetry.json`, `images/harness/`, `images/product/`):**
   - 11 locked cases audited across Product (`/`) and Harness (`/scripts/hybrid-section-visual.html`) with `0` console errors, `0` page errors, and `0` live model calls.

## 2. Recommended Next Step (Wave 1 — W1)

Proceed to **W1 (Product–Harness Parity & Chart-Metric Witness Fix)** upon user approval:
1. Transform `o.perpendicular_witness` in `scene3d-chart.ts` (`doiDoiTuong`).
2. Keep target carrier lines of active projection feet `H` visible in `scene3d-auxiliary.ts` when `auxiliaryShown = false`.
3. Prevent unselected `solid::face:i` from tinting solid faces amber, gate `td::face:0` on section closure, and deduplicate `td::vertex:i` against named `point3` in `scene3d-subentities.ts` / `scene3d-view.tsx`.
4. Align `hybrid-section-visual.tsx` and `result-binding-visual-check.mjs` with Product (`withSubEntities` + `aux=0` default checks + `||witness.foot - H.xyz|| < 1e-6` assertion).

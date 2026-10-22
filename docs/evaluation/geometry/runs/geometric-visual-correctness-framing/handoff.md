# Final Handoff — Geometric Visual Correctness & Adaptive Framing

- **Proposed Readiness Verdict:** `GEOMETRIC_VISUAL_CORRECTNESS_READY_FOR_HUMAN_REVIEW`
- **Owner Authorization:** `GO_GEOMETRIC_VISUAL_CORRECTNESS_LOCAL_ONLY`
- **Date:** `2026-10-22` (`Asia/Bangkok`)
- **Human Visual Approval:** `NOT_GRANTED` (awaiting owner inspection of before/after screenshots and interactive scenes)
- **Merge / Push Status:** `NO GO MAIN`, `NO PUSH` (`main` untouched at `43247c9e9375a3dbf2b5223324a58e6f932ca596`)

---

## 1. Actual Git Identities

- **Verified `main`:** `43247c9e9375a3dbf2b5223324a58e6f932ca596`
- **Source Branch (`research/visual-ux-final-quality`):** `164a5e25ad25bf42d689df115ade5d74b5c733e9` (candidate ancestry `9343e8d0d4c4cdf5bf0865e0a550c13f238f28b5`, previous product commit `56328b17462e9c4e903dc17687da07243d06846d`)
- **Campaign Branch & Worktree:** `research/geometric-visual-correctness-framing` at `D:\Documents\projects\algo-sim\.superpowers\worktrees\geometric-visual-correctness-framing`
- **Product + Regression Test Commit (`product_commit_sha`):** `ca84337e32c27c1116f5b1065ca45f2fcdf3e13c`
- **Frozen Candidate & Authoritative Full T3 Target Commit:** `7868db0aef3810e2089b5f8b8d6aecfb8b3e1400`
- **Measured System Tree Hash (`114` files):** `9bf35a1d6f4c3b3e90228964a3b5ee96288de29efcb3f580f22c6f126489bd9a`

---

## 2. Confirmed Owner Findings & Root Causes (`OWNER_VISUAL_FINDINGS.md`)

1. **Oversized solids & panel overlap (`CONFIRMED_PRESENTATION_DEFECT`):**
   - `khungNhinSuPham` fitted models to `70%` height / `72%` width of the full canvas without safe-area awareness for `#geo3d-bang-phan-tich`, and `diemHuuHan` placed `curved_solid` diagonal bounding points at distance $\sqrt{2}R$ / $\sqrt{3}R$ outside the actual radius-$R$ surface (`resetCamDiff = 0.892 / 0.506 / 0.505` on curved scenes; `geometryHeightRatioSafe = 0.440` on `family11_sphere_plane_cut`).
2. **Excessively thick curved-solid borders (`CONFIRMED_RENDER_DEFECT`):**
   - `circle3` and `ellipse3` rims used full `0.014 * sceneDiameter` ribbon rings centered at $r \pm \text{day}/2$ while shrinking interior fill disks to $r - 1.15 \cdot \text{day}$, creating a double-halo gap.
3. **Fragmented, camera-static dashed hidden curves (`CONFIRMED_RENDER_DEFECT`):**
   - Dashed hidden arcs were built as 20 fixed parameter ring wedges tested against GPU `GreaterDepth` fragments rather than camera-dependent analytical quadric occlusion.
4. **Section fills resembling external caps or missing interior fills (`CONFIRMED_RENDER_DEFECT` & `CONFIRMED_PRESENTATION_DEFECT`):**
   - `lopChieuSau` wrote `FrontSide` depth at `renderOrder = 5` before interior section fills (`renderOrder = 7`), occluding `100%` of interior section fill pixels (`0` px visible) in Normal mode on `family09`, `family10`, `family11`, and `family12`, while `ball` had no great-circle wireframe contours.
5. **Multi-solid scenes difficult to interpret (`CONFIRMED_RENDER_DEFECT` & `CONFIRMED_PRESENTATION_DEFECT`):**
   - `updateCanonicalEdgeVisibility` passed no `occluders` (`hidden_edge_ids = []` across all 9 edges in `family07`), used identical colors for both pyramids, and drew duplicate shared base edges `AB`, `BC`, `CA`.
6. **Scene & demonstration identity mismatches (`DATA_OR_SCENE_IDENTITY_MISMATCH`):**
   - Case A (`family05_prism`): category title said `ABC.A'B'C'` while problem and scene were `ABC.DEF`.
   - Case B (`family07_multi_solid_composition`): category title said prism + pyramid sharing `EFGH` while scene was two pyramids `S.ABC` and `D.ABC` sharing base `ABC`, and `adapter3_simulation.py` emitted internal fallback `D(pyr2)` on vertex collision.
   - Curved descriptions leaked `"đi qua đại lượng"` / `"qua đại lượng"` when `radius` was a scalar quantity `R`.
7. **Final construction step banner (`CONFIRMED_PRESENTATION_DEFECT`):**
   - `Scene3DExplorer.tsx` showed bare vertex symbols (`"C"`, `"F"`, `"D1"`) and did not distinguish the completed final step.

---

## 3. Verification Summary

- **Browser Visual & Geometric Receipt (`after/measurements.json`, `comparison.png`):**
  - Default `geometryHeightRatioSafe`: `0.566..0.585` (`combinedHeightRatioSafe`: `0.569..0.621`) across all 7 representative families.
  - Camera reset stability: `resetCamDiff = 0.000000` across all 7 scenes.
  - Multi-viewport analysis panel safe framing: `panelOverlapPx = 0` at `1440×900`, `1024×768`, and `820×640`.
  - Normal vs. X-ray depth honesty: interior section fills visible inside parent solid (`5,204..20,762` px) while opaque wall in front occludes `100%` of fill pixels in Normal mode (`occludedVisibleFillPixels = 0`, `frontVisibleFillPixels = 5,163`) and reveals them in X-ray mode (`xrayOccludedVisibleFillPixels = 5,163`).
  - Dynamic curved rim visibility: `family09`, `family10`, `family11`, `family12` update visible/hidden arc classifications across default and orbited camera orientations (`orbitChangedRimCount > 0`).
  - Multi-solid visibility: `family07_multi_solid_composition` classifies `7` visible + `2` hidden edges (`pyr1:edge:A-C`, `pyr2:edge:A-C`) with `0` duplicate visual edge owners and clean `D1` notation.
- **Independent Read-Only Review (`review.md`):** `INDEPENDENT_REVIEW_PASS` (`0 BLOCKER, 0 IMPORTANT, 0 MINOR`).
- **Authoritative Full T3 (`t3/execution.json`, `validation.json`):** `FULL_PRODUCT_GATE_PASS` (`551.88s`, backend pytest `11,442 passed`, frontend vitest `75 files / 1,183 passed`, `tsc -b && vite build` `PASS`, thesis demos `5/5`, crash surface `6/6`, post-T3 freeze `MATCH`).

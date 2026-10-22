# Geometric Visual Correctness & Adaptive Framing Report

- **Owner Authorization:** `GO_GEOMETRIC_VISUAL_CORRECTNESS_LOCAL_ONLY`
- **Date:** `2026-10-22` (`Asia/Bangkok`)
- **Source Branch:** `research/visual-ux-final-quality` (`HEAD` = `164a5e25ad25bf42d689df115ade5d74b5c733e9`, candidate ancestry = `9343e8d0d4c4cdf5bf0865e0a550c13f238f28b5`, product commit = `56328b17462e9c4e903dc17687da07243d06846d`, verified `main` = `43247c9e9375a3dbf2b5223324a58e6f932ca596`)
- **Campaign Branch & Worktree:** `research/geometric-visual-correctness-framing` in `.superpowers/worktrees/geometric-visual-correctness-framing`
- **Evaluation Nature:** Offline development regression and real-browser WebGL presentation audit (`DEVELOPMENT_EVALUATION_NOT_BLIND`, `0` live provider calls; not automatic human acceptance).

---

## 1. Confirmed Owner Findings & Exact Root Causes (`OWNER_VISUAL_FINDINGS.md`)

1. **Issue 1 — Several solids are excessively large in the viewport (`CONFIRMED_PRESENTATION_DEFECT`):**
   - **Root Cause:** `scene3d-camera.ts::khungNhinSuPham` applied an aggressive `CHIEU_CAO_MUC_TIEU = 0.70` (`CHIEU_RONG_MUC_TIEU = 0.72`) across the full canvas width (`1258×770`) without accounting for projected label padding, model aspect ratio, or the right-hand Mathematical Analysis panel (`#geo3d-bang-phan-tich`, `x = 858..1244`). In addition, `diemHuuHan` in `scene3d-model.ts` expanded `curved_solid` bounding points to `±R` along diagonal axes (`u ± v ± w`), which lay at distance $\sqrt{2}R$ or $\sqrt{3}R$ outside the actual radius-$R$ surface so step-0 bounds differed from tessellated mesh bounds (`resetCamDiff = 0.892` on `family09`, `0.506` on `family10`, `0.505` on `family12`, and `geometryHeightRatioSafe = 0.440` on `family11_sphere_plane_cut`).
2. **Issue 2 — Curved-solid borders are visually too thick (`CONFIRMED_RENDER_DEFECT`):**
   - **Root Cause:** `scene3d-view.tsx` rendered `circle3` and `ellipse3` rims as 3D ribbon rings of full width `beDayNet(diemNen, r) = 0.014 * sceneDiameter` split across `r ± day/2`, while shrinking the interior fill disk to `r - day * 1.15`, leaving a visible double-halo gap around base and section rings.
3. **Issue 3 — Dashed hidden curves look fragmented and inconsistent (`CONFIRMED_RENDER_DEFECT`):**
   - **Root Cause:** `scene3d-view.tsx` generated dashed hidden arcs by slicing `RingGeometry(trong, ngoai, 64, 1, start, len)` into 20 arbitrary parameter slices against GPU `GreaterDepth` buffer fragments, producing uneven wedge fragments and static/grazing artifacts.
4. **Issue 4 — Some section fills resemble external caps or floating sheets (`CONFIRMED_RENDER_DEFECT` & `CONFIRMED_PRESENTATION_DEFECT`):**
   - **Root Cause:** `lopChieuSau` wrote `FrontSide` depth in the opaque queue (`renderOrder = 5`) before interior section fills (`renderOrder = 7`), so in Normal mode (`depthTest: true`) the front hemisphere/shell of a solid occluded the entire interior section fill (`0` visible interior fill pixels in `family09`, `family10`, `family11`, `family12`), leaving only the outer rim ring floating on the purple cutting plane (`opacity = 0.07`). Moreover, `ball` (`family11_sphere_plane_cut`) had no great-circle wireframe contours, making its spherical curvature nearly invisible on a light background.
5. **Issue 5 — Multi-solid scenes are difficult to interpret (`CONFIRMED_RENDER_DEFECT` & `CONFIRMED_PRESENTATION_DEFECT`):**
   - **Root Cause:** `scene3d-view.tsx` passed only the single solid (`source`) into `classifySolidEdgeVisibility` without `occluders`, so `S.ABC` and `D.ABC` never occluded each other's back edges (`hidden_edge_ids = []` for all 9 edges in `family07_multi_solid_composition`). Both solids also shared identical surface/edge colors and drew duplicate overlapping owners on shared base edges `AB`, `BC`, `CA`.
6. **Issue 6 — Demonstration titles and Scene3D labels mismatch (`DATA_OR_SCENE_IDENTITY_MISMATCH`):**
   - **Root Cause:**
     - **Case A (`family05_prism`):** `audit_scenes.json` category title said `"5. Hình lăng trụ đứng / xiên (ABC.A'B'C')"` while the problem text and `Scene3D` vertices were `ABC.DEF`.
     - **Case B (`family07_multi_solid_composition`):** `audit_scenes.json` category title said `"7. Tổ hợp đa khối (Lăng trụ + Chóp chung mặt EFGH)"` while the fixture was two pyramids `S.ABC` and `D.ABC` sharing base `ABC`, and `adapter3_simulation.py` emitted internal solid-qualified fallback notation `D(pyr2)` when vertex `D` collided across solids.
     - **Curved description leak (`family10`, `family11`, `family12`):** `simulation_state.py` generated `"đi qua đại lượng"` / `"qua đại lượng"` in curved solid/section descriptions when `radius` was a scalar quantity `R`.
7. **Issue 7 — Final construction step guidance (`CONFIRMED_PRESENTATION_DEFECT`):**
   - **Root Cause:** `Scene3DExplorer.tsx` displayed the same banner at the final step (`buoc === maxStep`) and showed bare vertex symbols (`"C"`, `"F"`, `"D1"`) instead of full Vietnamese construction narration.

---

## 2. Scoped Implementation Summary (P2–P6, P8)

1. **True Surface Bounds & Step-Invariant Camera Framing (`scene3d-model.ts`, `scene3d-camera.ts`, `scene3d-view.tsx`):**
   - Replaced diagonal `±R` box corners in `diemHuuHan` with 8 unit-circle perimeter directions $(\cos(k\pi/4), \sin(k\pi/4))$ for `circle3`, `ellipse3`, `cylinder`, and `cone`, and 14 unit-sphere directions (6 cardinal $\pm 1$ + 8 octant $\pm 1/\sqrt{3}$) for `ball`, keeping every boundary point strictly at distance $R$ from the center/axis.
   - Updated `diemKhungNhin(goc, daCoDiemCanh)` in `scene3d-view.tsx` to skip tessellated `curvedRimLoop` and `curvedSolidVolume` vertices whenever analytical `diemCanh` points are already present, achieving `resetCamDiff = 0.000000` across all served scenes.
   - Extended `khungNhinSuPham` (`scene3d-camera.ts`) with `TuyChonKhungNhinSuPham` (`tiLeDoc`, `tiLeNgang`, `dichTamNgang`, `dichTamDoc`) and wired `tinhTuyChonKhung` + `.geo3d-san` `MutationObserver` in `scene3d-view.tsx` so default models occupy `56.6%–58.5%` (`combinedHeightRatioSafe = 56.9%–62.1%`) of the safe viewport height and automatically re-center into the left safe viewport when `#geo3d-bang-phan-tich` opens (`panelOverlapPx = 0` at `1440×900`, `1024×768`, and `820×640`).
2. **Restrained Curved Rims & Camera-Dependent Quadric Occlusion (`scene3d-edge-visibility.ts`, `scene3d-view.tsx`):**
   - Reduced inward rim ribbon thickness (`0.36x` for `BASE_REGION`, `0.46x` for `SECTION_REGION`) with zero gap (`bkTo = trongR`) between the inner rim edge and the fill disk.
   - Added `CurvedSolidVolumeMeta` and `diemVanhCongBiChe` in `scene3d-edge-visibility.ts` and `CurvedRimLoopMeta` / `capNhatHinhHocVanhCong` in `scene3d-view.tsx` to classify 96-segment circular/elliptical rims dynamically per camera pose (`24` uniform dash-gap cycles for occluded back arcs, continuous solid ribbons for visible front arcs).
3. **Honest Normal vs. X-Ray Section Depth & Sphere Contours (`scene3d-view.tsx`):**
   - `lopChieuSau(g)` writes `BackSide` depth at `renderOrder = 5` (before interior section fills at `renderOrder = 7`), while `lopChieuSauMatTruoc(g)` on `curved_solid` writes `FrontSide` depth at `renderOrder = 7.5` (after interior section fills at `7`, before lines at `8..10`). Interior section fills therefore render honestly inside the parent solid in Normal mode while still being occluded by any solid in front (`occludedVisibleFillPixels = 0`, `frontVisibleFillPixels = 5163` in `after/measurements.json`), and X-ray mode (`Nhìn xuyên khối`) explicitly disables `depthTest` on section fills (`xrayOccludedVisibleFillPixels = 5163`).
   - Added 3 subtle orthogonal great-circle wireframe contours to `ball` (`curved_kind === "ball"`) and lowered passive cutting-plane opacity from `0.07` to `0.055`.
4. **Multi-Solid Occlusion & Demo Identity Reconciliation (`scene3d-edge-visibility.ts`, `scene3d-view.tsx`, `adapter3_simulation.py`):**
   - Excluded coplanar shared faces from cross-solid self-occlusion in `scene3d-edge-visibility.ts` (`pointIsHidden`) and passed all active solids in `localOccluders` inside `updateCanonicalEdgeVisibility`, yielding `7` visible + `2` hidden edges (`pyr1:edge:A-C`, `pyr2:edge:A-C`) with `0` duplicate visual owners on `family07_multi_solid_composition`.
   - Styled secondary solids with a distinct muted teal-slate surface (`0x0d9488`, opacity `0.18`) and edge stroke (`0x0f766e`) while suppressing duplicate shared canonical edge owners.
   - Updated `adapter3_simulation.py` to emit subscripted geometric vertex notation `D1` (instead of `D(pyr2)`) on multi-solid symbol collisions and strip `"đi qua đại lượng"` / `"qua đại lượng"` placeholders from curved object labels/roles/events. Reconciled `family05_prism` (`5. Hình lăng trụ đứng ABC.DEF`) and `family07_multi_solid_composition` (`7. Tổ hợp đa khối (Hai hình chóp S.ABC và D.ABC chung đáy ABC)`) in `demos/audit_scenes.json`.
5. **Student-Facing Step Guidance (`Scene3DExplorer.tsx`):**
   - At the final construction step (`dangOBuocCuoi`), displays `"Đã dựng xong (bước N/N): ..."` and hides `"Xem mô hình đầy đủ"`; uses full `geometryNarrationAt` when the step label is a bare vertex symbol.

---

## 3. Before vs. After Browser Measurements (`before/measurements.json` vs. `after/measurements.json`)

| Scene ID | Before `geometryHeightRatioSafe` | After `geometryHeightRatioSafe` | After `combinedHeightRatioSafe` | Before `panelOverlapPx` (`1440×900`) | After `panelOverlapPx` (`1440×900` / `1024×768` / `820×640`) | Before `resetCamDiff` | After `resetCamDiff` |
|---|---:|---:|---:|---:|---:|---:|---:|
| `family01_triangular_pyramid` | `0.708` | `0.585` | `0.621` | `15` | `0 / 0 / 0` | `0.000000` | `0.000000` |
| `family05_prism` | `0.710` | `0.585` | `0.621` | `11` | `0 / 0 / 0` | `0.000000` | `0.000000` |
| `family07_multi_solid_composition` | `0.709` | `0.566` | `0.602` | `0` | `0 / — / —` | `0.000000` | `0.000000` |
| `family09_cylinder_and_sections` | `0.602` | `0.569` | `0.594` | `0` | `0 / 0 / 0` | `0.892074` | `0.000000` |
| `family10_cone_frustum_cut` | `0.597` | `0.579` | `0.615` | `0` | `0 / — / —` | `0.506384` | `0.000000` |
| `family11_sphere_plane_cut` | `0.440` | `0.581` | `0.581` | `0` | `0 / 0 / 0` | `0.000000` | `0.000000` |
| `family12_cylinder_ellipse_section` | `0.641` | `0.569` | `0.569` | `0` | `0 / — / —` | `0.505008` | `0.000000` |

- **Section fill visibility (Normal vs. X-Ray):**
  - `family09_cylinder_and_sections`: `td_sec_parallel` `0 -> 5,204` px (Normal), `5,248` px (X-ray); `td_sec_axial` `0 -> 14,296` px (Normal), `14,321` px (X-ray).
  - `family10_cone_frustum_cut`: `td_sec_parallel` `0 -> 1,923` px (Normal), `1,996` px (X-ray); `td_sec_axial` `0 -> 11,488` px (Normal), `11,932` px (X-ray).
  - `family11_sphere_plane_cut`: `td_sec_sph` `0 -> 20,762` px (Normal), `20,762` px (X-ray).
  - `family12_cylinder_ellipse_section`: `td_sec_el` `0 -> 13,572` px (Normal), `13,572` px (X-ray).
  - Synthetic opaque-wall probe (`after/measurements.json`): `frontVisibleFillPixels = 5,163`, `occludedVisibleFillPixels = 0` (Normal), `xrayOccludedVisibleFillPixels = 5,163` (X-ray).

---

## 4. Independent Review & Authoritative Full T3 Verification (P9)

- **Product & Test Commit:** `ca84337e32c27c1116f5b1065ca45f2fcdf3e13c`
- **Frozen Candidate Commit:** `7868db0aef3810e2089b5f8b8d6aecfb8b3e1400` (`measured_system.tree_hash = 9bf35a1d6f4c3b3e90228964a3b5ee96288de29efcb3f580f22c6f126489bd9a` across `114` files; `cay_lam_viec_sach = true`)
- **Independent Read-Only Review (`review.md`):** **`INDEPENDENT_REVIEW_PASS`** (`0 BLOCKER, 0 IMPORTANT, 0 MINOR`; reviewer conversation `589da610-17c3-4526-9684-a0d41700ccb0`).
- **Authoritative Full T3 (`t3/execution.json`, `validation.json`):** **`FULL_PRODUCT_GATE_PASS`** on clean detached checkout `verify-geometric-visual-correctness-framing` (`7868db0aef3810e2089b5f8b8d6aecfb8b3e1400`, `dirty_before = ""`, `dirty_after = ""`, `551.88s`):
  - **Backend pytest:** `11,442 passed, 1 skipped, 2 deselected, 9 xfailed` (`536.1s`). (Note: an initial run `t3-attempt1-maxpath/` hit a Windows 260-character `MAX_PATH` limit inside `git add -A` in `test_evaluation_candidate.py` when `PYTEST_DEBUG_TEMPROOT` was nested under the long worktree directory name; preserved intact in `t3-attempt1-maxpath/`, resolved by routing `PYTEST_DEBUG_TEMPROOT` to `.superpowers/pt-<pid>` and `core.longpaths=true` in `record-command.py` without touching product/test code.)
  - **Frontend vitest:** `75/75` files, `1,183/1,183` tests passed (`8.8s`).
  - **TypeScript + Vite production build:** `tsc -b && vite build` `PASS` (`5.1s`).
  - **Thesis demo replay:** `5/5` (`DEMO_REPLAY_PASS 5/5`, `REDUCED_CHAIN_CASES 1/1`, `0.7s`).
  - **Crash boundary surface:** `6/6` (`0` escaped 500s, `0.5s`).
  - **Raw log digests (`t3/`):** `t3/stdout.log` = `29,318` bytes (`sha256: 1d055da75315adfe5d377f82e761a26064b9acbe06d07f0f2a4d753964adf185`), `t3/stderr.log` = `144,823` bytes (`sha256: f9fb4b90d04609956ae4477578ed296ccc1d1d9a6322aa3c6fb6b0abe05a82fe`).
- **Post-T3 Freeze Verification (`post-t3-freeze/execution.json`):** **`MATCH`** (`exit_code = 0`, `dirty_before = ""`, `dirty_after = ""`; `post-t3-freeze/stdout.log` = `93` bytes, `sha256: 6c12d76fd31e4f780cf28cde36a52b49fd17330eb18fda30f704d5820c1e0933`; `post-t3-freeze/stderr.log` = `0` bytes, `sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`).

---

## 5. Remaining Visual Limitations & Governance Boundaries

- Headless Chromium + SwiftShader WebGL measurements and screenshots are deterministic software-rendered evidence, not physical GPU/monitor human sign-off (`human_approval = NOT_GRANTED`).
- Multi-solid CPU edge visibility (`classifySolidEdgeVisibility`) handles polyhedral solids in `localOccluders` with coplanar shared-face exclusion, while curved rim visibility (`diemVanhCongBiChe`) analytically tests quadric volumes (`ball`, `cylinder`, `cone`); general arbitrary mesh-vs-quadric intersection curves remain outside scope.
- Residual polyhedral/frustum 3D solid meshes remain `NOT_IMPLEMENTED`, standalone `cone_frustum` remains `BLOCKED_BY_KERNEL`, and all governance invariants (`DEFAULT_MODE = LLM_ONLY`, `RESPONSE_CONTRACT = flat`, `HYBRID_PRODUCT_ENABLEMENT = NO-GO`, `ALLOW_LIVE_AI = 0`, `CACHE_VERSION = 127`) are unchanged.
- **Proposed Readiness Verdict:** **`GEOMETRIC_VISUAL_CORRECTNESS_READY_FOR_HUMAN_REVIEW`**


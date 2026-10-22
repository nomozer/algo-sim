# OWNER VISUAL FINDINGS — REPRODUCTION & ROOT-CAUSE AUDIT (P1)

- **Campaign:** `ALGOSIM — GEOMETRIC VISUAL CORRECTNESS & ADAPTIVE FRAMING`
- **Authorization:** `GO_GEOMETRIC_VISUAL_CORRECTNESS_LOCAL_ONLY`
- **Source Branch:** `research/visual-ux-final-quality` (`164a5e25ad25bf42d689df115ade5d74b5c733e9`)
- **Candidate Ancestry Verified:** `9343e8d0d4c4cdf5bf0865e0a550c13f238f28b5` (`56328b17462e9c4e903dc17687da07243d06846d` product commit, `43247c9e9375a3dbf2b5223324a58e6f932ca596` verified `main`)
- **Target Branch:** `research/geometric-visual-correctness-framing`
- **Measured Baseline Artifacts:** `docs/evaluation/geometry/runs/geometric-visual-correctness-framing/before/measurements.json` and `before/*.png`

---

## 1. Executive Summary of Reproduced Owner Findings

All seven owner complaints were reproduced in a real Chromium WebGL browser across `1440×900`, `1024×768`, and `820×640` viewports and traced to exact code locations:

| # | Owner Finding | Classification | Affected Scenes | Root Cause |
|---|---|---|---|---|
| **F1** | Several solids are excessively large in the viewport (`76.8%–82.5%` of safe viewport height on `1440×900`, up to `99.9%` with `-10.5px` bottom clipping on orbit) | `CAMERA_OR_INTERACTION_DEFECT` | `family01_triangular_pyramid`, `family05_prism`, `family07_multi_solid_composition` | `scene3d-camera.ts` uses a fixed `TI_LE_LAP_KHUNG = 0.68` tuned for the old `464px`-tall canvas without adapting to projected aspect ratio (`cao/rong`), label margins, or the `729px`-tall simulation-first canvas; in addition, `diemKhungNhin` includes the cutting plane patch `plane3` (`PLANE_PATCH_MARGIN = 1.15`) once constructed, distorting post-step-0 framing. |
| **F2** | Opening `Phân tích toán học` places or clips the model behind the right-side analysis panel on `1024×768` and `820×640` (`panelOverlapPx` up to `23,049 px²` on `1024×768` and `35,426 px²` on `820×640`) | `CAMERA_OR_INTERACTION_DEFECT` | `family01`, `family05`, `family09`, `family11` on `1024×768` and `820×640`; `family05` (`52px` right margin) on `1440×900` | `Scene3DWorkspace` (`vuaKhungRef`) fits around the full canvas center `(w/2, h/2)` and full width `w`, ignoring the open right-side overlay `#geo3d-bang-phan-tich` (`.geo3d-ngan`, `320px` wide). Also `vuaKhungRef` inside `useEffect(..., [])` captures `scene` from initial mount without a `sceneRef`. |
| **F3** | Sphere scene (`family11_sphere_plane_cut`) is under-filled (`42.0%` of canvas height) and its circular section looks like a detached external cap / floating lid with a visible gap between fill and border | `CONFIRMED_RENDER_DEFECT` & `CONFIRMED_PRESENTATION_DEFECT` | `family11_sphere_plane_cut` | (1) `diemHuuHan` in `scene3d-model.ts` (lines 873–881) adds `±r` along all 3 axes simultaneously (`(±r, ±r, ±r)`), inflating the sphere's bounding box by $\sqrt{3} \approx 1.732\times$. (2) `circle3` in `scene3d-view.tsx` (line 1384) sets `bkTo = Math.max(2e-5, trong - day)`, leaving an empty ring gap of width `day` between the section fill disk and the border ring. (3) `SECTION_STROKE_RATIO = 0.014` + heavy section fill (`0.28`) over a low-contrast sphere silhouette makes the cut circle read like an external cap rather than an interior plane intersection. |
| **F4** | Curved-solid borders (`circle3` base rims and `ellipse3` / `circle3` section curves) are visually too thick and show empty fill-to-border gaps | `CONFIRMED_RENDER_DEFECT` | `family09_cylinder_and_sections`, `family10_cone_frustum_cut`, `family11_sphere_plane_cut`, `family12_cylinder_ellipse_section` | `SECTION_STROKE_RATIO = 0.014` in `scene3d-model.ts` (line 792) produces a ribbon width of `1.4%` of scene diameter for both section curves and structural base circles (`duongTronDay`). Furthermore, `circle3` (`bkTo = trong - day`) and `ellipse3` (`mepTo = P - 3*ra`, line 1468) shrink the fill polygon away from the inner border `trong = r - day/2`, leaving an artificial gap ring around every circular and elliptical fill. |
| **F5** | Dashed hidden curves on curved solids look fragmented, polygonal, and inconsistent | `CONFIRMED_RENDER_DEFECT` | `family09_cylinder_and_sections`, `family10_cone_frustum_cut`, `family11_sphere_plane_cut`, `family12_cylinder_ellipse_section` | `circle3` (lines 1414–1425) uses `soNet = VONG_CHIA / 4 = 16` dashes where each dash is `new THREE.RingGeometry(trong, ngoai, 2, 1, i * buoc, buoc / 2)` — only `2` straight chord segments per dash! Similarly, `ellipse3` (lines 1502–1504) uses `VONG_CHIA = 64` and `i % 4 < 2` (16 coarse 2-segment chord dashes) with flat coplanar ribbon geometry that z-fights against curved solid caps/surfaces near grazing angles. |
| **F6** | Demonstration titles do not match actual `Scene3D` labels, and multi-solid scene (`family07_multi_solid_composition`) is difficult to interpret (`D1.ABC`, `D(pyr2)`, collinear nested pyramids along `SA`) | `DATA_OR_SCENE_IDENTITY_MISMATCH` & `CONFIRMED_PRESENTATION_DEFECT` | `family05_prism`, `family07_multi_solid_composition` | **Case A (`family05_prism`):** `build_audit_scenes.py` (line 190) hardcodes `"5. Hình lăng trụ đứng ABC.A'B'C'"` while loading `triangular_prism_positive.json` whose problem text and `Scene3D` construct `ABC.DEF`. **Case B (`family07_multi_solid_composition`):** `build_audit_scenes.py` (line 214) hardcodes `"7. Tổ hợp đa khối (Lăng trụ + Chóp chung mặt EFGH)"` while loading `demo3-multi-solid-shared-geometry` (`S.ABC` + `D.ABC` collinear along `SA`), and `adapter3_simulation.py` (line 1823) emits `obj["notation"] = f"{local_n}({sid})"` (`"D(pyr2)"`) and solid label `"Hình chóp D1.ABC"` leaking internal `solid_id` and canonical symbol `D1` onto the canvas and narration. |
| **F7** | Final construction step banner still instructs the user to click `"Bước sau"` (`"Bấm Phát hoặc Bước sau để dựng hình"`) even though `"Bước sau"` is disabled at the final step | `CAMERA_OR_INTERACTION_DEFECT` | All served scenes (`family01..family12`, `family14`) at `chiSoBuoc === dsBuoc.length - 1` | `Scene3DExplorer.tsx` (lines 528–536) renders static text `"Đang dựng (bước N/N)..."` and `"Bấm Phát hoặc Bước sau để dựng hình · Kéo để xoay hình"` plus `"Xem mô hình đầy đủ"` regardless of whether `chiSoBuoc` has already reached the final step. |

---

## 2. Screen-Space Bounding Rectangle Measurements (`before/measurements.json`)

### 2.1 Desktop `1440×900` (Canvas `1423 × 729`, Safe Viewport `1391 × 697` closed / `1060 × 697` with Analysis Panel open)

| Scene ID | State | Safe Viewport `(x, y, w, h)` | Geometry Bounds `(x, y, w, h)` | Label Bounds `(x, y, w, h)` | Section Bounds `(x, y, w, h)` | Geo Height / Safe | Combined Height / Safe | Top / Bottom Margin (px) | Left / Right Safe Margin (px) | Classification |
|---|---|---|---|---|---|---|---|---|---|---|
| `family01_triangular_pyramid` | Complete (`4/4`) | `(16, 16, 1391, 697)` | `(489.0, 95.3, 444.3, 534.7)` | `(507.5, 91.4, 417.2, 502.3)` | `null` | **76.8%** | **77.3%** | `91.4 / 99.1` | `489.0 / 474.3` | `CAMERA_OR_INTERACTION_DEFECT` (Oversized height > 65%) |
| `family01_triangular_pyramid` | Analysis Open | `(16, 16, 1060, 697)` | `(489.0, 95.3, 444.3, 534.7)` | `(507.5, 91.4, 417.2, 502.3)` | `null` | **76.8%** | **77.3%** | `91.4 / 99.1` | `489.0 / 143.3` | `CAMERA_OR_INTERACTION_DEFECT` |
| `family01_triangular_pyramid` | Orbit | `(16, 16, 1391, 697)` | `(433.4, 255.7, 349.4, 455.7)` | `(447.3, 274.2, 319.8, 411.5)` | `null` | `65.4%` | `65.4%` | `255.7 / 17.6` | `433.4 / 624.9` | `CAMERA_OR_INTERACTION_DEFECT` (Bottom margin `17.6px`) |
| `family05_prism` | Complete (`6/6`) | `(16, 16, 1391, 697)` | `(396.7, 95.3, 627.3, 536.9)` | `(410.5, 91.4, 599.2, 503.1)` | `null` | **77.0%** | **77.6%** | `91.4 / 96.9` | `396.7 / 383.0` | `CAMERA_OR_INTERACTION_DEFECT` & `DATA_OR_SCENE_IDENTITY_MISMATCH` |
| `family05_prism` | Analysis Open | `(16, 16, 1060, 697)` | `(396.7, 95.3, 627.3, 536.9)` | `(410.5, 91.4, 599.2, 503.1)` | `null` | **77.0%** | **77.6%** | `91.4 / 96.9` | `396.7 / 52.0` | `CAMERA_OR_INTERACTION_DEFECT` (Right margin shrinks to `52px`) |
| `family05_prism` | Orbit | `(16, 16, 1391, 697)` | `(418.2, 46.9, 405.9, 692.6)` | `(432.1, 43.0, 378.1, 659.7)` | `null` | **99.4%** | **99.9%** | `43.0 / -10.5` | `418.2 / 582.9` | `CAMERA_OR_INTERACTION_DEFECT` (Clips bottom of canvas by `-10.5px`) |
| `family07_multi_solid_composition` | Complete (`7/7`) | `(16, 16, 1391, 697)` | `(570.8, 73.0, 281.2, 574.9)` | `(596.3, 91.4, 230.3, 512.3)` | `(605.3, 531.1, 212.3, 79.9)` | **82.5%** | **82.5%** | `73.0 / 81.1` | `570.8 / 555.0` | `DATA_OR_SCENE_IDENTITY_MISMATCH` & `CONFIRMED_PRESENTATION_DEFECT` |
| `family09_cylinder_and_sections` | Complete (`12/12`) | `(16, 16, 1391, 697)` | `(524.7, 122.8, 411.8, 430.6)` | `(594.4, 116.9, 232.1, 405.5)` | `(548.0, 142.1, 360.5, 387.5)` | `61.8%` | `62.6%` | `116.9 / 175.6` | `524.7 / 470.5` | `CONFIRMED_RENDER_DEFECT` (Thick rims, fill-border gap, coarse 16-wedge dashes) |
| `family10_cone_frustum_cut` | Complete (`12/12`) | `(16, 16, 1391, 697)` | `(522.8, 102.4, 415.1, 434.9)` | `(594.4, 96.3, 230.9, 404.6)` | `(603.9, 121.5, 240.1, 386.6)` | `62.4%` | `63.3%` | `96.3 / 191.7` | `522.8 / 469.1` | `CONFIRMED_RENDER_DEFECT` (Thick base/section rims, fill-border gap, coarse dashes) |
| `family11_sphere_plane_cut` | Complete (`4/4`) | `(16, 16, 1391, 697)` | `(578.9, 173.6, 301.5, 306.5)` | `(717.3, 308.6, 14.0, 18.0)` | `(588.5, 198.7, 274.1, 113.5)` | **44.0%** | **44.0%** | `173.6 / 248.9` | `578.9 / 526.6` | `CONFIRMED_RENDER_DEFECT` & `CONFIRMED_PRESENTATION_DEFECT` ($\sqrt{3}$ bbox inflation, cap-like section + ring gap) |
| `family12_cylinder_ellipse_section` | Complete (`8/8`) | `(16, 16, 1391, 697)` | `(575.7, 128.7, 290.7, 447.2)` | `(691.5, 143.5, 23.6, 339.2)` | `(575.7, 224.2, 290.7, 152.9)` | `64.1%` | `64.1%` | `128.7 / 153.2` | `575.7 / 540.6` | `CONFIRMED_RENDER_DEFECT` (Thick ellipse ribbon, `3*ra` fill-border gap, 16-segment dashes) |

### 2.2 Responsive Viewports (`1024×768` and `820×640`) with Analysis Panel Closed vs. Open

| Viewport | Scene ID | State | Safe Viewport `(x, y, w, h)` | Combined Bounds `(x, y, w, h)` | Combined Height / Safe | Combined Width / Safe | Right Safe Margin (px) | Panel Overlap (`px²`) | Classification |
|---|---|---|---|---|---|---|---|---|---|
| `1024×768` | `family01_triangular_pyramid` | Panel Open | `(16, 16, 644, 543)` | `(328.0, 70.3, 350.4, 412.4)` | **76.0%** | `54.4%` | **`-18.4px`** | **`2,202 px²`** | `CAMERA_OR_INTERACTION_DEFECT` (Overlaps `#geo3d-bang-phan-tich`) |
| `1024×768` | `family05_prism` | Panel Open | `(16, 16, 644, 543)` | `(260.5, 70.3, 486.0, 413.5)` | **76.2%** | `75.5%` | **`-86.4px`** | **`23,049 px²`** | `CAMERA_OR_INTERACTION_DEFECT` (Model & labels behind panel) |
| `1024×768` | `family09_cylinder_and_sections` | Panel Open | `(16, 16, 644, 543)` | `(350.5, 91.2, 337.3, 347.9)` | `64.1%` | `52.4%` | **`-27.8px`** | **`5,107 px²`** | `CAMERA_OR_INTERACTION_DEFECT` (Overlaps `#geo3d-bang-phan-tich`) |
| `1024×768` | `family11_sphere_plane_cut` | Panel Open | `(16, 16, 644, 543)` | `(394.9, 142.1, 246.9, 241.0)` | `44.4%` | `38.3%` | `18.2px` | `0 px²` | `CAMERA_OR_INTERACTION_DEFECT` (Tight `18.2px` right margin) |
| `820×640` | `family01_triangular_pyramid` | Panel Open | `(16, 16, 440, 415)` | `(267.8, 46.3, 267.0, 327.8)` | **79.0%** | `60.7%` | **`-78.8px`** | **`20,140 px²`** | `CAMERA_OR_INTERACTION_DEFECT` (Overlaps `#geo3d-bang-phan-tich`) |
| `820×640` | `family05_prism` | Panel Open | `(16, 16, 440, 415)` | `(217.4, 46.3, 368.1, 328.6)` | **79.2%** | `83.7%` | **`-129.5px`** | **`35,426 px²`** | `CAMERA_OR_INTERACTION_DEFECT` (Severely hidden behind panel) |
| `820×640` | `family09_cylinder_and_sections` | Panel Open | `(16, 16, 440, 415)` | `(287.0, 61.9, 252.5, 277.4)` | `66.8%` | `57.4%` | **`-83.5px`** | **`19,834 px²`** | `CAMERA_OR_INTERACTION_DEFECT` (Overlaps `#geo3d-bang-phan-tich`) |
| `820×640` | `family11_sphere_plane_cut` | Panel Open | `(16, 16, 440, 415)` | `(320.2, 106.4, 184.9, 187.9)` | `45.3%` | `42.0%` | **`-49.1px`** | **`6,975 px²`** | `CAMERA_OR_INTERACTION_DEFECT` (Overlaps `#geo3d-bang-phan-tich`) |

---

## 3. Detailed Per-Issue Technical Audit

### 3.1 Issue 1 & 2 — Oversized Solids & Analysis Panel Encroachment (`CAMERA_OR_INTERACTION_DEFECT`)
- **Code Locations:**
  - `frontend/src/simulations/domains/geometry/scene3d-camera.ts` (`TI_LE_LAP_KHUNG = 0.68`, `khungNhinVua`, `khungNhinSuPham`)
  - `frontend/src/simulations/domains/geometry/scene3d-model.ts` (`diemHuuHan`, lines 873–881)
  - `frontend/src/simulations/domains/geometry/scene3d-view.tsx` (`diemKhungNhin`, `vuaKhungRef`, lines 942–955 and 2548–2580)
- **Root Causes:**
  1. `TI_LE_LAP_KHUNG = 0.68` in `scene3d-camera.ts` does not account for tall aspect ratios (`cao / rong > 1.35`) or the larger `729px` canvas height, causing `family01`, `family05`, and `family07` to span `76.8%–82.5%` of safe viewport height and clip (`-10.5px`) when orbited.
  2. `diemKhungNhin(goc)` in `scene3d-view.tsx` did not skip `plane3` (`vat.name.startsWith("plane_patch:")` / `vat.name.startsWith("plane_border:")`), so once a cutting plane patch (`PLANE_PATCH_MARGIN = 1.15`) was constructed at later steps, clicking `Đặt lại góc nhìn` included the decorative plane patch in the bounding points.
  3. `diemHuuHan` in `scene3d-model.ts` inflated curved solids by adding unnormalized corner offsets `±u_1*r ± u_2*r ± u_3*r` ($\sqrt{3}r$ for spheres, $\sqrt{2}r$ for cylinders/cones), causing `family11_sphere_plane_cut` to be under-framed at `42.0%` of canvas height.
  4. Opening `#geo3d-bang-phan-tich` (`320px` wide on the right) did not trigger safe-area framing or shift the camera target into the uncovered viewport region, causing up to `35,426 px²` of overlap on `1024×768` and `820×640`.
  5. `vuaKhungRef.current` inside `useEffect(..., [])` referenced `scene.objects` directly instead of via a ref (`sceneRef.current`).

### 3.2 Issue 3 & 4 — Curved-Solid Border Thickness, Fill-to-Border Gap, and Fragmented Dashed Curves (`CONFIRMED_RENDER_DEFECT`)
- **Code Locations:**
  - `frontend/src/simulations/domains/geometry/scene3d-model.ts` (`SECTION_STROKE_RATIO = 0.014`, line 792)
  - `frontend/src/simulations/domains/geometry/scene3d-view.tsx` (`circle3` lines 1362–1430, `ellipse3` lines 1432–1536, `curved_solid` lines 1538–1591)
- **Root Causes:**
  1. `SECTION_STROKE_RATIO = 0.014` makes ribbon strokes overly thick (`1.4%` of scene diameter), and structural base circles (`duongTronDay`) use the same ribbon width as highlighted sections, producing heavy stacked dark rims on cylinders and cones.
  2. In `circle3` (line 1384), `bkTo = Math.max(2e-5, trong - day)` subtracts an extra `day` from `trong = r - day/2`, leaving a transparent gap ring of width `day` between the fill disk and the inner edge of the border ring.
  3. In `ellipse3` (line 1468), `mepTo.push(P.clone().sub(ra.clone().multiplyScalar(3)))` subtracts `3 * (day/2)` instead of `1 * (day/2)`, leaving an even wider transparent gap (`day`) between the elliptical section fill and its border ring.
  4. In `circle3` (lines 1414–1425), the hidden arc is drawn with `soNet = VONG_CHIA / 4 = 16` wedges where each wedge is `new THREE.RingGeometry(trong, ngoai, 2, 1, i * buoc, buoc / 2)` — only `2` straight chord segments per dash! In `ellipse3` (lines 1502–1504), `VONG_CHIA = 64` and `i % 4 < 2` also produces 16 coarse 2-segment chord dashes.

### 3.3 Issue 5 — Sphere Plane Section Looks Like an External Cap (`CONFIRMED_PRESENTATION_DEFECT` & `CONFIRMED_RENDER_DEFECT`)
- **Code Locations:**
  - `frontend/src/simulations/domains/geometry/scene3d-view.tsx` (`circle3` lines 1378–1430, `curved_solid` `ball` lines 1538–1591)
- **Root Causes:**
  1. The combination of the empty gap ring (`bkTo = trong - day`), the overly thick ribbon border (`SECTION_STROKE_RATIO = 0.014`), and high fill opacity (`0.28`) near the top of the sphere makes the circular section `td_sec_sph` look like a detached cap sitting on top of the sphere.
  2. Unlike cylinders and cones (which have structural base circles `duongTronDay` and axis segments to anchor 3D volume perception), the sphere `ball` has only a uniform translucent `SphereGeometry` with no subtle great-circle equator cue or rim definition, making it harder to perceive the sphere body enclosing the interior cut plane in normal mode vs. X-ray mode.

### 3.4 Issue 6 — Multi-Solid Readability & Demo Title / Scene Identity Mismatches (`DATA_OR_SCENE_IDENTITY_MISMATCH` & `CONFIRMED_PRESENTATION_DEFECT`)
- **Code Locations:**
  - `docs/evaluation/geometry/runs/simulation-visual-consistency-learning-ux/build_audit_scenes.py` (lines 189–226)
  - `backend/app/ai/adapter3_simulation.py` (lines 1369–1440, 1812–1825, 2248–2260)
- **Root Causes:**
  1. **Case A (`family05_prism`):** `build_audit_scenes.py` line 190 sets `"category": "5. Hình lăng trụ đứng ABC.A'B'C'"` while loading `triangular_prism_positive.json`, whose `problem_text` (`"Cho hình lăng trụ đứng ABC.DEF có đáy ABC vuông tại A..."`) and `Scene3D` vertices are `A, B, C, D, E, F` (`Lăng trụ đứng ABC.DEF`).
  2. **Case B (`family07_multi_solid_composition`):**
     - `build_audit_scenes.py` line 214 sets `"category": "7. Tổ hợp đa khối (Lăng trụ + Chóp chung mặt EFGH)"` while loading `demo3-multi-solid-shared-geometry.json` (`"Cho hai hình chóp S.ABC và D.ABC có chung mặt đáy ABC..."`).
     - In `adapter3_simulation.py` line 1823, solid-qualified vertex `pyr2::D` (canonical engine symbol `D1`) is assigned `obj["notation"] = f"{local_n}({sid})"` (`"D(pyr2)"`), leaking the internal `solid_id` `pyr2` onto the 3D canvas! Meanwhile, the solid object `khoi_D1_ABC` is labeled `"Hình chóp D1.ABC"` and step narration says `"Dựng hình chóp D1.ABC"` while the final step 7 adds an orphan midpoint `D` on `SA` (`"Đang dựng (bước 7/7): D"`).
     - Visually, `S.ABC` ($SA \perp (ABC), SA = 12$) and `D.ABC` ($DA \perp (ABC), DA = 6$) are nested along the exact same vertical edge $SA$, so one pyramid is completely inside the other and all three lateral faces are coplanar (`SAB`/`DAB`, `SAC`/`DAC`, `ABC`), making it visually indistinguishable as two separate solids.

### 3.5 Issue 7 — Final-Step Banner Guidance Contradiction (`CAMERA_OR_INTERACTION_DEFECT`)
- **Code Locations:**
  - `frontend/src/simulations/domains/geometry/Scene3DExplorer.tsx` (lines 526–538)
- **Root Cause:**
  - At the final construction step (`chiSoBuoc === dsBuoc.length - 1`), the `"Bước sau"` button in the playback bar is disabled (`disabled={chiSoBuoc >= dsBuoc.length - 1}`), yet the top guidance banner still says `"Đang dựng (bước N/N): ..."` and `"Bấm Phát hoặc Bước sau để dựng hình · Kéo để xoay hình"`, and still displays the `"Xem mô hình đầy đủ"` button even though the complete model is already shown.

# SIMULATION VISUAL BASELINE AUDIT (`P1`)

- **Campaign:** `ALGOSIM — SIMULATION VISUAL CONSISTENCY & LEARNING UX`
- **Owner Authorization:** `GO_SIMULATION_VISUAL_CONSISTENCY_LEARNING_UX_LOCAL`
- **Verified Baseline `main`:** `43247c9e9375a3dbf2b5223324a58e6f932ca596`
- **Research Branch:** `research/simulation-visual-consistency-learning-ux`
- **Browser Engine:** Headless Chromium + SwiftShader WebGL (`1440×900` viewport, `1233×495` 3D canvas)
- **Baseline Receipt:** [`browser-baseline/baseline_audit_receipt.json`](browser-baseline/baseline_audit_receipt.json)
- **BEFORE Screenshots:** [`screenshots/before/`](screenshots/before/)

---

## 1. Audited Geometric Families & Baseline Measurements

All 12 required geometric families (13 positive scenes + 1 invalid-geometry refusal scene) were rendered in a real headless Chromium WebGL browser on verified `main` (`43247c9e9375a3dbf2b5223324a58e6f932ca596`):

| Scene ID | Family Covered | Canvas Size | BBox Width × Height (`px`) | Canvas Fill (`W% × H%`) | Primary Objects (`ownPixels > 0`) | Console / Page Errors | BEFORE Screenshots |
|---|---|---|---|---|---|---|---|
| `family01_triangular_pyramid` | Triangular pyramid + perpendicular foot `H` | `1233×495` | `351×359` | `28.5% × 72.5%` | `2/2` (`chop`, `H`) | `0 / 0` | [`family01_triangular_pyramid_default.png`](screenshots/before/family01_triangular_pyramid_default.png), [`_explorer.png`](screenshots/before/family01_triangular_pyramid_explorer.png) |
| `family02_quadrilateral_pyramid` | Quadrilateral pyramid + distance foot `H` | `1233×495` | `460×361` | `37.3% × 72.9%` | `2/2` (`chop`, `H`) | `0 / 0` | [`family02_quadrilateral_pyramid_default.png`](screenshots/before/family02_quadrilateral_pyramid_default.png), [`_explorer.png`](screenshots/before/family02_quadrilateral_pyramid_explorer.png) |
| `family03_regular_pyramid` | Regular quadrilateral pyramid + altitude `SO` + slant `SM` | `1233×495` | `454×360` | `36.8% × 72.7%` | `3/3` (`chop`, `SO`, `SM`) | `0 / 0` | [`family03_regular_pyramid_default.png`](screenshots/before/family03_regular_pyramid_default.png), [`_explorer.png`](screenshots/before/family03_regular_pyramid_explorer.png) |
| `family04_derived_sub_pyramid` | Derived sub-pyramid `S.ABMN` + section `(ABMN)` | `1233×495` | `395×361` | `32.0% × 72.9%` | `2/2` (`k_1`, `td_1`) | `0 / 0` | [`family04_derived_sub_pyramid_default.png`](screenshots/before/family04_derived_sub_pyramid_default.png), [`_explorer.png`](screenshots/before/family04_derived_sub_pyramid_explorer.png) |
| `family05_prism` | Right triangular prism `ABC.A'B'C'` + plane section `(AB'C')` | `1233×495` | `258×360` | `20.9% × 72.7%` | `2/2` (`k_1`, `td_1`) | `0 / 0` | [`family05_prism_default.png`](screenshots/before/family05_prism_default.png), [`_explorer.png`](screenshots/before/family05_prism_explorer.png) |
| `family06a_cube` | Cube `ABCD.A'B'C'D'` + space diagonal `AC'` | `1233×495` | `428×359` | `34.7% × 72.5%` | `2/2` (`lap_phuong`, `ACp`) | `0 / 0` | [`family06a_cube_default.png`](screenshots/before/family06a_cube_default.png), [`_explorer.png`](screenshots/before/family06a_cube_explorer.png) |
| `family06b_cuboid` | Cuboid `ABCD.A'B'C'D'` + diagonal section `(ACC'A')` | `1233×495` | `370×360` | `30.0% × 72.7%` | `2/2` (`hop`, `td_cheo`) | `0 / 0` | [`family06b_cuboid_default.png`](screenshots/before/family06b_cuboid_default.png), [`_explorer.png`](screenshots/before/family06b_cuboid_explorer.png) |
| `family07_multi_solid_composition` | Multi-solid composition (`ABCD.EFGH` + `S.EFGH`) | `1233×495` | `152×360` | `12.3% × 72.7%` | `3/3` (`k_1`, `k_2`, `td_1`) | `0 / 0` | [`family07_multi_solid_composition_default.png`](screenshots/before/family07_multi_solid_composition_default.png), [`_explorer.png`](screenshots/before/family07_multi_solid_composition_explorer.png) |
| `family08_unnamed_section_vertices` | Plane section with unnamed intersection vertices `I1` | `1233×495` | `460×361` | `37.3% × 72.9%` | `3/3` (`k_1`, `td_1`, `I1`) | `0 / 0` | [`family08_unnamed_section_vertices_default.png`](screenshots/before/family08_unnamed_section_vertices_default.png), [`_explorer.png`](screenshots/before/family08_unnamed_section_vertices_explorer.png) |
| `family09_cylinder_and_sections` | Right circular cylinder + axial & parallel circular sections | `1233×495` | `238×227` | `19.3% × 45.9%` | `3/3` (`k_cyl`, `td_sec_axial`, `td_sec_parallel`) | `0 / 0` | [`family09_cylinder_and_sections_default.png`](screenshots/before/family09_cylinder_and_sections_default.png), [`_explorer.png`](screenshots/before/family09_cylinder_and_sections_explorer.png) |
| `family10_cone_frustum_cut` | Right circular cone + parallel circular cut & axial section | `1233×495` | `189×196` | `15.3% × 39.6%` | `3/3` (`k_cone`, `td_sec_cut`, `td_sec_axial`) | `0 / 0` | [`family10_cone_frustum_cut_default.png`](screenshots/before/family10_cone_frustum_cut_default.png), [`_explorer.png`](screenshots/before/family10_cone_frustum_cut_explorer.png) |
| `family11_sphere_plane_cut` | Sphere + plane cut circle `td_sec_sph` | `1233×495` | `179×179` | `14.5% × 36.2%` | `2/2` (`k_sph`, `td_sec_sph`) | `0 / 0` | [`family11_sphere_plane_cut_default.png`](screenshots/before/family11_sphere_plane_cut_default.png), [`_explorer.png`](screenshots/before/family11_sphere_plane_cut_explorer.png) |
| `family12_cylinder_ellipse_section` | Right circular cylinder + oblique plane elliptical section `td_sec_el` | `1233×495` | `204×267` | `16.5% × 53.9%` | `2/2` (`k_cyl`, `td_sec_el`) | `0 / 0` | [`family12_cylinder_ellipse_section_default.png`](screenshots/before/family12_cylinder_ellipse_section_default.png), [`_explorer.png`](screenshots/before/family12_cylinder_ellipse_section_explorer.png) |
| `family13_invalid_geometry_refusal` | Negative invalid sphere cut (`d = 6 > R = 5`) | Refusal | — | — | `scene3d = null` (`TYPED_FACT_NEXT_INCONSISTENT_WITNESS`) | `0 / 0` | Verified fail-closed |

---

## 2. Classified Baseline Defects

### 2.1 `VISUAL_INCONSISTENCY`

1. **`VI-01` — Curved solid surfaces use saturated purple (`0x7c3aed`) instead of the muted slate-blue solid palette (`0x647a96`):**
   - **Evidence:** In `scene3d-view.tsx` lines 1485–1531, `o.render === "curved_solid"` uses `MAU.surface = 0x7c3aed` (`opacity = 0.30` normal, `0.48` highlighted), which is the color of infinite mathematical reference planes (`plane3`), whereas all polyhedral solids (`family01..08`) use muted slate-blue `MAU.mesh = 0x647a96` (`opacity = 0.22` normal, `0.36` highlighted).
   - **Visual Impact:** Cylinders (`family09`, `family12`), cones (`family10`), and spheres (`family11`) look like purple reference planes rather than 3D geometric solids from the same visual design system as pyramids, prisms, and cubes.
2. **`VI-02` — Circular and elliptical cutting sections (`circle3`, `ellipse3`) lack warm amber section fill and section border semantics:**
   - **Evidence:** In `scene3d-view.tsx` lines 1361–1458, `o.render === "circle"` and `o.render === "ellipse"` render exclusively as hollow teal wire loops (`MAU.line = 0x0f766e`) with zero interior polygon fill. By contrast, polyhedral sections (`section` and `polygon3` with `surface_role === "AUXILIARY_SURFACE"`) render with warm amber translucent interior fill (`MAU.polygon = 0xf59e0b`, `opacity = 0.32–0.45`) and two-pass solid/dashed amber borders (`MAU.polygon = 0xf59e0b`).
   - **Visual Impact:** In `family09` (`td_sec_parallel`), `family10` (`td_sec_cut`), `family11` (`td_sec_sph`), and `family12` (`td_sec_el`), circular and elliptical plane sections do not look like sections at all—they appear as thin teal construction loops without interior shading.
3. **`VI-03` — Cylinder and cone structural base circles share the exact same teal auxiliary line color (`0x0f766e`) as cutting sections:**
   - **Evidence:** In `family09`, `family10`, and `family12`, `duong_tron_day_k_cyl`, `duong_tron_day_tren_k_cyl`, and `duong_tron_day_k_cone` are rendered as teal `circle` loops (`MAU.line = 0x0f766e`), visually colliding with `td_sec_parallel`, `td_sec_cut`, and `td_sec_el`. Structural base rims of curved solids should use the structural edge color (`MAU.canh = 0x1e293b`), while cutting-plane sections (`td_sec_*`) should use the section color (`MAU.polygon = 0xf59e0b`) and translucent amber fill.

### 2.2 `GEOMETRIC_VISIBILITY_DEFECT`

1. **`GV-01` — Circular and elliptical sections inside curved solids have no toggleable section fill (`section_fill:<id>`):**
   - **Evidence:** Because `circle` and `ellipse` only create `Line`/`LineSegments` children, `datHienToThietDien` (`section_fill:<id>`) has no effect on circular or elliptical sections in `family09`, `family10`, `family11`, and `family12`.
2. **`GV-02` — Curved solid lateral boundaries lack subtle silhouette/generator structure:**
   - **Evidence:** While polyhedral solids have crisp visible/hidden edge classification (`MAU.canh = 0x1e293b`), curved solids (`CylinderGeometry`, `ConeGeometry`, `SphereGeometry`) render as smooth unlined blobs except for their teal end-cap circles. Adding subtle structural rim/equator clarity and unifying base circles with `MAU.canh` makes curved solid geometry immediately legible.

### 2.3 `CAMERA_FRAMING_DEFECT`

1. **`CF-01` — Curved solid scenes (`family09..12`) occupy only `36.2%–53.9%` of canvas height vs `72.5%–72.9%` for polyhedral scenes:**
   - **Evidence:** Baseline bounding-box measurements in `baseline_audit_receipt.json`:
     - Polyhedral families (`family01..08`): `H% = 72.5%–72.9%` (`359–361 px` out of `495 px`).
     - `family09_cylinder_and_sections`: `238×227 px` (`19.3% × 45.9%`).
     - `family10_cone_frustum_cut`: `189×196 px` (`15.3% × 39.6%`).
     - `family11_sphere_plane_cut`: `179×179 px` (`14.5% × 36.2%`).
     - `family12_cylinder_ellipse_section`: `204×267 px` (`16.5% × 53.9%`).
   - **Root Cause A (`scene3d-view.tsx` line 2513):** `vuaKhungRef.current` checks `ct.canh.length > 0 ? khungNhinSuPham(...) : khungNhinVua(...)`. Because `cauTrucGocNhin` extracts edges only from `solid` and `section` polygons, `ct.canh.length === 0` for all curved-solid scenes, falling back to `khungNhinVua` (which divides the 3D bounding-sphere diagonal radius by `sin(fov/2) * 0.68`, leaving `50–64%` of the canvas height empty).
   - **Root Cause B (`scene3d-model.ts` line 859):** `diemHuuHan` expands `±r` perpendicular to the axis at BOTH `c` (base center) and `dinh` (apex `S`) even when `o.curved_kind === "cone"`, treating the cone's pointed apex as a disk of radius `r` and artificially inflating the top of the bounding box.
2. **`CF-02` — Multi-solid composition (`family07`) selects a narrow `45°` diagonal azimuth (`12.3%` width) where base vertices `B` and `C` project nearly on top of `A`:**
   - **Evidence:** In `family07_multi_solid_composition`, `A=(0,0,0), B=(1,0,0), C=(0,1,0)` and `A, D1(0,0,1), D(0,0,1.5), S(0,0,3)` all lie along the vertical $z$-axis (`SA`). Because `D=(0,0,1.5)` is outside the sub-segment `A-D1` (`[0,0,0]..[0,0,1]`) even though `D` lies on the colinear full edge `A-S` (`[0,0,0]..[0,0,3]`), `khoangDiemDoan3(D, A, D1)` is `0.5 > 0`, so `danhGiaGocNhin` treats `(D, A-D1)` as a non-incident vertex-edge pair and gives `khoangDinhCanhMin = 0` at every viewing angle (`dat = false` across all 216 grid directions). When `dat = false`, `chonHuongNhin` picks `pv = 45°`, looking straight down the $x=y$ symmetry bisector where the prism+pyramid profile is narrowest (`W% = 12.3%`).

### 2.4 `LABEL_READABILITY_DEFECT`

1. **`LR-01` — Curved solid given quantities and auxiliary points receive generic placeholder labels (`"Đại lượng đo"`, `"Điểm"`):**
   - **Evidence:** In `family09`, `family10`, `family11`, and `family12`, step 0 narration reads `"Dữ kiện đề cho: Đại lượng đo = 2, Đại lượng đo = 3."` and `family09` step 6 reads `"Diện tích «Đa giác A, B, điểm, điểm» = 12"` because `_run_curved_route` in `backend/app/ai/adapter3_simulation.py` and `display_names.py` do not assign mathematical notations/labels to `float` parameter objects (`R`, `h`, `R_cat_par`, `R_cat_cone`, `R_cat_sph`) or auxiliary axial points (`A_prime_sec_axial`, `B_prime_sec_axial`, `O_cat_cone_upper`).

### 2.5 `INTERACTION_DEFECT`

1. **`ID-01` — Raycast pick priority (`pick-target.ts`) ties outer `curved_solid` shells with interior `segment3`, `circle3`, and `ellipse3` objects at rank `4`:**
   - **Evidence:** In `frontend/src/simulations/domains/geometry/pick-target.ts` lines 125–128, `HANG_CU_THE` only defines `point3: 0, edge: 1, face: 2, polygon3: 3, line3: 3, plane3: 3, quantity: 4, section: 3, solid: 5`. It omits `segment3`, `circle3`, `ellipse3`, and `curved_solid` (`cylinder`, `cone`, `sphere`), so all of them fall back to default rank `4`. Because the outer `curved_solid` surface is hit first by the camera ray, `chonCuThe` picks the outer `curved_solid` (`k_cyl`, `k_cone`, `k_sph`) instead of interior `segment3` (axis `OO'`, height `SO`, radius `OA`) or interior `circle3` / `ellipse3` sections (`td_sec_parallel`, `td_sec_cut`, `td_sec_sph`, `td_sec_el`).

### 2.6 `INFORMATION_HIERARCHY_DEFECT`

1. **`IH-01` — Default `Scene3DExplorer` mode immediately surfaces final numerical answers (`solution.results` / `MEASURE`) in the bottom bar and floating panels without separating Simulation Mode (Mode A) from Mathematical Analysis Mode (Mode B):**
   - **Evidence:** Look at [`family01_triangular_pyramid_explorer.png`](screenshots/before/family01_triangular_pyramid_explorer.png) through [`family12_cylinder_ellipse_section_explorer.png`](screenshots/before/family12_cylinder_ellipse_section_explorer.png):
     - In `Scene3DExplorer.tsx`, the bottom HUD bar (`chan`) always renders `kq.results` (`"Kết quả: d(A,(SBC)) = 6/7"`, `"Kết quả: V(k_cyl) = 12*pi; S_xq(k_cyl) = 12*pi; S(td_sec_axial) = 12"`) in green badges at the final step by default.
     - In `scene3d-panels.tsx` (`BangLoiGiai`), the `"Lời giải"` floating panel mixes `"Dữ kiện đề cho"` (`given`), `"Các bước dựng"` (`steps`), and `"Kết quả"` (`results`) in a single panel without distinguishing **Mode A — Simulation (Default)** (construction steps, given premises, object identities, and interactive inspection without answer spoilers) from **Mode B — Mathematical Analysis (`"Phân tích toán học"` / `"Xem kết quả"`)** (requested results, derived measurements, exact symbolic values, and mathematical certificates).
     - In `scene3d-annotations.ts` (`nhanSoDoTaiBuoc`), final `MEASURE` result readouts are rendered on the 3D canvas as green answer pills (`vai: "ket_qua"`) even when the user has not requested mathematical analysis.
     - Object kinds and timeline events lack an explicit, machine-verifiable semantic information classification (`GIVEN_DIMENSION`, `GIVEN_RELATION`, `DERIVED_MEASUREMENT`, `CONSTRUCTION_STEP`, `GEOMETRY_IDENTITY`, `REQUESTED_RESULT`, `MATHEMATICAL_CERTIFICATE`, `ERROR_OR_REFUSAL`).

# SIMULATION VISUAL & LEARNING UX — CONTROLLED DEVELOPMENT EVALUATION REPORT

- **Evaluation Classification:** `SIMULATION_VISUAL_UX_DEVELOPMENT_EVALUATION_NOT_BLIND`
- **Holdout Exposure:** `false` (strictly development scenes & thesis/research demos)
- **Live Provider Calls:** `0` (`ALLOW_LIVE_AI = 0`)
- **Baseline Receipt SHA256:** `c2e0a4d7ea1a3cc84114cc0b33bef457e7c4b42d35dcb0d80790389e605156a8`
- **Session 1 Receipt SHA256:** `1a4e275b0cc3da1968306fd55eb21a3b9633f64d0d879820e39beb4d6bd0c1a0`
- **Final Acceptance Receipt SHA256:** `486837f325cc4324d60eefbf0a650105e615fc3a516548d5286d39c7c04569fb`

---

## 1. Automated Verification Summary (10 P11 Dimensions)

| # | Dimension | Passed / Total | Score / Rate | Status |
|---|---|---|---|---|
| 1 | Scene3D structural validity (`validate_geometry_v2` + fail-closed refusal) | `14/14` | `100.00%` | PASS |
| 2 | Primary object presence (`ownPixels > 0` in Chromium WebGL) | `13/13` | `100.00%` | PASS |
| 3 | Section visibility when expected (`SECTION_REGION` / `section` `ownPixels > 0`) | `6/6` | `100.00%` | PASS |
| 4 | Camera framing adequacy (settled, mean primary pixels `65906.3` → `107967.6`) | `13/13` | `100.00%` | PASS |
| 5 | Label collision rate (`0` collisions, `0` raw `_prime`/`_val` leaks) | `0 collisions` | `0.00%` | PASS |
| 6 | Interaction responsiveness (orbit/zoom/pan/select/explode > 0, `resetDiff = 0`) | `13/13` | `100.00%` | PASS |
| 7 | Step progression validity (`stepCount >= 2`, `step0DiffPixels > 0`) | `13/13` | `100.00%` | PASS |
| 8 | Default simulation mode compliance (Mode A hides final answers by default) | `13/13` | `100.00%` | PASS |
| 9 | Mathematical analysis mode availability (`Phân tích toán học` toggle on math scenes) | `13/13` | `100.00%` | PASS |
| 10 | Correct result presentation after explicit reveal (Mode B structured items & formulas) | `13/13` | `100.00%` | PASS |

---

## 2. Per-Scene Automated Metrics (Before vs. Session 1 vs. Final After)

| Scene ID | Family | Served | Primary `ownPixels` (Before → After) | Collisions | `resetDiff` | `step0Diff` | Mode A Compliant | Mode B Categories |
|---|---|---|---:|---:|---:|---:|---|---|
| `family01_triangular_pyramid` | `triangular_pyramid` | `true` | `46,418` → `47,649` | `0` | `0` | `45,862` | `True` | `DERIVED_MEASUREMENT`, `GIVEN_DIMENSION`, `MATHEMATICAL_CERTIFICATE`, `REQUESTED_RESULT` |
| `family02_quadrilateral_pyramid` | `quadrilateral_pyramid` | `true` | `33,570` → `34,136` | `0` | `0` | `33,101` | `True` | `DERIVED_MEASUREMENT`, `GIVEN_DIMENSION`, `REQUESTED_RESULT` |
| `family03_regular_pyramid` | `regular_pyramid` | `true` | `68,986` → `71,728` | `0` | `0` | `68,532` | `True` | `DERIVED_MEASUREMENT`, `GIVEN_DIMENSION`, `REQUESTED_RESULT` |
| `family04_derived_sub_pyramid` | `derived_sub_pyramid` | `true` | `61,810` → `61,810` | `0` | `0` | `53,065` | `True` | `DERIVED_MEASUREMENT`, `MATHEMATICAL_CERTIFICATE`, `REQUESTED_RESULT` |
| `family05_prism` | `prism` | `true` | `105,118` → `105,794` | `0` | `0` | `104,456` | `True` | `DERIVED_MEASUREMENT`, `GIVEN_DIMENSION`, `REQUESTED_RESULT` |
| `family06a_cube` | `cube` | `true` | `81,181` → `81,538` | `0` | `0` | `80,358` | `True` | `DERIVED_MEASUREMENT`, `GIVEN_DIMENSION`, `REQUESTED_RESULT` |
| `family06b_cuboid` | `cuboid` | `true` | `69,913` → `70,841` | `0` | `0` | `69,312` | `True` | `DERIVED_MEASUREMENT`, `GIVEN_DIMENSION`, `REQUESTED_RESULT` |
| `family07_multi_solid_composition` | `multi_solid_composition` | `true` | `17,102` → `17,102` | `0` | `0` | `23,155` | `True` | `MATHEMATICAL_CERTIFICATE`, `REQUESTED_RESULT` |
| `family08_unnamed_section_vertices` | `unnamed_section_vertices` | `true` | `47,117` → `47,117` | `0` | `0` | `43,672` | `True` | `DERIVED_MEASUREMENT`, `MATHEMATICAL_CERTIFICATE`, `REQUESTED_RESULT` |
| `family09_cylinder_and_sections` | `right_circular_cylinder` | `true` | `125,247` → `262,734` | `0` | `0` | `91,044` | `True` | `GIVEN_DIMENSION`, `MATHEMATICAL_CERTIFICATE`, `REQUESTED_RESULT` |
| `family10_cone_frustum_cut` | `right_circular_cone` | `true` | `63,028` → `205,758` | `0` | `0` | `67,482` | `True` | `REQUESTED_RESULT` |
| `family11_sphere_plane_cut` | `sphere` | `true` | `55,011` → `274,093` | `0` | `0` | `89,827` | `True` | `GIVEN_DIMENSION`, `MATHEMATICAL_CERTIFICATE`, `REQUESTED_RESULT` |
| `family12_cylinder_ellipse_section` | `curved_cylinder_ellipse_section` | `true` | `82,281` → `123,279` | `0` | `0` | `60,866` | `True` | `GIVEN_DIMENSION`, `MATHEMATICAL_CERTIFICATE`, `REQUESTED_RESULT` |
| `family13_invalid_geometry_refusal` | `safe_refusal` | `false` (`CURVED_PLANE_DOES_NOT_CUT`) | N/A | N/A | N/A | N/A | Refusal Notice (`UnsupportedNotice`) | `ERROR_OR_REFUSAL` |

---

## 3. Manual Visual Review (Separated from Automated Checks)

All 14 scenes were inspected visually across `screenshots/before/*.png`, `screenshots/session1-after/*.png`, and `screenshots/after/*.png`:

1. **Unified Visual Semantics Across Polyhedra and Curved Solids (`P2`, `P3`):**
   - Polyhedral solids (`family01..family08`) and curved solids (`family09..family12`) share a calm muted slate surface palette (`0x647a96`, opacity `0.22`), crisp visible contours (`0x1e293b`), and two-pass depth-tested dashed hidden contours (`0x64748b`).
   - Curved base circles (`BASE_REGION`) use structural slate border styling with subtle fill (`0.12`), whereas cutting-plane sections (`SECTION_REGION` / `section`) stand out immediately in warm amber (`0xf59e0b` fill at `0.28` opacity, `THU_TU_TO_THIET_DIEN = 7`).
   - Sphere (`family11_sphere_plane_cut`) renders a great-circle horizon ring for 3D curvature comprehension while the cutting-plane circular section `td_sec_sph` (`102,286` `ownPixels`, `2,778` amber pixels) is clearly differentiated in warm amber.
2. **Camera Framing & Canvas Utilization (`P4`):**
   - Using 2D projection fitting (`khungNhinSuPham`) along the canonical viewing direction `[8, 5, 6]` for curved solids (`ct.canh.length === 0`) and tightening `diemHuuHan` for cones (`±r` at base center only, single apex point) and circles increased mean primary object pixels across all 13 served scenes from `65,906.3` to `107,967.6` (`family09_cylinder_and_sections`: `125,247` → `262,734`, `family10_cone_frustum_cut`: `63,028` → `205,758`, `family11_sphere_plane_cut`: `55,011` → `274,093`, `family12_cylinder_ellipse_section`: `82,281` → `123,279`) with zero clipping and deterministic camera reset (`resetDiff = 0`).
3. **Label Notation Hygiene (`P2.F`):**
   - Raw internal variable keys (`A_prime`, `B_prime`, `O_prime`, generic `Đại lượng đo` on `R, h, r`) have been eliminated. Canvas badges now display clean mathematical notation (`R = 3`, `h = 4`, `r = 3/2`, `A′`, `B′`, `O′`) with `0` label collisions across all 13 served scenes.
4. **Simulation-First Default Experience vs. On-Demand Mathematical Analysis (`P6`, `P7`, `P8`, `P10`):**
   - In default Mode A (`*_explorer.png`), the 3D simulation workspace is completely unobstructed (`defaultPanelOpen = false` on all 13 served scenes); only given dimensions (`R = 3, h = 4, r = 3/2`, `AB = 3, AC = 4, SA = 5`, etc.) appear in the step strip/canvas, and final requested answers (`V`, `S_tp`, `V(cone_upper)/V(cone_main)`, `V_con_lai`, etc.) are hidden.
   - Clicking **`Phân tích toán học`** (`*_explorer_mode_b.png`) opens a structured floating panel (`#geo3d-bang-phan-tich`) grouping `Kết quả toán học` (`REQUESTED_RESULT`), `Số đo trung gian` (`DERIVED_MEASUREMENT`), `Kích thước đã cho` (`GIVEN_DIMENSION`), and `Quan hệ & Chứng chỉ kiểm chứng` (`GIVEN_RELATION` & `MATHEMATICAL_CERTIFICATE`), with clickable items that highlight the corresponding 3D geometry.
   - Invalid geometry (`family13_invalid_geometry_refusal_refused.png`) renders `<UnsupportedNotice>` explaining the exact geometric inconsistency (`CURVED_PLANE_DOES_NOT_CUT: mặt phẳng không cắt khối cầu — nó nằm xa tâm hơn bán kính`) with zero blank canvas.

# ALGOSIM — INDEPENDENT MATHEMATICAL CONSTRUCTION AUDIT
## GEMINI 4 ARGON · BACKEND VERIFICATION WORKSTREAM · `research/step-math-validation`

- **Run ID:** `step-math-validation`
- **Branch:** `research/step-math-validation`
- **Worktree:** `.superpowers/worktrees/step-math-validation`
- **Base Commit (`main` / `origin/main`):** `4abc4afbb976babc4740bf22e42dc368a24c1b13`
- **Frozen Backend Composition Commit Audited (Read-Only):** `a629ebee346bf0083cf90294ad352640bcc936ce` (`research/contract-driven-goal-composition`)
- **Frontend In-Flight Worktree Audited for Delta Hazards (Read-Only):** `research/scene3d-plane-grid-camera` (`HEAD = 4abc4afbb976babc4740bf22e42dc368a24c1b13` + active uncommitted working-tree edits by Gemini Session 1 in `Scene3DExplorer.tsx`, `interaction-state.ts`, `scene3d-annotations.ts`, `scene3d-model.ts`, `scene3d-view.tsx`, `global.css`)
- **Live Gemini API Calls:** `0` (`ALLOW_LIVE_AI=0`)
- **Overall Gate Verdict:**
  - **Backend Scene3D Mathematical Construction (`148/148` served scenes, `5,105` checks):** `BACKEND_MATH_CONSTRUCTION_VERIFIED`
  - **Counterexample & Fault-Injection Suite (`P3.1`–`P3.10`):** `10/10_COUNTEREXAMPLES_REPRODUCED_AND_DETECTED`
  - **End-to-End Scene3D Certification Status:** `WAITING_FOR_FRONTEND_FINAL_SNAPSHOT` *(Do NOT claim `FULL SCENE3D MATHEMATICAL PASS` until Gemini Session 1 finalizes and commits `research/scene3d-plane-grid-camera` and its final snapshot is re-verified against `P3.1`–`P3.5`)*

---

## 0. P0 — Safe Preflight & Worktree Isolation

1. **Git Baseline & Active Worktrees Verified:**
   - `main` = `origin/main` = `4abc4afbb976babc4740bf22e42dc368a24c1b13`.
   - Root workspace (`D:\Documents\projects\algo-sim`): untouched (`?? frontend/public/` preserved intact).
   - Frozen backend worktree (`.superpowers/worktrees/contract-driven-goal-composition` @ `a629ebee346bf0083cf90294ad352640bcc936ce`): untouched, read-only inspected.
   - Semantic Extraction v3 worktree (`.superpowers/worktrees/semantic-extraction-v3` @ `5c58774d`): untouched.
   - Frontend Scene3D worktree (`.superpowers/worktrees/scene3d-plane-grid-camera` @ `4abc4afb` + active uncommitted working-tree changes): untouched, read-only inspected for P3/P5 delta hazards; **not** used as an authoritative certification baseline.
2. **Isolated Verification Worktree:**
   - Created `.superpowers/worktrees/step-math-validation` on branch `research/step-math-validation` from `main` (`4abc4afb`).
   - Strictly **zero product code modifications** (`backend/app/**` and `frontend/src/**` are untouched).

---

## 1. P1 — Baseline Scene Catalog Audit (`148` Served Scenes + `6` Refusal Rows)

To prevent any conflation between static UI sample/fixture scenes and backend-compiled scenes, the audit strictly separates:
1. **Group A — Frontend Sample & Fixture Scenes (`13` scenes, `312` mathematical checks)** stored in `frontend/src/`.
2. **Group B — Backend Hybrid Route D & Semantic Program Scenes (`135` served scenes + `6` fail-closed refusal rows, `4,793` mathematical checks)** across 17 backend catalog groups (`112` served scenes on `main` `4abc4afb` + `23` served scenes on frozen `research/contract-driven-goal-composition` `a629ebee`).

### 1.1 Group A — Frontend Sample & Fixture Scenes (`13/13 VERIFIED`, `312` Checks)

All 13 frontend sample/fixture scenes use Euclidean chart metric $G = I_3$ and pass all 11 P2 mathematical categories (`312` individual mathematical checks, `0` coordinate/quantity errors, `0` uncertified `laChieuCao` triggers on static sample IDs).

| # | `scene_id` | Nguồn dữ liệu | Số bước (`events`) | Số kiểm tra (`checks`) | Đối tượng tạo ở từng bước (`objects_by_step`) | Mệnh đề / Hệ thức được biểu diễn (`represented_proposition`) | Kết quả tính toán kỳ vọng (`expected_math_result`) | Kết luận (`verdict`) |
|---|---|---|---:|---:|---|---|---|---|
| 1 | `thiet-dien-chop` | `frontend/src/data/geometry-samples.json` | `11` | `31` | `step_0`: `[]`; `step_1`: `chop`; `step_2`: `M`; `step_3`: `N`; `step_4`: `P`; `step_5`: `mp`; `step_6..10`: `thiet_dien` | `construct_section(chop, mp)` | `4-gon cross-section (thiet_dien)` | `VERIFIED` |
| 2 | `mat-cheo-sac` | `frontend/src/data/geometry-samples.json` | `7` | `21` | `step_0`: `[]`; `step_1`: `chop`; `step_2`: `sac`; `step_3..6`: `thiet_dien` | `construct_section(chop, sac)` | `3-gon cross-section (thiet_dien)` | `VERIFIED` |
| 3 | `vuong-goc-chop` | `frontend/src/data/geometry-samples.json` | `5` | `21` | `step_0`: `[]`; `step_1`: `chop`; `step_2`: `sab`; `step_3`: `bc`; `step_4`: `goc` | Côsin bình phương của góc giữa $BC$ và $(SAB)$ [`measure.angle_cos_sq(bc, sab)`] | `goc = 0` | `VERIFIED` |
| 4 | `mp-vuong-goc-duong` | `frontend/src/data/geometry-samples.json` | `6` | `24` | `step_0`: `[]`; `step_1`: `chop`; `step_2`: `sc`; `step_3`: `mpb`; `step_4`: `day`; `step_5`: `kc` | Khoảng cách giữa $S$ và mặt phẳng qua $B$ vuông góc $SC$ [`measure.distance(S, mpb)`] | `kc = 5√6/3` | `VERIFIED` |
| 5 | `the-tich-chop` | `frontend/src/data/geometry-samples.json` | `5` | `22` | `step_0`: `[]`; `step_1`: `chop`; `step_2`: `day`; `step_3`: `V`; `step_4`: `d` | Thể tích $S.ABCD$ [`measure.volume(chop)`]; Khoảng cách giữa $S$ và $(ABC)$ [`measure.distance(S, day)`] | `V = 16/3; d = 4` | `VERIFIED` |
| 6 | `cau-the-tich` | `frontend/src/data/geometry-samples.json` | `4` | `14` | `step_0`: `[]`; `step_1`: `cau`; `step_2`: `R`; `step_3`: `V` | Bán kính $(S)$ [`measure.radius(cau)`]; Thể tích $(S)$ [`measure.volume(cau)`] | `R = 3; V = 36π` | `VERIFIED` |
| 7 | `cau-cat-mat-phang` | `frontend/src/data/geometry-samples.json` | `6` | `22` | `step_0`: `[]`; `step_1`: `cau`; `step_2`: `P`; `step_3`: `C`; `step_4`: `r`; `step_5`: `S` | Bán kính & diện tích đường tròn giao của khối cầu và $(HUW)$ [`measure.radius(C)`, `measure.area(C)`] | `r = 4; S = 16π` | `VERIFIED` |
| 8 | `tru-truc-xien` | `frontend/src/data/geometry-samples.json` | `5` | `18` | `step_0`: `[]`; `step_1`: `tru`; `step_2`: `V`; `step_3`: `Sxq`; `step_4`: `h` | Thể tích [`measure.volume(tru)`], diện tích xung quanh [`measure.lateral_area(tru)`], chiều cao [`measure.distance(O, O_prime)`] | `V = 15π; Sxq = 6π√5; h = 3` | `VERIFIED` |
| 9 | `tru-thiet-dien-tron` | `frontend/src/data/geometry-samples.json` | `7` | `23` | `step_0`: `[]`; `step_1`: `tru`; `step_2`: `M`; `step_3`: `truc`; `step_4`: `P`; `step_5`: `C`; `step_6`: `r` | Bán kính đường tròn giao của khối trụ và mặt phẳng [`measure.radius(C)`] | `r = 2` | `VERIFIED` |
| 10 | `non-duong-sinh` | `frontend/src/data/geometry-samples.json` | `5` | `18` | `step_0`: `[]`; `step_1`: `non`; `step_2`: `l`; `step_3`: `V`; `step_4`: `Sxq` | Đường sinh $SA$ [`measure.distance(A, S)`], thể tích [`measure.volume(non)`], diện tích xung quanh [`measure.lateral_area(non)`] | `l = 5; V = 12π; Sxq = 15π` | `VERIFIED` |
| 11 | `non-thiet-dien-truc` | `frontend/src/data/geometry-samples.json` | `5` | `17` | `step_0`: `[]`; `step_1`: `non`; `step_2`: `B`; `step_3`: `td`; `step_4`: `Std` | Diện tích thiết diện qua trục $\triangle SAB$ [`measure.area(td)`] | `Std = 12` | `VERIFIED` |
| 12 | `scene3d-section-fixture` | `frontend/src/simulations/domains/geometry/scene3d-section-fixture.json` | `15` | `41` | `step_0`: `[]`; `step_1`: `M`; `step_2`: `d`; `step_3`: `day`; `step_4`: `chop`; `step_5..7`: `P1,P2,P3`; `step_8`: `mp`; `step_9..13`: `td`; `step_14`: `V` | Thiết diện `td` của chóp `chop` với `mp` & Thể tích $S.ABCD$ [`measure.volume(chop)`] | `V = 2/3` | `VERIFIED` |
| 13 | `scene3d-circumsphere-fixture` | `frontend/src/simulations/domains/geometry/scene3d-circumsphere-fixture.json` | `13` | `40` | `step_0`: `[]`; `step_1..2`: `vec_OB,vec_OC`; `step_3`: `A_prime`; `step_4`: `D`; `step_5`: `M`; `step_6`: `circumsphere`; `step_7..10`: `face_*`; `step_11`: `OABC`; `step_12`: `R` | Mặt cầu ngoại tiếp tứ diện vuông $OABC$ tâm $M$, bán kính [`measure.radius(circumsphere)`] | `R = √3` | `VERIFIED` |

---

### 1.2 Group B — Backend Hybrid Route D & Semantic Program Scenes (`135/135 VERIFIED` + `6/6` Refusals, `4,793` Checks)

Across all 17 backend scene catalog groups (`112` served scenes on `main` `4abc4afb` + `23` served scenes on frozen `research/contract-driven-goal-composition` `a629ebee`), `oracle.py` verified every scene's step-by-step construction, Riemannian metric tensor $G = \text{chart\_metric}$, object dependencies, and conclusion quantities (`4,793` checks on Group B scenes, `0` errors):

| # | Backend Catalog / Data Source (`catalog-audit.json`) | Branch / Commit | Served Scenes | Refusal Rows | Checks | Verdict (`oracle.py`) |
|---|---|---|---:|---:|---:|---|
| 1 | `docs/evaluation/geometry/runs/scene3d-visual-correctness/visual/scenes.json` | `main` (`4abc4afb`) | `10` | `1` | `441` | `10/10 VERIFIED` (`+1` refusal) |
| 2 | `docs/evaluation/geometry/runs/goal-directed-section-planning/visual/scenes.json` | `main` (`4abc4afb`) | `11` | `0` | `482` | `11/11 VERIFIED` |
| 3 | `docs/evaluation/geometry/runs/pedagogical-construction-sequencing/visual/scenes.json` | `main` (`4abc4afb`) | `3` | `1` | `198` | `3/3 VERIFIED` (`+1` refusal) |
| 4 | `docs/evaluation/geometry/runs/generalized-goal-entry/visual/scenes.json` | `main` (`4abc4afb`) | `2` | `1` | `68` | `2/2 VERIFIED` (`+1` refusal) |
| 5 | `docs/evaluation/geometry/runs/source-bound-result-planning/visual/scenes.json` | `main` (`4abc4afb`) | `3` | `1` | `150` | `3/3 VERIFIED` (`+1` refusal) |
| 6 | `docs/evaluation/geometry/runs/goal-directed-function-discovery/visual/scenes.json` | `main` (`4abc4afb`) | `5` | `1` | `204` | `5/5 VERIFIED` (`+1` refusal) |
| 7 | `docs/evaluation/geometry/runs/two-line-plane-section/visual/scenes.json` | `main` (`4abc4afb`) | `3` | `1` | `175` | `3/3 VERIFIED` (`+1` refusal) |
| 8 | `docs/evaluation/geometry/runs/hybrid-semantic-hardening/visual/scenes.json` | `main` (`4abc4afb`) | `8` | `0` | `304` | `8/8 VERIFIED` |
| 9 | `docs/evaluation/geometry/runs/hybrid-slice-review/visual/scenes.json` | `main` (`4abc4afb`) | `6` | `0` | `234` | `6/6 VERIFIED` |
| 10 | `docs/evaluation/geometry/runs/geometry-library-expansion/offline-certification/scenes.json` | `main` (`4abc4afb`) | `8` | `0` | `302` | `8/8 VERIFIED` |
| 11 | `docs/evaluation/geometry/runs/ai-function-route/offline/geometry_expansion_cases/scenes/*.json` | `main` (`4abc4afb`) | `5` | `0` | `151` | `5/5 VERIFIED` |
| 12 | `docs/evaluation/geometry/runs/ai-function-route/offline/paraphrase_cases/scenes/*.json` | `main` (`4abc4afb`) | `12` | `0` | `204` | `12/12 VERIFIED` |
| 13 | `docs/evaluation/geometry/runs/ai-function-route/offline/text_to_functions_cases/scenes/*.json` | `main` (`4abc4afb`) | `10` | `0` | `260` | `10/10 VERIFIED` |
| 14 | `docs/evaluation/geometry/runs/hybrid-compiler-selection/offline/scenes/*.json` | `main` (`4abc4afb`) | `16` | `0` | `440` | `16/16 VERIFIED` |
| 15 | `docs/evaluation/geometry/runs/text-to-geometry-functions/offline/scenes/*.json` | `main` (`4abc4afb`) | `10` | `0` | `260` | `10/10 VERIFIED` |
| 16 | `research/contract-driven-goal-composition@a629ebee:corpus.json` (production `positive` + `held_out` + `angle_line_plane_slice_b`) | `research/contract-driven-goal-composition` (`a629ebee`) | `19` | `0` | `751` | `19/19 VERIFIED` |
| 17 | `research/contract-driven-goal-composition@a629ebee:corpus.json (with experimental_centroid_contract)` | `research/contract-driven-goal-composition` (`a629ebee`) | `4` | `0` | `169` | `4/4 VERIFIED` |
| **Subtotal Group B** | **All 17 Backend Catalog Groups** | — | **`135`** | **`6`** | **`4,793`** | **`135/135 VERIFIED`** |
| **Grand Total (A + B)** | **All Frontend + Backend Served Scenes** | — | **`148`** (`13` FE + `135` BE) | **`6`** | **`5,105`** | **`148/148 VERIFIED`** |

Full per-scene step inventories (`objects_by_step`), dependency graphs, propositions (`represented_proposition`), expected results (`expected_math_result`), and per-category check counts for all 148 scenes are recorded in `docs/evaluation/geometry/runs/step-math-validation/catalog-audit.json`.

---

## 2. P2 — Independent Mathematical Construction Oracle (`oracle.py`)

`docs/evaluation/geometry/runs/step-math-validation/oracle.py` (`2,262` lines) is implemented from first principles using **only Python standard library modules** (`__future__`, `ast`, `dataclasses`, `math`, `re`, `typing`) with **zero imports from `app` or `tests`**.

### 2.1 Riemannian Chart Metric Tensor $G = \text{chart\_metric}$ & Coordinate Chart Transformation

Backend Exact Geometry scenes represent coordinates in an affine chart $\mathbb{R}^3$ equipped with a symmetric positive-definite constant metric tensor $G = \text{chart\_metric} \in \mathbb{R}^{3\times 3}$ (defaulting to $I_3$ when omitted, verified positive-definite via Sylvester's criterion $G_{00} > 0, \det G_{[0:2,0:2]} > 0, \det G > 0$):
- **Contravariant displacement vectors** $u = B - A \in \mathbb{R}^3$:
  $$\langle u, v \rangle_G = u^T G v, \qquad \|u\|_G = \sqrt{u^T G u}$$
- **Covariant plane normals** $n \in (\mathbb{R}^3)^*$:
  A plane through $P_0$ with normal covector $n$ has canonical dual pairing:
  $$n^T (X - P_0) = 0$$
  Its metric-dual contravariant normal vector is $n^\sharp = G^{-1} n$, so:
  $$\langle n^\sharp, u \rangle_G = (G^{-1} n)^T G u = n^T u, \qquad \|n\|_{G^{-1}} = \sqrt{n^T G^{-1} n}$$
- **Consistency with Frontend `veKhongGian` (`scene3d-chart.ts:154-205`):**
  `veKhongGian` computes the upper-triangular Cholesky factor $T$ satisfying $T^T T = G$, transforming points as $p_{\text{world}} = T p$ and plane normals as $n_{\text{world}} = T^{-T} n$. Consequently:
  $$(T u)^T (T v) = u^T (T^T T) v = u^T G v, \qquad (T^{-T} n)^T (T(X - P_0)) = n^T T^{-1} T (X - P_0) = n^T (X - P_0)$$
  Thus every incidence, orthogonality, distance, angle, area, and volume invariant verified by `oracle.py` under $G$ is preserved under exact Cholesky world embedding.

### 2.2 Summary of Independent Verification Across All 11 P2 Categories

| Category ID | Mathematical Invariant Verified by `oracle.py` | Scenes Passed | Total Checks | Failures |
|---|---|---:|---:|---:|
| `1_incidence` | Sylvester positive-definiteness of $G$, point-on-line, point-on-segment ($t \in [0,1]$), point-on-plane ($|n^T(P-P_0)|/\|n\|_{G^{-1}} \le 10^{-6}$), non-collinearity of `construct_plane` triples, polygon & solid-face coplanarity, sphere/cylinder/cone/circle incidence | `148 / 148` | `1,901` | `0` |
| `2_midpoint_centroid_ratio` | Midpoint $M = \frac{A+B}{2}$, triangle centroid $G_{\triangle} = \frac{A+B+C}{3}$ (plus non-collinearity), segment division collinearity and parameter $t \in [0,1]$ | `148 / 148` | `87` | `0` |
| `3_orthogonal_projection` | Foot $H = \text{proj}_d(P)$: $H \in d \land \langle P-H, v_d \rangle_G = 0$; Foot $H = \text{proj}_{(\alpha)}(P)$: $H \in (\alpha) \land G(P-H) \parallel n_\alpha$ | `148 / 148` | `24` | `0` |
| `4_intersection` | Line-line intersection ($I \in d_1 \cap d_2$, non-parallel), line-plane intersection ($I \in d \cap (\alpha)$, $n_\alpha^T v_d \neq 0$), plane-plane intersection line, plane-sphere circle radius $r^2 = R^2 - d^2$ under $G^{-1}$ | `148 / 148` | `22` | `0` |
| `5_line_line_perp_parallel` | $d_1 \perp d_2 \iff \frac{|\langle u_1, u_2 \rangle_G|}{\|u_1\|_G \|u_2\|_G} \le 10^{-6}$; $d_1 \parallel d_2 \iff \|u_1 \times u_2\| \le 10^{-6}$ across lines, prism edges, bases, altitudes, and right tetrahedra | `148 / 148` | `368` | `0` |
| `6_line_plane_perp` | $d \perp (\alpha) \iff G u_d \parallel n_\alpha$ and $\langle u_d, P_i - P_0 \rangle_G = 0$ across plane normals, projection altitudes, `perpendicular_witness`, right prisms, pyramid altitudes, and right tetrahedra | `148 / 148` | `140` | `0` |
| `7_angles` | $\cos^2\widehat{(d_1,d_2)} = \frac{\langle u_1,u_2\rangle_G^2}{\|u_1\|_G^2\|u_2\|_G^2}$; $\cos^2\widehat{(d,(\alpha))} = 1 - \frac{(n_\alpha^T u_d)^2}{\|n_\alpha\|_{G^{-1}}^2\|u_d\|_G^2}$; dihedral $\cos^2\widehat{((\alpha),(\beta))} = \frac{(n_\alpha^T G^{-1} n_\beta)^2}{\|n_\alpha\|_{G^{-1}}^2\|n_\beta\|_{G^{-1}}^2}$ | `148 / 148` | `13` | `0` |
| `8_distance_area_volume` | Point/line/plane/skew distances under $G, G^{-1}$; Gram polygon/section area $\frac{1}{2}\sqrt{\det\text{Gram}_G(u,v)}$; tetrahedron/polyhedron volume $\frac{1}{6}\sqrt{\det\text{Gram}_G(u,v,w)}$; sphere/cylinder/cone radius, lateral/surface area, volume | `148 / 148` | `147` | `0` |
| `9_section` | Section $\ge 3$ vertices, cutting-plane incidence, coplanarity, `vertex_sources` (`SOLID_VERTEX` / `SOLID_EDGE_INTERSECTION` with $t \in [0,1]$), exact bijection with solid-edge $\cap$ cutting-plane intersections, and `steps` segment incidence on `faces[face_index]` | `148 / 148` | `24` | `0` |
| `10_step_dependency_ordering` | Every `event.depends` and object dependency is created at `step_index <= current_step`; `formation.steps` never reveal a derived object before its dependencies (`dep_id in vis_set` and `created_at[dep_id] <= created_at[vid]`) | `148 / 148` | `2,078` | `0` |
| `11_conclusion_and_premises` | All `quantities`, `annotation.subject_ids`, and `FINAL_RESULT` references lie inside the forward inductive closure `valid_closure` from `free_objects`, satisfy structural operand alignment, and match expected symbolic/numeric answers | `148 / 148` | `301` | `0` |
| **Total** | **11 Independent Mathematical Categories** | **`148 / 148`** | **`5,105`** | **`0`** |

---

## 3. P3 — 10 Required Counterexample & Fault-Injection Categories (`P3.1`–`P3.10`)

Every required P3 category is implemented deterministically in `oracle.py` (`run_counterexample_suite()`), serialized in `docs/evaluation/geometry/runs/step-math-validation/counterexamples.json`, and verified by parametrized pytest tests in `backend/tests/geometry/test_step_math_validation.py`.

### Summary Table (`10/10` Detected)

| ID | Category (Yêu cầu P3 / `counterexamples.json`) | Target Layer | Detected | Primary Root-Cause / Verifier Location |
|---|---|---|---|---|
| `P3.1` | Mặt phẳng gần ngang nhưng không hoàn toàn ngang (`Nearly horizontal plane`) | Frontend Scene3D + Oracle | `True` | `frontend/src/simulations/domains/geometry/scene3d-model.ts:1049` (`moRongDaGiacMatPhang`: `const ngang = Math.abs(u[2]) > 0.98`) & `scene3d-model.ts:926` (`daGiacMatPhang`: `Math.abs(h) <= 1e-3`) |
| `P3.2` | Mặt phẳng gần đứng (`Nearly vertical plane`) | Frontend Scene3D + Oracle | `True` | `oracle.py` Category `1_incidence` (`|n·(S-P0)|/||n|| = 0.019999 > 1e-6`) + `scene3d-model.ts:996-1042` (`catDaGiacTheoDay`: `zMin` plane clipping) |
| `P3.3` | Đường thẳng nghiêng không vuông góc mặt phẳng (`Oblique line not perpendicular to plane`) | Frontend Scene3D + Oracle | `True` | `frontend/src/simulations/domains/geometry/scene3d-view.tsx:1173-1205` (`buildObject3D` draws two right-angle markers on oblique segment `seg_cao_SA`) + `oracle.py` Category `6_line_plane_perp` & `8_distance_area_volume` |
| `P3.4` | Quan hệ vuông góc chưa được chứng nhận (`Uncertified perpendicularity relation`) | Frontend Scene3D + Oracle | `True` | `frontend/src/simulations/domains/geometry/scene3d-view.tsx:1173` (`const laChieuCao = o.id.includes("cao") \|\| ...` string heuristic without perpendicularity certificate) |
| `P3.5` | Hai dấu góc vuông được dựng từ các hướng đã bị phép chiếu đồ họa chỉnh sửa (`Two right-angle markers from graphically projected directions`) | Frontend Scene3D + Oracle | `True` | `frontend/src/simulations/domains/geometry/scene3d-camera.ts:375-383` (`khungGocVuong`: Gram-Schmidt projection of arbitrary world axis `[1,0,0]`/`[0,1,0]`) |
| `P3.6` | Ba điểm thẳng hàng khi được dùng để xác định mặt phẳng (`Three collinear points used to define a plane`) | Backend Kernel + Oracle Category `1` | `True` | `backend/app/simulation/geometry/kernel.py:194-199` (`Plane3.through` `ERR_THANG_HANG`) & `oracle.py` Category `1_incidence` (`||(P2-P1) x (P3-P1)|| > TOL`) |
| `P3.7` | Thiết diện có đỉnh sai cạnh hoặc sai mặt (`Section with vertex on wrong edge or wrong face`) | Oracle Category `9_section` | `True` | `docs/evaluation/geometry/runs/step-math-validation/oracle.py` (`Category 9`: edge incidence `t in [0,1]`, solid-plane edge bijection, and `steps` `faces[face_index]` incidence) |
| `P3.8` | Điểm trung gian xuất hiện trước khi được dựng (`Intermediate point appearing before it is constructed`) | Oracle Category `10` | `True` | `docs/evaluation/geometry/runs/step-math-validation/oracle.py` (`Category 10`: temporal ordering `created_at[dep] <= step_idx` & `formation.steps` visibility closure) |
| `P3.9` | Bước kết luận sử dụng đối tượng không nằm trong closure phụ thuộc hợp lệ (`Conclusion step using object outside valid dependency closure`) | Oracle Category `11` | `True` | `docs/evaluation/geometry/runs/step-math-validation/oracle.py` (`Category 11`: forward inductive closure `valid_closure` from `free_objects`) |
| `P3.10` | Kết quả tính toán đúng số nhưng biểu diễn sai đối tượng toán học (`Numerically correct result representing wrong mathematical object`) | Backend Registry + Oracle Category `11` | `True` | `docs/evaluation/geometry/runs/step-math-validation/oracle.py` (`Category 11`: `_check_semantic_conclusion_alignment`) & `backend/app/simulation/geometry_functions/registry.py` (`_kiem_result_binding`) |

---

### Detailed Root-Cause Proofs for `P3.1`–`P3.10` (Matched to `counterexamples.json`)

#### `P3.1` — Mặt phẳng gần ngang nhưng không hoàn toàn ngang (`Nearly horizontal plane`)
- **Minimal Input (`counterexamples.json`):**
  Plane through `plane_point = [0, 0, 1]` with `plane_normal = [1, 0, 6]` (`unit_normal_uz = 6 / sqrt(37) ≈ 0.986394`, tilt angle $9.4623^\circ$ from horizontal), and defining points `P0 = [0, 0, 1]`, `P1 = [6, 0, 0]`, `P2 = [0, 2, 1]`.
- **Expected Mathematical Output:**
  All polygon vertices $V = (x,y,z)$ of plane $(x - P_0)\cdot n = 0$ with $n = (1,0,6)$ must satisfy $x + 6(z - 1) = 0$ (`max residual = 0`); non-incident points must not be snapped onto the plane.
- **Actual Erroneous Output:**
  1. In `research/scene3d-plane-grid-camera` snapshot (`frontend/src/simulations/domains/geometry/scene3d-model.ts:1049`), `const ngang = Math.abs(u[2]) > 0.98;` classifies any tilted plane with $|u_z| > 0.98$ (tilt up to $11.48^\circ$) as horizontal (`branch_moRongDaGiacMatPhang_is_horizontal_override = true`). Under constant-$z$ horizontal expansion (`z = 1.0`), the emitted vertices `[-1.2, -1.2, 1.0], [7.2, -1.2, 1.0], [7.2, 3.2, 1.0], [-1.2, 3.2, 1.0]` violate $(V - P_0)\cdot u = 0$ with `branch_max_plane_residual = 1.183673`, and a horizontalized point `P1_horiz = [6, 0, 1]` is rejected by `oracle.py` (`Plane plane_nearly_horiz defining point P1 does not satisfy n.(P-P0)=0 (err=9.864e-01)`). *(Note: Gemini Session 1's active uncommitted working tree on `scene3d-plane-grid-camera` is currently modifying `if (ngang)` in `scene3d-model.ts:1048-1086`, which will be re-verified once Session 1 commits its final snapshot.)*
  2. On `main` (`4abc4afb`, `scene3d-model.ts:926`), `daGiacMatPhang` checks `Math.abs(h) <= 1e-3` across all `diemNen`, snapping non-incident point `Q_non_incident` into the plane polygon.

#### `P3.2` — Mặt phẳng gần đứng (`Nearly vertical plane`)
- **Minimal Input (`counterexamples.json`):**
  Plane through `plane_point = [0, 0, 0]` with `plane_normal = [100, 0, 1]` ($89.43^\circ$ from horizontal, $0.57^\circ$ from vertical) and defining points `A = [0, 0, 0]`, `B = [0, 2, 0]`, and `S_vertical_approx = [0, 0, 2]`.
- **Expected Mathematical Output:**
  For plane $100x + z = 0$, a point at $z = 2$ must have $x = -0.02$; approximating a nearly vertical plane by vertical $x = 0$ leaves residual $|n\cdot(S - P_0)|/\|n\| = 2/\sqrt{10001} \approx 0.019999 > 10^{-6}$ and must be rejected.
- **Actual Erroneous Output:**
  - `oracle.py` Category `1_incidence` rejects the vertical approximation (`Plane plane_nearly_vert defining point S does not satisfy n.(P-P0)=0 (err=2.000e-02)`).
  - In frontend `scene3d-model.ts:996-1042` (`catDaGiacTheoDay`), clipping a nearly vertical plane purely at `zMin = min(diemNen.z)` discards valid lower half-space plane geometry whenever an intersection point lies below `zMin`.

#### `P3.3` — Đường thẳng nghiêng không vuông góc mặt phẳng (`Oblique line not perpendicular to plane`)
- **Minimal Input (`counterexamples.json`):**
  Base $A(0,0,0), B(2,0,0), C(0,2,0)$ in $z = 0$, oblique apex $S(1,1,3)$, segment `seg_cao_SA` from $S$ to claimed foot $A$.
- **Expected Mathematical Output:**
  Vector $\overrightarrow{AS} = (1,1,3)$ is **not** orthogonal to $\overrightarrow{AB} = (2,0,0)$ ($\cos\theta = 1/\sqrt{11} \approx 0.301511 \neq 0$); true foot of $S$ on $(ABC)$ is $H(1,1,0)$ with altitude $h = 3$, and no right-angle marker may be drawn at $A$.
- **Actual Erroneous Output:**
  - Frontend `buildObject3D` (`scene3d-view.tsx:1173-1205` on `main`; `:1180-1213` on `scene3d-plane-grid-camera`) matches `laChieuCao` on `seg_cao_SA` (`frontend_draws_two_right_angle_markers_at_A = true`) and draws two right-angle markers at $A$ tilted out of the base plane (`|e1_z| = 0.2860`).
  - `oracle.py` detects both the frontend hazard (`FE_OBLIQUE_HEIGHT_MARKER`) and rejects the false perpendicular witness (`Quantity q_dist perpendicular_witness (S->A) not G-orthogonal to (A->B) (cos=3.015e-01)` and `value=3.316625 != expected=3.0`).

#### `P3.4` — Quan hệ vuông góc chưa được chứng nhận (`Uncertified perpendicularity relation`)
- **Minimal Input (`counterexamples.json`):**
  Segment `segment_id = "doan_cao_gia"` with `source = "segment_between"` and `perpendicular_witness = null`.
- **Expected Mathematical Output:**
  Right-angle markers must only be rendered when backed by an explicit mathematical certificate (`perpendicular_witness`, `project_point_to_plane`, `altitude_from_to_plane`, or `plane_perpendicular_to_line`), never from substring matching on `o.id` / `o.label` / `o.role`.
- **Actual Erroneous Output:**
  In `frontend/src/simulations/domains/geometry/scene3d-view.tsx:1173` (`main`) and `:1180` (`scene3d-plane-grid-camera`), `const laChieuCao = o.id.includes("cao") || (o.label && /chiều cao/i.test(o.label)) || (o.role && /chiều cao/i.test(o.role));` synthesizes two right-angle markers (`frontend_laChieuCao_triggered = true`), flagged by `oracle.py` as `FE_UNCERTIFIED_HEIGHT_MARKER`.

#### `P3.5` — Hai dấu góc vuông được dựng từ các hướng đã bị phép chiếu đồ họa chỉnh sửa (`Two right-angle markers from graphically projected directions`)
- **Minimal Input (`counterexamples.json`):**
  Foot `chan = [0, 0, 0]`, apex `dinh = [1, 2, 2]` (normal to tilted plane $x + 2y + 2z = 0$), with true plane edges `AB = [2, -1, 0]` and `AC = [0, 2, -2]` lying in that plane.
- **Expected Mathematical Output:**
  Right-angle markers for a line perpendicular to a plane must align their legs with actual constructed rays/edges `(foot -> P_i)` in that plane (as `projectionWitnessesAt` does via `plane_point_ids`), NOT arbitrary Gram-Schmidt projections of world axes `[1,0,0]` / `[0,1,0]`.
- **Actual Erroneous Output (`khungGocVuong` in `scene3d-camera.ts:375-383`):**
  `khungGocVuong(chan, dinh)` projects `truc = [1,0,0]` orthogonal to `d = (1/3, 2/3, 2/3)`, producing `e1 = (0.942809, -0.235702, -0.235702)` and `e2 = (0, 0.707107, -0.707107)`. `e1` misses the true plane edge `AB` with `sin_angle_between_e1_and_AB = 0.316228 != 0` and tilts out of horizontal (`|e1_z| = 0.235702`), pointing into empty space.

#### `P3.6` — Ba điểm thẳng hàng khi được dùng để xác định mặt phẳng (`Three collinear points used to define a plane`)
- **Minimal Input (`counterexamples.json`):**
  Collinear points `A = [0, 0, 0]`, `B = [2, 2, 0]`, `M = [1, 1, 0]` used in `plane_depends = ["A", "B", "M"]`.
- **Expected Mathematical Output:**
  $(B - A) \times (M - A) = (0, 0, 0)$; three collinear points span only a 1D line and leave the plane normal underdetermined. Must fail-closed.
- **Actual Detection (`kernel.py` + `oracle.py` Category `1_incidence`):**
  Backend `Plane3.through(a, b, c)` (`backend/app/simulation/geometry/kernel.py:194-199`) raises `GeometryError(ERR_THANG_HANG, ...)`, and `oracle.py` Category `1_incidence` independently rejects the scene with `Plane plane_ABM constructed from collinear points ['A', 'B', 'M'] (||u x v||=0.000e+00)`.

#### `P3.7` — Thiết diện có đỉnh sai cạnh hoặc sai mặt (`Section with vertex on wrong edge or wrong face`)
- **Minimal Input (`counterexamples.json`):**
  Tetrahedron $S.ABC$ (`A(0,0,0), B(2,0,0), C(0,2,0), S(0,0,2)`) cut by plane `z = 1`, where `sec_bad` replaces true intersection `(0,1,1)` on edge `SC` with `corrupted_section_vertex = [1, 1, 1]` claiming `claimed_edge = ["S", "C"]`, and assigns boundary segment `(0,0,1)->(1,0,1)` to `corrupted_step_face_index = 0` (`ABC`, $z=0$) instead of `face[1]` (`SAB`).
- **Expected Mathematical Output:**
  Reject the off-edge vertex `(1,1,1)`, flag the missed true edge intersection `(0,1,1)`, and reject the boundary segment on `face[0]`.
- **Actual Detection (`oracle.py` Category `9_section`):**
  `oracle.py` flags all four violations:
  - `Section sec_bad vertex (1.0, 1.0, 1.0) does not lie on edge ['S', 'C']`
  - `Section sec_bad vertex[2]=(1.0, 1.0, 1.0) is NOT on any edge of solid solid_SABC`
  - `Section sec_bad missed solid-plane intersection point (0.0, 1.0, 1.0)`
  - `Section sec_bad boundary segment on face[0] has endpoint off-face (da=1.000e+00, db=1.000e+00)`

#### `P3.8` — Điểm trung gian xuất hiện trước khi được dựng (`Intermediate point appearing before it is constructed`)
- **Minimal Input (`counterexamples.json`):**
  `event_0` (`step 0`) creates `seg_CM` depending on `["C", "M"]` before `event_1` (`step 1`) constructs midpoint `M` from `["A", "B"]`, and `formation_step_0_visible_ids = ["A", "B", "C", "seg_CM"]` reveals `seg_CM` before `M`.
- **Expected Mathematical Output:**
  For every event and formation step, every dependency $D$ of an object $X$ must satisfy $t_{\text{create}}(D) \le t_{\text{create}}(X)$ and $D \in \text{visible\_ids}[s]$.
- **Actual Detection (`oracle.py` Category `10_step_dependency_ordering`):**
  `oracle.py` rejects the scene with:
  - `Event e0 (step 0) depends on M which is created later at step 1`
  - `Object seg_CM created at step 0 depends on M created later at step 1`
  - `Formation step[0] (fs0) makes seg_CM visible before its dependency M is visible`

#### `P3.9` — Bước kết luận sử dụng đối tượng không nằm trong closure phụ thuộc hợp lệ (`Conclusion step using object outside valid dependency closure`)
- **Minimal Input (`counterexamples.json`):**
  `free_objects = ["A", "B", "C"]`, `X_dangling` depends on `["A", "Z_ghost"]` (where `Z_ghost` is not in `free_objects`), and conclusion quantity `q_ax` depends on `["A", "X_dangling"]`.
- **Expected Mathematical Output:**
  Every object referenced by a conclusion quantity, `annotation.subject_ids`, or `FINAL_RESULT` step must belong to the forward inductive closure $\mathcal{C}(\text{free\_objects})$.
- **Actual Detection (`oracle.py` Category `11_conclusion_and_premises`):**
  `oracle.py` rejects the scene with:
  - `Conclusion quantity q_ax is outside the valid dependency closure from free_objects (depends=['A', 'X_dangling'])`
  - `Conclusion quantity q_ax annotation subject X_dangling is outside the valid dependency closure`
  - `FINAL_RESULT step fs_final references X_dangling outside valid dependency closure`

#### `P3.10` — Kết quả tính toán đúng số nhưng biểu diễn sai đối tượng toán học (`Numerically correct result representing wrong mathematical object`)
- **Minimal Input (`counterexamples.json`):**
  `A = [0, 0, 0]`, `B = [1, 0, 0]`, `C = [1, 1, 0]` where `||B - A|| = 1` and `||C - B|| = 1`. Quantity `q_wrong_obj` has `quantity_depends = ["A", "B"]` and numerically matching `quantity_value = "1"`, but binds to `claimed_subject_ids = ["C"]`.
- **Expected Mathematical Output:**
  Even when `value = 1` matches numerically, a quantity with `depends = ["A", "B"]` represents $d(A,B)$ and must be rejected when bound to disconnected target `subject_ids = ["C"]`.
- **Actual Detection (`oracle.py` Category `11_conclusion_and_premises` + Backend `registry.py`):**
  `oracle.py` rejects the scene with `Quantity q_wrong_obj annotation subject_ids=['C'] disconnected from mathematical operands depends=['A', 'B']` (matching backend `_kiem_result_binding` in `registry.py`).

---

## 4. P4 & P5 — Worktree Ownership & Frontend Delta Readiness Protocol

### 4.1 Worktree File Ownership (`research/step-math-validation`)
Only verification, oracle, receipt, report, and test files exist in the diff of `research/step-math-validation` from `main` (`4abc4afb`):
- `docs/evaluation/geometry/runs/step-math-validation/oracle.py`
- `docs/evaluation/geometry/runs/step-math-validation/catalog-audit.json`
- `docs/evaluation/geometry/runs/step-math-validation/counterexamples.json`
- `docs/evaluation/geometry/runs/step-math-validation/run.json`
- `docs/evaluation/geometry/runs/step-math-validation/report.md`
- `backend/scripts/audit_step_math_validation.py`
- `backend/tests/geometry/test_step_math_validation.py`

### 4.2 Frontend Delta Readiness (`WAITING_FOR_FRONTEND_FINAL_SNAPSHOT`)
Because Gemini Session 1 is still actively modifying `.superpowers/worktrees/scene3d-plane-grid-camera` (currently at `HEAD = 4abc4afb` with uncommitted working-tree changes in `Scene3DExplorer.tsx`, `interaction-state.ts`, `scene3d-annotations.ts`, `scene3d-model.ts`, `scene3d-view.tsx`, and `global.css`), **this audit does not certify the in-flight frontend worktree as final**.

Once Gemini Session 1 finishes and freezes a final commit SHA on `research/scene3d-plane-grid-camera`, the following delta verification checklist must pass before claiming `FULL SCENE3D MATHEMATICAL PASS`:
1. **Plane Polygon Tilt Fidelity (`P3.1`):**
   - Verify the final committed implementation of `moRongDaGiacMatPhang` in `scene3d-model.ts` so tilted planes with $0.98 < |u_z| < 1$ are expanded along tangent basis vectors $(e_1, e_2)$ orthogonal to $u$, satisfying $|(V - P_0)\cdot u| \le 10^{-6}$ for every vertex $V$.
   - In `daGiacMatPhang`, ensure point-on-plane incidence uses a strict mathematical tolerance rather than snapping arbitrary scene points within `1e-3`.
2. **Nearly Vertical / Half-Space Plane Clipping (`P3.2`):**
   - Verify whether `catDaGiacTheoDay` (`z >= zMin - 1e-4`) in `scene3d-model.ts` is restricted only to auxiliary base planes or if it clips general analytic/section planes that legitimately extend below `zMin`.
3. **Certified Right-Angle Markers (`P3.3`, `P3.4`, `P3.5`):**
   - Replace the uncertified string heuristic `laChieuCao` (`o.id.includes("cao")` / `role="Chiều cao"`) in `scene3d-view.tsx` and the arbitrary world-axis projection `khungGocVuong` in `scene3d-camera.ts` with certificate-driven right-angle markers (`perpendicular_witness` or verified orthogonal edges incident to the foot point).
4. **Re-run Automated Audit & Pytest:**
   - Run `python backend/scripts/audit_step_math_validation.py` and `pytest backend/tests/geometry/test_step_math_validation.py -v` against the final frontend commit SHA.

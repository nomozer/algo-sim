# Post-Merge Case Identity & Evidence Adjudication Addendum — `HYBRID_V2_W2_M5_POSTMERGE_CASE_IDENTITY_ADJUDICATION`

- **Addendum Wave ID:** `HYBRID_V2_W2_M5_POSTMERGE_CASE_IDENTITY_ADJUDICATION`
- **Corrects Wave ID:** `HYBRID_V2_W2_M5_ADAPTER4_CATEGORY_A_IDENTITY_REPAIR` (and post-merge conversational report errata from `HYBRID_V2_W2_M5_ADAPTER4_MAIN_INTEGRATION`)
- **Isolated Documentation Branch:** `docs/hybrid-v2-w2-m5-postmerge-case-identity-adjudication`
- **Isolated Worktree:** `.superpowers/worktrees/w2-m5-postmerge-case-identity-adjudication`
- **Authoritative `main = origin/main = remote`:** `2c42f6cf23ddde89cc752e0ee6dfec6e4e230d3b`
- **Frozen Full T3 Candidate:** `b61f16995dfbe0110a639a2127d0fb5a9c3afde0`
- **Product Commit:** `73ca8d92e74059680ce53b99692af396df37a2f8` (`backend/app/ai/adapter4_route.py` only)
- **Measured Product Tree (`118` files):** `1170ca163529dd40b57f4058826db92a6433359546aa2ad718712f38a538c10d` (`MATCH`)
- **Historical Holdout Wave 2 Commit:** `ecdc26b012c8ce80d53524a98dc75cdcb020079d` (`0` bytes changed)
- **Machine Adjudication Receipt:** [`results/postmerge-case-identity-adjudication.json`](results/postmerge-case-identity-adjudication.json)
- **Independent Review Receipt:** [`review-postmerge-adjudication.md`](review-postmerge-adjudication.md)
- **Final Adjudication Status:** `EVIDENCE_CORRECTION_REQUIRED` (`product_regression_found = false`)

---

## 1. Scope & Non-Destructive Preservation Rule

This additive correction addendum resolves all discrepancies between (a) the post-merge conversational summary emitted after context compaction, (b) narrative prose in [`report.md`](report.md), [`handoff.md`](handoff.md), and [`baseline-audit.md`](baseline-audit.md), (c) frozen Independent Holdout Wave 2 (`ecdc26b012c8ce80d53524a98dc75cdcb020079d`), and (d) actual product execution on GitHub `main` (`2c42f6cf23ddde89cc752e0ee6dfec6e4e230d3b`):

1. **Zero Product Regression or Code Diff:** `git diff --name-only b61f16995dfbe0110a639a2127d0fb5a9c3afde0..HEAD -- backend/app frontend/src` is empty (`0` files). `freeze_evaluation_candidate.py --verify` returns `MATCH` (`118` files, `1170ca163529dd40b57f4058826db92a6433359546aa2ad718712f38a538c10d`).
2. **Historical & Committed Artifacts Preserved Byte-for-Byte:** All files in `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/` (`ecdc26b0`) and all original committed files in `docs/evaluation/geometry/runs/hybrid-v2-w2-m5-adapter4-category-a-identity-repair/` at `2c42f6cf` ([`report.md`](report.md), [`handoff.md`](handoff.md), [`review.md`](review.md), [`run.json`](run.json), [`baseline-audit.md`](baseline-audit.md), [`architecture-decision.md`](architecture-decision.md), [`plan.md`](plan.md), [`inputs/development.json`](inputs/development.json), [`inputs/oracle.json`](inputs/oracle.json), [`results/red-before.json`](results/red-before.json), [`results/green-after.json`](results/green-after.json), [`results/tamper-results.json`](results/tamper-results.json), [`results/wave2-post-feedback-regression.json`](results/wave2-post-feedback-regression.json), [`results/w2-a10-scorer-adjudication-receipt.json`](results/w2-a10-scorer-adjudication-receipt.json), [`verification/scope-and-evidence.json`](verification/scope-and-evidence.json), [`verification/full-t3/receipt.json`](verification/full-t3/receipt.json), [`verification/full-t3/full-t3.log`](verification/full-t3/full-t3.log)) remain **100% byte-identical**.

---

## 2. Section 2 Audit — `W2-A07` Complete 9-Item Identity Verification

### 2.1 Nine-Item Trace from Frozen `inputs/holdout-wave2.json` to Product Response

1. **Problem text (`inputs/holdout-wave2.json`, LF SHA-256 `1104be2ad8d4c5c96363f3648bc3c57dfcef5af4334c714e9cc94fc466f38e2d`):**
   > *"Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại B, AB = 5, BC = 5 và cạnh bên AA' = 10. Mặt phẳng (α) đi qua điểm A' và vuông góc với đường thẳng AC', cắt các cạnh bên BB', CC' lần lượt tại M, N. Tính diện tích thiết diện của hình lăng trụ đứng ABC.A'B'C' cắt bởi mặt phẳng (α)."*
2. **TypedFactNext payload (`typed-fact-next/2`, canonical SHA-256 `ed8f11b8aa49478ee62bd6ce8c4a7e29e86865c336f5cd880edabbd2f3e23142`, canonical case SHA-256 `717ee585a0411ec67e2045ee4f71beb217088a0264eb649399bb4386d7999e73`):**
   - `length_unit`: `"1"`
   - `solids`: `[{"solid_id": "s1", "solid_type": "prism", "notation": "ABC.A'B'C'"}]`
   - `premises`: `right_prism(base=["A","B","C"], top=["A'","B'","C'"])`, `right_angle(vertices=["A","B","C"], right_at="B")`, `segment_length(AB="5")`, `segment_length(BC="5")`, `segment_length(AA'="10")`
   - `derived_sections`: `[{"section_id": "sec", "plane_name": "α", "target_solid_id": "s1", "plane_kind": "through_point_perpendicular_line", "through_point": "A'", "perpendicular_line": ["A", "C'"], "stated_intersections": [{"edge": ["B", "B'"], "point": "M"}, {"edge": ["C", "C'"], "point": "N"}]}]`
   - `math_goals`: `[{"goal_id": "mg1", "kind": "measurement", "goal_type": "area", "solid_id": "s1", "target": {"section_id": "sec"}}]`
3. **Solid topology:**
   - Right triangular prism `ABC.A'B'C'` (`khoi_ABC_A_primeB_primeC_prime`), 6 vertices `(A, B, C, A_prime, B_prime, C_prime)` at indices `0..5`, 5 faces `((0,1,2), (3,4,5), (0,1,4,3), (1,2,5,4), (2,0,3,5))`, 9 edges (`AB`, `BC`, `CA`, `A'B'`, `B'C'`, `C'A'`, `AA'`, `BB'`, `CC'`).
4. **Planner result (`geometry-fact-planner/17`):**
   - Emits calls `s1 (prism)`, `p2 (right_angle)`, `p3..p5 (segment_length)`, `sec_perp1_foot (H = proj(B, AC'))`, `sec_perp2_foot (H1 = proj(C, AC'))`, `sec_perp1 (H2 = A' + HB)`, `sec_perp2 (H3 = A' + H1C)`, `sec (section on plane [A', H2, H3])`, `sec_cut2 (intersect_line_plane M on BB')`, `sec_cut3 (intersect_line_plane N on CC')`, `mg1 (ask_section_area)`.
   - Emits Category A (`DINH_CAT_CANH`) auxiliary record (`rule = "section vertices on the stated cut edges of a derived plane"`, `vertices = [{"edge": ["A", "A'"], "label": "A'", "choice": "reuse_through_point", "stated": false}, {"edge": ["B", "B'"], "label": "M", "choice": "named_intersection", "stated": true}, {"edge": ["C", "C'"], "label": "N", "choice": "named_intersection", "stated": true}]`).
5. **Engine section (`geometry-function-engine/14`):**
   - `final_memory["td_sec"]`: `Section(polygon=(Vec3(1, 0, 3/4), Vec3(0, 0, 1), Vec3(0, 1, 1/2)))` in normalized unit prism coordinates (`A=(0,0,0), B=(1,0,0), C=(0,1,0), A'=(0,0,1), B'=(1,0,1), C'=(0,1,1)`), with `vertex_sources = (SOLID_EDGE_INTERSECTION(1,4), SOLID_VERTEX(3), SOLID_EDGE_INTERSECTION(2,5))` corresponding to cycle `[M, A', N]`.
   - `final_memory["kq_mg1"]`: `Radical(he=Fraction(25, 4), can=6, mu=0)` (`"25√6/4"`), `_binh_phuong(kq_mg1) = Fraction(1875, 8)`.
6. **Adapter response (`hybrid-simulation-adapter/4`):**
   - `route_d.status == "SERVED"`, `envelope.status == "ok"`, `route_d.answers == {"mg1": "25√6/4"}`.
7. **Scene3D polygon (`scene3d.objects["td_sec"]`):**
   - `id = "td_sec"`, `label = "Thiết diện MA′N"`, `notation = "MA′N"`, `polygon = [["1", "0", "3/4"], ["0", "0", "1"], ["0", "1", "1/2"]]` (`[M, A', N]` in normalized prism coordinates).
   - Point objects: `A_prime` (`notation = "A′"`, `xyz = ["0", "0", "1"]`), `M` (`notation = "M"`, `xyz = ["1", "0", "3/4"]`), `N` (`notation = "N"`, `xyz = ["0", "1", "1/2"]`).
8. **Category A certificate (`route_d.sections[0]`):**
   - `section_id = "sec"`, `boundary = null`, `closure_certificate = null`, `declared_boundary = null`, `vertices = [{"label": "A'", "edge": ["A", "A'"], "provenance": "THROUGH_POINT_REUSE", "stated": false}, {"label": "M", "edge": ["B", "B'"], "provenance": "SOURCE_NAMED", "stated": true}, {"label": "N", "edge": ["C", "C'"], "provenance": "SOURCE_NAMED", "stated": true}]`.
9. **Independent oracle (`oracle/geometry.json` & `oracle/expected.json`):**
   - In Euclidean coordinates $A=(0,0,0), B=(5,0,0), C=(5,5,0), A'=(0,0,10), B'=(5,0,10), C'=(5,5,10)$, plane $(\alpha)$ through $A'(0,0,10) \perp \overrightarrow{AC'}=(5,5,10)$ has equation $x + y + 2z = 20$, cutting $BB'$ at $M=(5,0,15/2)$ ($t = 3/4$) and $CC'$ at $N=(5,5,5)$ ($t = 1/2$).
   - Cross product $\overrightarrow{A'M} \times \overrightarrow{A'N} = (5, 0, -5/2) \times (5, 5, -5) = (25/2, 25/2, 25)$, giving $\text{area\_squared} = \frac{1}{4}(625/4 + 625/4 + 625) = \frac{1875}{8}$ and $\text{area} = \frac{25\sqrt{6}}{4}$.
   - Canonical boundary descriptors: Product cycle `[("EDGE", "B", "B'", "3/4"), ("VERTEX", "A'"), ("EDGE", "C", "C'", "1/2")]` (`[M, A', N]`) is the reversal (`shift = 1` of reversed list) of the oracle cycle `[("VERTEX", "A'"), ("EDGE", "B", "B'", "3/4"), ("EDGE", "C", "C'", "1/2")]` (`[A', M, N]`) — **exact cyclic equivalence (`True`)**.

### 2.2 Classification of `(A, B, C, A′)` / `section_37467f986437 (A, B, C, A′)` and `report.md:32`

- **Conversational post-merge report string `section_37467f986437 (A, B, C, A′)` (`POSTMERGE-CHAT-1`):**
  - **Classification:** **Lỗi ghi báo cáo hội thoại (`REPORT_RECORDING_ERROR_CONVERSATIONAL_ONLY`)**.
  - **Proof:** Immediately after step `9928` (`e2e_main_smoke: PASS`, which printed only `status`, `answer`, `area_squared`, and `notation_A_prime`), conversation compaction fired at step `9929` and fabricated `section_37467f986437 (A, B, C, A′)` in `<CONTEXT_SUMMARY>`, which step `9930` echoed in chat. Geometrically, $(A, B, C, A')$ are the 4 non-coplanar vertices of a tetrahedron, not a planar section. Full-repository `git grep` at `2c42f6cf` confirms **zero (`0`) occurrences** of `37467f986437` or `(A, B, C, A′)` across all product files, test files, preview fixtures, and evaluation runs.
- **Committed narrative prose in [`report.md:32`](report.md#L32) and [`baseline-audit.md:74–77`](baseline-audit.md#L74-L77) (`W2-M5-DOC-1`):**
  - `report.md:32` wrote illustrative coordinates `polygon_A_prime_M_N with exact coordinates A' = [0, 0, 5], M = [6, 0, 15/4], N = [0, 6, 5/2]`, and `baseline-audit.md:77` wrote `id = "td_alpha_ABC_A_prime_B_prime_C_prime"` with Euclidean coordinates `[0.0, 0.0, 10.0], [5.0, 0.0, 7.5], [5.0, 5.0, 5.0]`.
  - **Authoritative correction:** In actual product execution, the section object in `scene3d.objects` is `id = "td_sec"` (`label = "Thiết diện MA′N"`, `notation = "MA′N"`) with normalized prism coordinates `polygon = [["1", "0", "3/4"], ["0", "0", "1"], ["0", "1", "1/2"]]` (`[M, A', N]`) and Euclidean oracle coordinates `M = [5, 0, 15/2]`, `A' = [0, 0, 10]`, `N = [5, 5, 5]`.

---

## 3. Section 3 Audit — `W2-A10` Complete 9-Item Identity & Cyclic Equivalence Verification

### 3.1 Nine-Item Trace from Frozen `inputs/holdout-wave2.json` to Product Response

1. **Problem text (`inputs/holdout-wave2.json`):**
   > *"Cho hình hộp chữ nhật ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật với AB = 3a, AD = 6a và cạnh bên AA' = 9a. Mặt phẳng (Q) đi qua điểm A' và vuông góc với đường thẳng AC', cắt các cạnh bên BB', CC', DD'. Xác định thiết diện của hình hộp chữ nhật ABCD.A'B'C'D' cắt bởi mặt phẳng (Q)."*
2. **TypedFactNext payload (`typed-fact-next/2`, canonical SHA-256 `922e49a272dd8a3836c52792d8ee60e8e5156a34ee4c895a25df8610b7feb85d`, canonical case SHA-256 `3f1d5a6142b34b715032aca475ae7e97322b88c7bb08b1e2b077b2d11ec1b88a`):**
   - `length_unit`: `"a"`, `family`: `"cuboid"`, `question_type`: `"section_only"`
   - `solids`: `[{"solid_id": "s1", "solid_type": "prism", "notation": "ABCD.A'B'C'D'"}]`
   - `premises`: `right_prism(base=["A","B","C","D"], top=["A'","B'","C'","D'"])`, `rectangle(vertices=["A","B","C","D"])`, `segment_length(AB="3a")`, `segment_length(AD="6a")`, `segment_length(AA'="9a")`
   - `derived_sections`: `[{"section_id": "sec", "plane_name": "Q", "target_solid_id": "s1", "plane_kind": "through_point_perpendicular_line", "through_point": "A'", "perpendicular_line": ["A", "C'"], "stated_intersections": [{"edge": ["B", "B'"], "point": null}, {"edge": ["C", "C'"], "point": null}, {"edge": ["D", "D'"], "point": null}]}]`
   - `math_goals`: `[]`
3. **Solid topology:**
   - Rectangular cuboid (`hình hộp chữ nhật`) `ABCD.A'B'C'D'` (`khoi_ABCD_A_primeB_primeC_primeD_prime`), 8 vertices `(A, B, C, D, A_prime, B_prime, C_prime, D_prime)` at indices `0..7`, 6 faces `((0,1,2,3), (4,5,6,7), (0,1,5,4), (1,2,6,5), (2,3,7,6), (3,0,4,7))`, 12 edges.
4. **Planner result (`geometry-fact-planner/17`):**
   - Emits calls `s1 (prism)`, `p2 (rectangle)`, `p3..p5 (segment_length)`, `sec_perp1_foot (H)`, `sec_perp2_foot (H1)`, `sec_perp1 (H2)`, `sec_perp2 (H3)`, `sec (section on plane [A', H2, H3])`, `sec_cut2 (intersect_line_plane I on BB')`, `sec_cut3 (intersect_line_plane I1 on CC')`, `sec_cut4 (intersect_line_plane I2 on DD')`.
   - Emits Category A (`DINH_CAT_CANH`) auxiliary record with 4 vertices: `A'` on `AA'` (`reuse_through_point`, `stated = false`), `I` on `BB'` (`fresh_intersection`, `stated = true`), `I1` on `CC'` (`fresh_intersection`, `stated = true`), `I2` on `DD'` (`fresh_intersection`, `stated = true`).
5. **Engine section (`geometry-function-engine/14`):**
   - `final_memory["td_sec"]`: `Section(polygon=(Vec3(1, 0, 8/9), Vec3(0, 0, 1), Vec3(0, 1, 5/9), Vec3(1, 1, 4/9)))` in normalized unit prism coordinates, with `vertex_sources = (SOLID_EDGE_INTERSECTION(1,5), SOLID_VERTEX(4), SOLID_EDGE_INTERSECTION(3,7), SOLID_EDGE_INTERSECTION(2,6))` corresponding to 4-vertex cycle `[I, A', I2, I1]`.
6. **Adapter response (`hybrid-simulation-adapter/4`):**
   - `route_d.status == "SERVED"`, `envelope.status == "ok"`, `route_d.answers == {}`.
7. **Scene3D polygon (`scene3d.objects["td_sec"]`):**
   - `id = "td_sec"`, `label = "Thiết diện bởi (Q)"`, `notation = null`, `polygon = [["1", "0", "8/9"], ["0", "0", "1"], ["0", "1", "5/9"], ["1", "1", "4/9"]]` (`[I, A', I2, I1]`).
   - Point objects: `A_prime` (`notation = "A′"`, `xyz = ["0", "0", "1"]`), `I` (`notation = null`, `xyz = ["1", "0", "8/9"]`), `I1` (`notation = null`, `xyz = ["1", "1", "4/9"]`), `I2` (`notation = null`, `xyz = ["0", "1", "5/9"]`).
8. **Category A certificate (`route_d.sections[0]`):**
   - `section_id = "sec"`, `boundary = null`, `closure_certificate = null`, `declared_boundary = null`, `vertices = [{"label": "A'", "edge": ["A", "A'"], "provenance": "THROUGH_POINT_REUSE", "stated": false}, {"label": "I", "edge": ["B", "B'"], "provenance": "STATED_UNNAMED", "stated": true}, {"label": "I1", "edge": ["C", "C'"], "provenance": "STATED_UNNAMED", "stated": true}, {"label": "I2", "edge": ["D", "D'"], "provenance": "STATED_UNNAMED", "stated": true}]`.
9. **Independent oracle & Exact `Fraction` Cyclic Equivalence Proof:**
   - In Euclidean coordinates ($a = 1$): $A=(0,0,0), B=(3,0,0), C=(3,6,0), D=(0,6,0), A'=(0,0,9), B'=(3,0,9), C'=(3,6,9), D'=(0,6,9)$.
   - Plane $(Q)$ through $A'(0,0,9) \perp \overrightarrow{AC'}=(3,6,9)$ has equation $x + 2y + 3z = 27$, cutting:
     - $BB'$ ($x=3, y=0$) at $z = 8 \implies t_{BB'} = \text{Fraction}(8, 9)$, $I = (3, 0, 8)$
     - $CC'$ ($x=3, y=6$) at $z = 4 \implies t_{CC'} = \text{Fraction}(4, 9)$, $I_1 = (3, 6, 4)$
     - $DD'$ ($x=0, y=6$) at $z = 5 \implies t_{DD'} = \text{Fraction}(5, 9)$, $I_2 = (0, 6, 5)$
   - Parallelogram sides $\vec{u} = I - A' = (3, 0, -1)$ and $\vec{v} = I_2 - A' = (0, 6, -4)$ have cross product $\vec{u} \times \vec{v} = (6, 12, 18)$ and exact Euclidean area squared:
     $$\text{area\_squared} = 6^2 + 12^2 + 18^2 = 36 + 144 + 324 = 504$$
   - **Canonical Boundary Descriptor Cyclic Equivalence (`Fraction`):**
     - Product `td_sec.polygon` cycle (`[I, A', I2, I1]`):
       $$P = \left[(\text{EDGE}, B, B', \tfrac{8}{9}),\ (\text{VERTEX}, A'),\ (\text{EDGE}, D, D', \tfrac{5}{9}),\ (\text{EDGE}, C, C', \tfrac{4}{9})\right]$$
     - Oracle boundary cycle (`oracle/expected.json`):
       $$O = \left[(\text{VERTEX}, A'),\ (\text{EDGE}, B, B', \tfrac{8}{9}),\ (\text{EDGE}, C, C', \tfrac{4}{9}),\ (\text{EDGE}, D, D', \tfrac{5}{9})\right]$$
     - Reversing $P$ gives $P^{\text{rev}} = \left[(\text{EDGE}, C, C', \tfrac{4}{9}),\ (\text{EDGE}, D, D', \tfrac{5}{9}),\ (\text{VERTEX}, A'),\ (\text{EDGE}, B, B', \tfrac{8}{9})\right]$, and rotating $P^{\text{rev}}$ by `shift = 2` yields $O$ identically (`cyclic_equivalent = True`, `orientation = "reversed"`, `shift = 2`).

### 3.2 Classification of `(A, M, P, N)` / `section_fa8b24d27d9e (A, M, P, N)` and `report.md:33` / `handoff.md:25`

- **Conversational post-merge report string `section_fa8b24d27d9e (A, M, P, N)` (`POSTMERGE-CHAT-2`):**
  - **Classification:** **Lỗi ghi báo cáo hội thoại (`REPORT_RECORDING_ERROR_CONVERSATIONAL_ONLY`)**.
  - **Proof:** Fabricated by the step `9929` compaction summary and echoed in the step `9930` chat response. Full-repository `git grep` at `2c42f6cf` confirms **zero (`0`) occurrences** of `fa8b24d27d9e` or `(A, M, P, N)` across the entire repository.
- **Committed narrative prose in [`report.md:33–34`](report.md#L33-L34), [`handoff.md:25`](handoff.md#L25), and [`baseline-audit.md:114–118`](baseline-audit.md#L114-L118) (`W2-M5-DOC-2`):**
  - `report.md:33` and `handoff.md:25` summarized `W2-A10` in prose as `cube ABCD.A'B'C'D', edge a = 6, section (A'MN)` and `polygon_I_A_prime_I2_I1`, and `baseline-audit.md:118` wrote `id = "td_Q_ABCD_A_prime_B_prime_C_prime_D_prime"`.
  - **Authoritative correction:** Frozen `W2-A10` in `inputs/holdout-wave2.json`, `inputs/development.json`, and `results/wave2-post-feedback-regression.json` (`line 108: "family": "cuboid"`) is a **rectangular cuboid (`hình hộp chữ nhật ABCD.A'B'C'D'`) with $AB = 3a, AD = 6a, AA' = 9a$ and cutting plane `(Q)`**, and the actual section object in `scene3d.objects` is `id = "td_sec"` (`label = "Thiết diện bởi (Q)"`, `notation = null`) with normalized coordinates `[["1", "0", "8/9"], ["0", "0", "1"], ["0", "1", "5/9"], ["1", "1", "4/9"]]` (`[I, A', I2, I1]`) and exact Euclidean `area_squared = 504`.

---

## 4. Section 4 Audit — Scorer Adjudication Verification (`W2-A10` vs `W2-A07`)

- **Authoritative Finding:** The frozen historical scorer bug at [`evaluate_holdout_wave2.py:184–185`](../hybrid-v2-independent-vietnamese-section-holdout-wave2/tools/evaluate_holdout_wave2.py#L184-L185) occurs **exclusively on `W2-A10`** (and **not** on `W2-A07`).
- **Mathematical Proof:**
  1. In [`evaluate_holdout_wave2.py`](../hybrid-v2-independent-vietnamese-section-holdout-wave2/tools/evaluate_holdout_wave2.py#L146), `_find_point_xyz(objects_by_id, label)` is defined at line `146` to resolve primed labels (`"A'"` $\to$ `"A_prime"` / `"A′"`) and is called at line `232`, but line `184` checks `elif v.get("label") and v["label"] in objects_by_id:` directly when sorting `sec["vertices"]` into `td_sec["polygon"]` order.
  2. On **`W2-A07`** (`3-gon` triangle `{A', M, N}`): Even though `"A'" not in objects_by_id` causes `"A'"` to fall back to `poly_idx = 0`, **every permutation of 3 elements is either a cyclic shift or reversal of the 3-cycle**. Thus `[A', M, N]` is still cyclically equivalent to `[M, A', N]`, and `W2-A07` scores **`SERVED_CORRECT`** under the unmodified raw scorer (`47/48`).
  3. On **`W2-A10`** (`4-gon` quadrilateral `{I, A', I2, I1}`): `"A'"` falls back to `poly_idx = 0` (`idx_fallback = 0`), colliding with `"I"` (which sits at `poly_raw[0]`, so `poly_idx = 0`). Python's `sort` orders the tied `poly_idx = 0` entries as `["A'", "I"]`, scrambling the true product 4-cycle `[I, A', I2, I1]` into the non-cyclic bow-tie permutation `[A', I, I2, I1]`.
- **Committed Repository Record vs Conversational Summary (`POSTMERGE-CHAT-3`):**
  - All committed repository artifacts at `2c42f6cf` — [`results/w2-a10-scorer-adjudication-receipt.json`](results/w2-a10-scorer-adjudication-receipt.json) (LF SHA-256 `66f2dd0c41842bc9db1b9d3ab634b929363217f665c3b831b0f16e70a415e074`), [`results/wave2-post-feedback-regression.json`](results/wave2-post-feedback-regression.json) (LF SHA-256 `b02c3333cc776036abda432365b59f1a5bad9a42d27aa375fb30b584c3843262`), [`report.md:77–82`](report.md#L77-L82), [`handoff.md:29–31`](handoff.md#L29-L31), [`review.md:54`](review.md#L54), [`run.json:50,63`](run.json#L50), and [`docs/CURRENT_STATE.md:10`](../../../../CURRENT_STATE.md#L10) — correctly record **`W2-A10`**.
  - Only the post-compaction chat reply at step `9930` misstated `W2-A07` (`holdout_wave2_w2_a07_scorer_adjudication.json`).

---

## 5. Section 5 Audit — Corpus Denominators Verification

| Corpus Name | Authoritative Path | Commit | Total Cases | Positive Cases (`SERVE`) | Negative / Tamper Cases (`REFUSE`) | Stratum Breakdown |
|---|---|---|---:|---:|---:|---|
| **Independent Holdout Wave 2** | `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/inputs/holdout-wave2.json` | `ecdc26b012c8ce80d53524a98dc75cdcb020079d` | **`96`** | **`48`** | **`48`** | **`36` Category B (`P-B`) + `12` Category A (`P-A`) + `48` Negatives (`N`)** |
| **W2-M5 Development & Tamper Corpus** | `docs/evaluation/geometry/runs/hybrid-v2-w2-m5-adapter4-category-a-identity-repair/inputs/development.json` & `results/tamper-results.json` | `2c42f6cf23ddde89cc752e0ee6dfec6e4e230d3b` | **`26`** | **`14`** | **`12`** | **`14` Category A primed-vertex positives (`W2-A07`, `W2-A10`, `DEV-POS-03..14`) + `12` mandatory tamper vectors (`TAMPER-01..12`)** |
| **Independent Holdout Wave 1** | `docs/evaluation/geometry/runs/hybrid-v2-holdout-failure-repair/results/post-feedback-84-comparison.json` | `e3678608f1f7110d7046c9c43c312c69d7614f55` | **`84`** | **`42`** | **`42`** | **`42` Positives (`H001..H042`) + `42` Negatives (`H043..H084`)** |

- **Origin of the Erroneous `22 Category A, 14 Category B, 12 Category C` Table (`POSTMERGE-CHAT-4`):**
  - No 48-case corpus in the repository has `22 Category A, 14 Category B, 12 Category C`, and `Category C` does not exist in AlgoSim's section certificate taxonomy (only Category A `DINH_CAT_CANH` and Category B `ENGINE_DERIVED_SECTION` exist).
  - During context compaction at step `9929`, the compaction summarizer conflated Wave 2's `48` positive cases with W2-M5's `14` positive development cases and `12` tamper cases ($48 - 14 - 12 = 22$) and fabricated the breakdown `22 Category A, 14 Category B, 12 Category C` in `<CONTEXT_SUMMARY>`, which step `9930` echoed in chat.

---

## 6. Section 7 Deliverables — Authoritative Comparison Table & Locked Evidence Hashes

### 6.1 Side-by-Side Comparison Table (`W2-A07` and `W2-A10`)

| Deliverable Field | `W2-A07` | `W2-A10` |
|---|---|---|
| **Frozen Case Hash (Canonical SHA-256)** | `717ee585a0411ec67e2045ee4f71beb217088a0264eb649399bb4386d7999e73` | `3f1d5a6142b34b715032aca475ae7e97322b88c7bb08b1e2b077b2d11ec1b88a` |
| **Input Payload Identity (Canonical SHA-256)** | `ed8f11b8aa49478ee62bd6ce8c4a7e29e86865c336f5cd880edabbd2f3e23142` (`typed-fact-next/2`, `area_only`) | `922e49a272dd8a3836c52792d8ee60e8e5156a34ee4c895a25df8610b7feb85d` (`typed-fact-next/2`, `section_only`) |
| **Expected Solid** | Right triangular prism `ABC.A'B'C'` (`right_triangular_prism`, right at `B`, $AB=5, BC=5, AA'=10$), cut by $(\alpha) \ni A' \perp AC'$ | Rectangular cuboid `ABCD.A'B'C'D'` (`cuboid`, base rectangle $ABCD$, $AB=3a, AD=6a, AA'=9a$), cut by $(Q) \ni A' \perp AC'$ |
| **Expected Polygon (Oracle Descriptors)** | `[("VERTEX", "A'"), ("EDGE", "B", "B'", "3/4"), ("EDGE", "C", "C'", "1/2")]` (3-cycle `[A', M, N]`) | `[("VERTEX", "A'"), ("EDGE", "B", "B'", "8/9"), ("EDGE", "C", "C'", "4/9"), ("EDGE", "D", "D'", "5/9")]` (4-cycle `[A', I, I1, I2]`) |
| **Actual Polygon (`scene3d.objects["td_sec"]`)** | `id="td_sec"`, `notation="MA′N"`, normalized `[["1","0","3/4"], ["0","0","1"], ["0","1","1/2"]]`, descriptors `[("EDGE","B","B'","3/4"), ("VERTEX","A'"), ("EDGE","C","C'","1/2")]` (`[M, A', N]`, reversed shift `1` of oracle: **`MATCH`**) | `id="td_sec"`, `label="Thiết diện bởi (Q)"`, `notation=null`, normalized `[["1","0","8/9"], ["0","0","1"], ["0","1","5/9"], ["1","1","4/9"]]`, descriptors `[("EDGE","B","B'","8/9"), ("VERTEX","A'"), ("EDGE","D","D'","5/9"), ("EDGE","C","C'","4/9")]` (`[I, A', I2, I1]`, reversed shift `2` of oracle: **`MATCH`**) |
| **Exact Oracle** | Category A (`DINH_CAT_CANH`), `vertex_count = 3`, `area_squared = 1875/8`, `answer = "25√6/4"` | Category A (`DINH_CAT_CANH`), `vertex_count = 4`, `area_squared = 504`, `section_only` (`area_goal_id = null`) |
| **Product Response (`main` `2c42f6cf`)** | `route_status = "SERVED"`, `adapter4_status = "SERVED"`, `answers = {"mg1": "25√6/4"}`, `area_squared = 1875/8`, `A_prime.notation = "A′"`, `0` `_prime` leaks | `route_status = "SERVED"`, `adapter4_status = "SERVED"`, `answers = {}`, `polygon_area_squared = 504`, `A_prime.notation = "A′"`, `0` `_prime` leaks |
| **Scorer Outcome** | Raw frozen scorer: **`SERVED_CORRECT`** (`47/48`); Adjudicated scorer: **`SERVED_CORRECT`** (`48/48`) | Raw frozen scorer: **`WRONG_SERVED`** (`evaluate_holdout_wave2.py:184` `"A'" in objects_by_id` bug); Adjudicated scorer: **`SERVED_CORRECT`** (`48/48`) |
| **Root Cause of Discrepancy** | Chat report at step `9930` echoed context-compaction hallucination `section_37467f986437 (A, B, C, A′)` and misattributed `W2-A10`'s scorer bug to `W2-A07`; `report.md:32` wrote illustrative coords `[0,0,5],[6,0,15/4],[0,6,5/2]`. Product & JSON evidence are 100% exact. | Chat report at step `9930` echoed context-compaction hallucination `section_fa8b24d27d9e (A, M, P, N)`; `report.md:33` & `handoff.md:25` summarized `cuboid` ($3a, 6a, 9a$, plane $Q$) in prose as `cube, edge a=6, (A'MN)`. Product & JSON evidence are 100% exact. |

### 6.2 Authoritative Locked Evidence SHA-256 Inventory (`POSTMERGE-CHAT-5` & `W2-M5-DOC-3`)

| Locked Evidence File (relative to `hybrid-v2-w2-m5-adapter4-category-a-identity-repair/`) | LF SHA-256 (`verification/scope-and-evidence.json`) | Verification Status |
|---|---|---|
| `inputs/development.json` | `83d8f088cd1d15717977918eacca645c4af5ac7aa7cea21c4ceb3f844cb75696` | `MATCH` |
| `inputs/oracle.json` | `83137971fca1fc87e0cef6af10be164d8987eda5742db9c414a84af98002b40d` | `MATCH` |
| `results/red-before.json` | `b2453b541410e843dbd9b293d0fa3801e3541d85e83f9a95078431fc1d253262` | `MATCH` |
| `results/green-after.json` | `6f4b7262964d83bb5585aa3bd6322ebe944c50177752fc5bd1e43b72017c81a5` | `MATCH` |
| `results/tamper-results.json` | `448b0db733cda02d50578aefb7e6e6de3581d7f5986ca783fd520a66ef2caf74` | `MATCH` |
| `results/wave2-post-feedback-regression.json` | `b02c3333cc776036abda432365b59f1a5bad9a42d27aa375fb30b584c3843262` | `MATCH` |
| `results/w2-a10-scorer-adjudication-receipt.json` | `66f2dd0c41842bc9db1b9d3ab634b929363217f665c3b831b0f16e70a415e074` | `MATCH` |

*(Note on `W2-M5-DOC-3`: In [`report.md:64`](report.md#L64), the prose table listed generic tamper labels `MISSING_POINT_OBJECT, WRONG_OBJECT_TYPE, ...`; the exact locked `tamper_kind` identifiers in [`results/tamper-results.json`](results/tamper-results.json) are `NONEXISTENT_PRIMED_POINT`, `WRONG_SOLID_IDENTITY`, `VERTEX_FROM_ANOTHER_SOLID`, `CUT_VERTEX_OFF_EDGE`, `INTERPOLATION_T_OUTSIDE_0_1`, `SAME_LABEL_MISMATCHED_COORDINATES`, `MISSING_VERTEX_IN_CYCLE`, `DUPLICATE_VERTEX`, `WRONG_SECTION_TOPOLOGY_ORDER`, `CATEGORY_A_B_CERTIFICATE_MIXING`, `FORGED_PROVENANCE_STATED`, and `AREA_SQUARED_MISMATCH`.)*

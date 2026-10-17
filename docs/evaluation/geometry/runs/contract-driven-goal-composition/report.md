# Contract-Driven Goal Composition — Research Report

Status: `CONTRACT_DRIVEN_GOAL_COMPOSITION_READY_FOR_INTEGRATION_DECISION`
Branch: `research/contract-driven-goal-composition` (isolated worktree from verified `main` at `4abc4afb`)
Merge / Push: `NONE` · Live Gemini calls: `0` · Default mode: `LLM_ONLY` · Hybrid product enablement: `NO-GO` · `CACHE_VERSION = 125`

---

## 0. Baseline Verification & Reconciliation

Before writing any product code, `main` (`4abc4afbb976babc4740bf22e42dc368a24c1b13`) was verified against `origin/main` and the active worktrees, and machine receipts were captured in `baseline/`:

- **Registry Catalog (`REGISTRY_VERSION = "geometry-functions/6"` at baseline)**:
  - **31 total functions** across 5 `(kind, auxiliary_only)` groups:
    - `fact` (`auxiliary_only=False`): **11** (`regular_polygon`, `rectangle`, `right_angle`, `segment_length`, `perpendicular_line_plane`, `altitude`, `orthogonal_projection`, `perpendicular_lines`, `equal_length`, `height`, `face_perpendicular_base`)
    - `construct` (`auxiliary_only=False`): **10** (`orthogonal_projection_line`, `intersect_line_line`, `intersect_line_plane`, `midpoint`, `centroid`, `pyramid`, `regular_pyramid`, `prism`, `section`, `intersection_line`)
    - `construct` (`auxiliary_only=True`): **1** (`translate_point`)
    - `ask` (`auxiliary_only=False`): **8** (`ask_volume`, `ask_length`, `ask_distance_point_plane`, `ask_distance_lines`, `ask_angle_line_plane`, `ask_angle_plane_plane`, `ask_area`, `ask_section_area`)
    - `escape` (`auxiliary_only=False`): **1** (`unsupported`)
  - **5 functions with `PlanningContract` declarations (6 contracts total at baseline)**:
    1. `orthogonal_projection_line`: `Point(P), Line(L) -> Foot(F, P, L)` (`verifier="_construction_relation"`)
    2. `midpoint`: `Point(A), Point(B) -> Point(M)` (`descriptor="midpoint"`, `verifier="midpoint"`)
    3. `ask_length` (primary): `Point(P), Foot(F, P, L) -> AnswerDistance(P, L)` (`verifier="distance"`)
    4. `ask_length` (`planning_extra`): `Point(P), Point(Q) -> AnswerLength(P, Q)` (`goal="length"`, `verifier="length"`)
    5. `ask_distance_point_plane`: `Point(P), Plane(Q) -> AnswerDistance(P, Q)` (`verifier="distance"`)
    6. `intersection_line`: `Plane(A), Plane(B) -> Line(L)` (`verifier="intersect_plane_plane"`)
- **Historical Regression Bundle (`baseline/bundle-174.json`, `baseline/regression-174.json`)**:
  - **174 prior rows**: `benchmark30` (30), `result_binding` (18), `two_line` (77), `function_discovery` (`new/*`: 28), `generalized_goal_entry` (`goal/*`: 21).
- **Pinned Provider & Schema Surfaces**:
  - `TypedFact` schema SHA-256: `aa9d93eeac9f1659af8e5acd42af1904b7aaed674a8ab0f56f0c7dd8b2ad4ee8`
  - `function_declarations` SHA-256: `5ceb0f999d4d7c1ee37c02207ea6470a7f972a168d6c52fa597392934d86f169`
  - `function_calling` surface: `7ea511a6e3828c9adcc8402aa2d7d6b1d433e67a01ec4329c3009c46af652b25`
  - `fact_extraction` surface: `485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a`

---

## 1. General Design (RED $\rightarrow$ GREEN)

We inspected and generalized the six bottlenecks identified in the audit without adding any problem-type solver:

1. **Goal Contract & Effect Taxonomy (`registry.py`)**:
   - Extended `PlanningTerm.kind` with `"AnswerArea"` and `"AnswerAngleLinePlane"`.
   - Added `PlanningContract` on `ask_area`:
     - `inputs=(PlanningTerm("Point", ("P",)), PlanningTerm("Point", ("Q",)), PlanningTerm("Point", ("R",)))`
     - `effect=PlanningTerm("AnswerArea", ("P", "Q", "R"))`
     - `goal="area"`, `verifier="area"`, `call=(("polygon", ("P", "Q", "R")),)`
     - Closed Vietnamese source phrases for triangles formed by an unnamed described point and two named points (both orderings: `<desc> và hai điểm A, B` and `hai điểm A, B và <desc>`).
2. **Metadata-Driven Goal Entry & Multi-Point Target Decoding (`planner.py`)**:
   - Generalized `_cau_hoi` and `_muc_tieu_theo_loai` to inspect the target slot structure of the matched `PlanningContract`:
     - 1-point target slot (`AnswerLength`, `(P, Q)`): requires `len(points_b) == 1` (`{"point": Q}`).
     - 2-point unordered vertex pair (`AnswerArea`, `(P, Q, R)`): requires `len(points_b) == 2` with distinct named points (`{"points": [Q, R]}`).
     - Composite line-endpoint + plane target (`AnswerAngleLinePlane`, `(P, Q, R)` where `R` is `Plane`): refuses unnamed `point_kind` fail-closed (`UNSUPPORTED_QUESTION_FORM`) because frozen `TypedFact` cannot separate the named line endpoint from the plane vertices inside flat `points_b`.
3. **Backward Chaining Over Multi-Point Target Unification (`planner.py`)**:
   - Generalized `_EffectResolver._loai` and `_kham_pha` so an answer contract whose `effect.operands` has shape `(P, Q1, Q2, ...)` unifies `P` with the unnamed descriptor need and binds `Q1, Q2, ...` to the named target tuple `("points", (Q1, Q2, ...))`, expanding each input slot through `PlanningContract.inputs`.
   - Preserved available-binding reuse (`available[need]`) so if the source already named a point matching the same `(fn, args)` construction, the planner reuses that named point at cost `0` instead of minting a duplicate fresh point.
4. **Source-Grounded Certificate Verification (`registry.py`)**:
   - Generalized `_kiem_result_binding` (`rule == "effect-chain"`) and `_mau_muc_tieu_mo_ta` to validate both `{"point": Q}` (1-point target) and `{"points": [Q, R]}` (2-point unordered target for `AnswerArea`), checking:
     - Every chain step against its `PlanningContract` via `render_call` and `same_call`.
     - Exact source phrase span coverage (`(?P<target>{P})\s*(?:,|với|và)\s*(?P<target2>{P})`) and unordered vertex set identity `set(t["points"]) == {m.group("target"), m.group("target2")}`.
     - Rejection of duplicate target points, unbuilt labels, forged quotes, and contract/effect mismatches with `AUXILIARY_RULE_MISMATCH` or `SOURCE_OBJECT_MISMATCH`.
5. **Independent Gram-Metric Verifier Table `_KIEM_DICH` (`engine.py`)**:
   - Replaced the single-purpose `kc2_dich` implementation with a verifier dispatch table `_KIEM_DICH` keyed by `PlanningContract.verifier`:
     - `"distance"`: `_Dung._kc2_khoang_cach` (point-to-plane and point-to-line squared distance from Gram determinants)
     - `"length"`: `_Dung._kc2_do_dai` ($g(w, w)$)
     - `"area"`: `_Dung._kc2_dien_tich` $\rightarrow$ `_dt2_tam_giac(p, q, r)` computing $\frac{1}{4}(g(u,u)g(v,v) - g(u,v)^2)$ directly from the chart Gram metric $G$, independent of the kernel's `area` measurement.
     - `"angle_line_plane"`: `_Dung._kc2_goc_duong_mat` $\rightarrow$ `_goc_duong_mat_cos2(line, plane)` computing $\sin^2\theta = \frac{\det\operatorname{Gram}(u, v, w)}{g(w, w)\det\operatorname{Gram}(u, v)}$ and $\cos^2\theta = 1 - \sin^2\theta$ directly from 3D Gram determinants, independent of kernel covectors.
   - `kc2_dich` cross-checks that the certified goal contract's `contract.verifier` matches the target's verifier kind in `_KIEM_DICH`; any lying contract (e.g. `ask_area` claiming `verifier="length"`) is refused with `ENGINE_SELF_CHECK_FAILED`.
   - Furthermore, `dung_tu_loi_goi` runs `_dt2_tam_giac` on every `ask_area` triangle call and `_goc_duong_mat_cos2` on every `ask_angle_line_plane` call (both named and unnamed), refusing degenerate/collinear triangles (`COLLINEAR_POINTS`) and degenerate lines (`DEGENERATE_LINE`) in `kiem_mat_cat`.

---

## 2. Vertical Slice A (AREA) & Vertical Slice B (ANGLE LINE–PLANE)

### Vertical Slice A — Area Composition (`GREEN`)
- **`midpoint -> ask_area` (unnamed derived point)**:
  - Served across 4 solid families (right square pyramid `S.ABCD`, regular triangular pyramid `S.ABC`, cube `ABCD.A'B'C'D'`, right triangular prism `ABC.A'B'C'`), alternate Vietnamese wordings, symbolic edge unit `a` (`a²√13/4`), multi-goal queries (`ask_volume` + composed `ask_area`), and named-midpoint reuse (`Gọi M là trung điểm của SC` reused without minting a second midpoint).
  - Held-out split: **4/4** exact (`heldout-rect-pyramid-midpoint-area`, `heldout-rect-prism-midpoint-area`, `heldout-right-tri-pyramid-midpoint-area`, `heldout-regular-quad-pyramid-midpoint-area`).
- **`centroid -> ask_area` (zero-planner-edit discovery)**:
  - Without `centroid` contract in production `REGISTRY`: **0/4** served, all 4 refused fail-closed with `UNSUPPORTED_CAPABILITY`.
  - With the single `PlanningContract` added to `REGISTRY["centroid"]` (zero lines of `planner.py` or `engine.py` changed): **4/4** served with exact oracle answers, including `discovery-centroid-plus-projection-area` which composes a premise `orthogonal_projection` point `H` with an unnamed `centroid` of `SBC` to compute $\operatorname{ Area }(\triangle GAH)$!
- **`orthogonal_projection` / `orthogonal_projection_line -> ask_area`**:
  - Served for both plane projection (`H` = projection of `A` onto `(SBD)`, area of $\triangle SHC$) and line projection (`H` = projection of `A` onto `SB`, area of $\triangle AHC$), plus composed with unnamed `centroid` (`discovery-centroid-plus-projection-area`).
- **Degenerate & Underdetermined Refusals**:
  - Collinear triangle vertices (e.g. midpoint of $SC$ with $S, C$, or named midpoint $M$ in $\triangle SMC$) refused with `COLLINEAR_POINTS`.
  - Missing altitude / edge dimensions refused with `MISSING_DIMENSION`.

### Vertical Slice B — Angle Line–Plane (`GREEN` on Named Derived Points · `SCHEMA_REPRESENTATION_BLOCKER` on Unnamed `point_kind`)
- **Named Derived Points $\rightarrow$ `ask_angle_line_plane` (`5/5 GREEN`)**:
  - Verified by the new independent Gram verifier `_goc_duong_mat_cos2` across all three geometric regimes:
    1. **$0^\circ$ regime** (`angle-zero-deg-line-parallel-plane`, $MN \parallel (ABCD)$): $\cos^2\theta = 1$, $\sin^2\theta = 0$.
    2. **$90^\circ$ regime** (`angle-ninety-deg-line-perp-plane`, $SA \perp (ABCD)$): $\cos^2\theta = 0$, $\sin^2\theta = 1$.
    3. **Oblique midpoint regime** (`angle-oblique-midpoint-line-plane`, $AM$ with $(ABCD)$): $\cos^2\theta = 8/17$, $\sin^2\theta = 9/17$.
    4. **Oblique centroid regime** (`angle-oblique-centroid-line-plane`, $AG$ with $(ABCD)$): $\cos^2\theta = 20/29$, $\sin^2\theta = 9/29$.
    5. **Oblique orthogonal-projection regime** (`angle-oblique-projection-line-plane`, $HC$ with $(ABCD)$): $\cos^2\theta = 185/221$, $\sin^2\theta = 36/221$.
- **Unnamed `point_kind` + `quantity="angle"` (`SCHEMA_REPRESENTATION_BLOCKER`)**:
  - Proven and recorded in `corpus.json` and `test_slice_b_unnamed_angle_line_plane_is_schema_representation_blocker`:
    - A line–plane angle with an unnamed described point requires three distinct point groups: (1) the descriptor's parent points (2 or 3 labels), (2) the named second endpoint of the line (1 label), and (3) the target plane's defining vertices ($\ge 3$ labels).
    - Frozen `TypedFact` (`kind="question"`) provides only `points` (bound to the descriptor's parent points when `point_kind` is set) and a single flat `points_b: list[str]`. Packing both the named line endpoint and the plane vertices into `points_b` would require guessing by list position (`points_b[0]` vs `points_b[1:]`), which is explicitly forbidden by the architecture contract.
    - Therefore, unnamed `point_kind` with `quantity="angle"` is refused fail-closed with `UNSUPPORTED_QUESTION_FORM` and documented as `SCHEMA_REPRESENTATION_BLOCKER` until `TypedFact` schema ownership is open.

---

## 3. Capability Matrix: Planned vs Supported vs Grounded vs Executed vs Verified

| Composition Configuration | Planned (`_EffectResolver`) | Supported by Frozen `TypedFact` Schema | Source-Grounded (`kiem_nguon`) | Executed (`SemanticProgramInterpreter`) | Independently Verified (`_KIEM_DICH` & `oracle.py`) | Status |
|---|---|---|---|---|---|---|
| Unnamed `midpoint` $\rightarrow$ `ask_distance_point_plane` | Yes | Yes | Yes | Yes | Yes (`_kc2_khoang_cach`) | **PROVED (Prior Wave + Regression)** |
| Unnamed `midpoint` $\rightarrow$ `orthogonal_projection_line` $\rightarrow$ `ask_length` | Yes | Yes | Yes | Yes | Yes (`_kc2_khoang_cach`) | **PROVED (Prior Wave + Regression)** |
| Unnamed `midpoint` $\rightarrow$ `intersection_line` $\rightarrow$ `orthogonal_projection_line` $\rightarrow$ `ask_length` | Yes | Yes | Yes | Yes | Yes (`_kc2_khoang_cach`) | **PROVED (Prior Wave + Regression)** |
| Unnamed `midpoint` $\rightarrow$ `ask_length` | Yes | Yes | Yes | Yes | Yes (`_kc2_do_dai`) | **PROVED (Prior Wave + Regression)** |
| Unnamed `midpoint` $\rightarrow$ `ask_area` (Slice A) | Yes | Yes (`points` + 2-point `points_b`) | Yes (`_mau_muc_tieu_mo_ta`) | Yes (`construct_polygon` + `measure area`) | Yes (`_dt2_tam_giac` Gram det) | **PROVED (12/12 dev + held-out)** |
| Unnamed `centroid` $\rightarrow$ `ask_area` (Slice A Discovery) | Yes (0 planner edits) | Yes (`points` + 2-point `points_b`) | Yes (`PlanningContract.phrase`) | Yes (`divide_segment` + `measure area`) | Yes (`_MO_TA["centroid"]` + `_dt2_tam_giac`) | **PROVED (4/4 discovery arm)** |
| Named `orthogonal_projection` / `orthogonal_projection_line` + Unnamed `centroid` $\rightarrow$ `ask_area` | Yes | Yes | Yes | Yes | Yes (`_construction_relation` + `_dt2_tam_giac`) | **PROVED (`discovery-centroid-plus-projection-area`)** |
| Named `midpoint` / `centroid` / `orthogonal_projection` $\rightarrow$ `ask_angle_line_plane` (Slice B) | Direct (`doc_du_kien`) | Yes (`points_a` line + `points_b` plane) | Yes (`_CUM_HOI`) | Yes (`angle_cos_sq`) | Yes (`_goc_duong_mat_cos2` Gram det) | **PROVED (5/5 across $0^\circ, 90^\circ$, oblique)** |
| Unnamed `midpoint` / `centroid` $\rightarrow$ `ask_angle_line_plane` (Slice B Unnamed) | Blocked at entry | **No (`SCHEMA_REPRESENTATION_BLOCKER`)** | N/A | N/A | N/A | **FAIL-CLOSED (`UNSUPPORTED_QUESTION_FORM`)** |

---

## 4. Ablation, Tamper Resistance & Regression Summary

Measured by `backend/scripts/measure_goal_composition.py` (`ablation.json`, `regression-174.json`, **0 live calls**):

| Arm / Variant | Prior 174 Rows Diff vs Baseline | Slice A Positive (10) | Slice A Discovery Centroid (4) | Slice A Held-Out (4) | Slice B Angle Line–Plane (5) | Negative Refusals (17) | Wrong Served |
|---|---|---|---|---|---|---|---|
| `NEW[production]` | **0 / 174** | **10 / 10** | 0 / 4 (fail-closed) | **4 / 4** | **5 / 5** | **17 / 17** exact code | **0** |
| `NEW[centroid]` (+1 data contract, 0 planner edits) | — | **10 / 10** | **4 / 4** | **4 / 4** | **5 / 5** | **17 / 17** exact code | **0** |
| `NEW[reversed]` (reversed `REGISTRY` order) | **0 / 174** | **10 / 10** | 0 / 4 (fail-closed) | **4 / 4** | **5 / 5** | **17 / 17** exact code | **0** |
| `NEW[no-area]` (`ask_area` contract removed) | **0 / 174** | 2 / 10 (8 unnamed refused) | 0 / 4 | 0 / 4 | **5 / 5** | 17 / 17 refused | **0** |
| `NEW[no-midpoint]` (`midpoint` contract removed) | — | 2 / 10 (8 unnamed refused) | 0 / 4 | 0 / 4 | **5 / 5** | 17 / 17 refused | **0** |
| `NEW[lying]` (`midpoint` claims `descriptor="centroid"`) | — | 2 / 10 (8 unnamed refused by Engine) | 0 / 4 | 0 / 4 | **5 / 5** | 17 / 17 refused | **0** |
| `NEW[lying-area-verifier]` (`ask_area` claims `verifier="length"`) | **0 / 174** | 2 / 10 (8 unnamed refused by Engine) | 0 / 4 | 0 / 4 | **5 / 5** | 17 / 17 refused | **0** |

### Tamper & Security Suite (`test_contract_driven_goal_composition.py`)
All 8 tamper categories are tested and refused fail-closed (`0 wrong served`):
1. Forged effect (`AnswerLength` on `ask_area`) $\rightarrow$ `AUXILIARY_RULE_MISMATCH`
2. Forged target (`points: ["A", "D"]` when quote asks `A, B`) $\rightarrow$ `SOURCE_OBJECT_MISMATCH`
3. Forged quote (not in problem text) $\rightarrow$ `UNGROUNDED_QUOTE`
4. Uncertified point label (`K` not in figure) $\rightarrow$ `AUXILIARY_RULE_MISMATCH`
5. Swapped operands (`polygon: ["M", "A", "C"]` vs target `["A", "B"]`) $\rightarrow$ `AUXILIARY_RULE_MISMATCH`
6. Lying producer contract (`midpoint` claiming `centroid`) $\rightarrow$ `ENGINE_SELF_CHECK_FAILED`
7. Lying goal verifier (`ask_area` claiming `verifier="length"`) $\rightarrow$ `ENGINE_SELF_CHECK_FAILED`
8. Tampered engine coordinates vs kernel execution $\rightarrow$ `ENGINE_SELF_CHECK_FAILED`

---

## 5. Parallel Safety & Conflict Check Against `research/semantic-extraction-v3`

We inspected `git diff main -- backend/app/simulation/geometry_functions/registry.py` across both worktrees:
- `semantic-extraction-v3` does **not** modify `planner.py` or `engine.py`.
- In `registry.py`, `semantic-extraction-v3` modifies lines `60–64`, `338–383`, `598–616`, `1352`, and `1666–1792` (premise source coverage and solid/cube premise grounding).
- Our branch `research/contract-driven-goal-composition` modifies lines `258` (`PlanningTerm`), `403` (`ask_area` `PlanningContract`), `959–1012` (`_kiem_result_binding` `effect-chain`), and `2050–2059` (`_mau_muc_tieu_mo_ta`, `_mau_hoi_tat_ca`, `REGISTRY_VERSION`).
- The line ranges in `registry.py` are **100% disjoint**, and semantically orthogonal (premise extraction/grounding vs `effect-chain` goal composition).

---

## 6. Files Changed in Worktree (`research/contract-driven-goal-composition`)

- **Product files (3)**:
  - `backend/app/simulation/geometry_functions/registry.py`
  - `backend/app/simulation/geometry_functions/planner.py`
  - `backend/app/simulation/geometry_functions/engine.py`
- **Tests & measurement tooling (2)**:
  - `backend/tests/geometry/test_contract_driven_goal_composition.py` (67 tests)
  - `backend/scripts/measure_goal_composition.py`
- **Run package (`docs/evaluation/geometry/runs/contract-driven-goal-composition/`)**:
  - `run.json`, `report.md`, `oracle.py`, `corpus.json`, `red.txt`, `green.txt`, `ablation.json`, `regression-174.json`, `baseline/{receipt.json,bundle-174.json,regression-174.json}`

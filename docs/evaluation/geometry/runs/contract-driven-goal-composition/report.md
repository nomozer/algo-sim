# Contract-Driven Goal Composition — Research Report

Status: `FROZEN_PENDING_INTEGRATION` (`READY_FOR_INTEGRATION` · `INDEPENDENT_REVIEW_PASS` · `INTEGRATION_DEFERRED_PENDING_SEMANTIC_V3`)
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
   - Extended `PlanningTerm.kind` (`registry.py:258`) with `"AnswerArea"` and `"AnswerAngleLinePlane"`.
   - Added `PlanningContract` on `ask_area` (`registry.py:403-411`):
     - `inputs=(PlanningTerm("Point", ("P",)), PlanningTerm("Point", ("Q",)), PlanningTerm("Point", ("R",)))`
     - `effect=PlanningTerm("AnswerArea", ("P", "Q", "R"))`
     - `goal="area"`, `verifier="area"`, `call=(("polygon", ("P", "Q", "R")),)`
     - Closed Vietnamese source phrases (`(?P<t1>{P})\s*(?:,|và)\s*(?P<t2>{P})`) for triangles formed by an unnamed described point and two named points in both operand orders (`<desc> và hai điểm A, B` and `hai điểm A, B và <desc>`).
2. **Metadata-Driven Goal Entry & Multi-Point Target Decoding (`planner.py`)**:
   - Generalized `_doc_toan_hang_mo_ta` (`planner.py:221-247`) and `_cau_hoi` (`planner.py:474-532`) to inspect the target slot structure of the matched `PlanningContract`:
     - 1-point target slot (`AnswerLength`, `(P, Q)`): requires `len(points_b) == 1` (`("point", Q)`).
     - 2-point unordered vertex pair (`AnswerArea`, `(P, Q, R)`): requires `len(points_b) == 2` with distinct named points (`("points", (Q, R))`).
     - Any goal quantity without a matching all-`Point` contract (including `quantity="angle"` with unnamed `point_kind`): refused fail-closed in `_doc_toan_hang_mo_ta` with `UNSUPPORTED_CAPABILITY` because frozen `TypedFact` cannot separate a named line endpoint from the plane vertices inside flat `points_b`.
3. **Backward Chaining Over Multi-Point Target Unification (`planner.py`)**:
   - Generalized `_EffectResolver._loai` (`planner.py:626-646`) and `_EffectResolver._resolve` (`planner.py:648-742`) so an answer contract whose `effect.operands` has shape `(P, Q1, Q2, ...)` unifies `P` with the unnamed descriptor need and binds `Q1, Q2, ...` to the named target tuple `("points", (Q1, Q2, ...))`, expanding each input slot through `PlanningContract.inputs`.
   - Preserved existing premise-call reuse (`self.plan.calls` checked via `same_call(contract, render_call(contract, bound), c["args"])` in `_EffectResolver._resolve`, `planner.py:706-718`) so if the source already named a point matching the same `(fn, args)` construction, the planner reuses that named point at cost `0` instead of minting a duplicate fresh point.
4. **Source-Grounded Certificate Verification (`registry.py`)**:
   - Generalized `_kiem_result_binding` (`rule == "effect-chain"`, `registry.py:967-1038`) and `_mau_muc_tieu_mo_ta` (`registry.py:2072-2084`) to validate both `{"point": Q}` (1-point target) and `{"points": [Q, R]}` (2-point unordered target for `AnswerArea`), checking:
     - Every chain step against its `PlanningContract` via `render_call` and `same_call`.
     - Exact source phrase span coverage (`{m["t1"], m["t2"]} == set(rest)` and `m["t1"] != m["t2"]`).
     - Rejection of duplicate target points, unknown labels (`UNKNOWN_LABEL`), ungrounded quotes (`QUOTE_NOT_IN_SOURCE`), and contract/effect mismatches (`AUXILIARY_RULE_MISMATCH` or `SOURCE_OBJECT_MISMATCH`).
5. **Independent Gram-Metric Verifier Table `_KIEM_DICH` (`engine.py`)**:
   - Replaced the single-purpose `kc2_dich` implementation with a verifier dispatch table `_KIEM_DICH` (`engine.py:1113-1118`) keyed by `PlanningContract.verifier`:
     - `"distance"`: `_Dung._kc2_khoang_cach` (point-to-plane and point-to-line squared distance from Gram determinants)
     - `"length"`: `_Dung._kc2_do_dai` ($g(w, w)$)
     - `"area"`: `_Dung._kc2_dien_tich` $\rightarrow$ `_dt2_tam_giac(p, q, r)` (`engine.py:1041-1047`) computing $\frac{1}{4}(g(u,u)g(v,v) - g(u,v)^2)$ directly from the chart Gram metric $G$, independent of the kernel's `area_polygon` measurement.
     - `"angle_line_plane"`: `_Dung._kc2_goc_duong_mat` $\rightarrow$ `_goc_duong_mat_cos2(line, plane)` (`engine.py:1049-1062`) computing $\sin^2\theta = \frac{\det\operatorname{Gram}(u, v, w)}{g(w, w)\det\operatorname{Gram}(u, v)}$ and $\cos^2\theta = 1 - \sin^2\theta$ directly from 3D Gram determinants, independent of kernel covectors (`Plane3.normal`).
   - `kc2_dich` (`engine.py:1088-1105`) cross-checks that the certified goal contract's `contract.verifier` matches the target's verifier kind in `_KIEM_DICH`; any lying contract (e.g. `ask_area` claiming `verifier="length"`) is refused with `ENGINE_SELF_CHECK_FAILED`.
   - Furthermore, `dung_tu_loi_goi` (`engine.py:1273-1278`) runs `_dt2_tam_giac` on every 3-vertex `ask_area` call and `_goc_duong_mat_cos2` on every `ask_angle_line_plane` call (both named and unnamed), while `kiem_mat_cat` (`engine.py:917-923`) refuses degenerate/collinear triangles (`COLLINEAR_POINTS`) and degenerate lines (`DEGENERATE_LINE`).

---

## 2. Vertical Slice A (AREA) & Vertical Slice B (ANGLE LINE–PLANE)

> **Provenance & Independence Note**: The 40-case `corpus.json` (`positive`: 10, `discovery`: 4, `held_out`: 4, `angle_line_plane_slice_b`: 5, `negative`: 17) is **agent-authored with an independent first-principles Fraction/Gram oracle (`oracle.py`, 0 imports from `app`/`tests`), not human-expert-validated (`AGENT_AUTHORED_WITH_INDEPENDENT_ORACLE_NOT_HUMAN_VALIDATED`)**.

### Vertical Slice A — Area Composition (`GREEN`)
- **`midpoint -> ask_area` (unnamed derived point, enabled in production `REGISTRY`)**:
  - Served across 4 solid families (right square pyramid `S.ABCD`, cube `ABCD.A'B'C'D'`, cuboid `ABCD.A'B'C'D'`, right triangular prism `ABC.A'B'C'`), alternate Vietnamese wordings, premise projection + unnamed midpoint (`pyramid-projection-and-unnamed-midpoint-area`), named-midpoint reuse (`pyramid-reuse-named-midpoint-area`, `0` new points minted), and multi-goal queries (`pyramid-shared-midpoint-area-and-distance`).
  - Held-out split (**4/4 exact**): `heldout-tetrahedron-midpoint-area` ($S^2=2$), `heldout-regular-pyramid-midpoint-area` ($S^2=4$), `heldout-cuboid-projection-and-midpoint-area` ($S^2=3169/100$), `heldout-prism-midpoint-area-reversed` ($S^2=27/4$). Together with the 8 unnamed-midpoint dev positives, `12/12` unnamed-midpoint area cases + `2/2` named projection-premise area cases = `14/14` area cases served in production.
- **`centroid -> ask_area` (zero-planner-edit discovery, experimental contract injection)**:
  - Without `centroid` contract in production `REGISTRY`: **0/4** served, all 4 refused fail-closed with `UNSUPPORTED_CAPABILITY`.
  - With the single `PlanningContract` added to `REGISTRY["centroid"]` (zero lines of `planner.py` or `engine.py` changed): **4/4** served with exact oracle answers (`pyramid-centroid-area-AB`, `pyramid-centroid-area-AD-reversed-wording`, `prism-centroid-area`, and `pyramid-projection-and-unnamed-centroid-area` which composes a premise `orthogonal_projection_line` foot `H` of `A` onto `SB` with an unnamed `centroid` $G$ of $\triangle SBC$ to compute $\operatorname{Area}^2(\triangle GHD) = 490/1521$).
- **`orthogonal_projection` / `orthogonal_projection_line -> ask_area`**:
  - Served for both plane projection (`pyramid-projection-plane-area`, $H = \operatorname{proj}_{(SBC)}(A)$, $S^2(\triangle HAB) = 144/169$) and line projection (`pyramid-projection-line-area`, $H = \operatorname{proj}_{SB}(A)$, $S^2(\triangle HCD) = 820/169$), plus composed with unnamed `midpoint` (`pyramid-projection-and-unnamed-midpoint-area`, $S^2 = 509/338$) and unnamed `centroid` (`pyramid-projection-and-unnamed-centroid-area`, $S^2 = 490/1521$).
- **Degenerate & Underdetermined Refusals**:
  - Collinear triangle vertices (`collinear-triangle-unnamed-midpoint`, `collinear-triangle-named-midpoint`) refused with `COLLINEAR_POINTS`.
  - Missing altitude / edge dimensions (`underdetermined-metric`) refused with `MISSING_DIMENSION`.

### Vertical Slice B — Angle Line–Plane (`GREEN` on Named Derived Points · `SCHEMA_REPRESENTATION_BLOCKER` on Unnamed `point_kind`)
- **Named Derived Points $\rightarrow$ `ask_angle_line_plane` (`5/5 GREEN` — proves independent Gram verifier `_goc_duong_mat_cos2` on named constructions, not unnamed composition)**:
  - Verified by `_goc_duong_mat_cos2` across all three geometric regimes:
    1. **$90^\circ$ regime** (`angle-90deg-perpendicular-line-plane`, $SA \perp (ABCD)$): $\cos^2\theta = 0$, $\sin^2\theta = 1$.
    2. **$0^\circ$ regime** (`angle-0deg-parallel-midline-plane`, $MN \parallel (ABCD)$): $\cos^2\theta = 1$, $\sin^2\theta = 0$.
    3. **Oblique midpoint regime** (`angle-oblique-midpoint-line-plane`, $AM$ with $(ABCD)$): $\cos^2\theta = 8/17$, $\sin^2\theta = 9/17$.
    4. **Oblique centroid regime** (`angle-oblique-centroid-line-plane`, $AG$ with $(ABCD)$): $\cos^2\theta = 20/29$, $\sin^2\theta = 9/29$.
    5. **Oblique orthogonal-projection regime** (`angle-oblique-projection-line-plane`, $HC$ with $(ABCD)$): $\cos^2\theta = 185/221$, $\sin^2\theta = 36/221$.
- **Unnamed `point_kind` + `quantity="angle"` (`SCHEMA_REPRESENTATION_BLOCKER`)**:
  - Proven and recorded in `corpus.json` (`unnamed-angle-line-plane-blocker`) and `test_slice_b_unnamed_point_kind_schema_representation_blocker`:
    - A line–plane angle with an unnamed described point requires three distinct point groups: (1) the descriptor's parent points (2 or 3 labels), (2) the named second endpoint of the line (1 label), and (3) the target plane's defining vertices ($\ge 3$ labels).
    - Frozen `TypedFact` (`kind="question"`) provides only `points` (bound to the descriptor's parent points when `point_kind` is set) and a single flat `points_b: list[str]`. Packing both the named line endpoint and the plane vertices into `points_b` would require guessing by list position (`points_b[0]` vs `points_b[1:]`), which is forbidden by the architecture contract.
    - Therefore, unnamed `point_kind` with `quantity="angle"` is refused fail-closed with `UNSUPPORTED_CAPABILITY` and documented as `SCHEMA_REPRESENTATION_BLOCKER` until `TypedFact` schema ownership is open.

---

## 3. Capability Matrix: Planned vs Supported vs Grounded vs Executed vs Verified

| Composition Configuration | Catalog Scope | Planned (`_EffectResolver`) | Supported by Frozen `TypedFact` Schema | Source-Grounded (`kiem_nguon`) | Executed (`SemanticProgramInterpreter`) | Independently Verified (`_KIEM_DICH` & `oracle.py`) | Status |
|---|---|---|---|---|---|---|---|
| Unnamed `midpoint` $\rightarrow$ `ask_distance_point_plane` | Default Production | Yes | Yes | Yes | Yes | Yes (`_kc2_khoang_cach`) | **PROVED (Prior Wave + Regression)** |
| Unnamed `midpoint` $\rightarrow$ `orthogonal_projection_line` $\rightarrow$ `ask_length` | Default Production | Yes | Yes | Yes | Yes | Yes (`_kc2_khoang_cach`) | **PROVED (Prior Wave + Regression)** |
| Unnamed `midpoint` $\rightarrow$ `intersection_line` $\rightarrow$ `orthogonal_projection_line` $\rightarrow$ `ask_length` | Default Production | Yes | Yes | Yes | Yes | Yes (`_kc2_khoang_cach`) | **PROVED (Prior Wave + Regression)** |
| Unnamed `midpoint` $\rightarrow$ `ask_length` | Default Production | Yes | Yes | Yes | Yes | Yes (`_kc2_do_dai`) | **PROVED (Prior Wave + Regression)** |
| Unnamed `midpoint` $\rightarrow$ `ask_area` (Slice A) | Default Production | Yes | Yes (`points` + 2-point `points_b`) | Yes (`_mau_muc_tieu_mo_ta`) | Yes (`construct_polygon` + `measure area`) | Yes (`_dt2_tam_giac` Gram det) | **PROVED (8/8 dev + 4/4 held-out = 12/12)** |
| Named `orthogonal_projection` / `orthogonal_projection_line` $\rightarrow$ `ask_area` | Default Production | Direct (`doc_du_kien`) | Yes (`points` triangle) | Yes (`_CUM_HOI`) | Yes (`project_onto` + `measure area`) | Yes (`_construction_relation` + `_dt2_tam_giac`) | **PROVED (2/2 dev + 1/1 held-out with midpoint)** |
| Unnamed `centroid` $\rightarrow$ `ask_area` (Slice A Discovery) | Experimental Contract Injection | Yes (0 planner edits) | Yes (`points` + 2-point `points_b`) | Yes (`PlanningContract.phrase`) | Yes (`divide_segment` + `measure area`) | Yes (`_MO_TA["centroid"]` + `_dt2_tam_giac`) | **PROVED (4/4 discovery arm)** |
| Named `orthogonal_projection_line` + Unnamed `centroid` $\rightarrow$ `ask_area` | Experimental Contract Injection | Yes (0 planner edits) | Yes | Yes | Yes | Yes (`_construction_relation` + `_dt2_tam_giac`) | **PROVED (`pyramid-projection-and-unnamed-centroid-area`)** |
| Named `midpoint` / `centroid` / `orthogonal_projection_line` $\rightarrow$ `ask_angle_line_plane` (Slice B) | Default Production | Direct (`doc_du_kien`) | Yes (`points_a` line + `points_b` plane) | Yes (`_CUM_HOI`) | Yes (`angle_cos_sq`) | Yes (`_goc_duong_mat_cos2` Gram det) | **PROVED (5/5 across $0^\circ, 90^\circ$, oblique)** |
| Unnamed `midpoint` / `centroid` $\rightarrow$ `ask_angle_line_plane` (Slice B Unnamed) | Schema-Blocked | Blocked at entry | **No (`SCHEMA_REPRESENTATION_BLOCKER`)** | N/A | N/A | N/A | **FAIL-CLOSED (`UNSUPPORTED_CAPABILITY`)** |

---

## 4. Ablation, Negative Taxonomy Reconciliation & Tamper Resistance

Measured by `backend/scripts/measure_goal_composition.py` (`ablation.json`, `ablation-reconciled.json`, `regression-174.json`, **0 live calls**):

| Arm / Variant | Prior 174 Rows Diff vs Baseline | Slice A Positive (10) | Slice A Discovery Centroid (4) | Slice A Held-Out (4) | Slice B Angle Line–Plane (5) | Slice A/B Negatives (17) | True Safety Negatives Refused (`118/118`) | Safety Wrong Served | Capability-Disabled Negative (`1`: `new/negative::centroid-without-contract`) |
|---|---|---|---|---|---|---|---|---|---|
| `NEW[production]` | **0 / 174** | **10 / 10** | 0 / 4 (fail-closed) | **4 / 4** | **5 / 5** | **17 / 17** exact code | **118 / 118** | **0** | `REFUSED / UNSUPPORTED_CAPABILITY` (`correct_refusal_disabled_capability`) |
| `NEW[centroid]` (+1 data contract, 0 planner edits) | — | **10 / 10** | **4 / 4** | **4 / 4** | **5 / 5** | **17 / 17** exact code | **118 / 118** | **0** | `SERVED` `4/3` ($d^2=16/9$, matches oracle twin `new/discovery::centroid-to-plane`; raw `fd.classify`: `wrong_served`) |
| `NEW[reversed]` (reversed `REGISTRY` order) | **0 / 174** | **10 / 10** | 0 / 4 (fail-closed) | **4 / 4** | **5 / 5** | **17 / 17** exact code | **118 / 118** | **0** | `REFUSED / UNSUPPORTED_CAPABILITY` (`correct_refusal_disabled_capability`) |
| `NEW[no-area]` (`ask_area` contract removed) | **0 / 174** | 2 / 10 (8 unnamed refused) | 0 / 4 | 0 / 4 | **5 / 5** | 17 / 17 refused | **118 / 118** | **0** | `REFUSED / UNSUPPORTED_CAPABILITY` |
| `NEW[no-midpoint]` (`midpoint` contract removed) | — | 2 / 10 (8 unnamed refused) | 0 / 4 | 0 / 4 | **5 / 5** | 17 / 17 refused | **118 / 118** | **0** | `REFUSED / UNSUPPORTED_CAPABILITY` |
| `NEW[lying]` (`midpoint` claims `descriptor="centroid"`) | — | 2 / 10 (8 unnamed refused by Engine) | 0 / 4 | 0 / 4 | **5 / 5** | 17 / 17 refused | **118 / 118** | **0** | `REFUSED / ENGINE_SELF_CHECK_FAILED` (`correct_refusal_lying_contract_caught`) |
| `NEW[lying-area-verifier]` (`ask_area` claims `verifier="length"`) | **0 / 174** | 2 / 10 (8 unnamed refused by Engine) | 0 / 4 | 0 / 4 | **5 / 5** | 17 / 17 refused | **118 / 118** | **0** | `REFUSED / UNSUPPORTED_CAPABILITY` |

### Exact 214-Row Corpus Taxonomy Breakdown & Reconciliation of `new/negative::centroid-without-contract` (`ablation-reconciled.json`)
- **Total Evaluated Rows (`214`)**: `174` historical regression rows + `40` new rows in `corpus.json`:
  - **Production Positive / Supported Rows (`86`)**: `benchmark30` (`21`), `two_line` (`23`), `result_binding/positive` (`6`), `new/positive` (`9`), `goal/positive` (`8`), `goal_composition/positive` (`10`), `goal_composition/held_out` (`4`), `goal_composition/angle_line_plane_slice_b` (`5`).
  - **Experimental `centroid`-Contract Discovery Positive Rows (`9`)**: `new/discovery` (`3`), `goal/discovery` (`2`), `goal_composition/discovery` (`4`).
  - **Total Negative / Expected-Refusal Rows (`119`)**, partitioned into:
    1. **True Safety Negatives (`118` rows)**:
       - `55` rows in explicit `*/negative` splits (`result_binding/negative`: `12`, `new/negative`: `15`, `goal/negative`: `11`, `goal_composition/negative`: `17`).
       - `63` implicit refusal rows inside `benchmark30` (`9`) and `two_line/*` (`31` `LINE_CONTAINED_IN_PLANE`, `6` `NO_POLYGON`, `10` `PLANE_NOT_UNIQUE`, `7` `SECTION_PLANE_IS_FACE`).
       - Across all 7 ablation arms, **`118/118` true safety negatives are refused** and **`safety_wrong_served = 0`**. (Earlier phrasing `"213 safety-checked rows"` summed `86` production positives + `9` discovery positives + `118` true safety negatives = `213` non-capability-disabled rows; `ablation-reconciled.json` now reports the exact `86 / 9 / 118 / 1` taxonomy explicitly.)
    2. **Capability-Disabled Negatives (`1` row: `new/negative::centroid-without-contract`)**:
       - In the historical `goal-directed-function-discovery` corpus, the valid problem *"Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 2. SA vuông góc với (ABCD). SA = 3. Tính khoảng cách từ trọng tâm của tam giác SBC đến (SAD)."* appears twice with byte-identical `text` and `payload.facts`:
         - `new/negative::centroid-without-contract` (`expected_codes: ["UNSUPPORTED_CAPABILITY"]`), testing fail-closed refusal when `centroid` has no `PlanningContract` in the production catalog.
         - `new/discovery::centroid-to-plane` (`expected_squared: {"q": "16/9"}`), testing that when the experimental `centroid` contract is enabled (`NEW[centroid]`), the route serves the exact distance $4/3$ ($d^2 = 16/9$).
       - Because the legacy classifier `fd.classify` evaluates `new/negative::centroid-without-contract` against its static production-only expectation (`expected_codes: ["UNSUPPORTED_CAPABILITY"]`), enabling `NEW[centroid]` produces a raw `wrong_served` count of `1` even though the served answer `4/3` ($d^2 = 16/9$) is mathematically exact and matches `new/discovery::centroid-to-plane`.
       - `measure_goal_composition.py reconcile` (`ablation-reconciled.json`) separates the `118` **True Safety Negatives** (`true_safety_negatives_refused = 118`, `safety_wrong_served = 0` across all 7 arms) from the `1` **Capability-Disabled Negative** (`capability_enabled_oracle_verified_served = 1` in `NEW[centroid]`), while keeping raw `ablation.json` and all gold labels untouched.

### Tamper & Security Suite (`test_contract_driven_goal_composition.py`)
All 8 tamper categories are tested and refused fail-closed (`0 wrong served`):
1. Forged effect (`AnswerLength` on `ask_area`) $\rightarrow$ `AUXILIARY_RULE_MISMATCH`
2. Forged target (`points: ["A", "D"]` when quote asks `A, B`) $\rightarrow$ `SOURCE_OBJECT_MISMATCH`
3. Forged quote (not in problem text) $\rightarrow$ `QUOTE_NOT_IN_SOURCE` / `SOURCE_OBJECT_MISMATCH`
4. Uncertified point label (`K` not in figure) $\rightarrow$ `AUXILIARY_RULE_MISMATCH`
5. Swapped operands (`polygon: ["M", "A", "C"]` vs target `["A", "B"]`) $\rightarrow$ `AUXILIARY_RULE_MISMATCH`
6. Lying producer contract (`midpoint` claiming `centroid`) $\rightarrow$ `ENGINE_SELF_CHECK_FAILED`
7. Lying goal verifier (`ask_area` claiming `verifier="length"`) $\rightarrow$ `ENGINE_SELF_CHECK_FAILED`
8. Tampered engine coordinates vs kernel execution $\rightarrow$ `ENGINE_SELF_CHECK_FAILED`

---

## 5. Parallel Safety & Compatibility Check Against `research/semantic-extraction-v3`

We audited both Git hunks and semantic interactions against `research/semantic-extraction-v3` (`d785277d`) (full checklist in `handoff.md`):
- **Git Hunk Disjointness**:
  - `semantic-extraction-v3` does **not** modify `planner.py` or `engine.py`.
  - In `registry.py`, `semantic-extraction-v3` modifies lines `60–64`, `338–383`, `598–616`, `1352`, and `1666–1792` (exporting `NUMBER_PATTERN`, `_HOP_CHU_NHAT_KW`, `_DAI_BAO_NHIEU_KW`, `_khoi_dung(c)`, `_MAO_TU_KHOI`).
  - Our branch `research/contract-driven-goal-composition` modifies lines `258` (`PlanningTerm`), `403` (`ask_area` `PlanningContract`), `959–1012` (`_kiem_result_binding` `effect-chain`), and `2050–2059` (`_mau_muc_tieu_mo_ta`, `_mau_hoi_tat_ca`).
- **Semantic Compatibility & Compatibility Hypothesis**:
  1. **Right-Prism Grounding (`_khoi_dung`)**: Every prism, cuboid, and cube case in `contract-driven-goal-composition/corpus.json` places the solid cue (`lập phương`, `hộp chữ nhật`, `lăng trụ đứng`) immediately before the 2-face solid label (`ABCD.A'B'C'D'`, `ABC.A'B'C'`), satisfying `_khoi_dung(c)` in `semantic-extraction-v3`.
  2. **Default Response Contract (`RESPONSE_CONTRACT = "flat"`)**: 100% compatible without changes; `TypedFact` schema and `surface_fingerprint("flat")` are identical.
  3. **Compatibility Hypothesis for Research Schema-Contract v3 (`_contract_v3()` in `fact_extraction.py`)**: In `semantic-extraction-v3`, `_contract_v3()` defines `anyOf` variants for unnamed `point_kind` questions over `for quantity in ("length", "distance")`. We did **not** modify `fact_extraction.py` or the `semantic-extraction-v3` worktree. Whether extending that comprehension in `_contract_v3()` to include `"area"` (`points_b=labels(2, 2)`) is desired and sufficient for `RESPONSE_CONTRACT == "v3"` is recorded strictly as a **compatibility hypothesis to be tested on the combined integration candidate** after `semantic-extraction-v3` completes (see `handoff.md` §2.3).
  4. **Integration Status**: `FROZEN_PENDING_INTEGRATION` (`INTEGRATION_DEFERRED_PENDING_SEMANTIC_V3`).

---

## 6. Files Changed in Worktree (`research/contract-driven-goal-composition`)

- **Product files (3)**:
  - `backend/app/simulation/geometry_functions/registry.py`
  - `backend/app/simulation/geometry_functions/planner.py`
  - `backend/app/simulation/geometry_functions/engine.py`
- **Tests & measurement tooling (2)**:
  - `backend/tests/geometry/test_contract_driven_goal_composition.py` (68 tests)
  - `backend/scripts/measure_goal_composition.py` (`run-all` + `reconcile`)
- **Run package (`docs/evaluation/geometry/runs/contract-driven-goal-composition/`)**:
  - `run.json`, `report.md`, `quality-gate-report.md`, `handoff.md`, `oracle.py`, `corpus.json`, `red.txt`, `green.txt`, `green-quality-gate.txt`, `ablation.json`, `ablation-reconciled.json`, `regression-174.json`, `baseline/{receipt.json,bundle-174.json,regression-174.json}`

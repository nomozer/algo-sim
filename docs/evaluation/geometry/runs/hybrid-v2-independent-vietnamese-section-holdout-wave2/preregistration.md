# preregistration.md — `hybrid-v2-independent-vietnamese-section-holdout-wave2`

Registered and committed **before** any Wave 2 holdout case or oracle entry is authored. The preregistration, scoring contract, refusal taxonomy, and evaluator self-tests are committed first; the corpus, independent oracle, and expected labels are then authored by an isolated curator context, audited for independence and semantic deduplication, independently recomputed by a separate reviewer, and frozen (SHA-256 in `holdout-manifest.json`) before the product is executed once.

- **Task:** `HYBRID_V2_INDEPENDENT_VIETNAMESE_SECTION_HOLDOUT_WAVE2` (Owner GO 2026-10-27).
- **Authoritative Baseline (`main = origin/main = GitHub remote`):** `d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c` (Product commit `e3678608f1f7110d7046c9c43c312c69d7614f55`, T3 candidate `e7bcff316ee6d443e753105a887e0689ea04848b`).
- **Measured System:** `118` product files, `measured_system.tree_hash = 84ccf653441d1bd54f352756b9a5e917ee02a9ea11a83ac60585dfc585f3f99f`.
- **Architecture Versions:** Registry `geometry-functions/18`, Planner `geometry-fact-planner/17`, Engine `geometry-function-engine/14`, Adapter `hybrid-simulation-adapter/4`, Certificate `plane-section-certificate/1`, `CACHE_VERSION = 130`, `DEFAULT_MODE = LLM_ONLY` (Hybrid opt-in only).
- **Live Provider Calls:** `0` (`ALLOW_LIVE_AI = 0`). No product edits during the wave.

---

## 1. Research Questions

1. **RQ1 (Track A — Primary Generalization & Mathematical Accuracy):** Given 48 newly authored, previously unseen Vietnamese spatial-geometry section problems within the contract-supported family matrix (36 Category B plane-only problems and 12 Category A stated-intersection problems) paired with faithful `typed-fact-next/2` payloads, what proportion does the frozen deterministic Hybrid V2 pipeline (`run_typed_fact_next_v2_route` → `build_adapter4_response`: Bridge `/2` → Registry Source Gate `/18` → Planner `/17` → Engine `/14` → Adapter `/4`) serve with exact mathematical agreement against an independent exact-`Fraction` oracle?
2. **RQ2 (Track A — Fail-Closed Safety & Refusal Accuracy):** Given 48 newly authored negative and adversarial Vietnamese section problems/payloads across 16 failure classes (including boundary cases designed to challenge the M1–M5 repairs), does the frozen pipeline refuse 100% of negative cases (`0` wrong-served negatives) and emit refusal codes within the preregistered acceptable refusal categories?
3. **RQ3 (Track B — Contract Representability):** Across all 96 problems, how does the problem text classify under the `typed-fact-next/2` contract (`representable_without_loss`, `missing_required_information`, `ambiguous`, `contradictory`, `unsupported_relation`, `unsupported_topology`, `not_representable_by_current_contract`), and where do remaining post-M1–M5 pipeline refusals occur relative to contract representability?
4. **RQ4 (Scene3D Learner-Facing Semantics):** Among served problems, (a) are all Scene3D objects free of source-identity leaks (no internal auxiliary identifier masquerading as `origin == "given"` or appearing in plane/section/solid/answer names), and (b) how often do O4/R1-mandated pedagogical auxiliary points (`R2_AUXILIARY_POINT_NOTATION_DEFERRED`) appear with explicit `origin == "derived"` / `role == "Điểm dựng phụ"` distinction?

Track A evaluates the deterministic Hybrid V2 pipeline from `problem_text` + `typed-fact-next/2` payload. It is **not** a live natural-language extraction or OCR evaluation (`LIVE_NL_E2E_NOT_MEASURED`), and no browser execution claim is made (`BROWSER_E2E_NOT_MEASURED`).

---

## 2. Inclusion and Exclusion Rules

- **Evidence Boundary:**
  - Holdout Wave 1 (`hybrid-v2-independent-vietnamese-section-holdout`, `H001..H084`, now classified as `POST_FEEDBACK_DEVELOPMENT_REGRESSION`) and the M1–M5 development corpus (`hybrid-v2-holdout-failure-repair`, `D001..D016`, `N001..N016`) are strictly off-limits and may not contribute problems, templates, vertex relabellings, uniform rescalings, or expected answers to Wave 2.
- **Pre-Freeze Inclusion Criteria:**
  - Every problem must be newly authored in natural Vietnamese spatial-geometry prose.
  - Every `SERVE` case (`W2-B01..W2-B36`, `W2-A01..W2-A12`) must be mathematically well-defined, non-degenerate (cutting plane intersects the convex polyhedron in a polygon of $\ge 3$ vertices), representable without loss in `typed-fact-next/2`, and within the contract-level supported family matrix (`supported-family-matrix.md`), with exact rational `area_squared`.
  - Do **not** classify a mathematically valid, contract-representable problem as unsupported merely because the current implementation has a known limitation (such as Engine `/14`'s `Radical` factorization cap or partial stated intersections). If a valid positive case hits such a limit, it must be included as `expected_disposition = "SERVE"` and scored honestly if refused (`FALSE_REFUSAL`).
- **Pre-Freeze Exclusion / Replacement Protocol:**
  - Before freezing, automated checks are restricted to:
    1. Input-schema parsing (`parse_typed_fact_next_v2`) for positive payloads (ensuring no accidental curator schema typo invalidates a positive test item).
    2. 9-dimensional semantic deduplication (`tools/dedup_check_wave2.py`) against all historical corpora and fixtures.
    3. Independent oracle self-check (`oracle/oracle_holdout_wave2.py --check`) and independent reviewer recomputation of all 48 positive cases.
  - Any case failing pre-freeze deduplication or oracle mathematical validity is replaced by the curator **before** product execution, with every replacement logged in `corpus-provenance.md`.
  - **Product execution (`run_typed_fact_next_v2_route`, `build_adapter4_response`, `registry.kiem_nguon`, `planner`, `engine`) is strictly prohibited before the corpus, oracle, expected labels, and scorer are frozen in `holdout-manifest.json`.**
- **Post-Freeze Rule:** Zero cases may be excluded, removed, or edited after `holdout-manifest.json` is committed. Every one of the 96 cases remains in the final denominator.

---

## 3. Family Coverage, Case Counts, and Strata (96 Cases Total)

| Stratum | Case IDs | Count | Description |
|---|---|---:|---|
| `P-B` (Supported Category B — plane-only derived section) | `W2-B01` .. `W2-B36` | 36 | 6 solid families (`triangular_pyramid`, `quadrilateral_pyramid`, `right_triangular_prism`, `oblique_triangular_prism`, `cuboid`, `cube`) $\times$ 3 cutting-plane relations (`perpendicular_line`, `parallel_plane`, `parallel_two_lines`) $\times$ 2 independently designed problems per cell. Balanced across `question_type`: `section_only` (12), `area_only` (12), `section_and_area` (12). Expected certificate category: `ENGINE_DERIVED_SECTION`. |
| `P-A` (Supported Category A — source-stated edge intersections) | `W2-A01` .. `W2-A12` | 12 | 6 pyramids (`3` `triangular_pyramid`, `3` `quadrilateral_pyramid`) and 6 prisms (`2` `right_triangular_prism`, `1` `oblique_triangular_prism`, `2` `cuboid`, `1` `cube`) with source-stated edge intersections (`stated_intersections`). Covers through-points coinciding with solid vertices (4 cases) and all-interior edge cuts (8 cases), named (`named_intersection`) and unnamed (`fresh_intersection`) cut points, exact cut ratios, and balanced `question_type`: `section_only` (4), `area_only` (4), `section_and_area` (4). Expected certificate category: `DINH_CAT_CANH`. |
| `N` (Negative / Adversarial / Unsupported / Ambiguous) | `W2-N01` .. `W2-N48` | 48 | 16 negative classes $\times$ 3 cases per class (`wrong_solid_identity`, `contradictory_solid_kind`, `wrong_cutting_plane`, `ambiguous_plane_name`, `multiple_planes`, `multiple_solids`, `incorrect_source_quotations`, `unsupported_topology`, `missing_dimensions`, `underconstrained_geometry`, `conditional_or_negated_premises`, `wrong_question_target`, `incorrect_named_section`, `ambiguous_anaphoric_area_request`, `contradictory_cut_point_claims`, `degenerate_or_tampered_section_plane`). Includes cases specifically challenging M1–M5 boundaries. |
| **Total** | | **96** | **48 Positive (`SERVE`) + 48 Negative (`REFUSE`)** |

---

## 4. Expected Dispositions & Refusal-Code Scoring Rules

- **Positive cases (`W2-B01..W2-B36`, `W2-A01..W2-A12`):** `expected_disposition = "SERVE"`.
- **Negative cases (`W2-N01..W2-N48`):** `expected_disposition = "REFUSE"`, with `acceptable_categories` registered before execution from `tools/refusal_taxonomy.json`:
  - `SOURCE_GROUNDING`
  - `CONTRADICTION`
  - `UNDERDETERMINED`
  - `AMBIGUOUS`
  - `UNSUPPORTED_CAPABILITY`
  - `GEOMETRY_DEGENERATE`
  - `INPUT_INVALID`
- `INTERNAL_OR_VALIDATION` is **never** an acceptable refusal category for any case.
- Multiple acceptable categories are registered only when a defect can legitimately be caught at more than one architectural boundary (for example, a contradictory or ungrounded section claim that may be refused at Bridge `/2`, Source Gate `/18`, Planner `/17`, or Engine `/14`).

---

## 5. Exact-Oracle Verification Rules

1. The oracle (`oracle/oracle_holdout_wave2.py`) is implemented in pure Python using `fractions.Fraction` only, with **zero** imports from `app.*`.
2. For each of the 48 positive cases (`W2-B01..W2-B36`, `W2-A01..W2-A12`), `oracle/geometry.json` specifies an exact rational orthonormal 3D coordinate embedding consistent with all metric premises in `problem_text` (side lengths, right angles, altitudes, regular bases, projections).
3. From `oracle/geometry.json`, `oracle/oracle_holdout_wave2.py` derives the cutting plane from the stated geometric relation (`perpendicular_line` via normal vector, `parallel_plane` via cross product of reference plane edges, `parallel_two_lines` via cross product of the two direction vectors, or `stated_intersections` via plane through the stated points/through-point, verifying coplanarity when $\ge 4$ points are stated) and computes the exact convex polygon intersection of the cutting plane with the polyhedron:
   - `solid`: canonical solid notation (e.g., `"S.ABC"`, `"ABC.A'B'C'"`).
   - `section_id`: expected section identifier.
   - `expected_certificate_category`: `"ENGINE_DERIVED_SECTION"` for `P-B`, `"DINH_CAT_CANH"` for `P-A`.
   - `area_goal_id`: math goal ID when area is asked (`area_only` or `section_and_area`), else `null`.
   - `vertex_count`: exact number of polygon vertices ($\ge 3$).
   - `boundary`: cyclic list of boundary vertices around the section polygon, where each vertex is explicitly classified as:
     - `{"vertex": "<LABEL>"}` when the section vertex coincides with a polyhedron vertex ($t \in \{0, 1\}$), **or**
     - `{"edge": ["<U>", "<V>"], "t": "<p/q>"}` when the section vertex lies strictly in the interior of polyhedron edge $UV$ ($0 < t < 1$, with $P = (1 - t)U + tV$).
   - `area_squared`: exact rational string `"p/q"` for $(\text{Area})^2$ of the section polygon (computed via exact 3D cross-product triangulation in the orthonormal frame; always populated in `expected.json` as a geometric invariant, while the scorer checks `kq_<area_goal_id>` when `area_goal_id` is non-null and also checks `closure_certificate.area_squared` for Category B).
4. **Independent Reviewer Re-Verification:** Before freezing `holdout-manifest.json`, a separate reviewer context independently recomputes all 48 positive oracle cases from the problem texts and verifies 100% agreement on `vertex_count`, canonical `boundary`, and `area_squared`.

---

## 6. Definitions of Outcomes (`SERVED_CORRECT`, `WRONG_SERVED`, `FALSE_REFUSAL`, etc.)

Full operational details are specified in [`scoring-contract.md`](scoring-contract.md). In summary:

- **`SERVED_CORRECT`**: `expected_disposition == "SERVE"`, product serves (`r.status == "SERVED"`, `route_d.status == "SERVED"`, `envelope.status == "ok"`), and **all** exact oracle checks pass (solid identity, section object presence, certificate presence and category `ENGINE_DERIVED_SECTION` vs `DINH_CAT_CANH` without mixing, exact vertex count, exact solid-vertex set and interior edge-cut `(edge, t)` set, cyclic polygon equivalence up to starting vertex and orientation, and exact `area_squared`).
- **`WRONG_SERVED`**:
  - On a `SERVE` case: product serves, but **any** oracle or certificate check fails.
  - On a `REFUSE` case: product serves instead of refusing.
- **`FALSE_REFUSAL`**: `expected_disposition == "SERVE"`, and product refuses (or raises an unhandled product exception).
- **`REFUSED_CORRECT_REASON`**: `expected_disposition == "REFUSE"`, product refuses, and the mapped refusal category is in `acceptable_categories` (and is not `INTERNAL_OR_VALIDATION`).
- **`REFUSED_REASON_DISAGREEMENT`**: `expected_disposition == "REFUSE"`, product refuses, and the mapped refusal category is not in `acceptable_categories` (or is `UNMAPPED` / `INTERNAL_OR_VALIDATION`).
- **`PRODUCT_EXCEPTION`**: Product raises an unhandled Python exception during `run_typed_fact_next_v2_route` or `build_adapter4_response` (counted as a product failure: `FALSE_REFUSAL` on `SERVE` or `REFUSED_REASON_DISAGREEMENT` on `REFUSE`, and tracked explicitly under `internal_exceptions`).
- **`HARNESS_ERROR`**: Exception inside the evaluation harness/scorer itself after product execution.

---

## 7. Statistical Reporting & Scope Limits

- Report exact numerators, denominators, proportions, and descriptive two-sided 95% Wilson score intervals (`z = 1.959964`) for all primary metrics.
- Because the 96-case corpus is a stratified purposive sample designed to cover the 6-family $\times$ 3-relation matrix, Category A intersections, and 16 adversarial classes, Wilson intervals quantify finite-sample binomial precision only and **must not** be interpreted as THPT population or national curriculum accuracy.
- Do **not** use the 40/42 post-feedback score on Holdout Wave 1 as a blind baseline or claim a paired causal effect between Wave 1 and Wave 2.

---

## 8. Independence Criteria & Stop Conditions

- **Curator Firewall:** The curator context may read only the 8 allowed files listed in `curator-brief.md`. Every tool call in the curator's transcript is audited by `tools/audit_curator_log.py`.
- **Stop Conditions:**
  1. Product baseline or freeze verification mismatch (`freeze_evaluation_candidate.py --verify` $\ne$ `MATCH`) $\Rightarrow$ `EVALUATION_BLOCKED`.
  2. Any synthetic control test in `tools/test_evaluate_holdout_wave2.py` fails prior to opening the holdout $\Rightarrow$ `EVALUATION_BLOCKED`.
  3. Curator reads any forbidden product implementation (`registry.py`, `planner.py`, `engine.py`, `adapter4_route.py`, `typed_fact_next_bridge.py`), product test, or existing evaluation corpus $\Rightarrow$ `HOLDOUT_INDEPENDENCE_NOT_ESTABLISHED`.
  4. Fewer than 96 eligible deduplicated cases or unresolved oracle disagreement prior to freeze $\Rightarrow$ `EVALUATION_BLOCKED`.
  5. Any `HARNESS_ERROR` during the scored run $\Rightarrow$ preserve raw run untouched, document defect, and follow Section 9 below.

---

## 9. Handling of Harness Defects & Prohibition of Post-Result Tuning

- **No Post-Result Tuning:** Once `holdout-manifest.json` is committed and `evaluate_holdout_wave2.py` executes `results/scored-run-1/`, zero edits are permitted to product code, corpus payloads, oracle coordinates/expectations, acceptable refusal categories, or refusal taxonomy.
- **Harness Defect Protocol:** If a genuine scorer/harness defect is discovered after `results/scored-run-1/` is written, `results/scored-run-1/` must be preserved byte-identically, the harness defect must be proved with an independent mathematical receipt, and any corrected re-evaluation must be written to a separate directory (`results/scored-run-2-harness-corrected/`) with both raw and corrected numbers reported side by side.

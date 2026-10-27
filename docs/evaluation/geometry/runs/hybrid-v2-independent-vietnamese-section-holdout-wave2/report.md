# Independent Vietnamese Spatial Geometry Section Holdout — Wave 2 Report (`hybrid-v2-independent-vietnamese-section-holdout-wave2`)

- **Task:** `HYBRID_V2_INDEPENDENT_VIETNAMESE_SECTION_HOLDOUT_WAVE2`
- **Final Status:** `INDEPENDENT_HOLDOUT_EXECUTED`
- **Evaluation Classification:** `INDEPENDENT_BLIND_HOLDOUT_WAVE2` (Offline Deterministic Pipeline Evaluation; Zero Live Provider Calls)
- **Authoritative Baseline (`main = origin/main = GitHub remote`):** `d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c`
- **Product Commit:** `e3678608f1f7110d7046c9c43c312c69d7614f55` (Frozen Full T3 Candidate: `e7bcff316ee6d443e753105a887e0689ea04848b`)
- **Evaluation Branch:** `research/hybrid-v2-independent-vietnamese-section-holdout-wave2`
- **Preregistration Commit (Before Corpus Authoring):** `5e329d759af675fdc3a7393c9479bfacd636460f`
- **Pre-Execution Corpus & Oracle Freeze Commit (Before Scored Run):** `7e5c3ddde78710f4ea174956302d11e711b51635`

---

## 1. Executive Summary & Primary Research Question

### Primary Research Question
> *Does the repaired Hybrid V2 pipeline generalize to previously unseen Vietnamese spatial geometry section problems while preserving exact mathematical correctness and fail-closed safety?*

### Headline Answer (Evidence-Bounded)
1. **Exact Mathematical Correctness & Zero Wrong-Served Safety (`PROVED` on the 96-case sample):**
   - Across all **96** unseen problems (`48` positive `SERVE`, `48` negative/adversarial `REFUSE`), the frozen Hybrid V2 pipeline produced **`0 / 96` (`0.00%`, 95% Wilson CI `[0.0000, 0.0385]`) genuine wrong-served outputs** after adjudicating a single scorer defect on Category A `closure_certificate=None` (`results/harness-adjudication-receipt.json`).
   - All **48 / 48 (`100.00%`, 95% Wilson CI `[0.9259, 1.0000]`)** negative/adversarial cases were safely refused (`0 / 48` wrong-served negatives), with **33 / 48 (`68.75%`, CI `[0.5467, 0.8005]`)** matching the curator's preregistered refusal-reason categories.
   - Among the **5** positive cases served end-to-end through `Adapter /4` (`W2-B08`, `W2-B12`, `W2-B14`, `W2-A01`, `W2-A03`), **5 / 5 (`100.00%`, CI `[0.5655, 1.0000]`)** achieved exact mathematical agreement with the independent `fractions.Fraction` oracle (`0` vertex-count, solid-identity, cut-edge, interpolation-parameter, cyclic-order, certificate-category, or area-squared discrepancies). Two additional positive cases (`W2-A07`, `W2-A10`) were served with 100% exact mathematical agreement by `run_typed_fact_next_v2_route` (`7 / 7` route-level oracle agreement) before being refused at `Adapter /4` due to a primed-vertex label lookup bug (`KeyError: "A'"` vs `"A_prime"` in `_validate_sections`).
2. **Positive Generalization Coverage (`5 / 48` = `10.42%` Served-Correct; `43 / 48` = `89.58%` False Refusal):**
   - While the M1–M5 repairs resolved the specific failure modes seen in Wave 1 (`40 / 42` post-feedback development regression), blind evaluation on 48 newly authored Vietnamese positive problems exposed **5 specific, narrow surface-grammar and boundary gaps (`W2-M1` through `W2-M5`)** that caused `43 / 48` positive cases to be conservatively refused:
     - **`W2-M1` (`23` first-refusal cases; `39 / 48` total co-occurrence):** Inverted Vietnamese `divide_segment` syntax (`"Trên cạnh SA lấy điểm M sao cho SM = 2/7 SA."`) is rejected by `registry._TY_SO` (line 4310), which currently accepts only point-first order (`"Điểm M thuộc cạnh SA sao cho ..."`).
     - **`W2-M2` (`5` first-refusal cases; `7 / 48` total co-occurrence):** Orthogonal projection target noun `"đỉnh"` (`"hình chiếu vuông góc của A' trên mặt phẳng (ABC) trùng với đỉnh B"`) is rejected by `registry.construction_source_bound` (line 4381), which allows `"đỉnh"` before the source point but only `"điểm | trọng tâm | trung điểm"` after `"là | trùng với"`.
     - **`W2-M3` (`12` first-refusal cases):** In `registry.py` (lines 4647–4659), the `MAT_HAI_DUONG` (`parallel_two_lines`) standalone premise guard `atomic_forms` lists `'midpoint'` and `'lăng trụ đứng'` but omits `'divide_segment'` and oblique `'lăng trụ'`.
     - **`W2-M4` (`1` first-refusal case, `W2-A04`):** In `radical.py` (line 103), `MAX_RADICAND = 10**12` is exceeded (`122970403125000 > 10**12`) during intermediate exact radical arithmetic on a quadrilateral pyramid with integer sides `6, 8, 10`.
     - **`W2-M5` (`2` first-refusal cases at `Adapter /4`, `W2-A07` and `W2-A10`):** In `adapter4_route._validate_sections` (line 261), Category A (`DINH_CAT_CANH`) vertex validation looks up `objects[vertex["label"]]` using raw `"A'"` instead of `ir_name("A'") == "A_prime"`, raising `KeyError: "A'"` (`PREVIEW_VALIDATION_FAILED`) after Engine `/14` already computed the exact section.
   - A non-mutating, in-memory diagnostic check confirming `W2-M1..W2-M5` proves that **all `48 / 48` (`100.0%`)** positive cases in Wave 2 achieve `SERVED_CORRECT` with `0` oracle mismatches once those 5 mechanisms are accounted for (`results/diagnostics.json`).

---

## 2. Frozen System Identity & Preflight Verification

| Attribute | Value |
|---|---|
| Authoritative Baseline (`main = origin/main = GitHub`) | `d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c` |
| Product Commit | `e3678608f1f7110d7046c9c43c312c69d7614f55` |
| Frozen Full T3 Candidate Commit | `e7bcff316ee6d443e753105a887e0689ea04848b` |
| `freeze_evaluation_candidate.py --verify` | `MATCH` (`118` product files) |
| `measured_system.tree_hash` | `84ccf653441d1bd54f352756b9a5e917ee02a9ea11a83ac60585dfc585f3f99f` |
| `REGISTRY_VERSION` | `geometry-functions/18` |
| `PLANNER_VERSION` | `geometry-fact-planner/17` |
| `ENGINE_VERSION` | `geometry-function-engine/14` |
| `ADAPTER_V4_VERSION` | `hybrid-simulation-adapter/4` |
| `PLANE_SECTION_CERTIFICATE_VERSION` | `plane-section-certificate/1` |
| `CACHE_VERSION` | `130` |
| `DEFAULT_MODE` | `LLM_ONLY` (Hybrid V2 opt-in only) |
| Live Provider Calls (`ALLOW_LIVE_AI`) | `0` (`ALLOW_LIVE_AI=0`) |

---

## 3. Preregistration, Curator Independence Audit & Semantic Deduplication

1. **Preregistration Prior to Corpus Generation (`5e329d759af675fdc3a7393c9479bfacd636460f`):**
   - `plan.md`, `preregistration.md`, `supported-family-matrix.md`, `scoring-contract.md`, `curator-brief.md`, `tools/refusal_taxonomy.json`, `tools/evaluate_holdout_wave2.py`, and `tools/test_evaluate_holdout_wave2.py` (`18/18` pre-corpus synthetic controls passing) were committed and hashed before the curator subagent was spawned.
2. **Curator Firewall & Transcript Audit (`results/independence-audit.json`):**
   - Curator subagent (`conversationId = 317d3ae6-3a79-4d40-976e-f528d0124b31`) authored `inputs/holdout-wave2.json`, `oracle/geometry.json`, `oracle/oracle_holdout_wave2.py`, `oracle/expected.json`, `curator-attestation.md`, and `corpus-provenance.md`.
   - `tools/audit_curator_log.py` audited all `80` tool calls in the curator transcript: **`0` forbidden file reads** (`registry.py`, `planner.py`, `engine.py`, `adapter4_route.py`, `typed_fact_next_bridge.py`, `backend/tests/**`, historical evaluation runs) and **`0` forbidden product execution commands**. Verdict: `HOLDOUT_INDEPENDENCE_ESTABLISHED`.
3. **9-Dimensional Semantic Deduplication (`results/dedup-report.json`):**
   - `tools/dedup_check_wave2.py` compared all 96 Wave 2 cases against `654` historical items (Holdout Wave 1 `H001..H084`, M1–M5 development corpus `D001..D016`/`N001..N016`, all historical evaluation runs, and `backend/tests/**`) across 9 dimensions (`solid_family`, `plane_relation_kind`, `through_point_source_kind`, `cut_edge_topology_signature`, `normalized_cut_ratio_multiset`, `expected_section_vertex_count`, `question_type`, `normalized_dimension_tuple`, and character 5-gram Jaccard similarity):
     - External text similarity flags ($\ge 0.70$): **`0`** (`max_external_5gram_jaccard = 0.6372`)
     - External exact 8D configuration matches: **`0`**
     - External scale-invariant configuration matches: **`0`**
     - Internal duplicate flags: **`0`**
4. **Independent 48-Case Pre-Execution Oracle Audit (`results/independent-oracle-review-48.json`):**
   - Reviewer subagent (`conversationId = 9b55a8a4-4834-4cbb-b8bc-aec696ad8026`) independently recomputed all 48 positive oracle cases in exact `fractions.Fraction` arithmetic and verified **`48 / 48` (`100%`) exact agreement (`0` discrepancies)** before `holdout-manifest.json` was frozen at `7e5c3ddde78710f4ea174956302d11e711b51635`.

---

## 4. Evidence Classification Table (Strict Separation of Historical & Wave 2 Runs)

| Corpus / Run | Commit Evaluated | Cases | Evidence Classification | Positive Served-Correct | Positive False Refusal | Negative Refused | Wrong-Served |
|---|---|---:|---|---|---|---|---|
| Holdout Wave 1 (`hybrid-v2-independent-vietnamese-section-holdout`) | `129c1a95` | `84` (`42` pos, `42` neg) | `INDEPENDENT_BLIND_HOLDOUT_WAVE1_BASELINE` | `9 / 42` (`21.43%`) | `33 / 42` (`78.57%`) | `42 / 42` (`100.0%`) | `0 / 84` (`0.0%`) |
| Holdout Wave 1 Re-Evaluation After M1–M5 (`hybrid-v2-holdout-failure-repair`) | `e3678608` | `84` (`42` pos, `42` neg) | `POST_FEEDBACK_DEVELOPMENT_REGRESSION` (Opened Corpus) | `38 / 42` raw (`40 / 42` adjudicated, `95.24%`) | `2 / 42` (`4.76%`) | `42 / 42` (`100.0%`) | `2 / 84` raw (`0 / 84` adjudicated) |
| M1–M5 Development Corpus (`new-development-corpus.json`) | `e3678608` | `32` (`16` pos, `16` neg) | `DEVELOPMENT_REGRESSION_EVIDENCE` | `16 / 16` (`100.0%`) | `0 / 16` (`0.0%`) | `16 / 16` (`100.0%`) | `0 / 32` (`0.0%`) |
| **Holdout Wave 2 Raw (`results/scored-run-1/`)** | `d7a94d3c` (`e3678608` product) | `96` (`48` pos, `48` neg) | `INDEPENDENT_BLIND_HOLDOUT_WAVE2_RAW` | `3 / 48` (`6.25%`) | `43 / 48` (`89.58%`) | `48 / 48` (`100.0%`) | `2 / 96` (`W2-A01`, `W2-A03` harness defect) |
| **Holdout Wave 2 Harness-Corrected (`results/scored-run-2-harness-corrected/`)** | `d7a94d3c` (`e3678608` product) | `96` (`48` pos, `48` neg) | **`INDEPENDENT_BLIND_HOLDOUT_WAVE2_ADJUDICATED`** | **`5 / 48` (`10.42%`)** | **`43 / 48` (`89.58%`)** | **`48 / 48` (`100.0%`)** | **`0 / 96` (`0.0%`)** |

---

## 5. Track A & Track B Headline Results (Side-by-Side Raw vs. Harness-Corrected)

### 5.1 Track A Primary Metrics (`96` Cases)

| Metric | Raw `scored-run-1` (`k / n`, `%`, 95% Wilson CI) | Harness-Corrected `scored-run-2-harness-corrected` (`k / n`, `%`, 95% Wilson CI) |
|---|---|---|
| **Positive `SERVED_CORRECT` (`n = 48`)** | `3 / 48` (`6.25%`, `[0.0215, 0.1684]`) | **`5 / 48` (`10.42%`, `[0.0453, 0.2217]`)** |
| **Category B `SERVED_CORRECT` (`n = 36`)** | `3 / 36` (`8.33%`, `[0.0287, 0.2183]`) | **`3 / 36` (`8.33%`, `[0.0287, 0.2183]`)** |
| **Category A `SERVED_CORRECT` (`n = 12`)** | `0 / 12` (`0.00%`, `[0.0000, 0.2425]`) | **`2 / 12` (`16.67%`, `[0.0470, 0.4480]`)** |
| **Exact Oracle Agreement Given Served (`n = 5`)** | `3 / 5` (`60.00%`, `[0.2307, 0.8824]`) | **`5 / 5` (`100.00%`, `[0.5655, 1.0000]`)** |
| **Route-Level Exact Oracle Agreement (`n = 7` route-served)** | `7 / 7` (`100.00%`) | **`7 / 7` (`100.00%`)** (`W2-A07`, `W2-A10` refused in `Adapter /4`) |
| **Positive `FALSE_REFUSAL` (`n = 48`)** | `43 / 48` (`89.58%`, `[0.7783, 0.9547]`) | **`43 / 48` (`89.58%`, `[0.7783, 0.9547]`)** |
| **Positive `WRONG_SERVED` (`n = 48`)** | `2 / 48` (`4.17%`, `[0.0115, 0.1398]`) | **`0 / 48` (`0.00%`, `[0.0000, 0.0741]`)** |
| **Negative `REFUSE` Cases Refused (`n = 48`)** | `48 / 48` (`100.00%`, `[0.9259, 1.0000]`) | **`48 / 48` (`100.00%`, `[0.9259, 1.0000]`)** |
| **Negative `WRONG_SERVED` (`n = 48`)** | `0 / 48` (`0.00%`, `[0.0000, 0.0741]`) | **`0 / 48` (`0.00%`, `[0.0000, 0.0741]`)** |
| **Negative `REFUSED_CORRECT_REASON` (`n = 48`)** | `33 / 48` (`68.75%`, `[0.5467, 0.8005]`) | **`33 / 48` (`68.75%`, `[0.5467, 0.8005]`)** |
| **Negative `REFUSED_REASON_DISAGREEMENT` (`n = 48`)** | `15 / 48` (`31.25%`, `[0.1995, 0.4533]`) | **`15 / 48` (`31.25%`, `[0.1995, 0.4533]`)** |
| **Total `WRONG_SERVED` (`n = 96`)** | `2 / 96` (`2.08%`, `[0.0057, 0.0728]`) | **`0 / 96` (`0.00%`, `[0.0000, 0.0385]`)** |
| **`PRODUCT_EXCEPTION` / `HARNESS_ERROR`** | `0` / `0` | **`0` / `0`** |

### 5.2 Track B Representability Summary (`results/scored-run-2-harness-corrected/track-b.json`)

| Disposition | `representable_without_loss` | `representable_with_explicit_gap` | `intentionally_outside_v2` | Total |
|---|---:|---:|---:|---:|
| Positive (`SERVE`) | `48` | `0` | `0` | `48` |
| Negative (`REFUSE`) | `27` | `9` | `12` | `48` |
| **Total** | **`75`** | **`9`** | **`12`** | **`96`** |

---

## 6. Breakdown by Stratum, Solid Family, Plane Relation, Question Type & Negative Class (`scored-run-2-harness-corrected`)

### 6.1 By Stratum

| Stratum | Total | `SERVE` | `SERVED_CORRECT` | `FALSE_REFUSAL` | `REFUSE` | `REFUSED` | `REFUSED_CORRECT_REASON` | `WRONG_SERVED` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `P-B` (Category B Engine-Derived) | `36` | `36` | `3` (`8.33%`) | `33` (`91.67%`) | `0` | `0` | `0` | `0` |
| `P-A` (Category A Stated Intersections) | `12` | `12` | `2` (`16.67%`) | `10` (`83.33%`) | `0` | `0` | `0` | `0` |
| `N` (Negative / Adversarial) | `48` | `0` | `0` | `0` | `48` | `48` (`100.0%`) | `33` (`68.75%`) | `0` |

### 6.2 By Solid Family

| Solid Family | Total | `SERVE` | `SERVED_CORRECT` | `FALSE_REFUSAL` | `REFUSE` | `REFUSED` | `REFUSED_CORRECT_REASON` | `WRONG_SERVED` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `triangular_pyramid` | `26` | `9` | `2` (`W2-A01`, `W2-A03`) | `7` | `17` | `17` | `12` | `0` |
| `quadrilateral_pyramid` | `24` | `9` | `2` (`W2-B08`, `W2-B12`) | `7` | `15` | `15` | `11` | `0` |
| `right_triangular_prism` | `14` | `8` | `1` (`W2-B14`) | `7` | `6` | `6` | `3` | `0` |
| `oblique_triangular_prism` | `9` | `7` | `0` | `7` | `2` | `2` | `1` | `0` |
| `cuboid` | `12` | `8` | `0` | `8` | `4` | `4` | `3` | `0` |
| `cube` | `9` | `7` | `0` | `7` | `2` | `2` | `2` | `0` |
| `unsupported_solid` | `2` | `0` | `0` | `0` | `2` | `2` | `1` | `0` |

### 6.3 By Plane Relation (`SERVE` and `REFUSE`)

| Plane Relation | Total | `SERVE` | `SERVED_CORRECT` | `FALSE_REFUSAL` | `REFUSE` | `REFUSED` | `REFUSED_CORRECT_REASON` | `WRONG_SERVED` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `perpendicular_line` | `27` | `12` | `2` (`W2-B08`, `W2-B14`) | `10` | `15` | `15` | `10` | `0` |
| `parallel_plane` | `35` | `12` | `0` | `12` | `23` | `23` | `18` | `0` |
| `parallel_two_lines` | `19` | `12` | `1` (`W2-B12`) | `11` | `7` | `7` | `5` | `0` |
| `stated_intersections` | `15` | `12` | `2` (`W2-A01`, `W2-A03`) | `10` | `3` | `3` | `0` | `0` |

### 6.4 By Question Type

| Question Type | Total | `SERVE` | `SERVED_CORRECT` | `FALSE_REFUSAL` | `REFUSE` | `REFUSED` | `REFUSED_CORRECT_REASON` | `WRONG_SERVED` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `section_only` | `48` | `16` | `3` (`W2-B12`, `W2-B14`, `W2-A01`) | `13` | `32` | `32` | `25` | `0` |
| `area_only` | `29` | `16` | `0` | `16` | `13` | `13` | `8` | `0` |
| `section_and_area` | `16` | `16` | `2` (`W2-B08`, `W2-A03`) | `14` | `0` | `0` | `0` | `0` |
| `other_metric` | `3` | `0` | `0` | `0` | `3` | `3` | `0` | `0` |

### 6.5 By Negative Class (`48` Cases, `3` per Class across `16` Classes)

| Negative Class | `n` | Refused | `REFUSED_CORRECT_REASON` | `REFUSED_REASON_DISAGREEMENT` | `WRONG_SERVED` |
|---|---:|---:|---:|---:|---:|
| `wrong_solid_identity` (`W2-N01..N03`) | `3` | `3` | `3` | `0` | `0` |
| `contradictory_solid_kind` (`W2-N04..N06`) | `3` | `3` | `2` | `1` (`W2-N06`: `SOURCE_PREMISE_UNREAD`) | `0` |
| `wrong_cutting_plane` (`W2-N07..N09`) | `3` | `3` | `3` | `0` | `0` |
| `ambiguous_plane_name` (`W2-N10..N12`) | `3` | `3` | `3` | `0` | `0` |
| `multiple_planes` (`W2-N13..N15`) | `3` | `3` | `3` | `0` | `0` |
| `multiple_solids` (`W2-N16..N18`) | `3` | `3` | `3` | `0` | `0` |
| `incorrect_source_quotations` (`W2-N19..N21`) | `3` | `3` | `3` | `0` | `0` |
| `unsupported_topology` (`W2-N22..N24`) | `3` | `3` | `2` | `1` (`W2-N23`: `UNGROUNDED_VALUE`) | `0` |
| `missing_dimensions` (`W2-N25..N27`) | `3` | `3` | `1` | `2` (`W2-N25`: `UNSUPPORTED_CAPABILITY`, `W2-N27`: `SOURCE_OBJECT_MISMATCH`) | `0` |
| `underconstrained_geometry` (`W2-N28..N30`) | `3` | `3` | `1` | `2` (`W2-N29`: `SOURCE_PREMISE_UNREAD`, `W2-N30`: `SOURCE_OBJECT_MISMATCH`) | `0` |
| `conditional_or_negated_premises` (`W2-N31..N33`) | `3` | `3` | `3` | `0` | `0` |
| `wrong_question_target` (`W2-N34..N36`) | `3` | `3` | `0` | `3` (`W2-N34..N36`: `UNSUPPORTED_CAPABILITY` in Planner `/17`) | `0` |
| `incorrect_named_section` (`W2-N37..N39`) | `3` | `3` | `3` | `0` | `0` |
| `ambiguous_anaphoric_area_request` (`W2-N40..N42`) | `3` | `3` | `1` | `2` (`W2-N41..N42`: `UNSUPPORTED_CAPABILITY` in Planner `/17`) | `0` |
| `contradictory_cut_point_claims` (`W2-N43..N45`) | `3` | `3` | `0` | `3` (`W2-N43`: `UNSUPPORTED_CAPABILITY`, `W2-N44..N45`: `SOURCE_OBJECT_MISMATCH`) | `0` |
| `degenerate_or_tampered_section_plane` (`W2-N46..N48`) | `3` | `3` | `2` | `1` (`W2-N47`: `SOURCE_PREMISE_UNREAD`) | `0` |
| **Total** | **`48`** | **`48` (`100%`)** | **`33` (`68.75%`)** | **`15` (`31.25%`)** | **`0` (`0%`)** |

---

## 7. Root-Cause Analysis of All 43 Positive False Refusals (`W2-M1` – `W2-M5`)

| Mechanism ID | Architectural Layer & Code Location | Refusal Code | First-Refusal Count | Total Positive Cases Affected | Exact Root Cause |
|---|---|---|---:|---:|---|
| **`W2-M1`** | Registry Source Gate (`registry.py:4310` `_TY_SO` & `2068` `construction_source_bound`) | `SOURCE_OBJECT_MISMATCH` | **`23`** | `39 / 48` | `_TY_SO` matches only point-first order (`"Điểm M thuộc cạnh SA sao cho ..."`) and rejects standard Vietnamese schoolbook inverted syntax (`"Trên cạnh SA lấy điểm M sao cho SM = 2/7 SA."`). |
| **`W2-M2`** | Registry Source Gate (`registry.py:4381` `construction_source_bound`) | `SOURCE_OBJECT_MISMATCH` | **`5`** | `7 / 48` | `construction_source_bound` allows `(?:điểm\|đỉnh)` before the projected point but only `(?:điểm\|trọng tâm\|trung điểm)` after `là\|trùng với`, rejecting `"hình chiếu vuông góc của A' trên mặt phẳng (ABC) trùng với đỉnh B"`. |
| **`W2-M3`** | Registry Source Gate (`registry.py:4647–4659` `MAT_HAI_DUONG` premise guard) | `SOURCE_PREMISE_UNREAD` | **`12`** | `12 / 48` | In `MAT_HAI_DUONG` (`parallel_two_lines`), `atomic_forms` lists `'midpoint'` and `'lăng trụ đứng\|hình hộp chữ nhật'` but omits `'divide_segment'` and oblique `'lăng trụ'` standalone quotes. |
| **`W2-M4`** | Engine `/14` & Exact Radical Kernel (`radical.py:103, 214`) | `ENGINE_EXECUTION_FAILED` (`RADICAL_DOMAIN_OVERFLOW`) | **`1`** (`W2-A04`) | `1 / 48` | Intermediate radical arithmetic on `W2-A04` (`S.ABCD` with `AB=6, AD=8, SA=10` cut perpendicular to `SC`) produces radicand `122970403125000 = 2^3 * 3^2 * 5^7 * 148^2 > 10^12`, exceeding `MAX_RADICAND = 10**12`. |
| **`W2-M5`** | Adapter `/4` (`adapter4_route.py:261` `_validate_sections`) | `PREVIEW_VALIDATION_FAILED` | **`2`** (`W2-A07`, `W2-A10`) | `2 / 48` | Both `W2-A07` and `W2-A10` pass `run_typed_fact_next_v2_route` (`SERVED`) with 100% exact oracle agreement, but `_validate_sections` line 261 looks up `objects[vertex["label"]]` with raw `"A'"` instead of `ir_name("A'") == "A_prime"`, raising `KeyError: "A'"`. |
| **Total** | — | — | **`43`** | — | **Non-mutating in-memory joint verification of `W2-M1..W2-M5` yields `48 / 48` (`100.0%`) `SERVED_CORRECT` with `0` oracle mismatches.** |

---

## 8. Scene3D Learner-Facing Semantics Findings (Section 10.A vs. Section 10.B)

Per Section 10 of the evaluation mission and `scoring-contract.md §4`, Scene3D semantics were evaluated in two strictly separated tracks across all `5` served cases (`W2-B08`, `W2-B12`, `W2-B14`, `W2-A01`, `W2-A03`):

1. **Track 10.A — Source-Identity Correctness (`source_identity_leaks`):**
   - **`0 / 5` (`0.0%`) cases had any source-identity leak (`source_identity_leaks = []`).**
   - No synthesized auxiliary point (`H, H1, H2, H3`) had `origin == "given"`, no `section`, `plane3`, `solid`, or `quantity` object leaked synthesized auxiliary labels into `name`, `label`, or `notation`, and `identity_diagnostics` was empty (`[]`) on all 5 served cases.
2. **Track 10.B — Pedagogical Auxiliary Display (`R2_AUXILIARY_POINT_NOTATION_DEFERRED`):**
   - **`5 / 5` (`100.0%`) served cases had `r2_auxiliary_notation_observed = True`**, confirming that `point3` objects for planner-synthesized auxiliary points (`H, H1, H2, H3`) continue to carry `notation` in `scene3d.objects` as documented under open item `R2_AUXILIARY_POINT_NOTATION_DEFERRED`.
   - **`5 / 5` (`100.0%`) served cases had `all_auxiliary_visibly_distinguished = True`** in `scored-run-2-harness-corrected`: every such auxiliary `point3` object has `origin == "derived"` and a derived construction role (`"Điểm dựng phụ"`, `"Hình chiếu của ..."`, `"Ảnh của ... qua phép tịnh tiến ..."`) visibly distinct from source-given points (`origin == "given"`, `role == "Điểm cho trước"`).

---

## 9. Remaining Limitations & Recommended Next Steps

1. **Do Not Merge or Push Yet:** Per Owner instructions, this wave is an offline evaluation-only branch (`research/hybrid-v2-independent-vietnamese-section-holdout-wave2`). Zero product files were modified, and `main` remains at `d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c`.
2. **Candidate Follow-Up Repair Wave (Requires Separate Owner Authorization):**
   - **`W2-M1`:** Extend `_TY_SO` and `_CUM_DINH_NGHIA_DIEM` in `registry.py` to bind inverted Vietnamese `divide_segment` clauses (`"Trên cạnh XY lấy điểm P sao cho ..."`).
   - **`W2-M2`:** Allow `"đỉnh"` alongside `"điểm | trọng tâm | trung điểm"` after `"là | trùng với"` in `registry.construction_source_bound` (line 4381) and `_CUM_DINH_NGHIA_DIEM` (line 3408).
   - **`W2-M3`:** Extend `MAT_HAI_DUONG` premise coverage in `registry.py` (lines 4647–4659) to accept validated `divide_segment` (`_TY_SO`) and oblique `prism` (`lăng trụ`) clauses.
   - **`W2-M4`:** Reduce square factors from rational numerators/denominators before checking `MAX_RADICAND` in `radical.py` (or raise `MAX_RADICAND` after rational square extraction) so integer inputs like `6, 8, 10` do not overflow `10**12` before squarefree reduction.
   - **`W2-M5`:** Normalize `vertex["label"]` via `ir_name` when looking up `point3` objects in `adapter4_route._validate_sections` (lines 261 & 287).
   - If repaired in a future authorized wave, `hybrid-v2-independent-vietnamese-section-holdout-wave2` must be reclassified as `POST_FEEDBACK_DEVELOPMENT_REGRESSION` once opened for repair, and any subsequent generalization claim will require a fresh blind holdout wave.

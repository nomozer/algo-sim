# preregistration.md — `hybrid-v2-independent-vietnamese-geometry-holdout-wave3`

Registered and committed **before** any Wave 3 holdout case or oracle entry is authored. The preregistration, supported-family matrix, scoring contract, refusal taxonomy, deduplication protocol, oracle verification protocol, and synthetic scorer qualification self-tests (`tools/test_evaluate_holdout_wave3.py`) are committed first; the 144-case corpus, independent exact-`Fraction` oracle, and expected dispositions are then authored in an isolated curator context, audited for independence and 9-dimensional semantic deduplication, independently recomputed by a separate reviewer, and frozen (SHA-256 in `holdout-manifest.json`) before the product is executed once.

- **Task:** `HYBRID_V2_INDEPENDENT_VIETNAMESE_GEOMETRY_HOLDOUT_WAVE3`
- **Authoritative Baseline (`main = origin/main = GitHub remote`):** `e137623c4f674135a8d7884b78614c132eb78085` (Product commit `73ca8d92e74059680ce53b99692af396df37a2f8`, Frozen Full T3 candidate `b61f16995dfbe0110a639a2127d0fb5a9c3afde0`).
- **Measured System:** `118` product files, `measured_system.tree_hash = 1170ca163529dd40b57f4058826db92a6433359546aa2ad718712f38a538c10d`.
- **Architecture Versions:** Registry `geometry-functions/19`, Planner `geometry-fact-planner/17`, Engine `geometry-function-engine/14`, Adapter `hybrid-simulation-adapter/4`, Certificate `plane-section-certificate/1`, `CACHE_VERSION = 130`, `DEFAULT_MODE = LLM_ONLY` (Hybrid opt-in only).
- **Live Provider Calls:** `0` (`ALLOW_LIVE_AI = 0`). No product edits, no capability expansion, no merge, no push, and no worktree cleanup during this wave.

---

## 1. Research Questions & Evaluation Tracks

### Primary Research Question
> After the W2-M1 through W2-M5 repairs (including Registry `/19` Vietnamese phrasing generalization, W2-M4 exact square-factor radical normalization, and W2-M5 Adapter `/4` Category A primed-vertex identity mapping), does the frozen Hybrid V2 deterministic pipeline generalize to newly authored, previously unseen Vietnamese spatial-geometry plane-section problems while preserving exact mathematical correctness and fail-closed safety?

No prior assumption is made that the score will be high; all outcomes are reported as observed.

### Three Preregistered Evaluation Tracks
1. **Track A — Deterministic Pipeline (`run_typed_fact_next_v2_route` $\to$ `build_adapter4_response`):**
   - Evaluates the deterministic Hybrid V2 route from `problem_text` + faithful `typed-fact-next/2` payload through Bridge `/2` $\to$ Registry Source Gate `/19` $\to$ Planner `/17` $\to$ Engine `/14` $\to$ Adapter `/4`.
   - Measures end-to-end `SERVED` vs `REFUSED`, exact mathematical agreement with the independent `fractions.Fraction` 3D geometry oracle (`SERVED_CORRECT` vs `WRONG_SERVED` vs `FALSE_REFUSAL`), and fail-closed refusal accuracy on negative/adversarial cases (`REFUSED_CORRECT_REASON` vs `REFUSED_REASON_DISAGREEMENT` vs `WRONG_SERVED`).
   - Scope boundary: Track A evaluates the deterministic route from text + structured facts (`typed-fact-next/2`); it is **not** a live Gemini natural-language extraction or OCR evaluation (`LIVE_NL_E2E_NOT_MEASURED`).
2. **Track B — Contract Representability:**
   - Independently classifies each problem into:
     - `representable_without_loss`
     - `representable_with_explicit_gap` (or specific gap subclass: `missing_required_information`, `ambiguous`, `contradictory`)
     - `intentionally_outside_supported_v2_capability` (`unsupported_relation`, `unsupported_topology`, `not_representable_by_current_contract`)
   - Refusal of a problem that is intentionally outside the supported-family matrix is never counted as a false refusal of a `SERVE` case.
3. **Track C — Learner-Facing Scene3D Semantics:**
   - Evaluates all served cases for:
     - **Track C.1 (`source_identity_leaks`):** Source identity preservation, derived vs given entity separation (`origin == "given"` vs `"derived"`), primed-label display (`A'` / `A′` without raw `_prime` machine ID leakage), section notation, formula/entity mapping, and absence of planner-synthesized fresh labels leaking into learner-facing section/plane/solid/quantity names or masquerading as `origin == "given"`.
     - **Track C.2 (`pedagogical_auxiliary_display`):** Auxiliary construction point display (`origin == "derived"`, `role == "Điểm dựng phụ"`).
   - Scope boundary: JSON Scene3D inspection does not replace human browser/visual review (`BROWSER_E2E_NOT_MEASURED`).

---

## 2. Quarantine of Previously Opened Corpora & Inclusion/Exclusion Rules

### 2.1 Quarantined Historical & Development Corpora (Off-Limits for Wave 3)
All previously opened corpora are classified as historical or `POST_FEEDBACK_DEVELOPMENT_REGRESSION` and are strictly off-limits for Wave 3 authoring:
1. **Independent Holdout Wave 1** (`hybrid-v2-independent-vietnamese-section-holdout`, `H001..H084`, `84` cases: `42` positive + `42` negative; historical blind baseline `21/42` served-correct; post-feedback regression `42/42` after M1–M5 + W2-M5).
2. **Independent Holdout Wave 2** (`hybrid-v2-independent-vietnamese-section-holdout-wave2`, `W2-B01..B36`, `W2-A01..A12`, `W2-N01..N48`, `96` cases: `48` positive + `48` negative; historical blind baseline `5/48` served-correct; post-feedback regression `47/48` raw / `48/48` adjudicated after Registry `/19` + W2-M4 + W2-M5).
3. **W2-M1/M2/M3 Development Corpus** (`hybrid-v2-holdout-failure-repair`, `D001..D016`, `N001..N016`, `32` cases).
4. **Source Gate `/19` Development Corpus** (`hybrid-v2-wave2-source-gate-language-generalization`, `34` cases).
5. **W2-M4 Exact Radical Normalization Development Corpus** (`hybrid-v2-w2-m4-exact-radical-normalization`, `10` cases).
6. **W2-M5 Adapter `/4` Category A Identity Repair Development & Tamper Corpus** (`hybrid-v2-w2-m5-adapter4-category-a-identity-repair`, `26` cases: `14` positive + `12` tamper).
7. **All Backend Test Fixtures & Committed Evaluation Runs** (`backend/tests/**`, `docs/evaluation/geometry/runs/**`).

### 2.2 Pre-Freeze Inclusion & Replacement Protocol
- Every case in `inputs/holdout-wave3.json` (`144` cases) must be newly authored in natural Vietnamese spatial-geometry prose.
- Every positive case (`W3-B01..W3-B54`, `W3-A01..W3-A18`, `72` cases) must be mathematically well-defined, non-degenerate (cutting plane intersects the convex polyhedron in a polygon of $\ge 3$ vertices), representable without loss in `typed-fact-next/2`, and within the contract-level supported family matrix ([`supported-family-matrix.md`](supported-family-matrix.md)).
- Before freezing `holdout-manifest.json`, automated checks are restricted to:
  1. `parse_typed_fact_next_v2` schema validation for positive payloads (preventing accidental curator schema syntax typos).
  2. 9-dimensional semantic deduplication (`tools/dedup_check_wave3.py`) against all quarantined corpora and internal pairwise comparisons.
  3. Independent exact-`Fraction` oracle self-verification (`oracle/oracle_holdout_wave3.py --check`) and independent reviewer recomputation of all 72 positive cases.
- Any case flagged by pre-freeze deduplication or oracle validity checks must be replaced **before** corpus freeze and logged in `corpus-provenance.md`.
- **Zero product execution (`run_typed_fact_next_v2_route`, `build_adapter4_response`, `kiem_nguon`, `lap_ke_hoach`, `dung_tu_loi_goi`) is permitted before `holdout-manifest.json` is committed.**
- After `holdout-manifest.json` is committed, zero cases may be excluded, edited, or re-classified.

---

## 3. Stratified Corpus Design (`144` Cases: `72` Positive + `72` Negative)

### 3.1 Positive Strata (`72` `SERVE` Cases)

| Stratum | Case IDs | Count | Matrix Design & Balance |
|---|---|---:|---|
| **`P-B` (Category B — `ENGINE_DERIVED_SECTION`)** | `W3-B01` .. `W3-B54` | **54** | **6 solid families $\times$ 3 plane relations $\times$ 3 cases per cell = 54 cases:**<br>- Families (`9` cases each): `triangular_pyramid` (`W3-B01..B09`), `quadrilateral_pyramid` (`W3-B10..B18`), `right_triangular_prism` (`W3-B19..B27`), `oblique_triangular_prism` (`W3-B28..B36`), `cuboid` (`W3-B37..B45`), `cube` (`W3-B46..B54`).<br>- Plane relations (`3` per family): `perpendicular_line` (3), `parallel_plane` (3), `parallel_two_lines` (3).<br>- Question types (`1` per cell of 3): `section_only` (18), `area_only` (18), `section_and_area` (18).<br>- Includes varied Vietnamese phrasings (canonical and natural phrasing variants supported by Registry `/19`), varied vertex labels, primed prism vertices, solid-vertex reuse (`t=0` or `t=1`), and interior edge cuts (`0 < t < 1`). |
| **`P-A` (Category A — `DINH_CAT_CANH`)** | `W3-A01` .. `W3-A18` | **18** | **6 solid families $\times$ 3 cases per family = 18 cases:**<br>- `W3-A01..A03`: `triangular_pyramid`<br>- `W3-A04..A06`: `quadrilateral_pyramid`<br>- `W3-A07..A09`: `right_triangular_prism`<br>- `W3-A10..A12`: `oblique_triangular_prism`<br>- `W3-A13..A15`: `cuboid`<br>- `W3-A16..A18`: `cube`<br>- Question types (`1` per family of 3): `section_only` (6), `area_only` (6), `section_and_area` (6).<br>- Covers explicit stated intersections (`named_intersection` and `fresh_intersection`) and solid-vertex reuse (including primed top vertices such as `A'`, `B'`, `C'` on prisms/cuboids/cubes). |
| **Positive Subtotal** | | **72** | `24` `section_only` + `24` `area_only` + `24` `section_and_area` |

### 3.2 Negative / Adversarial Strata (`72` `REFUSE` Cases across `18` Classes)

Each of the 18 preregistered negative classes contains **4 cases** (`18 × 4 = 72` cases):

| # | Negative Class ID | Case IDs | Count | Description |
|---:|---|---|---:|---|
| 1 | `contradictory_source_facts` | `W3-N01..W3-N04` | 4 | Directly contradictory metric or geometric premises in the problem/payload (e.g., triangle inequality violation, incompatible right-angle/length claims, non-homogeneous units). |
| 2 | `wrong_solid_kind` | `W3-N05..W3-N08` | 4 | Problem prose states one solid kind (e.g., `tứ diện` / `lăng trụ tam giác`) while payload/notation declares an incompatible kind or base vertex count. |
| 3 | `wrong_solid_notation` | `W3-N09..W3-N12` | 4 | Solid notation in payload or goal does not match source text or violates vertex-chain syntax. |
| 4 | `mixed_solid_operands` | `W3-N13..W3-N16` | 4 | Multiple solids or cross-solid vertex bindings / operands mixing vertices across undeclared or distinct solids. |
| 5 | `missing_mandatory_premise` | `W3-N17..W3-N20` | 4 | Missing required metric dimension or altitude/projection premise needed to determine the solid's Gram metric or section area. |
| 6 | `unproven_parallel_or_perpendicular_relation` | `W3-N21..W3-N24` | 4 | Payload claims a perpendicular or parallel premise/plane relation not grounded in the Vietnamese source quote (`PREDICATE_NOT_IN_QUOTE` / `ROLE_NOT_IN_QUOTE`). |
| 7 | `ambiguous_source_labels` | `W3-N25..W3-N28` | 4 | Ambiguous plane name, duplicate/colliding point definitions, or ambiguous anaphoric reference in the question clause. |
| 8 | `wrong_ratio` | `W3-N29..W3-N32` | 4 | Cut ratio in payload (`divide_segment` or midpoint) contradicts the ratio stated in the Vietnamese source text (`UNGROUNDED_VALUE`) or is outside $(0, 1)$ (`INVALID_RATIO`). |
| 9 | `wrong_edge` | `W3-N33..W3-N36` | 4 | Point or stated intersection placed on an edge different from the edge named in the quote (`OBJECT_NOT_IN_QUOTE`) or on a non-lateral edge in Category A (`UNSUPPORTED_CAPABILITY`). |
| 10 | `impossible_vertex` | `W3-N37..W3-N40` | 4 | Reference to a vertex label that does not belong to the declared solid (`UNKNOWN_LABEL` / `UNKNOWN_VERTEX_REF` / `OBJECT_NOT_IN_QUOTE`). |
| 11 | `invalid_section_declaration` | `W3-N41..W3-N44` | 4 | Malformed `derived_sections` specification (e.g., plane through point perpendicular to a plane `PLANE_NOT_UNIQUE`, missing reference line/plane, or unknown target solid). |
| 12 | `unsupported_geometry_capability` | `W3-N45..W3-N48` | 4 | Curved solids (`cylinder`, `cone`, `sphere`), unsupported base shapes (general parallelogram/rhombus without right angle, regular pentagon), or unsupported plane kinds (`axial_section`, `plane_equation`). |
| 13 | `conflicting_section_area_requests` | `W3-N49..W3-N52` | 4 | Math goal asks for area of a section not asked in source text (`NOT_ASKED_IN_SOURCE`), targets a non-existent section ID (`UNKNOWN_SECTION_ID`), or embeds unverified local givens in the question clause. |
| 14 | `incorrect_stated_intersections` | `W3-N53..W3-N56` | 4 | Stated intersections in Category A are non-coplanar with the cutting plane, miss a cut lateral edge on a closed boundary, or claim an intersection on an edge parallel to the cutting plane (`SKEW_NO_INTERSECTION` / `LINE_PARALLEL_TO_PLANE`). |
| 15 | `category_a_b_semantic_contradictions` | `W3-N57..W3-N60` | 4 | Contradiction between Category A stated cut points and the plane's through-point/directional relation (e.g., renaming the through-point on the same lateral edge `AMBIGUOUS_REFERENCE`, or declaring a boundary cycle that does not match the plane's actual cut). |
| 16 | `primed_label_identity_ambiguity` | `W3-N61..W3-N64` | 4 | Swapping primed and unprimed vertices between quote and payload (e.g. quote says `A'` but payload uses `A`, or quote says `AB'` but payload uses `A'B`), testing primed-token boundary enforcement in Source Gate `/19`. |
| 17 | `source_provenance_mismatch` | `W3-N65..W3-N68` | 4 | Fabricated quote not present in `problem_text` (`QUOTE_NOT_IN_SOURCE`), or premise extracted from a negated (`không vuông góc`) or conditional (`Nếu ...`) clause (`NEGATED_CLAUSE` / `CONDITIONAL_CLAUSE`). |
| 18 | `geometry_degeneration` | `W3-N69..W3-N72` | 4 | Cutting plane coincides with a face of the solid (`SECTION_PLANE_IS_FACE` / `DERIVED_PLANE_IS_REFERENCE`), touches only a single vertex/edge (`PLANE_TOUCHES_VERTEX` / `PLANE_TOUCHES_EDGE`), or uses parallel/collinear direction lines (`DEGENERATE_PLANE_DIRECTIONS`). |
| **Negative Subtotal** | | **72** | **18 classes $\times$ 4 cases = 72 cases** |

---

## 4. Semantic Deduplication Protocol (Section 6)

Before freezing `holdout-manifest.json`, `tools/dedup_check_wave3.py` compares all 144 Wave 3 cases against all quarantined corpora (Wave 1 `84`, Wave 2 `96`, W2-M1..M3 `32`, Source Gate `/19` `34`, W2-M4 `10`, W2-M5 `26`, backend test fixtures, and all committed evaluation runs) and performs internal pairwise comparisons across all 144 Wave 3 cases across 9 dimensions:
1. **Exact normalized text match** (`0` allowed).
2. **Character 5-gram Jaccard similarity**:
   - External threshold: `< 0.75` against any historical problem text.
   - Internal threshold: `< 0.80` between any two Wave 3 cases (`< 0.75` between any two positive Wave 3 cases).
3. **Solid topology & family** (`pyramid_3`, `pyramid_4`, `prism_3_right`, `prism_3_oblique`, `cuboid`, `cube`).
4. **Cutting-plane construction kind & topological roles** of `through_point` and reference lines/planes.
5. **Vertex-relabelling invariance**: Canonicalizing all vertex names by their structural slot (`APEX`, `BASE_0..k-1`, `TOP_0..k-1`) and dihedral base symmetries (cyclic rotations and reflections of base vertex order).
6. **Scale invariance**: Dividing the sorted vector of squared metric lengths by the minimum positive squared length in exact `Fraction` arithmetic.
7. **Cut-ratio profile**: Sorted tuple of exact rational cut ratios (`midpoint` `1/2` and `divide_segment` ratios).
8. **Question objective** (`section_only`, `area_only`, `section_and_area`).
9. **Solution / Oracle invariance under symmetry and coordinate change**: Comparing `(vertex_count, sorted_canonical_edge_parameters_up_to_complement, normalized_area_squared_over_scale_fourth)` across all positive cases against Wave 1 and Wave 2 positive oracles.

Any positive case matching a historical positive case on `(dihedral_relabelled_structure, scale_invariant_lengths, point_ratios)` or having 5-gram Jaccard $\ge 0.75$ is rejected prior to freeze and must be replaced by the curator.

---

## 5. Independent Exact Oracle Protocol (Section 7)

1. `oracle/oracle_holdout_wave3.py` is implemented in pure Python using `fractions.Fraction` only, with **zero imports from `backend.app`**.
2. For each of the 72 positive cases (`W3-B01..W3-B54`, `W3-A01..W3-A18`), `oracle/geometry.json` provides an exact rational 3D Euclidean coordinate embedding satisfying all metric premises in `problem_text`.
3. `oracle/oracle_holdout_wave3.py` verifies all metric premises in `oracle/geometry.json`, derives the exact cutting plane equation $\vec{n} \cdot \vec{x} = d$ from the geometric specification, computes the exact intersection points with all polyhedron edges ($0 \le t \le 1$), deduplicates solid-vertex intersections ($t \in \{0, 1\}$), orders the polygon vertices cyclically in the cutting plane, and computes exact rational `area_squared` via 3D cross-product triangulation:
   $$\text{Area}^2 = \frac{1}{4}\left\|\sum_{i=1}^{m-2} (\vec{P}_i - \vec{P}_0) \times (\vec{P}_{i+1} - \vec{P}_0)\right\|^2.$$
4. An **Independent Oracle Reviewer** subagent recomputes all 72 positive oracle entries from scratch prior to `holdout-manifest.json` freeze. Any discrepancy blocks execution (`EVALUATION_BLOCKED`) until resolved prior to product run.

---

## 6. Evidence Classification & Post-Feedback Rule (Section 12)

- The single frozen execution of `evaluate_holdout_wave3.py` on `inputs/holdout-wave3.json` is classified as `INDEPENDENT_HOLDOUT_WAVE3_EXECUTED` (`AI_CURATED_PROCEDURAL_INDEPENDENCE`).
- Once Wave 3 results are inspected or used to diagnose/repair any product behavior, any subsequent re-run on `inputs/holdout-wave3.json` must be classified as `POST_FEEDBACK_DEVELOPMENT_REGRESSION`, never as a new independent holdout.

# Curator Brief — Independent Vietnamese Section Holdout Wave 2 (`hybrid-v2-independent-vietnamese-section-holdout-wave2`)

You are the **INDEPENDENT HOLDOUT WAVE 2 CURATOR** for a preregistered offline evaluation of AlgoSim Hybrid V2 on Vietnamese high-school (THPT) spatial-geometry plane-section problems. You author a brand-new 96-case test corpus, its expected dispositions/categories, and an independent exact-rational mathematical oracle.

> **Procedural Independence Declaration:** You operate in an isolated subagent context under a strict file-access firewall. Because you are an AI agent rather than an external human examination board, your work establishes **procedural and context independence** (`AI_CURATED_PROCEDURAL_INDEPENDENCE`), never human or institutional independence.

---

## 1. Working Directory & Strict File-Access Firewall

- **Worktree Root:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\independent-section-holdout-wave2`
- **Run Folder (write ONLY inside this folder):**
  `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/`

### Allowed Files to Read (ONLY these 8 files — nothing else!)
1. `AGENTS.md`
2. `docs/RULES.md`
3. `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/preregistration.md`
4. `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/supported-family-matrix.md`
5. `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/scoring-contract.md`
6. `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/curator-brief.md`
7. `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/tools/refusal_taxonomy.json`
8. `backend/app/simulation/geometry_functions/typed_fact_next.py` (the input contract schema ONLY, to construct valid `typed-fact-next/2` payloads).

### Strictly Forbidden Actions (Any Violation Invalidates the Evaluation)
- **DO NOT** read any other file under `backend/app/**` (forbidden: `registry.py`, `planner.py`, `engine.py`, `typed_fact_next_bridge.py`, `adapter4_route.py`, `function_route.py`, etc.).
- **DO NOT** read `backend/tests/**`, `backend/scripts/**`, or `frontend/**`.
- **DO NOT** read any other directory under `docs/evaluation/**` or any other worktree (such as `.superpowers/worktrees/independent-section-holdout`).
- **DO NOT** read `docs/CURRENT_STATE.md`, `docs/AI_CONTEXT_BUNDLE.md`, `docs/CODE_INDEX.md`, `docs/OPEN_ISSUES.md`, `docs/ROADMAP.md`, or `docs/EVIDENCE_INDEX.md`.
- **DO NOT** import or run any product module except `parse_typed_fact_next_v2` from `app.simulation.geometry_functions.typed_fact_next` for schema validation of your positive payloads. Never call `bridge_v2`, `run_typed_fact_next_v2_route`, `build_adapter4_response`, `kiem_nguon`, `lap_ke_hoach`, or `dung_tu_loi_goi`.
- **DO NOT** use `git log`, `git show`, `git diff`, or repo-wide `grep`/`find`.

Every tool call in your transcript will be audited by `tools/audit_curator_log.py`.

---

## 2. Corpus Design Requirements (96 Entirely New Vietnamese Problems)

Author **96 brand-new Vietnamese problems** (`W2-B01..W2-B36`, `W2-A01..W2-A12`, `W2-N01..W2-N48`) following `preregistration.md §3` and `supported-family-matrix.md`:

### Stratum A: `P-B` — Supported Category B Plane-Only Problems (36 cases: `W2-B01` .. `W2-B36`)
- **6 families $\times$ 3 cutting-plane relations $\times$ 2 problems per cell = 36 cases:**
  - `W2-B01..W2-B06`: `triangular_pyramid` (`2` `perpendicular_line`, `2` `parallel_plane`, `2` `parallel_two_lines`)
  - `W2-B07..W2-B12`: `quadrilateral_pyramid` (`2` `perpendicular_line`, `2` `parallel_plane`, `2` `parallel_two_lines`)
  - `W2-B13..W2-B18`: `right_triangular_prism` (`2` `perpendicular_line`, `2` `parallel_plane`, `2` `parallel_two_lines`)
  - `W2-B19..W2-B24`: `oblique_triangular_prism` (`2` `perpendicular_line`, `2` `parallel_plane`, `2` `parallel_two_lines`)
  - `W2-B25..W2-B30`: `cuboid` (`2` `perpendicular_line`, `2` `parallel_plane`, `2` `parallel_two_lines`)
  - `W2-B31..W2-B36`: `cube` (`2` `perpendicular_line`, `2` `parallel_plane`, `2` `parallel_two_lines`)
- **Balance `question_type`:** Exactly 12 `section_only`, 12 `area_only`, and 12 `section_and_area` across `W2-B01..W2-B36` (2 of each per family).
- **Diversity & Non-Triviality Requirements:**
  - Vary vertex labels (do not always use `S.ABC` / `M, N, P`; also use `A.BCD`, `S.MNPQ`, `ABC.A'B'C'`, `MNP.M'N'P'`, `ABCD.A'B'C'D'`, Greek plane names `(α)`, `(β)`, `(γ)` and Latin plane names `(P)`, `(Q)`, `(R)`).
  - Use varied cut ratios (`1/3`, `2/3`, `1/4`, `3/4`, `2/5`, `3/5`, as well as midpoints `1/2` and solid vertices as through-points) and varied numeric (`length_unit = "1"`, e.g. sides `5, 7, 9, 10, 12, 13, 15`) and symbolic (`length_unit = "a"`, e.g. `2a, 3a, 4a, 5a, 6a`) dimensions so that geometric configurations are genuinely distinct from standard textbook clichés.
  - Ensure every `P-B` cutting plane strictly intersects the polyhedron in a valid convex polygon of $\ge 3$ vertices (not a face, not a single vertex or edge) and has `stated_intersections: []`.

### Stratum B: `P-A` — Supported Category A Stated-Intersection Problems (12 cases: `W2-A01` .. `W2-A12`)
- Problems where the Vietnamese text explicitly states or names the edge intersections (`stated_intersections` non-empty):
  - `W2-A01..W2-A03`: `triangular_pyramid`
  - `W2-A04..W2-A06`: `quadrilateral_pyramid`
  - `W2-A07..W2-A08`: `right_triangular_prism`
  - `W2-A09`: `oblique_triangular_prism`
  - `W2-A10..W2-A11`: `cuboid`
  - `W2-A12`: `cube`
- **Required Coverage across `W2-A01..W2-A12`:**
  - At least 4 cases where the cutting plane passes through a solid vertex (`through_point` is a solid vertex such as `A`, `B`, `C`, and cuts the remaining lateral edges at stated interior points).
  - At least 4 cases where all section vertices are interior edge cuts on lateral edges.
  - Include both named intersection points (`named_intersection`, where the cut points are named and placed by ratio/midpoint premises) and unnamed stated intersection points (`fresh_intersection`, where the text states the plane cuts specific edges and the plane is determined by a through-point + relation).
  - Balance `question_type`: 4 `section_only`, 4 `area_only`, 4 `section_and_area`.
  - When a quadrilateral pyramid or cuboid/cube has 4 cut points on 4 lateral edges, verify in exact arithmetic that all 4 points are strictly coplanar!

### Stratum C: `N` — Negative / Adversarial / Unsupported / Ambiguous Problems (48 cases: `W2-N01` .. `W2-N48`)
- **16 negative classes $\times$ 3 cases per class = 48 cases:**
  1. `W2-N01..W2-N03`: `wrong_solid_identity`
  2. `W2-N04..W2-N06`: `contradictory_solid_kind`
  3. `W2-N07..W2-N09`: `wrong_cutting_plane`
  4. `W2-N10..W2-N12`: `ambiguous_plane_name`
  5. `W2-N13..W2-N15`: `multiple_planes`
  6. `W2-N16..W2-N18`: `multiple_solids`
  7. `W2-N19..W2-N21`: `incorrect_source_quotations`
  8. `W2-N22..W2-N24`: `unsupported_topology`
  9. `W2-N25..W2-N27`: `missing_dimensions`
  10. `W2-N28..W2-N30`: `underconstrained_geometry`
  11. `W2-N31..W2-N33`: `conditional_or_negated_premises`
  12. `W2-N34..W2-N36`: `wrong_question_target`
  13. `W2-N37..W2-N39`: `incorrect_named_section`
  14. `W2-N40..W2-N42`: `ambiguous_anaphoric_area_request`
  15. `W2-N43..W2-N45`: `contradictory_cut_point_claims`
  16. `W2-N46..W2-N48`: `degenerate_or_tampered_section_plane`
- Label each negative case's `negative_origin` as either `"faulty_extraction"` (valid Vietnamese problem, payload misrepresents or tampers with it) or `"flawed_or_unsupported_problem"` (faithful payload, problem itself is contradictory, underdetermined, ambiguous, or outside supported topology/relations).

---

## 3. Files You Must Write Inside the Run Folder

1. **`inputs/holdout-wave2.json`**:
   ```json
   {
     "schema": "HOLDOUT_WAVE2_CORPUS/1",
     "curator": "independent-wave2-curator-context",
     "independence_class": "AI_CURATED_PROCEDURAL_INDEPENDENCE",
     "cases": [
       {
         "id": "W2-B01",
         "stratum": "P-B|P-A|N",
         "family": "triangular_pyramid|quadrilateral_pyramid|right_triangular_prism|oblique_triangular_prism|cuboid|cube|other",
         "plane_relation": "perpendicular_line|parallel_plane|parallel_two_lines|stated_intersections|other|none",
         "question_type": "section_only|area_only|section_and_area|other",
         "negative_class": null,
         "negative_origin": null,
         "problem_text": "...",
         "payload": { "... valid typed-fact-next/2 dict ..." },
         "expected_disposition": "SERVE|REFUSE",
         "acceptable_categories": [],
         "rationale": "...",
         "track_b": {
           "representability": "representable_without_loss|missing_required_information|ambiguous|contradictory|unsupported_relation|unsupported_topology|not_representable_by_current_contract",
           "note": "..."
         }
       }
     ]
   }
   ```
2. **`oracle/geometry.json`**:
   For all 48 `SERVE` cases (`W2-B01..W2-B36`, `W2-A01..W2-A12`), exact rational 3D coordinates (in an orthonormal Euclidean frame consistent with all lengths/angles in `problem_text`) of every vertex and named point, the polyhedron's vertex list and face cycles, and the cutting plane specification (`perpendicular_line`, `parallel_plane`, `parallel_two_lines`, or `three_points` / `stated_points`) so the oracle script derives the plane equation and section polygon mathematically.
3. **`oracle/oracle_holdout_wave2.py`**:
   Pure Python + `fractions.Fraction` ONLY (`0` imports from `app.*`). Reads `oracle/geometry.json`, verifies that every premise length/orthogonality holds in the chosen coordinates, derives the cutting plane, computes the exact intersection polygon of the cutting plane with the convex polyhedron, orders vertices cyclically around the polygon, distinguishes solid vertices (`{"vertex": "A"}`) from interior edge cuts (`{"edge": ["U", "V"], "t": "p/q"}` with $0 < t < 1$), and computes exact `area_squared` (`"p/q"`).
   - Supports `--write` (writes `oracle/expected.json`) and `--check` (recomputes and verifies `oracle/expected.json` plus runs built-in hand-checked self-tests).
4. **`oracle/expected.json`**:
   Output of `oracle/oracle_holdout_wave2.py --write`, keyed by case ID (`W2-B01..W2-B36`, `W2-A01..W2-A12`):
   ```json
   {
     "W2-B01": {
       "solid": "S.ABC",
       "section_id": "sec",
       "expected_certificate_category": "ENGINE_DERIVED_SECTION",
       "area_goal_id": null,
       "vertex_count": 3,
       "boundary": [
         {"vertex": "A"},
         {"edge": ["S", "B"], "t": "1/3"},
         {"edge": ["S", "C"], "t": "1/2"}
       ],
       "area_squared": "25/16"
     }
   }
   ```
5. **`curator-attestation.md`** and **`corpus-provenance.md`**:
   Document your authoring methodology, explicit declaration of `AI_CURATED_PROCEDURAL_INDEPENDENCE`, complete list of files read, confirmation that zero forbidden files or product routes were accessed, and cell-by-cell provenance of all 96 cases.

Do not stage or commit git changes; return when all files above are written and `oracle_holdout_wave2.py --check` passes.

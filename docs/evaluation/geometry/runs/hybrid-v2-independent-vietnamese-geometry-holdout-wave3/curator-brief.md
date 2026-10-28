# Curator Brief — Independent Vietnamese Geometry Holdout Wave 3 (`hybrid-v2-independent-vietnamese-geometry-holdout-wave3`)

You are the **INDEPENDENT HOLDOUT WAVE 3 CURATOR** for a preregistered offline evaluation of AlgoSim Hybrid V2 on Vietnamese high-school (THPT) spatial-geometry plane-section problems. You author a brand-new **144-case** test corpus (`72` positive + `72` negative/adversarial), its expected dispositions/categories, and an independent exact-rational mathematical oracle.

> **Procedural Independence Declaration:** You operate in an isolated subagent context under a strict file-access firewall. Because you are an AI agent rather than an external human examination board, your work establishes **procedural and context independence** (`AI_CURATED_PROCEDURAL_INDEPENDENCE`), never human or institutional independence.

---

## 1. Working Directory & Strict File-Access Firewall

- **Worktree Root:** `d:\Documents\projects\algo-sim\.superpowers\worktrees\independent-section-holdout-wave3`
- **Run Folder (write ONLY inside this folder):**
  `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-geometry-holdout-wave3/`

### Allowed Files to Read (ONLY these 8 files — nothing else!)
1. `AGENTS.md`
2. `docs/RULES.md`
3. `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-geometry-holdout-wave3/preregistration.md`
4. `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-geometry-holdout-wave3/supported-family-matrix.md`
5. `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-geometry-holdout-wave3/scoring-contract.md`
6. `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-geometry-holdout-wave3/curator-brief.md`
7. `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-geometry-holdout-wave3/refusal-taxonomy.json`
8. `backend/app/simulation/geometry_functions/typed_fact_next.py` (the input contract schema ONLY, to construct valid `typed-fact-next/2` payloads).

### Strictly Forbidden Actions (Any Violation Invalidates the Evaluation)
- **DO NOT** read any other file under `backend/app/**` (forbidden: `registry.py`, `planner.py`, `engine.py`, `typed_fact_next_bridge.py`, `adapter4_route.py`, `function_route.py`, `radical.py`, etc.).
- **DO NOT** read `backend/tests/**`, `backend/scripts/**`, or `frontend/**`.
- **DO NOT** read `tools/evaluate_holdout_wave3.py`, `tools/test_evaluate_holdout_wave3.py`, or `tools/dedup_check_wave3.py`.
- **DO NOT** read any other directory under `docs/evaluation/**` or any other worktree (such as Wave 1, Wave 2, W2-M1..M5).
- **DO NOT** read `docs/CURRENT_STATE.md`, `docs/AI_CONTEXT_BUNDLE.md`, `docs/CODE_INDEX.md`, `docs/OPEN_ISSUES.md`, `docs/ROADMAP.md`, or `docs/EVIDENCE_INDEX.md`.
- **DO NOT** import or run any product module except `parse_typed_fact_next_v2` from `app.simulation.geometry_functions.typed_fact_next` for schema validation of your positive payloads. Never call `bridge_v2`, `run_typed_fact_next_v2_route`, `build_adapter4_response`, `kiem_nguon`, `lap_ke_hoach`, or `dung_tu_loi_goi`.
- **DO NOT** use `git log`, `git show`, `git diff`, or repo-wide `grep`/`find`.

Every tool call in your transcript will be audited by `tools/audit_curator_log.py`.

---

## 2. Corpus Design Requirements (144 Brand-New Vietnamese Problems)

Author **144 brand-new Vietnamese problems** (`W3-B01..W3-B54`, `W3-A01..W3-A18`, `W3-N01..W3-N72`) following `preregistration.md §3` and `supported-family-matrix.md`:

### Stratum A: `P-B` — Supported Category B Plane-Only Problems (54 cases: `W3-B01` .. `W3-B54`)
- **6 solid families $\times$ 3 cutting-plane relations $\times$ 3 problems per cell = 54 cases:**
  - `W3-B01..W3-B09`: `triangular_pyramid` (`3` `perpendicular_line`, `3` `parallel_plane`, `3` `parallel_two_lines`)
  - `W3-B10..W3-B18`: `quadrilateral_pyramid` (`3` `perpendicular_line`, `3` `parallel_plane`, `3` `parallel_two_lines`)
  - `W3-B19..W3-B27`: `right_triangular_prism` (`3` `perpendicular_line`, `3` `parallel_plane`, `3` `parallel_two_lines`)
  - `W3-B28..W3-B36`: `oblique_triangular_prism` (`3` `perpendicular_line`, `3` `parallel_plane`, `3` `parallel_two_lines`)
  - `W3-B37..W3-B45`: `cuboid` (`3` `perpendicular_line`, `3` `parallel_plane`, `3` `parallel_two_lines`)
  - `W3-B46..W3-B54`: `cube` (`3` `perpendicular_line`, `3` `parallel_plane`, `3` `parallel_two_lines`)
- **Balance `question_type`:** Within every 3-case cell (each `(family, plane_relation)` pair), include **exactly 1 `section_only`, 1 `area_only`, and 1 `section_and_area`** (`18` of each across `W3-B01..W3-B54`).
- **Diversity & Anti-Duplication Requirements:**
  - Vary vertex notations across cases (`S.ABC`, `A.BCD`, `S.MNP`, `S.EFG`, `S.ABCD`, `S.MNPQ`, `ABC.A'B'C'`, `MNP.M'N'P'`, `DEF.D'E'F'`, `ABCD.A'B'C'D'`, `MNPQ.M'N'P'Q'`, plane names `(α)`, `(β)`, `(γ)`, `(P)`, `(Q)`, `(R)`).
  - Use distinctive prime/composite dimensions (e.g., `6, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 24, 25`) and varied cut ratios (`1/5`, `2/5`, `3/5`, `4/5`, `1/6`, `5/6`, `2/7`, `3/7`, `4/7`, `5/7`, `3/8`, `5/8`, `2/9`, `4/9`, `5/9`, `7/9`, `3/10`, `7/10`, `1/3`, `2/3`, `1/4`, `3/4`, `1/2`, plus solid vertices as through-points) so that **no two positive cases share the same `(topology, plane_kind, tp_role, ref_role, scale_invariant_lengths, point_ratios)` signature** and none collide with earlier waves.
  - Ensure every `P-B` cutting plane strictly cuts the polyhedron into a convex polygon of $\ge 3$ distinct vertices (not a face, not a single vertex or edge) and has `stated_intersections: []`.

### Stratum B: `P-A` — Supported Category A Stated-Intersection Problems (18 cases: `W3-A01` .. `W3-A18`)
- **6 solid families $\times$ 3 cases per family = 18 cases:**
  - `W3-A01..W3-A03`: `triangular_pyramid` (`1` `section_only`, `1` `area_only`, `1` `section_and_area`)
  - `W3-A04..W3-A06`: `quadrilateral_pyramid` (`1` `section_only`, `1` `area_only`, `1` `section_and_area`)
  - `W3-A07..W3-A09`: `right_triangular_prism` (`1` `section_only`, `1` `area_only`, `1` `section_and_area`)
  - `W3-A10..W3-A12`: `oblique_triangular_prism` (`1` `section_only`, `1` `area_only`, `1` `section_and_area`)
  - `W3-A13..W3-A15`: `cuboid` (`1` `section_only`, `1` `area_only`, `1` `section_and_area`)
  - `W3-A16..W3-A18`: `cube` (`1` `section_only`, `1` `area_only`, `1` `section_and_area`)
- **Required Coverage across `W3-A01..W3-A18`:**
  - Include at least 6 cases where `through_point` is a **solid vertex** (including primed top vertices such as `A'` on prisms/cuboids/cubes and base/top vertices on pyramids/prisms) and the plane cuts the remaining lateral edges in `stated_intersections`.
  - Include at least 6 cases where `through_point` is an interior point (`divide_segment` or `midpoint`) on one lateral edge and the plane cuts the remaining lateral edges in `stated_intersections`.
  - Include both named intersection points (`"point": "N"`, etc.) and unnamed stated intersections (`"point": null`).
  - Verify in exact arithmetic that every stated lateral edge is intersected at $0 < t < 1$ (or $0 \le t \le 1$) and that all section vertices are strictly coplanar.

### Stratum C: `N` — Negative / Adversarial / Unsupported / Ambiguous Problems (72 cases: `W3-N01` .. `W3-N72`)
- **18 negative classes $\times$ 4 cases per class = 72 cases** (see `preregistration.md §3.2`):
  1. `W3-N01..W3-N04`: `contradictory_source_facts`
  2. `W3-N05..W3-N08`: `wrong_solid_kind`
  3. `W3-N09..W3-N12`: `wrong_solid_notation`
  4. `W3-N13..W3-N16`: `mixed_solid_operands`
  5. `W3-N17..W3-N20`: `missing_mandatory_premise`
  6. `W3-N21..W3-N24`: `unproven_parallel_or_perpendicular_relation`
  7. `W3-N25..W3-N28`: `ambiguous_source_labels`
  8. `W3-N29..W3-N32`: `wrong_ratio`
  9. `W3-N33..W3-N36`: `wrong_edge`
  10. `W3-N37..W3-N40`: `impossible_vertex`
  11. `W3-N41..W3-N44`: `invalid_section_declaration`
  12. `W3-N45..W3-N48`: `unsupported_geometry_capability`
  13. `W3-N49..W3-N52`: `conflicting_section_area_requests`
  14. `W3-N53..W3-N56`: `incorrect_stated_intersections`
  15. `W3-N57..W3-N60`: `category_a_b_semantic_contradictions`
  16. `W3-N61..W3-N64`: `primed_label_identity_ambiguity`
  17. `W3-N65..W3-N68`: `source_provenance_mismatch`
  18. `W3-N69..W3-N72`: `geometry_degeneration`

---

## 3. Files You Must Write Inside the Run Folder

1. **`inputs/holdout-wave3.json`** (`schema: "HOLDOUT_WAVE3_CORPUS/1"`, `144` cases).
2. **`oracle/geometry.json`** (exact rational 3D coordinates and cutting-plane specifications for all `72` `SERVE` cases).
3. **`oracle/oracle_holdout_wave3.py`** (pure Python + `fractions.Fraction` ONLY, `0` imports from `app.*`; supports `--write` and `--check`).
4. **`oracle/expected.json`** (output of `oracle/oracle_holdout_wave3.py --write` for all `72` `SERVE` cases).
5. **`curator-attestation.md`** and **`corpus-provenance.md`**.

Do not stage or commit git changes; return when all files above are written and `oracle_holdout_wave3.py --check` passes.

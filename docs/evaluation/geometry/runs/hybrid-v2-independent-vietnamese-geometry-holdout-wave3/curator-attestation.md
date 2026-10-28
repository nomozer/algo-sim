# Curator Attestation — Holdout Wave 3 (`HYBRID_V2_INDEPENDENT_VIETNAMESE_GEOMETRY_HOLDOUT_WAVE3`)

## 1. Evidence Classification & Independence Scope

- **Task ID:** `HYBRID_V2_INDEPENDENT_VIETNAMESE_GEOMETRY_HOLDOUT_WAVE3`
- **Evidence Class:** `AI_CURATED_PROCEDURAL_INDEPENDENCE`
- **Independence Boundary:** This corpus (`144` Vietnamese 3D geometry section problems) and its standalone rational geometry oracle were authored in an isolated subagent session operating under a strict procedural information firewall. As required by `preregistration.md` and `curator-brief.md`, this evidence is classified as `AI_CURATED_PROCEDURAL_INDEPENDENCE` (procedural separation from product solver/verifier internals and prior evaluation corpora, not human-external independence).
- **Baseline Commit:** `e137623c4f674135a8d7884b78614c132eb78085`
- **Frozen Product Commit:** `73ca8d92e74059680ce53b99692af396df37a2f8`

---

## 2. Information Firewall Attestation

During the entire curation and oracle-authoring session, **only** the following eight (8) pre-authorized repository files were read:

1. `AGENTS.md`
2. `docs/RULES.md`
3. `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-geometry-holdout-wave3/preregistration.md`
4. `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-geometry-holdout-wave3/supported-family-matrix.md`
5. `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-geometry-holdout-wave3/scoring-contract.md`
6. `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-geometry-holdout-wave3/curator-brief.md`
7. `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-geometry-holdout-wave3/refusal-taxonomy.json`
8. `backend/app/simulation/geometry_functions/typed_fact_next.py`

### Explicitly Unread & Unexecuted Paths

- **Unread Product Implementation:** No file under `backend/app/**` other than `backend/app/simulation/geometry_functions/typed_fact_next.py` was read. Specifically, `bridge_v2.py`, `source_grounding.py`, `planner.py`, `compiler.py`, `adapter4.py`, and all solver/verifier modules were never read.
- **Unread Tests, Tooling & Prior Corpora:** No file under `backend/tests/**`, `tools/**`, `docs/evaluation/geometry/runs/**` (outside this Wave 3 run directory), or any other `docs/**` path was read. No Wave 1, Wave 2, T3, or benchmark corpus was inspected.
- **Zero Product Route Execution:** None of `run_typed_fact_next_v2_route`, `build_adapter4_response`, `kiem_nguon`, `lap_ke_hoach`, `dung_tu_loi_goi`, or any `bridge_v2` function was imported or executed at any point during corpus authoring or oracle generation. No candidate case was filtered, tuned, or selected by running the product solver or verifier.
- **Schema Validation Helper Only:** Only `parse_typed_fact_next_v2` from `app.simulation.geometry_functions.typed_fact_next` was called to verify that the 72 positive `typed-fact-next/2` payloads conform to the frozen Pydantic contract schema.

---

## 3. Standalone Rational Oracle Attestation

- **Oracle Script:** `oracle/oracle_holdout_wave3.py`
- **Pure Standard Library Implementation:** `oracle/oracle_holdout_wave3.py` uses only Python standard library modules (`argparse`, `fractions.Fraction`, `functools.cmp_to_key`, `json`, `math`, `pathlib.Path`, `sys`, `typing`) with **zero** imports from `app.*` or `backend.*`.
- **Independent Verification:** `oracle/oracle_holdout_wave3.py` independently verifies that every positive case's `oracle/geometry.json` coordinates satisfy all geometric premises (`right_angle`, `rectangle`, `base_is_square`, `right_prism`, `perpendicular_line_plane`, `orthogonal_projection`, `segment_length`, `midpoint`, `divide_segment`) and cutting-plane relations (`through_point_parallel_plane`, `through_point_perpendicular_line`, `through_point_parallel_two_lines`) in exact rational arithmetic before computing edge intersections, cyclic polygon ordering, canonical edge parameters, `area_squared`, and reduced radical `area_display`.

---

## 4. Deliverable Manifest & SHA-256 Hashes

| Deliverable | Relative Path | Size (Bytes) | SHA-256 |
|---|---|---:|---|
| Holdout Wave 3 Corpus (`144` cases) | `inputs/holdout-wave3.json` | `748048` | `cf2d3fd759b6a94c4eae2545a4a409e50859ff28e861f797609b6a259fe4dee0` |
| Positive Coordinate & Plane Spec (`72` cases) | `oracle/geometry.json` | `293326` | `a7c04b77211d85fc7912bbcc6ad34e83e864cf46ea5904e4ebc5e201b520b983` |
| Standalone Exact Rational Oracle | `oracle/oracle_holdout_wave3.py` | `17921` | `aa156523cc6895d935fc6428995dad48a4684bfc60d96be89e51d41ef4b5c1c0` |
| Expected Oracle Output (`72` cases) | `oracle/expected.json` | `177204` | `9cabeb19ae0d10e1112795097e7ed18e0b0b3aa7bc18700a9d60813a0cbcf9df` |


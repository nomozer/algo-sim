# Curator Attestation — Independent Holdout Wave 2

## 1. Independence Class Declaration

- **Suite ID:** `holdout-wave2`
- **Run ID:** `hybrid-v2-independent-vietnamese-section-holdout-wave2`
- **Declared Independence Class:** `AI_CURATED_PROCEDURAL_INDEPENDENCE`
- **Curator Role:** Independent Holdout Wave 2 Curator (isolated subagent session)

This corpus and its accompanying independent oracle were authored under procedural firewall rules (`AI_CURATED_PROCEDURAL_INDEPENDENCE`). All 96 Vietnamese THPT spatial-geometry prompts, their `typed_fact_next_v2` payloads, the 48 3D rational geometry specifications, and the pure-Python rational oracle were authored from first-principles 3D analytic geometry without inspecting product solver implementations, historical benchmark waves, or existing tests.

---

## 2. Information Firewall Compliance

### 2.1 Complete List of Repository Files Read (Exactly 8 Allowed Files)

1. `AGENTS.md`
2. `docs/RULES.md`
3. `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/preregistration.md`
4. `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/supported-family-matrix.md`
5. `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/scoring-contract.md`
6. `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/curator-brief.md`
7. `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/tools/refusal_taxonomy.json`
8. `backend/app/simulation/geometry_functions/typed_fact_next.py`

### 2.2 Firewall Prohibitions Verified

- **Zero forbidden repository files read:** No other files under `backend/**`, `frontend/**`, `docs/**`, or `.superpowers/worktrees/**` were opened, searched, or read.
- **Zero git history inspection:** No `git log`, `git show`, `git diff`, or workspace search commands were executed against previous runs or solver commits.
- **Zero product solver or route execution:** None of `bridge_v2.py`, `run_typed_fact_next_v2_route`, `build_adapter4_response`, `kiem_nguon`, `lap_ke_hoach`, or `dung_tu_loi_goi` were read, imported, or called.
- **Schema-only import:** The only symbol imported from `app.*` during authoring validation was `parse_typed_fact_next_v2` from `app.simulation.geometry_functions.typed_fact_next` to confirm that all 48 positive `SERVE` payloads (`W2-B01..W2-B36`, `W2-A01..W2-A12`) and 43 schema-valid negative `REFUSE` payloads parse cleanly (`5` negative cases intentionally carry schema-level invalidities to test `INPUT_INVALID` / `UNSUPPORTED_CAPABILITY` rejection at the schema boundary).

---

## 3. Authoring & Oracle Verification Methodology

1. **Corpus Construction (`inputs/holdout-wave2.json`):**
   - **96 cases total:** 36 `P-B` (`W2-B01..W2-B36`), 12 `P-A` (`W2-A01..W2-A12`), and 48 `N` (`W2-N01..W2-N48`).
   - Every case uses fresh, pairwise-distinct non-cliché integer/symbolic dimension tuples and natural Vietnamese THPT problem wording.
   - Varied solid vertex naming (`S.ABC`, `A.BCD`, `S.MNP`, `S.EFG`, `S.ABCD`, `S.MNPQ`, `S.EFGH`, `ABC.A'B'C'`, `MNP.M'N'P'`, `EFG.E'F'G'`, `ABCD.A'B'C'D'`, `MNPQ.M'N'P'Q'`, `EFGH.E'F'G'H'`) and varied interior cut ratios (`1/3`, `1/4`, `2/5`, `3/5`, `2/3`, `3/4`, plus midpoints `1/2`).
2. **Independent Oracle (`oracle/oracle_holdout_wave2.py`, `oracle/geometry.json`, `oracle/expected.json`):**
   - Pure Python standard library (`fractions.Fraction`, `argparse`, `json`, `pathlib`, `sys`), with **zero imports from `app.*`**.
   - Verifies that every 3D coordinate in `oracle/geometry.json` satisfies all stated metric premises (`segment_length^2`, `right_angle` dot products, `altitude` / `orthogonal_projection` / `right_prism` / `base_is_square` / `base_is_rectangle` constraints, and `midpoint` / `divide_segment` affine combinations).
   - Derives the exact cutting plane $\mathbf{n} \cdot \mathbf{X} = d$ from `through_point` and the stated plane relation (`parallel_plane`, `perpendicular_line`, `parallel_two_lines`, or `stated_intersections`), and cross-checks that all `stated_intersections` in `W2-A01..W2-A12` lie on the derived plane and cut every lateral edge in a closed lateral cycle.
   - Computes exact plane-edge intersections across all solid edges, orders the resulting polygon vertices cyclically around a normal projection axis, verifies strict convexity and shared-face adjacency of every consecutive polygon edge, and computes exact rational `area_squared` via 3D cross-product fan triangulation:
     $$\text{area}^2 = \frac{1}{4}\left\|\sum_{i=1}^{m-2} (\mathbf{V}_i - \mathbf{V}_0) \times (\mathbf{V}_{i+1} - \mathbf{V}_0)\right\|^2 \in \mathbb{Q}_{>0}.$$
   - Includes two self-contained hand-checked unit self-tests (`SELFTEST-1` and `SELFTEST-2`) executed on every `--write` and `--check` invocation.

---

## 4. Pre-Freeze Deduplication Replacement Log (`preregistration.md §2.4` / Owner GO §6)

Before freezing `inputs/holdout-wave2.json` and `oracle/expected.json`, pre-freeze semantic deduplication (`tools/dedup_check_wave2.py`, executed without running any product solver code) was run and the following replacements were applied within their original strata and cells:

1. **`W2-B34` (`P-B`, `cube`, `parallel_plane`, `section_and_area`, symbolic unit `"a"`):**
   - Replaced midpoint through-point placement (`M` midpoint of `AB`) with a `divide_segment` placement `AM = 3/5 AB` on base edge `AB` of cube `ABCD.A'B'C'D'` (side `10a`) cut by plane `(Q)` parallel to diagonal plane `(BDD')`, yielding `vertex_count = 4` and `area_squared = 7200`.
2. **`W2-A04` (`P-A`, `quadrilateral_pyramid`, `stated_intersections`, `section_and_area`, numeric unit `"1"`):**
   - Replaced square-base pyramid (`AB = BC = SA = 10`) with a non-square rectangle-base pyramid `S.ABCD` (`AB = 6`, `AD = 8`, altitude `SA = 10` perpendicular to `(ABCD)`, distinct squared-length profile `(36, 64, 100)`) cut by plane `(Q)` through base vertex `A` perpendicular to lateral edge `SC` at named interior points `M ∈ SB`, `N ∈ SC`, `P ∈ SD`, yielding `vertex_count = 4` and `area_squared = 253125000/485809`.
3. **Negative-case wording and solid-family diversification (`W2-N01, W2-N07..W2-N15, W2-N19..W2-N21, W2-N25, W2-N31, W2-N34, W2-N36..W2-N38, W2-N40, W2-N42, W2-N43`):**
   - Diversified Vietnamese phrasing, vertex labels (`A.BCD`, `S.MNP`, `S.EFG`, `S.ABCD`, `MNP.M'N'P'`, `ABCD.A'B'C'D'`, `EFGH.E'F'G'H'`), and solid families across negative cases so that zero case pairs in `inputs/holdout-wave2.json` have character 5-gram Jaccard $\ge 0.80$ (maximum pairwise 5-gram Jaccard across all 96 cases is `0.756`).

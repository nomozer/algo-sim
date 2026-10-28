# Corpus Provenance & Design Specification — Holdout Wave 3

## 1. Overview & Provenance Summary

- **Task:** `HYBRID_V2_INDEPENDENT_VIETNAMESE_GEOMETRY_HOLDOUT_WAVE3`
- **Corpus Schema:** `HOLDOUT_WAVE3_CORPUS/1` (`inputs/holdout-wave3.json`)
- **Evidence Class:** `AI_CURATED_PROCEDURAL_INDEPENDENCE`
- **Total Cases:** `144` brand-new Vietnamese 3D solid-section problems authored from scratch under the Wave 3 procedural information firewall.
  - **Stratum `P-B` (Positive Category B — Unstated Section Vertices):** `54` cases (`W3-B01` .. `W3-B54`)
  - **Stratum `P-A` (Positive Category A — Stated Lateral-Edge Cuts):** `18` cases (`W3-A01` .. `W3-A18`)
  - **Stratum `N` (Negative / Refusal Cases):** `72` cases (`W3-N01` .. `W3-N72`)

---

## 2. Positive Corpus Stratification (`P-B` and `P-A`, 72 Cases)

### 2.1 Family × Plane-Relation × Question-Type Matrix

All `72` positive cases cover the `6 × 3 = 18` supported `(solid_family, plane_relation)` cells defined in `supported-family-matrix.md`:

| Solid Family | Plane Relation | Stratum `P-B` (`section_only`, `area_only`, `section_and_area`) | Stratum `P-A` (Stated Cuts, Cyclic Question Type) |
|---|---|---|---|
| `triangular_pyramid` | `perpendicular_line` | `W3-B01`, `W3-B02`, `W3-B03` | `W3-A02` (`area_only`) |
| `triangular_pyramid` | `parallel_two_lines` | `W3-B04`, `W3-B05`, `W3-B06` | `W3-A03` (`section_and_area`) |
| `triangular_pyramid` | `parallel_plane` | `W3-B07`, `W3-B08`, `W3-B09` | `W3-A01` (`section_only`) |
| `quadrilateral_pyramid` | `parallel_plane` | `W3-B10`, `W3-B11`, `W3-B12` | `W3-A04` (`section_only`) |
| `quadrilateral_pyramid` | `perpendicular_line` | `W3-B13`, `W3-B14`, `W3-B15` | `W3-A05` (`area_only`) |
| `quadrilateral_pyramid` | `parallel_two_lines` | `W3-B16`, `W3-B17`, `W3-B18` | `W3-A06` (`section_and_area`) |
| `right_triangular_prism` | `parallel_plane` | `W3-B19`, `W3-B20`, `W3-B21` | `W3-A07` (`section_only`) |
| `right_triangular_prism` | `perpendicular_line` | `W3-B22`, `W3-B23`, `W3-B24` | `W3-A08` (`area_only`) |
| `right_triangular_prism` | `parallel_two_lines` | `W3-B25`, `W3-B26`, `W3-B27` | `W3-A09` (`section_and_area`) |
| `oblique_triangular_prism` | `parallel_plane` | `W3-B28`, `W3-B29`, `W3-B30` | `W3-A10` (`section_only`) |
| `oblique_triangular_prism` | `perpendicular_line` | `W3-B31`, `W3-B32`, `W3-B33` | `W3-A11` (`area_only`) |
| `oblique_triangular_prism` | `parallel_two_lines` | `W3-B34`, `W3-B35`, `W3-B36` | `W3-A12` (`section_and_area`) |
| `cuboid` | `parallel_plane` | `W3-B37`, `W3-B38`, `W3-B39` | `W3-A13` (`section_only`) |
| `cuboid` | `perpendicular_line` | `W3-B40`, `W3-B41`, `W3-B42` | `W3-A14` (`area_only`) |
| `cuboid` | `parallel_two_lines` | `W3-B43`, `W3-B44`, `W3-B45` | `W3-A15` (`section_and_area`) |
| `cube` | `parallel_plane` | `W3-B46`, `W3-B47`, `W3-B48` | `W3-A16` (`section_only`) |
| `cube` | `perpendicular_line` | `W3-B49`, `W3-B50`, `W3-B51` | `W3-A17` (`area_only`) |
| `cube` | `parallel_two_lines` | `W3-B52`, `W3-B53`, `W3-B54` | `W3-A18` (`section_and_area`) |

### 2.2 Structural Diversity & Anti-Collision Verification

- **Scale-Invariant Signatures:** All `72` positive cases have pairwise-distinct `(family, plane_relation, scale_invariant_lengths, point_ratios)` signatures (`72 / 72` unique).
  - Non-cube families (`60` positive cases) use pairwise non-proportional integer dimension triples `(L1, L2, H)` with coprime / prime-heavy side lengths (`5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 23, 25`).
  - Cube cases (`12` positive cases: `W3-B46..W3-B54`, `W3-A16..W3-A18`) use pairwise-distinct `divide_segment` ratios (`2/11, 3/11, 4/11, 5/11, 2/13, 3/13, 4/13, 5/13, 6/13, 3/16, 5/16, 2/17`) so no two cube cases share point ratios or edge intersection parameters.
- **Length Units:** Alternates between numeric (`length_unit: "1"`) and symbolic (`length_unit: "a"`).
- **Vertex & Plane Naming Diversity:** Cycles across diverse vertex labelings (`S.ABC`, `S.MNP`, `S.DEF`, `S.EFG`, `S.PQR`, `S.GHK`, `S.ABCD`, `S.MNPQ`, `S.EFGH`, `ABC.A'B'C'`, `MNP.M'N'P'`, `DEF.D'E'F'`, `EFG.E'F'G'`, `ABCD.A'B'C'D'`, `MNPQ.M'N'P'Q'`, `EFGH.E'F'G'H'`) and cutting-plane names (`α`, `β`, `γ`, `P`, `Q`, `R`).
- **5-gram Jaccard Similarity:**
  - Maximum pairwise character 5-gram Jaccard similarity across the `72` positive problem texts: **`0.7153`** (`< 0.75` threshold).
  - Maximum pairwise character 5-gram Jaccard similarity across all `144` problem texts: **`0.7153`** (`< 0.80` threshold).
- **Pre-Freeze Deduplication Replacement Log (Section 6):**
  - During the pre-freeze external deduplication check, `143 / 144` cases passed all 9 deduplication checks cleanly, while initial candidate `W3-B01` (`S.ABC`, lengths `(7, 11, 13)`, ratio `2/5`) triggered a scale-invariant collision flag (`external_scale_invariant_flags`).
  - Before corpus freeze, `W3-B01` (`triangular_pyramid`, `perpendicular_line`, `section_only`) was replaced under the same procedural firewall with a brand-new configuration: solid `S.EFG` right-angled at `E` (`EF = 13`, `EG = 19`, `SE = 23`), auxiliary point `H` on `SE` with `SH = 3/11 SE`, and plane `(P)` through `H` perpendicular to `SF` (max 5-gram Jaccard of `W3-B01` against all other cases: `0.3909`).

---

## 3. Negative Corpus Stratification (`N`, 72 Cases)

All `72` negative cases (`W3-N01` .. `W3-N72`) are evenly distributed across the `18` required negative classes (`4` cases per class):

| Negative Class | Case IDs |Acceptable Refusal Categories | Track B Representability | Gap Subclass |
|---|---|---|---|---|
| `contradictory_source_facts` | `W3-N01` .. `W3-N04` | `CONTRADICTION`, `GEOMETRY_DEGENERATE`, `INPUT_INVALID`, `SOURCE_GROUNDING` | `representable_with_explicit_gap` | `contradictory` |
| `wrong_solid_kind` | `W3-N05` .. `W3-N08` | `SOURCE_GROUNDING`, `INPUT_INVALID`, `CONTRADICTION` | `representable_with_explicit_gap` | `contradictory` |
| `wrong_solid_notation` | `W3-N09` .. `W3-N12` | `INPUT_INVALID`, `SOURCE_GROUNDING` | `representable_with_explicit_gap` | `contradictory` |
| `mixed_solid_operands` | `W3-N13` .. `W3-N16` | `UNSUPPORTED_CAPABILITY`, `INPUT_INVALID`, `SOURCE_GROUNDING`, `CONTRADICTION` | `intentionally_outside_supported_v2_capability` (`N13..N14`), `representable_with_explicit_gap` (`N15..N16`) | `unsupported_topology` (`N13..N14`), `contradictory` (`N15..N16`) |
| `missing_mandatory_premise` | `W3-N17` .. `W3-N20` | `UNDERDETERMINED`, `CONTRADICTION` | `representable_with_explicit_gap` | `missing_required_information` |
| `unproven_parallel_or_perpendicular_relation` | `W3-N21` .. `W3-N24` | `SOURCE_GROUNDING`, `UNDERDETERMINED`, `CONTRADICTION` | `representable_with_explicit_gap` | `missing_required_information` (`N21..N23`), `contradictory` (`N24`) |
| `ambiguous_source_labels` | `W3-N25` .. `W3-N28` | `AMBIGUOUS`, `CONTRADICTION`, `INPUT_INVALID`, `SOURCE_GROUNDING`, `GEOMETRY_DEGENERATE` | `representable_with_explicit_gap` | `ambiguous` |
| `wrong_ratio` | `W3-N29` .. `W3-N32` | `SOURCE_GROUNDING`, `INPUT_INVALID`, `CONTRADICTION`, `GEOMETRY_DEGENERATE` | `representable_with_explicit_gap` | `contradictory` |
| `wrong_edge` | `W3-N33` .. `W3-N36` | `SOURCE_GROUNDING`, `INPUT_INVALID`, `CONTRADICTION`, `UNSUPPORTED_CAPABILITY`, `GEOMETRY_DEGENERATE` | `representable_with_explicit_gap` (`N33..N34`), `intentionally_outside_supported_v2_capability` (`N35..N36`) | `contradictory` (`N33..N34`), `unsupported_relation` (`N35..N36`) |
| `impossible_vertex` | `W3-N37` .. `W3-N40` | `INPUT_INVALID`, `SOURCE_GROUNDING`, `UNDERDETERMINED` | `representable_with_explicit_gap` | `contradictory` |
| `invalid_section_declaration` | `W3-N41` .. `W3-N44` | `INPUT_INVALID`, `UNDERDETERMINED`, `CONTRADICTION` | `representable_with_explicit_gap` | `missing_required_information` (`N41..N43`), `contradictory` (`N44`) |
| `unsupported_geometry_capability` | `W3-N45` .. `W3-N48` | `UNSUPPORTED_CAPABILITY` | `intentionally_outside_supported_v2_capability` | `unsupported_topology` (`N45..N47`), `unsupported_relation` (`N48`) |
| `conflicting_section_area_requests` | `W3-N49` .. `W3-N52` | `SOURCE_GROUNDING`, `INPUT_INVALID` | `representable_with_explicit_gap` | `contradictory` |
| `incorrect_stated_intersections` | `W3-N53` .. `W3-N56` | `GEOMETRY_DEGENERATE`, `CONTRADICTION`, `UNSUPPORTED_CAPABILITY` | `representable_with_explicit_gap` | `contradictory` |
| `category_a_b_semantic_contradictions` | `W3-N57` .. `W3-N60` | `AMBIGUOUS`, `CONTRADICTION`, `INPUT_INVALID`, `GEOMETRY_DEGENERATE` | `representable_with_explicit_gap` | `contradictory` |
| `primed_label_identity_ambiguity` | `W3-N61` .. `W3-N64` | `SOURCE_GROUNDING`, `INPUT_INVALID`, `CONTRADICTION`, `GEOMETRY_DEGENERATE` | `representable_with_explicit_gap` | `contradictory` |
| `source_provenance_mismatch` | `W3-N65` .. `W3-N68` | `SOURCE_GROUNDING`, `UNDERDETERMINED` | `representable_with_explicit_gap` | `contradictory` |
| `geometry_degeneration` | `W3-N69` .. `W3-N72` | `GEOMETRY_DEGENERATE`, `CONTRADICTION`, `UNDERDETERMINED` | `representable_with_explicit_gap` | `contradictory` |

---

## 4. Independent Rational Oracle Verification

The standalone oracle (`oracle/oracle_holdout_wave3.py`) computes and checks `oracle/expected.json` from `inputs/holdout-wave3.json` and `oracle/geometry.json` using exact `fractions.Fraction` 3D vector arithmetic:

- Command:
  ```powershell
  python docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-geometry-holdout-wave3/oracle/oracle_holdout_wave3.py --check
  ```
- Output:
  ```text
  OK: verified 72 positive cases in ...\oracle\expected.json
  ```
- Artifact Hashes:
  - `inputs/holdout-wave3.json`: `cf2d3fd759b6a94c4eae2545a4a409e50859ff28e861f797609b6a259fe4dee0`
  - `oracle/geometry.json`: `a7c04b77211d85fc7912bbcc6ad34e83e864cf46ea5904e4ebc5e201b520b983`
  - `oracle/oracle_holdout_wave3.py`: `aa156523cc6895d935fc6428995dad48a4684bfc60d96be89e51d41ef4b5c1c0`
  - `oracle/expected.json`: `9cabeb19ae0d10e1112795097e7ed18e0b0b3aa7bc18700a9d60813a0cbcf9df`

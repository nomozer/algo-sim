# Corpus Provenance — Independent Holdout Wave 2 (`holdout-wave2`)

## 1. Corpus Overview & Stratification Summary

- **Suite ID:** `holdout-wave2`
- **Independence Class:** `AI_CURATED_PROCEDURAL_INDEPENDENCE`
- **Total Cases:** 96 (`48` positive `SERVE` + `48` negative `REFUSE`)
  - **Stratum `P-B` (`W2-B01..W2-B36`, 36 cases):**
    - 6 supported solid families × 3 cutting-plane relations (`perpendicular_line`, `parallel_plane`, `parallel_two_lines`) × 2 cases per cell = 36 cases.
    - Question-type balance: `12` `section_only`, `12` `area_only`, `12` `section_and_area` (`2` of each per family).
    - Length-unit balance: `1` numeric (`length_unit = "1"`) and `1` symbolic (`length_unit = "a"`) case in every `(family, relation)` cell (`18` numeric + `18` symbolic).
  - **Stratum `P-A` (`W2-A01..W2-A12`, 12 cases):**
    - 6 pyramids (`3` `triangular_pyramid`, `3` `quadrilateral_pyramid`) and 6 prisms (`2` `right_triangular_prism`, `1` `oblique_triangular_prism`, `2` `cuboid`, `1` `cube`) with `cutting_plane_relation = "stated_intersections"`.
    - Plane-kind mix: `4` `through_point_parallel_plane`, `4` `through_point_perpendicular_line`, `4` `through_point_parallel_two_lines`.
    - Stated-intersections mix: `6` cases with named intersection points (`point: "N", "P", ...`) and `6` cases with unnamed edge intersections (`point: null`); `4` cases where `through_point` is a solid vertex on one lateral edge and `8` cases where `through_point` is an interior point (`midpoint` or `divide_segment`) on one lateral edge and the plane cuts all remaining lateral edges in `(0, 1)`.
    - Question-type balance: `4` `section_only`, `4` `area_only`, `4` `section_and_area`.
    - Length-unit balance: `6` numeric (`"1"`) and `6` symbolic (`"a"`).
  - **Stratum `N` (`W2-N01..W2-N48`, 48 cases):**
    - 16 negative classes × 3 cases per class = 48 cases (`expected_disposition = "REFUSE"`).
    - Every negative case maps its `acceptable_categories` strictly to executable refusal categories defined in `tools/refusal_taxonomy.json` (`SOURCE_GROUNDING`, `CONTRADICTION`, `UNDERDETERMINED`, `AMBIGUOUS`, `UNSUPPORTED_CAPABILITY`, `GEOMETRY_DEGENERATE`, `INPUT_INVALID`).

---

## 2. Stratum `P-B` Cell-by-Cell Provenance (`W2-B01..W2-B36`)

| Case ID | Family | Cutting-Plane Relation | Question Type | Unit | Solid | Plane Specification | Oracle `vertex_count` | Oracle `area_squared` |
|---|---|---|---|---|---|---|---|---|
| `W2-B01` | `triangular_pyramid` | `perpendicular_line` | `section_only` | `1` | `S.ABC` | `(M) ⊥ SB` | `3` | `64/5` |
| `W2-B02` | `triangular_pyramid` | `perpendicular_line` | `area_only` | `a` | `A.BCD` | `(M) ⊥ AB` | `3` | `23716/625` |
| `W2-B03` | `triangular_pyramid` | `parallel_plane` | `section_and_area` | `1` | `S.MNP` | `(K) // (MNP)` | `3` | `12100/9` |
| `W2-B04` | `triangular_pyramid` | `parallel_plane` | `section_only` | `a` | `S.ABC` | `(E) // (SAC)` | `3` | `173056/81` |
| `W2-B05` | `triangular_pyramid` | `parallel_two_lines` | `area_only` | `1` | `S.EFG` | `(H) // EF, EG` | `3` | `585225/256` |
| `W2-B06` | `triangular_pyramid` | `parallel_two_lines` | `section_and_area` | `a` | `A.BCD` | `(I) // AB, CD` | `4` | `99225/64` |
| `W2-B07` | `quadrilateral_pyramid` | `perpendicular_line` | `area_only` | `1` | `S.ABCD` | `(M) ⊥ SA` | `4` | `17424/25` |
| `W2-B08` | `quadrilateral_pyramid` | `perpendicular_line` | `section_and_area` | `a` | `S.MNPQ` | `(M) ⊥ SP` | `4` | `2187/4` |
| `W2-B09` | `quadrilateral_pyramid` | `parallel_plane` | `section_only` | `1` | `S.ABCD` | `(I) // (ABC)` | `4` | `3111696/625` |
| `W2-B10` | `quadrilateral_pyramid` | `parallel_plane` | `area_only` | `a` | `S.EFGH` | `(K) // (SEH)` | `4` | `153664/81` |
| `W2-B11` | `quadrilateral_pyramid` | `parallel_two_lines` | `section_and_area` | `1` | `S.MNPQ` | `(E) // MN, MQ` | `4` | `625` |
| `W2-B12` | `quadrilateral_pyramid` | `parallel_two_lines` | `section_only` | `a` | `S.ABCD` | `(M) // SA, BC` | `4` | `53361/64` |
| `W2-B13` | `right_triangular_prism` | `perpendicular_line` | `section_and_area` | `1` | `ABC.A'B'C'` | `(M) ⊥ AA'` | `3` | `8281/4` |
| `W2-B14` | `right_triangular_prism` | `perpendicular_line` | `section_only` | `a` | `MNP.M'N'P'` | `(I) ⊥ MN` | `4` | `20449/4` |
| `W2-B15` | `right_triangular_prism` | `parallel_plane` | `area_only` | `1` | `EFG.E'F'G'` | `(K) // (EFG)` | `3` | `5184` |
| `W2-B16` | `right_triangular_prism` | `parallel_plane` | `section_and_area` | `a` | `ABC.A'B'C'` | `(M) // (ACC')` | `4` | `21609/4` |
| `W2-B17` | `right_triangular_prism` | `parallel_two_lines` | `section_only` | `1` | `MNP.M'N'P'` | `(H) // MN, MP` | `3` | `5929` |
| `W2-B18` | `right_triangular_prism` | `parallel_two_lines` | `area_only` | `a` | `ABC.A'B'C'` | `(E) // AB, AA'` | `4` | `1764` |
| `W2-B19` | `oblique_triangular_prism` | `perpendicular_line` | `section_only` | `1` | `ABC.A'B'C'` | `(M) ⊥ A'B` | `3` | `1764` |
| `W2-B20` | `oblique_triangular_prism` | `perpendicular_line` | `area_only` | `a` | `MNP.M'N'P'` | `(K) ⊥ M'N` | `3` | `1089` |
| `W2-B21` | `oblique_triangular_prism` | `parallel_plane` | `section_and_area` | `1` | `ABC.A'B'C'` | `(M) // (ABC)` | `3` | `4624` |
| `W2-B22` | `oblique_triangular_prism` | `parallel_plane` | `section_only` | `a` | `EFG.E'F'G'` | `(I) // (EFG)` | `3` | `1225` |
| `W2-B23` | `oblique_triangular_prism` | `parallel_two_lines` | `area_only` | `1` | `MNP.M'N'P'` | `(E) // MN, MP` | `3` | `29241/4` |
| `W2-B24` | `oblique_triangular_prism` | `parallel_two_lines` | `section_and_area` | `a` | `ABC.A'B'C'` | `(M) // AB, AA'` | `4` | `2304` |
| `W2-B25` | `cuboid` | `perpendicular_line` | `area_only` | `1` | `ABCD.A'B'C'D'` | `(M) ⊥ AA'` | `4` | `5929` |
| `W2-B26` | `cuboid` | `perpendicular_line` | `section_and_area` | `a` | `MNPQ.M'N'P'Q'` | `(I) ⊥ MN` | `4` | `4225` |
| `W2-B27` | `cuboid` | `parallel_plane` | `section_only` | `1` | `EFGH.E'F'G'H'` | `(K) // (EFG)` | `4` | `5929` |
| `W2-B28` | `cuboid` | `parallel_plane` | `area_only` | `a` | `ABCD.A'B'C'D'` | `(M) // (ADD')` | `4` | `6084` |
| `W2-B29` | `cuboid` | `parallel_two_lines` | `section_and_area` | `1` | `MNPQ.M'N'P'Q'` | `(H) // MN, MQ` | `4` | `3025` |
| `W2-B30` | `cuboid` | `parallel_two_lines` | `section_only` | `a` | `ABCD.A'B'C'D'` | `(E) // AB, AA'` | `4` | `3969` |
| `W2-B31` | `cube` | `perpendicular_line` | `section_and_area` | `1` | `ABCD.A'B'C'D'` | `(M) ⊥ AA'` | `4` | `14641` |
| `W2-B32` | `cube` | `perpendicular_line` | `section_only` | `a` | `MNPQ.M'N'P'Q'` | `(I) ⊥ MN` | `4` | `28561` |
| `W2-B33` | `cube` | `parallel_plane` | `area_only` | `1` | `EFGH.E'F'G'H'` | `(K) // (EFG)` | `4` | `38416` |
| `W2-B34` | `cube` | `parallel_plane` | `section_and_area` | `a` | `ABCD.A'B'C'D'` | `(M) // (BDD')` | `4` | `7200` |
| `W2-B35` | `cube` | `parallel_two_lines` | `section_only` | `1` | `MNPQ.M'N'P'Q'` | `(H) // MN, MQ` | `4` | `20736` |
| `W2-B36` | `cube` | `parallel_two_lines` | `area_only` | `a` | `EFGH.E'F'G'H'` | `(I) // EH, EE'` | `4` | `50625` |

---

## 3. Stratum `P-A` Cell-by-Cell Provenance (`W2-A01..W2-A12`)

| Case ID | Family | Plane Kind | Question Type | Unit | Solid | `through_point` | `stated_intersections` | Oracle `vertex_count` | Oracle `area_squared` |
|---|---|---|---|---|---|---|---|---|---|
| `W2-A01` | `triangular_pyramid` | `through_point_perpendicular_line` | `section_only` | `1` | `S.ABC` | `A` | named (`M∈SB, N∈SC`) | `3` | `2401/48` |
| `W2-A02` | `triangular_pyramid` | `through_point_parallel_plane` | `area_only` | `a` | `S.ABC` | `M` | named (`N∈SB, P∈SC`) | `3` | `225/4` |
| `W2-A03` | `triangular_pyramid` | `through_point_perpendicular_line` | `section_and_area` | `1` | `S.MNP` | `I` | unnamed (`SN, SP`) | `3` | `1225/4` |
| `W2-A04` | `quadrilateral_pyramid` | `through_point_perpendicular_line` | `section_and_area` | `1` | `S.ABCD` | `A` | named (`M∈SB, N∈SC, P∈SD`) | `4` | `253125000/485809` |
| `W2-A05` | `quadrilateral_pyramid` | `through_point_parallel_plane` | `section_only` | `a` | `S.ABCD` | `M` | unnamed (`SB, SC, SD`) | `4` | `144` |
| `W2-A06` | `quadrilateral_pyramid` | `through_point_parallel_two_lines` | `area_only` | `1` | `S.ABCD` | `M` | unnamed (`SB, SC, SD`) | `4` | `4096` |
| `W2-A07` | `right_triangular_prism` | `through_point_perpendicular_line` | `area_only` | `1` | `ABC.A'B'C'` | `A'` | named (`M∈BB', N∈CC'`) | `3` | `1875/8` |
| `W2-A08` | `right_triangular_prism` | `through_point_parallel_plane` | `section_and_area` | `a` | `ABC.A'B'C'` | `M` | unnamed (`BB', CC'`) | `3` | `1764` |
| `W2-A09` | `oblique_triangular_prism` | `through_point_parallel_plane` | `section_only` | `1` | `ABC.A'B'C'` | `M` | named (`N∈BB', P∈CC'`) | `3` | `1600` |
| `W2-A10` | `cuboid` | `through_point_perpendicular_line` | `section_only` | `a` | `ABCD.A'B'C'D'` | `A'` | unnamed (`BB', CC', DD'`) | `4` | `504` |
| `W2-A11` | `cuboid` | `through_point_parallel_plane` | `area_only` | `1` | `ABCD.A'B'C'D'` | `M` | named (`N∈BB', P∈CC', Q∈DD'`) | `4` | `9801` |
| `W2-A12` | `cube` | `through_point_perpendicular_line` | `section_and_area` | `a` | `ABCD.A'B'C'D'` | `M` | unnamed (`BB', CC', DD'`) | `4` | `65536` |

---

## 4. Stratum `N` Cell-by-Cell Provenance (`W2-N01..W2-N48`)

| Case ID | Negative Class | Negative Origin | Acceptable Taxonomy Categories | Target Family | Target Relation | Question Type | `payload` |
|---|---|---|---|---|---|---|---|
| `W2-N01` | `wrong_solid_identity` | `faulty_extraction` | `SOURCE_GROUNDING`, `INPUT_INVALID` | `triangular_pyramid` | `parallel_plane` | `section_only` | valid `2.0` |
| `W2-N02` | `wrong_solid_identity` | `faulty_extraction` | `SOURCE_GROUNDING`, `INPUT_INVALID` | `right_triangular_prism` | `perpendicular_line` | `section_only` | valid `2.0` |
| `W2-N03` | `wrong_solid_identity` | `faulty_extraction` | `SOURCE_GROUNDING`, `INPUT_INVALID` | `quadrilateral_pyramid` | `parallel_plane` | `section_only` | valid `2.0` |
| `W2-N04` | `contradictory_solid_kind` | `flawed_or_unsupported_problem` | `CONTRADICTION` | `quadrilateral_pyramid` | `parallel_plane` | `section_only` | valid `2.0` |
| `W2-N05` | `contradictory_solid_kind` | `flawed_or_unsupported_problem` | `CONTRADICTION` | `triangular_pyramid` | `perpendicular_line` | `area_only` | valid `2.0` |
| `W2-N06` | `contradictory_solid_kind` | `flawed_or_unsupported_problem` | `CONTRADICTION`, `GEOMETRY_DEGENERATE` | `triangular_pyramid` | `parallel_plane` | `section_only` | valid `2.0` |
| `W2-N07` | `wrong_cutting_plane` | `faulty_extraction` | `SOURCE_GROUNDING` | `triangular_pyramid` | `perpendicular_line` | `section_only` | valid `2.0` |
| `W2-N08` | `wrong_cutting_plane` | `faulty_extraction` | `SOURCE_GROUNDING` | `triangular_pyramid` | `parallel_plane` | `section_only` | valid `2.0` |
| `W2-N09` | `wrong_cutting_plane` | `faulty_extraction` | `SOURCE_GROUNDING` | `triangular_pyramid` | `parallel_two_lines` | `section_only` | valid `2.0` |
| `W2-N10` | `ambiguous_plane_name` | `faulty_extraction` | `SOURCE_GROUNDING`, `AMBIGUOUS` | `right_triangular_prism` | `parallel_plane` | `section_only` | valid `2.0` |
| `W2-N11` | `ambiguous_plane_name` | `flawed_or_unsupported_problem` | `SOURCE_GROUNDING`, `AMBIGUOUS` | `cuboid` | `perpendicular_line` | `section_only` | valid `2.0` |
| `W2-N12` | `ambiguous_plane_name` | `faulty_extraction` | `SOURCE_GROUNDING`, `AMBIGUOUS` | `cube` | `parallel_plane` | `section_only` | valid `2.0` |
| `W2-N13` | `multiple_planes` | `faulty_extraction` | `INPUT_INVALID`, `SOURCE_GROUNDING`, `UNSUPPORTED_CAPABILITY` | `triangular_pyramid` | `other` | `section_only` | valid `2.0` |
| `W2-N14` | `multiple_planes` | `faulty_extraction` | `SOURCE_GROUNDING`, `AMBIGUOUS` | `quadrilateral_pyramid` | `other` | `section_only` | valid `2.0` |
| `W2-N15` | `multiple_planes` | `flawed_or_unsupported_problem` | `SOURCE_GROUNDING`, `AMBIGUOUS`, `UNSUPPORTED_CAPABILITY` | `triangular_pyramid` | `other` | `section_only` | valid `2.0` |
| `W2-N16` | `multiple_solids` | `flawed_or_unsupported_problem` | `UNSUPPORTED_CAPABILITY`, `SOURCE_GROUNDING`, `INPUT_INVALID` | `other` | `parallel_plane` | `section_only` | valid `2.0` |
| `W2-N17` | `multiple_solids` | `flawed_or_unsupported_problem` | `UNSUPPORTED_CAPABILITY`, `SOURCE_GROUNDING` | `triangular_pyramid` | `parallel_plane` | `other` | valid `2.0` |
| `W2-N18` | `multiple_solids` | `flawed_or_unsupported_problem` | `UNSUPPORTED_CAPABILITY`, `SOURCE_GROUNDING`, `UNDERDETERMINED` | `other` | `parallel_plane` | `section_only` | valid `2.0` |
| `W2-N19` | `incorrect_source_quotations` | `faulty_extraction` | `SOURCE_GROUNDING` | `triangular_pyramid` | `parallel_plane` | `section_only` | valid `2.0` |
| `W2-N20` | `incorrect_source_quotations` | `faulty_extraction` | `SOURCE_GROUNDING` | `triangular_pyramid` | `perpendicular_line` | `section_only` | valid `2.0` |
| `W2-N21` | `incorrect_source_quotations` | `faulty_extraction` | `SOURCE_GROUNDING` | `triangular_pyramid` | `parallel_plane` | `section_only` | valid `2.0` |
| `W2-N22` | `unsupported_topology` | `flawed_or_unsupported_problem` | `UNSUPPORTED_CAPABILITY` | `other` | `other` | `section_and_area` | valid `2.0` |
| `W2-N23` | `unsupported_topology` | `flawed_or_unsupported_problem` | `UNSUPPORTED_CAPABILITY` | `other` | `parallel_plane` | `section_only` | valid `2.0` |
| `W2-N24` | `unsupported_topology` | `flawed_or_unsupported_problem` | `UNSUPPORTED_CAPABILITY`, `UNDERDETERMINED` | `quadrilateral_pyramid` | `parallel_plane` | `section_only` | valid `2.0` |
| `W2-N25` | `missing_dimensions` | `flawed_or_unsupported_problem` | `UNDERDETERMINED` | `triangular_pyramid` | `parallel_plane` | `area_only` | valid `2.0` |
| `W2-N26` | `missing_dimensions` | `flawed_or_unsupported_problem` | `UNDERDETERMINED` | `right_triangular_prism` | `parallel_plane` | `area_only` | valid `2.0` |
| `W2-N27` | `missing_dimensions` | `flawed_or_unsupported_problem` | `UNDERDETERMINED` | `cuboid` | `parallel_plane` | `area_only` | valid `2.0` |
| `W2-N28` | `underconstrained_geometry` | `flawed_or_unsupported_problem` | `UNDERDETERMINED` | `triangular_pyramid` | `perpendicular_line` | `section_only` | valid `2.0` |
| `W2-N29` | `underconstrained_geometry` | `flawed_or_unsupported_problem` | `UNDERDETERMINED`, `INPUT_INVALID` | `triangular_pyramid` | `parallel_plane` | `area_only` | valid `2.0` |
| `W2-N30` | `underconstrained_geometry` | `flawed_or_unsupported_problem` | `UNDERDETERMINED` | `triangular_pyramid` | `parallel_plane` | `section_only` | valid `2.0` |
| `W2-N31` | `conditional_or_negated_premises` | `faulty_extraction` | `SOURCE_GROUNDING` | `triangular_pyramid` | `parallel_plane` | `section_only` | valid `2.0` |
| `W2-N32` | `conditional_or_negated_premises` | `faulty_extraction` | `SOURCE_GROUNDING` | `triangular_pyramid` | `parallel_plane` | `section_only` | valid `2.0` |
| `W2-N33` | `conditional_or_negated_premises` | `flawed_or_unsupported_problem` | `SOURCE_GROUNDING` | `triangular_pyramid` | `parallel_plane` | `section_only` | valid `2.0` |
| `W2-N34` | `wrong_question_target` | `faulty_extraction` | `SOURCE_GROUNDING` | `triangular_pyramid` | `parallel_plane` | `section_only` | valid `2.0` |
| `W2-N35` | `wrong_question_target` | `faulty_extraction` | `SOURCE_GROUNDING` | `triangular_pyramid` | `parallel_plane` | `other` | valid `2.0` |
| `W2-N36` | `wrong_question_target` | `faulty_extraction` | `SOURCE_GROUNDING` | `triangular_pyramid` | `parallel_plane` | `other` | valid `2.0` |
| `W2-N37` | `incorrect_named_section` | `flawed_or_unsupported_problem` | `SOURCE_GROUNDING`, `CONTRADICTION` | `triangular_pyramid` | `stated_intersections` | `area_only` | valid `2.0` |
| `W2-N38` | `incorrect_named_section` | `faulty_extraction` | `SOURCE_GROUNDING`, `CONTRADICTION`, `INPUT_INVALID` | `triangular_pyramid` | `stated_intersections` | `section_only` | valid `2.0` |
| `W2-N39` | `incorrect_named_section` | `flawed_or_unsupported_problem` | `SOURCE_GROUNDING`, `CONTRADICTION` | `triangular_pyramid` | `stated_intersections` | `area_only` | valid `2.0` |
| `W2-N40` | `ambiguous_anaphoric_area_request` | `flawed_or_unsupported_problem` | `SOURCE_GROUNDING`, `AMBIGUOUS` | `triangular_pyramid` | `parallel_plane` | `area_only` | valid `2.0` |
| `W2-N41` | `ambiguous_anaphoric_area_request` | `flawed_or_unsupported_problem` | `SOURCE_GROUNDING`, `AMBIGUOUS` | `triangular_pyramid` | `perpendicular_line` | `area_only` | valid `2.0` |
| `W2-N42` | `ambiguous_anaphoric_area_request` | `flawed_or_unsupported_problem` | `SOURCE_GROUNDING`, `AMBIGUOUS` | `triangular_pyramid` | `parallel_plane` | `area_only` | valid `2.0` |
| `W2-N43` | `contradictory_cut_point_claims` | `flawed_or_unsupported_problem` | `CONTRADICTION`, `GEOMETRY_DEGENERATE` | `triangular_pyramid` | `stated_intersections` | `section_only` | valid `2.0` |
| `W2-N44` | `contradictory_cut_point_claims` | `flawed_or_unsupported_problem` | `CONTRADICTION`, `GEOMETRY_DEGENERATE`, `UNSUPPORTED_CAPABILITY` | `quadrilateral_pyramid` | `stated_intersections` | `section_only` | valid `2.0` |
| `W2-N45` | `contradictory_cut_point_claims` | `flawed_or_unsupported_problem` | `CONTRADICTION`, `GEOMETRY_DEGENERATE`, `INPUT_INVALID` | `triangular_pyramid` | `stated_intersections` | `section_only` | valid `2.0` |
| `W2-N46` | `degenerate_or_tampered_section_plane` | `flawed_or_unsupported_problem` | `GEOMETRY_DEGENERATE`, `CONTRADICTION` | `triangular_pyramid` | `parallel_plane` | `section_only` | valid `2.0` |
| `W2-N47` | `degenerate_or_tampered_section_plane` | `flawed_or_unsupported_problem` | `GEOMETRY_DEGENERATE`, `CONTRADICTION`, `UNDERDETERMINED` | `cuboid` | `parallel_two_lines` | `section_only` | valid `2.0` |
| `W2-N48` | `degenerate_or_tampered_section_plane` | `flawed_or_unsupported_problem` | `GEOMETRY_DEGENERATE`, `CONTRADICTION` | `triangular_pyramid` | `perpendicular_line` | `section_only` | valid `2.0` |

---

## 5. Pre-Freeze Deduplication Replacement Log (`preregistration.md §2.4` / Owner GO §6)

- **`W2-B34` (`P-B`, `cube`, `parallel_plane`, `section_and_area`, unit `"a"`):** Updated through-point `M` on `AB` from midpoint (`1/2`) to `divide_segment` ratio `3/5` (`AM = 3/5 AB`) on cube `ABCD.A'B'C'D'` (side `10a`) parallel to `(BDD')` (`area_squared = 7200`).
- **`W2-A04` (`P-A`, `quadrilateral_pyramid`, `stated_intersections`, `section_and_area`, unit `"1"`):** Updated base `ABCD` from square (`10 × 10`, `SA = 10`) to non-square rectangle (`AB = 6`, `AD = 8`, `SA = 10` with `SA ⊥ (ABCD)`) with plane `(Q)` through vertex `A` perpendicular to `SC` cutting `SB, SC, SD` at named interior points `M, N, P` (`area_squared = 253125000/485809`).
- **Negative-case diversification (`W2-N01, W2-N07..W2-N15, W2-N19..W2-N21, W2-N25, W2-N31, W2-N34, W2-N36..W2-N38, W2-N40, W2-N42, W2-N43`):** Diversified Vietnamese phrasing, solid families (`triangular_pyramid`, `quadrilateral_pyramid`, `right_triangular_prism`, `cuboid`, `cube`), and vertex labels (`A.BCD`, `S.MNP`, `S.EFG`, `S.ABCD`, `MNP.M'N'P'`, `ABCD.A'B'C'D'`, `EFGH.E'F'G'H'`) so that all pairwise character 5-gram Jaccard similarities across the 96 cases are strictly `< 0.80` (max `0.756`).

# Independent Oracle Review Report — `hybrid-v2-independent-vietnamese-geometry-holdout-wave3`

- **Schema:** `HOLDOUT_WAVE3_INDEPENDENT_ORACLE_REVIEW/1`
- **Task:** `HYBRID_V2_INDEPENDENT_VIETNAMESE_GEOMETRY_HOLDOUT_WAVE3`
- **Reviewer Role:** Independent Holdout Wave 3 Oracle Reviewer (Section 7 of Owner GO)
- **Timing:** Executed **BEFORE** any product route execution (`0` product imports, `0` product calls)
- **Final Verdict:** **`ORACLE_VERIFIED_BEFORE_EXECUTION`**
- **Positive Cases Verified:** `72 / 72` (`54` `P-B` + `18` `P-A`)
- **Negative Cases Verified:** `72 / 72` (`18` classes × `4` cases)
- **Discrepancies Found:** `0`

---

## 1. Audited Artifact Hashes (Pre-Execution Freeze Check)

| File | SHA-256 |
|---|---|
| `inputs/holdout-wave3.json` | `cf2d3fd759b6a94c4eae2545a4a409e50859ff28e861f797609b6a259fe4dee0` |
| `oracle/geometry.json` | `a7c04b77211d85fc7912bbcc6ad34e83e864cf46ea5904e4ebc5e201b520b983` |
| `oracle/oracle_holdout_wave3.py` | `aa156523cc6895d935fc6428995dad48a4684bfc60d96be89e51d41ef4b5c1c0` |
| `oracle/expected.json` | `9cabeb19ae0d10e1112795097e7ed18e0b0b3aa7bc18700a9d60813a0cbcf9df` |
| `refusal-taxonomy.json` | `b393995bbc11ae25f904052b597d9e89b9cf5adaaeaba468dcb2a27003319b00` |

---

## 2. Independent Verification Methodology

1. **Zero Product Coupling:** Verification was performed using a clean-room Python script (`fractions.Fraction` only, `0` imports from `backend.app.*`, and independent of `oracle/oracle_holdout_wave3.py`).
2. **Independent Premise-Only 3D Coordinate Synthesis & Euclidean Isometry Check:**
   - For all `72` positive cases, the reviewer independently synthesized 3D vertex coordinates and named edge-division points directly from `inputs/holdout-wave3.json` (`solids[0].notation` and `premises`) without reading `oracle/geometry.json` coordinates.
   - Every premise in `inputs/holdout-wave3.json` (`segment_length`, `right_angle`, `rectangle`, `base_is_square`, `right_prism`, `perpendicular_line_plane`, `orthogonal_projection`, `midpoint`, `divide_segment`) was checked both against `oracle/geometry.json` and against the Vietnamese source quote in `problem_text`.
   - All $\binom{V}{2}$ pairwise squared distances $d^2(U, V)$ between solid vertices and named points in `oracle/geometry.json` were compared against the premise-synthesized coordinates: **`0` mismatches across all `72` positive solids**, proving `oracle/geometry.json` is an exact Euclidean isometry of the unique 3D configuration determined by the problem text.
3. **Independent Cutting-Plane Derivation:**
   - From `derived_sections[0]` (`through_point` and `plane_kind` $\in$ `{through_point_perpendicular_line, through_point_parallel_plane, through_point_parallel_two_lines}`), the plane normal $\vec{n}$ and offset $d = \vec{n} \cdot \vec{P}_0$ were derived independently and verified against `oracle/expected.json`.
4. **Exact Rational Edge Intersection, Cyclic Ordering & Strict Convexity:**
   - Every solid edge $(U, V)$ was intersected with $\vec{n} \cdot \vec{X} = d$ in exact `Fraction` arithmetic: $t = -(\vec{n}\cdot\vec{U} - d) / (\vec{n}\cdot(\vec{V} - \vec{U}))$.
   - Intersections with $0 \le t \le 1$ were collected, deduplicating solid-vertex hits ($t \in \{0, 1\}$) and strict interior edge cuts ($0 < t < 1$).
   - Vertices were ordered cyclically around the section centroid $\vec{C} = \frac{1}{m}\sum_{i=0}^{m-1} \vec{P}_i$ in the 2D basis $(\vec{e}_1, \vec{e}_2) = (\vec{P}_0 - \vec{C},\, \vec{n} \times (\vec{P}_0 - \vec{C}))$, and strict convexity was verified at every vertex via $(\vec{P}_{i+1}-\vec{P}_i)\times(\vec{P}_{i+2}-\vec{P}_{i+1})\cdot\vec{n} > 0$.
5. **Lagrange's Identity & Gram Determinant Area Verification:**
   - Exact `area_squared` was computed via 3D triangulation $\text{Area}^2 = \frac{1}{4}\left\|\sum_{i=1}^{m-2} (\vec{P}_i - \vec{P}_0) \times (\vec{P}_{i+1} - \vec{P}_0)\right\|^2$ and cross-checked against the 2-edge Gram determinant $\frac{1}{4}(\|\vec{u}\|^2\|\vec{v}\|^2 - (\vec{u}\cdot\vec{v})^2)$ on each triangle.
   - Exact square-factor radical extraction produced `area_display` and verified every field in `oracle/expected.json` (`vertex_count`, canonical boundary descriptors up to endpoint reversal, dihedral cyclic order, `polygon_3d`, `area_squared`, `plane_equation`, `expected_category`).

---

## 3. Step-by-Step Independent Hand / Rational Checks Across Strata

### 3.1 `W3-B01` (`P-B` · `triangular_pyramid` · `perpendicular_line` · `section_only`)
- **Premises:** Right pyramid `S.EFG` with $\angle FEG = 90^\circ$, $SE \perp (EFG)$, $EF = 13$, $EG = 19$, $SE = 23$. Point $H \in SE$ with $SH = \frac{3}{11}SE$.
- **Coordinates:** $E=(0,0,0)$, $F=(13,0,0)$, $G=(0,19,0)$, $S=(0,0,23)$, $H = S + \frac{3}{11}(E-S) = \left(0, 0, \frac{184}{11}\right)$.
- **Cutting Plane `(P)`:** Through $H$ and $\perp SF$. Normal $\vec{n} = F - S = (13, 0, -23)$, offset $d = \vec{n}\cdot H = -23 \cdot \frac{184}{11} = -\frac{4232}{11}$.
- **Edge Cuts:**
  - $SE$: $t_{SE} = \frac{3}{11} \implies P_0 = H = \left(0, 0, \frac{184}{11}\right)$.
  - $SG$: $\vec{n}\cdot(S + t(G-S)) = -23(23)(1-t) = -\frac{4232}{11} \implies t_{SG} = \frac{3}{11} \implies P_1 = \left(0, \frac{57}{11}, \frac{184}{11}\right)$.
  - $SF$: $\vec{n}\cdot(S + t(F-S)) = -529 + (169+529)t = -529 + 698t = -\frac{4232}{11} \implies 698t = \frac{1587}{11} \implies t_{SF} = \frac{1587}{7678} \implies P_2 = \left(\frac{20631}{7678}, 0, \frac{140093}{7678}\right)$.
- **Area Squared:** Since $P_1 - P_0 = \left(0, \frac{57}{11}, 0\right) \perp (P_2 - P_0) = \left(\frac{20631}{7678}, 0, \frac{36501}{7678}\right)$,
  $$\text{Area}^2 = \frac{1}{4}\left(\frac{57}{11}\right)^2 \cdot \frac{20631^2 + 36501^2}{7678^2} = \frac{1}{4} \cdot \frac{3249}{121} \cdot \frac{1757971182}{58951684} = \frac{2614174641}{40877672}.$$
  Matches `oracle/expected.json` (`2614174641/40877672`).

### 3.2 `W3-B10` (`P-B` · `quadrilateral_pyramid` · `perpendicular_line` · `section_only`)
- **Premises:** Pyramid `S.ABCD` with rectangle base $ABCD$ ($AB=5, AD=9$), $SA \perp (ABCD)$, $SA=13$. Plane `(Q)` through vertex $A$ and $\perp SC$.
- **Coordinates:** $A=(0,0,0), B=(5,0,0), C=(5,9,0), D=(0,9,0), S=(0,0,13)$.
- **Cutting Plane `(Q)`:** Normal $\vec{n} = C - S = (5, 9, -13)$, through $A=(0,0,0) \implies d = 0$.
- **Edge Cuts:**
  - $SA$: $t=1$ (vertex $A$).
  - $SB$: $\vec{n}\cdot(S + t(B-S)) = -169 + (25+169)t = 0 \implies t_{SB} = \frac{169}{194}$.
  - $SC$: $\vec{n}\cdot(S + t(C-S)) = -169 + (25+81+169)t = 0 \implies t_{SC} = \frac{169}{275}$.
  - $SD$: $\vec{n}\cdot(S + t(D-S)) = -169 + (81+169)t = 0 \implies t_{SD} = \frac{169}{250}$.
- **Area Squared:** $\text{Area}^2 = \frac{4817160208809}{6468687500}$, matching `oracle/expected.json`.

### 3.3 `W3-B30` (`P-B` · `oblique_triangular_prism` · `perpendicular_line` · `section_and_area`)
- **Premises:** Oblique prism `DEF.D'E'F'` with $\angle EDF = 90^\circ$, $DE=5, DF=6$, projection of $D'$ on $(DEF)$ is $E$, $D'E=13$. Point $I \in DD'$ with $DI = \frac{5}{7}DD'$. Plane `(R)` through $I$ and $\perp DF'$.
- **Coordinates:** $D=(0,0,0), E=(5,0,0), F=(0,6,0), D'=(5,0,13) \implies \vec{v}_{\text{lat}} = (5,0,13)$, so $E'=(10,0,13), F'=(5,6,13)$.
- **Cutting Plane `(R)`:** $I = \frac{5}{7}D' = \left(\frac{25}{7}, 0, \frac{65}{7}\right)$, $\vec{n} = F' - D = (5, 6, 13)$, $d = \vec{n}\cdot I = \frac{125 + 845}{7} = \frac{970}{7}$.
- **Edge Cuts:**
  - $DD'$: $t_{DD'} = \frac{5}{7}$.
  - $EE'$: $\vec{n}\cdot(E + t(E'-E)) = 25 + 194t = \frac{970}{7} \implies 194t = \frac{795}{7} \implies t_{EE'} = \frac{795}{1358}$.
  - $FF'$: $\vec{n}\cdot(F + t(F'-F)) = 36 + 194t = \frac{970}{7} \implies 194t = \frac{718}{7} \implies t_{FF'} = \frac{359}{679}$.
- **Area Squared:** $\text{Area}^2 = \frac{4372875}{18818}$, matching `oracle/expected.json`.

### 3.4 `W3-A01`, `W3-A07`, `W3-A10`, `W3-A13` (`P-A` · Category A `DINH_CAT_CANH` Solid-Vertex & Primed-Vertex Reuse)
- **`W3-A01` (`S.ABC`):** Plane through base vertex $B$ (on lateral edge $SB$ at $t=1$) $\perp SC$, cutting $SA, SC$ at $M, N$ with $t_{SA} = \frac{169}{205} \in (0,1)$ and $t_{SC} = \frac{169}{254} \in (0,1)$, $\text{Area}^2 = \frac{2128622769}{10674350}$.
- **`W3-A07` (`ABC.A'B'C'`):** Plane through primed top vertex $B'$ (on lateral edge $BB'$ at $t=1$) $\perp BC'$, cutting $AA', CC'$ at $M, N$ with $t_{AA'} = \frac{96}{121} \in (0,1)$ and $t_{CC'} = \frac{60}{121} \in (0,1)$, $\text{Area}^2 = \frac{40950}{121}$.
- **`W3-A10` (`ABC.A'B'C'` oblique):** Plane through primed top vertex $A'$ (on lateral edge $AA'$ at $t=1$) $\perp AC'$, cutting $BB', CC'$ at $M, N$ with $t_{BB'} = \frac{169}{194} \in (0,1)$ and $t_{CC'} = \frac{65}{97} \in (0,1)$, $\text{Area}^2 = \frac{4360200}{9409}$.
- **`W3-A13` (`ABCD.A'B'C'D'` cuboid):** Plane through primed top vertex $A'$ (on lateral edge $AA'$ at $t=1$) $\perp AC'$, cutting $BB', CC', DD'$ at $M, N, P$ with $t_{BB'} = \frac{153}{169}, t_{CC'} = \frac{8}{13}, t_{DD'} = \frac{120}{169} \in (0,1)$, $\text{Area}^2 = \frac{14112}{13}$.

---

## 4. Complete Verification of All 54 Positive Category B Cases (`W3-B01..W3-B54`)

| Case ID | Family | Plane Relation | Question Type | Solid | Plane $(\vec{n};\, d)$ | $V$ | Cyclic Boundary Ring | `area_squared` | `area_display` | Status |
|---|---|---|---|---|---|---:|---|---|---|---|
| `W3-B01` | `triangular_pyramid` | `perpendicular_line` | `section_only` | `S.EFG` | `(13, 0, -23); -4232/11` | 3 | `SE@3/11 -> SG@3/11 -> SF@1587/7678` | `2614174641/40877672` | `(51129*sqrt(698))/168916` | `PASS` |
| `W3-B02` | `triangular_pyramid` | `perpendicular_line` | `area_only` | `S.MNP` | `(0, 13, -17); -1156/7` | 3 | `SM@3/7 -> SP@867/3206 -> SN@3/7` | `31648968/549829` | `(3978*sqrt(458))/11221a^2` | `PASS` |
| `W3-B03` | `triangular_pyramid` | `perpendicular_line` | `section_and_area` | `S.EFG` | `(9, 0, -19); -361/2` | 3 | `SE@1/2 -> SG@1/2 -> SF@361/884` | `1432809/7072` | `(1197*sqrt(442))/1768` | `PASS` |
| `W3-B04` | `triangular_pyramid` | `parallel_plane` | `section_only` | `S.PQR` | `(0, 0, 66); 2805/4` | 3 | `SP@3/8 -> SQ@3/8 -> SR@3/8` | `88209/4096` | `297/64a^2` | `PASS` |
| `W3-B05` | `triangular_pyramid` | `parallel_plane` | `area_only` | `S.DEF` | `(247, 0, 0); 6916/9` | 3 | `SE@4/9 -> DE@4/9 -> EF@5/9` | `38130625/26244` | `6175/162` | `PASS` |
| `W3-B06` | `triangular_pyramid` | `parallel_plane` | `section_and_area` | `A.BCD` | `(0, -184, 0); -5520/7` | 3 | `AD@2/7 -> DB@5/7 -> CD@2/7` | `5290000/2401` | `2300/49a^2` | `PASS` |
| `W3-B07` | `triangular_pyramid` | `parallel_two_lines` | `section_only` | `S.GHK` | `(0, 0, 117); 3861/4` | 3 | `SG@5/8 -> SH@5/8 -> SK@5/8` | `8555625/16384` | `2925/128` | `PASS` |
| `W3-B08` | `triangular_pyramid` | `parallel_two_lines` | `area_only` | `S.BCD` | `(330, 0, 105); 1617` | 4 | `SB@3/10 -> BC@7/10 -> CD@3/10 -> SD@3/10` | `2115477/400` | `(63*sqrt(533))/20a^2` | `PASS` |
| `W3-B09` | `triangular_pyramid` | `parallel_two_lines` | `section_and_area` | `S.KLM` | `(0, -210, 0); -1560` | 3 | `SM@4/7 -> MK@3/7 -> LM@4/7` | `18225/49` | `135/7` | `PASS` |
| `W3-B10` | `quadrilateral_pyramid` | `perpendicular_line` | `section_only` | `S.ABCD` | `(5, 9, -13); 0` | 4 | `V(A) -> SD@169/250 -> SC@169/275 -> SB@169/194` | `4817160208809/6468687500` | `(2194803*sqrt(11))/266750` | `PASS` |
| `W3-B11` | `quadrilateral_pyramid` | `perpendicular_line` | `area_only` | `S.MNPQ` | `(6, 0, -15); -135` | 4 | `SM@2/5 -> SQ@2/5 -> SP@10/29 -> SN@10/29` | `50808384/609725` | `(7128*sqrt(29))/4205a^2` | `PASS` |
| `W3-B12` | `quadrilateral_pyramid` | `perpendicular_line` | `section_and_area` | `S.EFGH` | `(0, 12, -17); -1445/8` | 4 | `SE@3/8 -> SH@867/3464 -> SG@867/3464 -> SF@3/8` | `1345351771449/20782780672` | `(1159893*sqrt(433))/2999824` | `PASS` |
| `W3-B13` | `quadrilateral_pyramid` | `parallel_plane` | `section_only` | `S.PQRT` | `(0, 0, 88); 6688/9` | 4 | `SP@5/9 -> SQ@5/9 -> SR@5/9 -> ST@5/9` | `4840000/6561` | `2200/81a^2` | `PASS` |
| `W3-B14` | `quadrilateral_pyramid` | `parallel_plane` | `area_only` | `S.KLMN` | `(221, 0, 0); 3978/7` | 4 | `SL@2/7 -> KL@2/7 -> MN@5/7 -> SM@2/7` | `98903025/9604` | `9945/98` | `PASS` |
| `W3-B15` | `quadrilateral_pyramid` | `parallel_plane` | `section_and_area` | `A.BCDE` | `(0, -133, 0); -5320/9` | 4 | `AD@4/9 -> AE@4/9 -> EB@5/9 -> CD@4/9` | `74736025/26244` | `8645/162a^2` | `PASS` |
| `W3-B16` | `quadrilateral_pyramid` | `parallel_two_lines` | `section_only` | `S.BCDE` | `(0, 0, 78); 10608/11` | 4 | `SB@3/11 -> SC@3/11 -> SD@3/11 -> SE@3/11` | `492804/14641` | `702/121` | `PASS` |
| `W3-B17` | `quadrilateral_pyramid` | `parallel_two_lines` | `area_only` | `S.UVWX` | `(273, 0, 0); 10920/11` | 4 | `SV@5/11 -> UV@5/11 -> WX@6/11 -> SW@5/11` | `171714816/14641` | `13104/121a^2` | `PASS` |
| `W3-B18` | `quadrilateral_pyramid` | `parallel_two_lines` | `section_and_area` | `S.GHKL` | `(0, -207, 0); -9936/7` | 4 | `SK@3/7 -> SL@3/7 -> LG@4/7 -> HK@3/7` | `17139600/2401` | `4140/49` | `PASS` |
| `W3-B19` | `right_triangular_prism` | `perpendicular_line` | `section_only` | `ABC.A'B'C'` | `(0, 0, 13); 676/9` | 3 | `AA'@4/9 -> BB'@4/9 -> CC'@4/9` | `400` | `20` | `PASS` |
| `W3-B20` | `right_triangular_prism` | `perpendicular_line` | `area_only` | `MNP.M'N'P'` | `(4, 0, 13); 507/4` | 3 | `MM'@3/4 -> NN'@443/676 -> PP'@3/4` | `36260/169` | `(14*sqrt(185))/13a^2` | `PASS` |
| `W3-B21` | `right_triangular_prism` | `perpendicular_line` | `section_and_area` | `DEF.D'E'F'` | `(0, 6, 11); 484/5` | 3 | `DD'@4/5 -> EE'@4/5 -> FF'@304/605` | `35325/121` | `(15*sqrt(157))/11` | `PASS` |
| `W3-B22` | `right_triangular_prism` | `parallel_plane` | `section_only` | `EFG.E'F'G'` | `(0, 0, 63); 224` | 3 | `EE'@2/9 -> FF'@2/9 -> GG'@2/9` | `3969/4` | `63/2a^2` | `PASS` |
| `W3-B23` | `right_triangular_prism` | `parallel_plane` | `area_only` | `PQR.P'Q'R'` | `(247, 0, 0); 2470/3` | 4 | `PQ@5/9 -> QR@4/9 -> Q'R'@4/9 -> P'Q'@5/9` | `976144/81` | `988/9` | `PASS` |
| `W3-B24` | `right_triangular_prism` | `parallel_plane` | `section_and_area` | `GHK.G'H'K'` | `(0, -136, 0); -561` | 4 | `HK@3/8 -> H'K'@3/8 -> K'G'@5/8 -> KG@5/8` | `7225` | `85a^2` | `PASS` |
| `W3-B25` | `right_triangular_prism` | `parallel_two_lines` | `section_only` | `BCD.B'C'D'` | `(0, 0, 70); 637` | 3 | `BB'@7/10 -> CC'@7/10 -> DD'@7/10` | `1225` | `35` | `PASS` |
| `W3-B26` | `right_triangular_prism` | `parallel_two_lines` | `area_only` | `KLM.K'L'M'` | `(-220, 0, 0); -540` | 4 | `KL@3/11 -> K'L'@3/11 -> L'M'@8/11 -> LM@8/11` | `25600` | `160a^2` | `PASS` |
| `W3-B27` | `right_triangular_prism` | `parallel_two_lines` | `section_and_area` | `RST.R'S'T'` | `(0, 264, 0); 1248` | 4 | `ST@4/11 -> TR@7/11 -> T'R'@7/11 -> S'T'@4/11` | `28224` | `168` | `PASS` |
| `W3-B28` | `oblique_triangular_prism` | `perpendicular_line` | `section_only` | `ABC.A'B'C'` | `(0, 0, -12); -432/7` | 3 | `AA'@3/7 -> CC'@3/7 -> BB'@3/7` | `1225/4` | `35/2` | `PASS` |
| `W3-B29` | `oblique_triangular_prism` | `perpendicular_line` | `area_only` | `MNP.M'N'P'` | `(4, 0, 11); 411/5` | 3 | `MM'@3/5 -> NN'@331/685 -> PP'@3/5` | `39204/137` | `(198*sqrt(137))/137a^2` | `PASS` |
| `W3-B30` | `oblique_triangular_prism` | `perpendicular_line` | `section_and_area` | `DEF.D'E'F'` | `(5, 6, 13); 970/7` | 3 | `DD'@5/7 -> EE'@795/1358 -> FF'@359/679` | `4372875/18818` | `(195*sqrt(230))/194` | `PASS` |
| `W3-B31` | `oblique_triangular_prism` | `parallel_plane` | `section_only` | `EFG.E'F'G'` | `(0, 0, 42); 1092/5` | 3 | `EE'@2/5 -> FF'@2/5 -> GG'@2/5` | `441` | `21a^2` | `PASS` |
| `W3-B32` | `oblique_triangular_prism` | `parallel_plane` | `area_only` | `PQR.P'Q'R'` | `(136, 0, -56); 357` | 4 | `PQ@3/8 -> QR@5/8 -> Q'R'@5/8 -> P'Q'@3/8` | `8450` | `65*sqrt(2)` | `PASS` |
| `W3-B33` | `oblique_triangular_prism` | `parallel_plane` | `section_and_area` | `GHK.G'H'K'` | `(0, -70, 0); -3850/9` | 4 | `HK@5/9 -> H'K'@5/9 -> K'G'@4/9 -> KG@4/9` | `78400/81` | `280/9a^2` | `PASS` |
| `W3-B34` | `oblique_triangular_prism` | `parallel_two_lines` | `section_only` | `BCD.B'C'D'` | `(0, 0, 66); 1408/3` | 3 | `BB'@4/9 -> CC'@4/9 -> DD'@4/9` | `1089` | `33` | `PASS` |
| `W3-B35` | `oblique_triangular_prism` | `parallel_two_lines` | `area_only` | `KLM.K'L'M'` | `(-228, 0, 84); -456` | 4 | `KL@2/7 -> K'L'@2/7 -> L'M'@5/7 -> LM@5/7` | `1476000/49` | `(60*sqrt(410))/7a^2` | `PASS` |
| `W3-B36` | `oblique_triangular_prism` | `parallel_two_lines` | `section_and_area` | `UVW.U'V'W'` | `(0, 152, 0); 6840/11` | 4 | `VW@5/11 -> WU@6/11 -> W'U'@6/11 -> V'W'@5/11` | `831744/121` | `912/11` | `PASS` |
| `W3-B37` | `cuboid` | `perpendicular_line` | `section_only` | `ABCD.A'B'C'D'` | `(0, 0, 11); 33` | 4 | `AA'@3/11 -> BB'@3/11 -> CC'@3/11 -> DD'@3/11` | `1225` | `35` | `PASS` |
| `W3-B38` | `cuboid` | `perpendicular_line` | `area_only` | `MNPQ.M'N'P'Q'` | `(4, 0, 11); 605/7` | 4 | `MM'@5/7 -> NN'@493/847 -> PP'@493/847 -> QQ'@5/7` | `54800/121` | `(20*sqrt(137))/11a^2` | `PASS` |
| `W3-B39` | `cuboid` | `perpendicular_line` | `section_and_area` | `EFGH.E'F'G'H'` | `(5, 6, 13); 169` | 4 | `V(E') -> FF'@144/169 -> GG'@108/169 -> HH'@133/169` | `207000/169` | `(30*sqrt(230))/13` | `PASS` |
| `W3-B40` | `cuboid` | `parallel_plane` | `section_only` | `PQRS.P'Q'R'S'` | `(0, 0, 54); 3672/13` | 4 | `PP'@4/13 -> QQ'@4/13 -> RR'@4/13 -> SS'@4/13` | `2916` | `54a^2` | `PASS` |
| `W3-B41` | `cuboid` | `parallel_plane` | `area_only` | `KLMN.K'L'M'N'` | `(198, 0, 0); 6930/13` | 4 | `KL@5/13 -> MN@8/13 -> M'N'@8/13 -> K'L'@5/13` | `39204` | `198` | `PASS` |
| `W3-B42` | `cuboid` | `parallel_plane` | `section_and_area` | `GHKL.G'H'K'L'` | `(0, -168, 0); -5544/13` | 4 | `HK@3/13 -> H'K'@3/13 -> L'G'@10/13 -> LG@10/13` | `28224` | `168a^2` | `PASS` |
| `W3-B43` | `cuboid` | `parallel_two_lines` | `section_only` | `BCDE.B'C'D'E'` | `(0, 0, 99); 13662/13` | 4 | `BB'@6/13 -> CC'@6/13 -> DD'@6/13 -> EE'@6/13` | `9801` | `99` | `PASS` |
| `W3-B44` | `cuboid` | `parallel_two_lines` | `area_only` | `UVWX.U'V'W'X'` | `(-253, 0, 0); -460` | 4 | `UV@2/11 -> U'V'@2/11 -> W'X'@9/11 -> WX@9/11` | `64009` | `253a^2` | `PASS` |
| `W3-B45` | `cuboid` | `parallel_two_lines` | `section_and_area` | `CDEF.C'D'E'F'` | `(0, 275, 0); 2100` | 4 | `DE@7/11 -> FC@4/11 -> F'C'@4/11 -> D'E'@7/11` | `75625` | `275` | `PASS` |
| `W3-B46` | `cube` | `perpendicular_line` | `section_only` | `ABCD.A'B'C'D'` | `(0, 0, 7); 98/11` | 4 | `AA'@2/11 -> BB'@2/11 -> CC'@2/11 -> DD'@2/11` | `2401` | `49` | `PASS` |
| `W3-B47` | `cube` | `perpendicular_line` | `area_only` | `MNPQ.M'N'P'Q'` | `(9, 9, 0); 243/11` | 4 | `MN@3/11 -> QM@8/11 -> Q'M'@8/11 -> M'N'@3/11` | `118098/121` | `(243*sqrt(2))/11a^2` | `PASS` |
| `W3-B48` | `cube` | `perpendicular_line` | `section_and_area` | `EFGH.E'F'G'H'` | `(11, 0, 0); 44` | 4 | `EF@4/11 -> GH@7/11 -> G'H'@7/11 -> E'F'@4/11` | `14641` | `121` | `PASS` |
| `W3-B49` | `cube` | `parallel_plane` | `section_only` | `PQRS.P'Q'R'S'` | `(0, 0, 169); 10985/11` | 4 | `PP'@5/11 -> QQ'@5/11 -> RR'@5/11 -> SS'@5/11` | `28561` | `169a^2` | `PASS` |
| `W3-B50` | `cube` | `parallel_plane` | `area_only` | `KLMN.K'L'M'N'` | `(196, 0, 0); 5488/13` | 4 | `KL@2/13 -> MN@11/13 -> M'N'@11/13 -> K'L'@2/13` | `38416` | `196` | `PASS` |
| `W3-B51` | `cube` | `parallel_plane` | `section_and_area` | `GHKL.G'H'K'L'` | `(0, -225, 0); -10125/13` | 4 | `HK@3/13 -> H'K'@3/13 -> L'G'@10/13 -> LG@10/13` | `50625` | `225a^2` | `PASS` |
| `W3-B52` | `cube` | `parallel_two_lines` | `section_only` | `BCDE.B'C'D'E'` | `(0, 0, 256); 16384/13` | 4 | `BB'@4/13 -> CC'@4/13 -> DD'@4/13 -> EE'@4/13` | `65536` | `256` | `PASS` |
| `W3-B53` | `cube` | `parallel_two_lines` | `area_only` | `UVWX.U'V'W'X'` | `(-324, 0, 0); -29160/13` | 4 | `UV@5/13 -> U'V'@5/13 -> W'X'@8/13 -> WX@8/13` | `104976` | `324a^2` | `PASS` |
| `W3-B54` | `cube` | `parallel_two_lines` | `section_and_area` | `CDEF.C'D'E'F'` | `(0, 441, 0); 55566/13` | 4 | `DE@6/13 -> FC@7/13 -> F'C'@7/13 -> D'E'@6/13` | `194481` | `441` | `PASS` |

---

## 5. Complete Verification of All 18 Positive Category A Cases (`W3-A01..W3-A18`)

| Case ID | Family | Plane Relation | Question Type | Solid | `through_point` | Stated Cuts | $V$ | Cyclic Boundary Ring | `area_squared` | `area_display` | Status |
|---|---|---|---|---|---|---:|---:|---|---|---|---|
| `W3-A01` | `triangular_pyramid` | `perpendicular_line` | `section_only` | `S.ABC` | `B` | 2 | 3 | `SA@169/205 -> SC@169/254 -> V(B)` | `2128622769/10674350` | `(46137*sqrt(254))/52070` | `PASS` |
| `W3-A02` | `triangular_pyramid` | `parallel_plane` | `area_only` | `S.MNP` | `K` | 2 | 3 | `SM@3/11 -> SN@3/11 -> SP@3/11` | `142884/14641` | `378/121a^2` | `PASS` |
| `W3-A03` | `triangular_pyramid` | `perpendicular_line` | `section_and_area` | `S.EFG` | `M` | 2 | 3 | `SE@1/2 -> SG@1/2 -> SF@128/281` | `12100/281` | `(110*sqrt(281))/281` | `PASS` |
| `W3-A04` | `quadrilateral_pyramid` | `perpendicular_line` | `section_only` | `S.ABCD` | `A` | 3 | 4 | `V(A) -> SD@225/289 -> SC@225/314 -> SB@9/10` | `10589490450/13112797` | `(72765*sqrt(314))/45373a^2` | `PASS` |
| `W3-A05` | `quadrilateral_pyramid` | `parallel_plane` | `area_only` | `S.MNPQ` | `K` | 3 | 4 | `SM@4/11 -> SN@4/11 -> SP@4/11 -> SQ@4/11` | `1016064/14641` | `1008/121` | `PASS` |
| `W3-A06` | `quadrilateral_pyramid` | `perpendicular_line` | `section_and_area` | `S.EFGH` | `I` | 3 | 4 | `SE@3/7 -> SH@675/1918 -> SG@135/434 -> SF@75/203` | `5868506953125/191816026808` | `(1083375*sqrt(310))/3448564a^2` | `PASS` |
| `W3-A07` | `right_triangular_prism` | `perpendicular_line` | `section_only` | `ABC.A'B'C'` | `B'` | 2 | 3 | `V(B') -> CC'@60/121 -> AA'@96/121` | `40950/121` | `(15*sqrt(182))/11` | `PASS` |
| `W3-A08` | `right_triangular_prism` | `perpendicular_line` | `area_only` | `MNP.M'N'P'` | `N` | 2 | 3 | `V(N) -> MM'@16/121 -> PP'@65/121` | `36456/121` | `(14*sqrt(186))/11a^2` | `PASS` |
| `W3-A09` | `right_triangular_prism` | `parallel_plane` | `section_and_area` | `DEF.D'E'F'` | `K` | 2 | 3 | `DD'@5/14 -> EE'@5/14 -> FF'@5/14` | `1225` | `35` | `PASS` |
| `W3-A10` | `oblique_triangular_prism` | `perpendicular_line` | `section_only` | `ABC.A'B'C'` | `A'` | 2 | 3 | `V(A') -> BB'@169/194 -> CC'@65/97` | `4360200/9409` | `(130*sqrt(258))/97a^2` | `PASS` |
| `W3-A11` | `oblique_triangular_prism` | `parallel_plane` | `area_only` | `MNP.M'N'P'` | `K` | 2 | 3 | `MM'@3/14 -> NN'@3/14 -> PP'@3/14` | `1521` | `39` | `PASS` |
| `W3-A12` | `oblique_triangular_prism` | `perpendicular_line` | `section_and_area` | `DEF.D'E'F'` | `I` | 2 | 3 | `DD'@6/11 -> EE'@1270/2651 -> FF'@6/11` | `44100/241` | `(210*sqrt(241))/241a^2` | `PASS` |
| `W3-A13` | `cuboid` | `perpendicular_line` | `section_only` | `ABCD.A'B'C'D'` | `A'` | 3 | 4 | `V(A') -> BB'@153/169 -> CC'@8/13 -> DD'@120/169` | `14112/13` | `(84*sqrt(26))/13` | `PASS` |
| `W3-A14` | `cuboid` | `perpendicular_line` | `area_only` | `MNPQ.M'N'P'Q'` | `M` | 3 | 4 | `V(M) -> QQ'@64/289 -> PP'@89/289 -> NN'@25/289` | `604800/289` | `(120*sqrt(42))/17a^2` | `PASS` |
| `W3-A15` | `cuboid` | `parallel_two_lines` | `section_and_area` | `EFGH.E'F'G'H'` | `K` | 3 | 4 | `EE'@4/15 -> FF'@4/15 -> GG'@4/15 -> HH'@4/15` | `3969` | `63` | `PASS` |
| `W3-A16` | `cube` | `parallel_plane` | `section_only` | `ABCD.A'B'C'D'` | `M` | 3 | 4 | `AA'@3/16 -> BB'@3/16 -> CC'@3/16 -> DD'@3/16` | `83521` | `289` | `PASS` |
| `W3-A17` | `cube` | `perpendicular_line` | `area_only` | `MNPQ.M'N'P'Q'` | `K` | 3 | 4 | `MM'@5/16 -> NN'@5/16 -> PP'@5/16 -> QQ'@5/16` | `130321` | `361a^2` | `PASS` |
| `W3-A18` | `cube` | `parallel_two_lines` | `section_and_area` | `EFGH.E'F'G'H'` | `I` | 3 | 4 | `EE'@2/17 -> FF'@2/17 -> GG'@2/17 -> HH'@2/17` | `279841` | `529` | `PASS` |

---

## 6. Complete Verification of All 72 Negative Cases (`W3-N01..W3-N72`)

All `18` negative classes defined in `preregistration.md §3.2` contain exactly `4` cases each (`72` total). Every case has `expected_disposition == "REFUSE"`, `expected_category is None`, non-empty `acceptable_categories` drawn strictly from `refusal-taxonomy.json` (never including `INTERNAL_OR_VALIDATION`), valid `contract_representability`, and a verified mathematical, semantic, or scope defect:

| Case ID | Negative Class | Representability / Gap | Acceptable Refusal Categories | Verified Defect Summary |
|---|---|---|---|---|
| `W3-N01` | `contradictory_source_facts` | `representable_with_explicit_gap` (`contradictory`) | `CONTRADICTION`, `INPUT_INVALID`, `SOURCE_GROUNDING` | Non-homogeneous length units (`AB=7, SA=15` numeric vs `AC=11a` symbolic) |
| `W3-N02` | `contradictory_source_facts` | `representable_with_explicit_gap` (`contradictory`) | `CONTRADICTION`, `GEOMETRY_DEGENERATE` | Contradictory duplicate segment lengths on `MN` (`MN=8` and `MN=13`) |
| `W3-N03` | `contradictory_source_facts` | `representable_with_explicit_gap` (`contradictory`) | `CONTRADICTION`, `GEOMETRY_DEGENERATE` | Right triangle hypotenuse contradiction (`EF=9, EG=12` at right angle `E`, but `FG=6`) |
| `W3-N04` | `contradictory_source_facts` | `representable_with_explicit_gap` (`contradictory`) | `CONTRADICTION`, `GEOMETRY_DEGENERATE`, `SOURCE_GROUNDING` | Regular quadrilateral pyramid `S.ABCD` contradicted by non-square rectangle base (`AB=7, AD=13`) |
| `W3-N05` | `wrong_solid_kind` | `representable_with_explicit_gap` (`contradictory`) | `SOURCE_GROUNDING`, `INPUT_INVALID`, `CONTRADICTION` | Source prose states triangular pyramid `S.ABC`, payload declares prism `ABC.A'B'C'` |
| `W3-N06` | `wrong_solid_kind` | `representable_with_explicit_gap` (`contradictory`) | `SOURCE_GROUNDING`, `INPUT_INVALID`, `CONTRADICTION` | Source prose states right prism `MNP.M'N'P'`, payload declares pyramid `M'.MNP` |
| `W3-N07` | `wrong_solid_kind` | `representable_with_explicit_gap` (`contradictory`) | `SOURCE_GROUNDING`, `INPUT_INVALID`, `CONTRADICTION` | Source prose states tetrahedron `S.DEF`, payload declares 4-base pyramid `S.DEFG` |
| `W3-N08` | `wrong_solid_kind` | `representable_with_explicit_gap` (`contradictory`) | `SOURCE_GROUNDING`, `INPUT_INVALID`, `CONTRADICTION` | Source prose states cuboid `ABCD.A'B'C'D'`, payload declares pyramid `A'.ABCD` |
| `W3-N09` | `wrong_solid_notation` | `representable_with_explicit_gap` (`contradictory`) | `INPUT_INVALID`, `SOURCE_GROUNDING` | Invalid solid notation `S.ABA` with duplicate base vertex `A` |
| `W3-N10` | `wrong_solid_notation` | `representable_with_explicit_gap` (`contradictory`) | `INPUT_INVALID`, `SOURCE_GROUNDING` | Malformed prism notation `PQR.PQ'R'` (unprimed `P` repeated in top chain) vs pyramid quote |
| `W3-N11` | `wrong_solid_notation` | `representable_with_explicit_gap` (`contradictory`) | `INPUT_INVALID`, `SOURCE_GROUNDING` | Degenerate 2-vertex base pyramid notation `S.GH` vs `S.GHK` in source |
| `W3-N12` | `wrong_solid_notation` | `representable_with_explicit_gap` (`contradictory`) | `SOURCE_GROUNDING`, `INPUT_INVALID` | Solid notation `S.XYZ` does not match source solid `S.KLM` |
| `W3-N13` | `mixed_solid_operands` | `intentionally_outside_supported_v2_capability` (`unsupported_topology`) | `UNSUPPORTED_CAPABILITY`, `INPUT_INVALID`, `CONTRADICTION` | Unsupported non-identity `vertex_bindings: {"A": "X", "B": "Y"}` |
| `W3-N14` | `mixed_solid_operands` | `intentionally_outside_supported_v2_capability` (`unsupported_topology`) | `UNSUPPORTED_CAPABILITY`, `SOURCE_GROUNDING`, `INPUT_INVALID`, `CONTRADICTION` | Multiple solids declared (`s1: S.MNP` and ungrounded `s2: T.EFG`) |
| `W3-N15` | `mixed_solid_operands` | `representable_with_explicit_gap` (`contradictory`) | `INPUT_INVALID`, `UNSUPPORTED_CAPABILITY` | `derived_sections[0].target_solid_id` references undeclared solid `s2` |
| `W3-N16` | `mixed_solid_operands` | `representable_with_explicit_gap` (`contradictory`) | `INPUT_INVALID`, `UNSUPPORTED_CAPABILITY` | Unsupported non-identity `vertex_bindings: {"Z": "P"}` |
| `W3-N17` | `missing_mandatory_premise` | `representable_with_explicit_gap` (`missing_required_information`) | `UNDERDETERMINED`, `CONTRADICTION` | Missing altitude length `SA` required for perpendicular section area in `S.ABC` |
| `W3-N18` | `missing_mandatory_premise` | `representable_with_explicit_gap` (`missing_required_information`) | `UNDERDETERMINED`, `CONTRADICTION` | Missing perpendicularity premise `SM ⊥ (MNP)` (solid metric underdetermined) |
| `W3-N19` | `missing_mandatory_premise` | `representable_with_explicit_gap` (`missing_required_information`) | `UNDERDETERMINED`, `CONTRADICTION` | Missing second base leg `DF` in right prism `DEF.D'E'F'` |
| `W3-N20` | `missing_mandatory_premise` | `representable_with_explicit_gap` (`missing_required_information`) | `UNDERDETERMINED`, `CONTRADICTION` | Missing lateral edge length `AA'` in cuboid `ABCD.A'B'C'D'` for vertical section area |
| `W3-N21` | `unproven_parallel_or_perpendicular_relation` | `representable_with_explicit_gap` (`missing_required_information`) | `SOURCE_GROUNDING`, `UNDERDETERMINED` | Premise claims `SA ⊥ (ABC)` from quote `'SA nghiêng đều với mặt phẳng (ABC)'` (`PREDICATE_NOT_IN_QUOTE`) |
| `W3-N22` | `unproven_parallel_or_perpendicular_relation` | `representable_with_explicit_gap` (`missing_required_information`) | `SOURCE_GROUNDING`, `UNDERDETERMINED` | Premise claims `right_angle` at `M` from quote `'tam giác nhọn tại M'` (`PREDICATE_NOT_IN_QUOTE`) |
| `W3-N23` | `unproven_parallel_or_perpendicular_relation` | `representable_with_explicit_gap` (`missing_required_information`) | `SOURCE_GROUNDING`, `UNDERDETERMINED` | Section claims `perpendicular_line` `SF` from quote `'cắt đường thẳng SF'` (`PREDICATE_NOT_IN_QUOTE`) |
| `W3-N24` | `unproven_parallel_or_perpendicular_relation` | `representable_with_explicit_gap` (`contradictory`) | `SOURCE_GROUNDING`, `CONTRADICTION` | Section claims `parallel_plane` `(PQR)` from quote `'vuông góc với đường thẳng SQ'` (`PREDICATE_NOT_IN_QUOTE`) |
| `W3-N25` | `ambiguous_source_labels` | `representable_with_explicit_gap` (`ambiguous`) | `AMBIGUOUS`, `CONTRADICTION`, `INPUT_INVALID` | Point label `M` defined twice on different edges (`SA` with ratio `2/5` and midpoint of `SB`) |
| `W3-N26` | `ambiguous_source_labels` | `representable_with_explicit_gap` (`ambiguous`) | `AMBIGUOUS`, `CONTRADICTION`, `INPUT_INVALID`, `GEOMETRY_DEGENERATE` | Point label `E` on `SD` collides with existing base vertex `E` of `S.DEF` |
| `W3-N27` | `ambiguous_source_labels` | `representable_with_explicit_gap` (`ambiguous`) | `SOURCE_GROUNDING`, `AMBIGUOUS`, `CONTRADICTION` | Ambiguous segment length in source (`'biết GH = 7 hoặc 9'`) |
| `W3-N28` | `ambiguous_source_labels` | `representable_with_explicit_gap` (`ambiguous`) | `INPUT_INVALID`, `AMBIGUOUS`, `CONTRADICTION` | Colliding stated intersection point label `N` assigned to both `SL` and `SM` (`'lần lượt tại N, N'`) |
| `W3-N29` | `wrong_ratio` | `representable_with_explicit_gap` (`contradictory`) | `SOURCE_GROUNDING`, `INPUT_INVALID`, `CONTRADICTION` | Payload ratio `3/5` contradicts source quote `'SM = 2/5 SA'` (`UNGROUNDED_VALUE`) |
| `W3-N30` | `wrong_ratio` | `representable_with_explicit_gap` (`contradictory`) | `SOURCE_GROUNDING`, `INPUT_INVALID`, `CONTRADICTION` | Payload ratio `5/8` contradicts source quote `'SK = 3/8 SM'` (`UNGROUNDED_VALUE`) |
| `W3-N31` | `wrong_ratio` | `representable_with_explicit_gap` (`contradictory`) | `INPUT_INVALID`, `SOURCE_GROUNDING`, `GEOMETRY_DEGENERATE` | Cut ratio `7/5` lies outside open interval `(0, 1)` (`INVALID_RATIO`) |
| `W3-N32` | `wrong_ratio` | `representable_with_explicit_gap` (`contradictory`) | `INPUT_INVALID`, `SOURCE_GROUNDING`, `GEOMETRY_DEGENERATE` | Cut ratio `0` lies outside open interval `(0, 1)` (`INVALID_RATIO`) |
| `W3-N33` | `wrong_edge` | `representable_with_explicit_gap` (`contradictory`) | `SOURCE_GROUNDING`, `INPUT_INVALID`, `CONTRADICTION` | `divide_segment` places `M` on `SB` while quote states `SA` (`OBJECT_NOT_IN_QUOTE`) |
| `W3-N34` | `wrong_edge` | `representable_with_explicit_gap` (`contradictory`) | `SOURCE_GROUNDING`, `INPUT_INVALID`, `CONTRADICTION` | `divide_segment` places `K` on `NP` while quote states `SM` (`OBJECT_NOT_IN_QUOTE`) |
| `W3-N35` | `wrong_edge` | `intentionally_outside_supported_v2_capability` (`unsupported_relation`) | `UNSUPPORTED_CAPABILITY`, `GEOMETRY_DEGENERATE`, `CONTRADICTION`, `SOURCE_GROUNDING` | Category A `stated_intersections` includes base edge `FG` instead of lateral edge |
| `W3-N36` | `wrong_edge` | `intentionally_outside_supported_v2_capability` (`unsupported_relation`) | `UNSUPPORTED_CAPABILITY`, `GEOMETRY_DEGENERATE`, `CONTRADICTION`, `SOURCE_GROUNDING` | Category A `stated_intersections` includes base edge `DE` on prism `DEF.D'E'F'` |
| `W3-N37` | `impossible_vertex` | `representable_with_explicit_gap` (`contradictory`) | `INPUT_INVALID`, `SOURCE_GROUNDING`, `UNDERDETERMINED` | Premise references non-existent vertex `D` in `S.ABC` (`segment: ["S", "D"]`) |
| `W3-N38` | `impossible_vertex` | `representable_with_explicit_gap` (`contradictory`) | `INPUT_INVALID`, `SOURCE_GROUNDING`, `UNDERDETERMINED` | Section references non-existent vertex `D'` in `S.MNP` (`perpendicular_line: ["S", "D'"]`) |
| `W3-N39` | `impossible_vertex` | `representable_with_explicit_gap` (`contradictory`) | `INPUT_INVALID`, `SOURCE_GROUNDING`, `UNDERDETERMINED` | Section `through_point` references undeclared point `Z` |
| `W3-N40` | `impossible_vertex` | `representable_with_explicit_gap` (`contradictory`) | `INPUT_INVALID`, `SOURCE_GROUNDING`, `UNDERDETERMINED` | Section `parallel_plane` references undeclared vertex `W` (`["P", "Q", "W"]`) |
| `W3-N41` | `invalid_section_declaration` | `representable_with_explicit_gap` (`missing_required_information`) | `INPUT_INVALID`, `UNDERDETERMINED` | Malformed `through_point_perpendicular_line` with `perpendicular_line: null` |
| `W3-N42` | `invalid_section_declaration` | `representable_with_explicit_gap` (`missing_required_information`) | `INPUT_INVALID`, `UNDERDETERMINED` | Malformed `parallel_plane: ["M", "N"]` with only 2 points instead of ≥ 3 |
| `W3-N43` | `invalid_section_declaration` | `representable_with_explicit_gap` (`missing_required_information`) | `INPUT_INVALID`, `UNDERDETERMINED` | Malformed `derived_sections` with `through_point: null` |
| `W3-N44` | `invalid_section_declaration` | `representable_with_explicit_gap` (`contradictory`) | `INPUT_INVALID`, `CONTRADICTION` | Duplicate edge `["S", "H"]` in `stated_intersections` |
| `W3-N45` | `unsupported_geometry_capability` | `intentionally_outside_supported_v2_capability` (`unsupported_topology`) | `UNSUPPORTED_CAPABILITY` | Unsupported curved solid `cylinder` and `axial_section` |
| `W3-N46` | `unsupported_geometry_capability` | `intentionally_outside_supported_v2_capability` (`unsupported_topology`) | `UNSUPPORTED_CAPABILITY` | Unsupported curved solid `cone` and `axial_section` |
| `W3-N47` | `unsupported_geometry_capability` | `intentionally_outside_supported_v2_capability` (`unsupported_topology`) | `UNSUPPORTED_CAPABILITY` | Unsupported regular pentagon base (`n = 5` in `regular_polygon`) |
| `W3-N48` | `unsupported_geometry_capability` | `intentionally_outside_supported_v2_capability` (`unsupported_relation`) | `UNSUPPORTED_CAPABILITY` | Unsupported `plane_kind: "plane_equation"` |
| `W3-N49` | `conflicting_section_area_requests` | `representable_with_explicit_gap` (`contradictory`) | `SOURCE_GROUNDING`, `INPUT_INVALID` | `math_goals` asks for area not requested in `problem_text` (`NOT_ASKED_IN_SOURCE`) |
| `W3-N50` | `conflicting_section_area_requests` | `representable_with_explicit_gap` (`contradictory`) | `INPUT_INVALID`, `SOURCE_GROUNDING` | `simulation_goals` targets unknown section ID `sec_unknown` (`UNKNOWN_SECTION_ID`) |
| `W3-N51` | `conflicting_section_area_requests` | `representable_with_explicit_gap` (`contradictory`) | `INPUT_INVALID`, `SOURCE_GROUNDING` | Malformed `math_goals` with empty `target: {}` and unasked area goal |
| `W3-N52` | `conflicting_section_area_requests` | `representable_with_explicit_gap` (`contradictory`) | `SOURCE_GROUNDING`, `INPUT_INVALID` | Mandatory length `SP = 19` embedded inside conditional question clause `'Biết rằng nếu SP = 19 thì...'` |
| `W3-N53` | `incorrect_stated_intersections` | `representable_with_explicit_gap` (`contradictory`) | `GEOMETRY_DEGENERATE`, `CONTRADICTION`, `UNSUPPORTED_CAPABILITY` | Plane through `M ∈ AC` parallel to `(ABB')` cuts `AB` and `A'C'`, not lateral edge `BB'` (`LINE_PARALLEL_TO_PLANE`) |
| `W3-N54` | `incorrect_stated_intersections` | `representable_with_explicit_gap` (`contradictory`) | `GEOMETRY_DEGENERATE`, `CONTRADICTION`, `UNSUPPORTED_CAPABILITY` | Category A on 4-pyramid `S.ABCD` lists only `SB, SC`, omitting cut lateral edge `SD` (`SECTION_NOT_CLOSED_ON_LATERAL_EDGES`) |
| `W3-N55` | `incorrect_stated_intersections` | `representable_with_explicit_gap` (`contradictory`) | `GEOMETRY_DEGENERATE`, `CONTRADICTION`, `UNSUPPORTED_CAPABILITY` | Category A on cuboid `ABCD.A'B'C'D'` lists only `BB', CC'`, omitting `DD'` |
| `W3-N56` | `incorrect_stated_intersections` | `representable_with_explicit_gap` (`contradictory`) | `GEOMETRY_DEGENERATE`, `CONTRADICTION` | Stated intersection on `NN'` lies outside segment (`t < 0` on `NN'` and `PP'`) |
| `W3-N57` | `category_a_b_semantic_contradictions` | `representable_with_explicit_gap` (`contradictory`) | `AMBIGUOUS`, `CONTRADICTION`, `INPUT_INVALID`, `GEOMETRY_DEGENERATE` | Category A re-declares cut point `K` on `SA` which already contains `through_point` `M` |
| `W3-N58` | `category_a_b_semantic_contradictions` | `representable_with_explicit_gap` (`contradictory`) | `AMBIGUOUS`, `CONTRADICTION`, `INPUT_INVALID`, `GEOMETRY_DEGENERATE` | Stated intersection `H` on `SN` (midpoint `t=1/2`) contradicts plane parallel to base through `K` (`t=2/5`) |
| `W3-N59` | `category_a_b_semantic_contradictions` | `representable_with_explicit_gap` (`contradictory`) | `INPUT_INVALID`, `CONTRADICTION` | Malformed/contradictory `declared_boundary` with only 2 edges `[[S,E],[S,F]]` |
| `W3-N60` | `category_a_b_semantic_contradictions` | `representable_with_explicit_gap` (`contradictory`) | `AMBIGUOUS`, `CONTRADICTION`, `INPUT_INVALID`, `GEOMETRY_DEGENERATE` | Category A re-declares cut point `M` on lateral edge `AA'` which already contains `through_point` `A'` |
| `W3-N61` | `primed_label_identity_ambiguity` | `representable_with_explicit_gap` (`contradictory`) | `SOURCE_GROUNDING`, `INPUT_INVALID`, `CONTRADICTION` | Quote states `đỉnh A'` (`through_point`), payload uses unprimed `A` (`OBJECT_NOT_IN_QUOTE`) |
| `W3-N62` | `primed_label_identity_ambiguity` | `representable_with_explicit_gap` (`contradictory`) | `SOURCE_GROUNDING`, `INPUT_INVALID`, `CONTRADICTION` | Quote states `đường thẳng MN'`, payload swaps prime to `M'N` (`OBJECT_NOT_IN_QUOTE`) |
| `W3-N63` | `primed_label_identity_ambiguity` | `representable_with_explicit_gap` (`contradictory`) | `SOURCE_GROUNDING`, `INPUT_INVALID`, `CONTRADICTION` | Quote states `cạnh A'B'`, payload uses unprimed `AB` (`OBJECT_NOT_IN_QUOTE`) |
| `W3-N64` | `primed_label_identity_ambiguity` | `representable_with_explicit_gap` (`contradictory`) | `SOURCE_GROUNDING`, `CONTRADICTION`, `GEOMETRY_DEGENERATE` | Quote states projection of `D'`, payload uses unprimed `D` (`OBJECT_NOT_IN_QUOTE` / zero projection vector) |
| `W3-N65` | `source_provenance_mismatch` | `representable_with_explicit_gap` (`contradictory`) | `SOURCE_GROUNDING` | Fabricated premise quote `'chiều cao SA bằng 17 đơn vị'` not in `problem_text` (`QUOTE_NOT_IN_SOURCE`) |
| `W3-N66` | `source_provenance_mismatch` | `representable_with_explicit_gap` (`contradictory`) | `SOURCE_GROUNDING` | Fabricated section quote `'Mặt phẳng (Q) đi qua K và song song với đáy (MNP)'` not in `problem_text` (`QUOTE_NOT_IN_SOURCE`) |
| `W3-N67` | `source_provenance_mismatch` | `representable_with_explicit_gap` (`contradictory`) | `SOURCE_GROUNDING`, `UNDERDETERMINED` | Premise extracted from negated clause `'cạnh bên SE không vuông góc với mặt phẳng (EFG)'` (`NEGATED_CLAUSE`) |
| `W3-N68` | `source_provenance_mismatch` | `representable_with_explicit_gap` (`contradictory`) | `SOURCE_GROUNDING`, `UNDERDETERMINED` | Premise extracted from conditional clause `'giả sử nếu đáy PQR là tam giác vuông tại P'` (`CONDITIONAL_CLAUSE`) |
| `W3-N69` | `geometry_degeneration` | `representable_with_explicit_gap` (`contradictory`) | `GEOMETRY_DEGENERATE`, `CONTRADICTION` | Plane through base vertex `A` parallel to `(ABC)` coincides with base face (`DERIVED_PLANE_IS_REFERENCE` / `SECTION_PLANE_IS_FACE`) |
| `W3-N70` | `geometry_degeneration` | `representable_with_explicit_gap` (`contradictory`) | `GEOMETRY_DEGENERATE`, `CONTRADICTION` | Plane through apex `S` parallel to `(MNP)` touches only apex `S` (`PLANE_TOUCHES_VERTEX`) |
| `W3-N71` | `geometry_degeneration` | `representable_with_explicit_gap` (`contradictory`) | `GEOMETRY_DEGENERATE`, `CONTRADICTION`, `UNDERDETERMINED` | `through_point_parallel_two_lines` uses parallel direction lines `AB` and `CD` (`DEGENERATE_PLANE_DIRECTIONS`) |
| `W3-N72` | `geometry_degeneration` | `representable_with_explicit_gap` (`contradictory`) | `GEOMETRY_DEGENERATE`, `CONTRADICTION` | Plane through `D` perpendicular to `DF` contains edge `DE` and touches only face boundary (`SECTION_PLANE_IS_FACE` / `PLANE_TOUCHES_EDGE`) |

---

## 7. Final Conclusion

All `72` positive cases (`W3-B01..W3-B54` and `W3-A01..W3-A18`) and all `72` negative cases (`W3-N01..W3-N72`) in `inputs/holdout-wave3.json`, `oracle/geometry.json`, and `oracle/expected.json` have been independently verified with `0` discrepancies before any product execution (`ORACLE_VERIFIED_BEFORE_EXECUTION`).

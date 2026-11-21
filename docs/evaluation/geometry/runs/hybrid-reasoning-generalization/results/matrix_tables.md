## Matrix `ab1_after` (HEAD `dd551ffec79d`, measured: worktree backend/app (git_head + working tree), 72 cases)

| outcome | count |
|---|---:|
| `CORRECT_CLARIFICATION` | 1 |
| `CORRECT_REFUSAL` | 9 |
| `EXACT_SERVED` | 56 |
| `NO_PLAN_DESPITE_PRIMITIVES` | 5 |
| `SEARCH_BUDGET_EXCEEDED` | 1 |

| case | family | outcome | status / code | answers | classification | states | cands | pruned | depth | reuse |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| PP1 | point-plane distance | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PP2 | point-plane distance | `EXACT_SERVED` | SERVED  | {"q1": "√2/2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PP3 | point-plane distance (described centroid) | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | SOURCE_EXPLICIT_SEQUENCE | 7 | 3 | 0 | 2 | 0 |
| PP4 | point-plane distance (described intersection) | `EXACT_SERVED` | SERVED  | {"q1": "√2/2"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| PP5 | point-plane distance (nested described) | `EXACT_SERVED` | SERVED  | {"q1": "1"} | DISCOVERED_FUNCTION_COMPOSITION | 8 | 4 | 0 | 3 | 0 |
| PP6 | point-plane distance (point on plane) | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PL1 | point-line distance | `EXACT_SERVED` | SERVED  | {"q1": "2√6/3"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PL2 | point-line distance | `EXACT_SERVED` | SERVED  | {"q1": "√6"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PL3 | point-line distance (described point) | `EXACT_SERVED` | SERVED  | {"q1": "1"} | REGISTERED_DECOMPOSITION | 6 | 3 | 0 | 2 | 1 |
| PL4 | point-line distance (described intersection) | `EXACT_SERVED` | SERVED  | {"q1": "√6/3"} | REGISTERED_DECOMPOSITION | 6 | 3 | 0 | 2 | 1 |
| PL5 | point-line distance (line through described point) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PL6 | point-line distance (point on line, degenerate) | `EXACT_SERVED` | SERVED  | {"q1": "0"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PL7 | point-line distance (intersection line result) | `EXACT_SERVED` | SERVED  | {"q1": "3"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PR1 | prism point-plane | `EXACT_SERVED` | SERVED  | {"q1": "12√61/61"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR2 | prism point-line | `EXACT_SERVED` | SERVED  | {"q1": "2√61/5"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PR3 | prism angle line-plane | `EXACT_SERVED` | SERVED  | {"q1": "9/13"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR4 | prism angle plane-plane | `EXACT_SERVED` | SERVED  | {"q1": "36/61"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR5 | prism skew lines distance | `EXACT_SERVED` | SERVED  | {"q1": "12/5"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR6 | prism point-plane (described point) | `EXACT_SERVED` | SERVED  | {"q1": "12√61/61"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| PR7 | prism circumcenter of right base | `EXACT_SERVED` | SERVED  | {"q1": "√41/2"} | REGISTERED_DECOMPOSITION | 24 | 20 | 9 | 4 | 0 |
| PR8 | prism orthocenter of right base (coincides with A) | `EXACT_SERVED` | SERVED  | {"q1": "2"} | REGISTERED_DECOMPOSITION | 24 | 17 | 6 | 4 | 0 |
| AN1 | angle line-plane | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN2 | angle plane-plane | `EXACT_SERVED` | SERVED  | {"q1": "1/2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN3 | angle line-line | `EXACT_SERVED` | SERVED  | {"q1": "1/2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN4 | angle line-plane (described point) | `EXACT_SERVED` | SERVED  | {"q1": "5/9"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 2 | 0 | 2 | 0 |
| AN5 | angle line-plane (lateral face) | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN6 | angle line-line (described centroid) | `EXACT_SERVED` | SERVED  | {"q1": "1/6"} | SOURCE_EXPLICIT_SEQUENCE | 7 | 2 | 0 | 2 | 0 |
| AN7 | angle line-plane (described point, slanted plane) | `EXACT_SERVED` | SERVED  | {"q1": "3/5"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 2 | 0 | 2 | 0 |
| PE1 | perpendicular (angle 90°) | `EXACT_SERVED` | SERVED  | {"q1": "0"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PE2 | perpendicular (tetrahedron pairwise ⊥) | `EXACT_SERVED` | SERVED  | {"q1": "6/7"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PE3 | perpendicular (tetrahedron angle) | `EXACT_SERVED` | SERVED  | {"q1": "36/49"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PE4 | perpendicular (tetrahedron point-line) | `EXACT_SERVED` | SERVED  | {"q1": "6√13/13"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PE5 | perpendicular (tetrahedron, apex A over right base OBC) | `EXACT_SERVED` | SERVED  | {"q1": "6/7"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PE6 | perpendicular (tetrahedron volume) | `EXACT_SERVED` | SERVED  | {"q1": "1"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PY1 | pyramid apex fixed by three lateral edges | `EXACT_SERVED` | SERVED  | {"q1": "12/5"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PY2 | pyramid apex fixed by three lateral edges (height) | `EXACT_SERVED` | SERVED  | {"q1": "6"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PA1 | parallel line-plane distance | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PA2 | parallel skew lines (AB ∥ (SCD)) | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PA3 | parallel line-plane (line through described point) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| SE1 | section ∥ base | `EXACT_SERVED` | SERVED  | {"q1": "1"} | REGISTERED_DECOMPOSITION | 0 | 0 | 0 | 0 | 0 |
| SE2 | section ⊥ line through vertex | `EXACT_SERVED` | SERVED  | {"q1": "2√3/3"} | REGISTERED_DECOMPOSITION | 0 | 0 | 0 | 0 | 0 |
| SE3 | section by three midpoints (constrained) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED SOURCE_OBJECT_MISMATCH | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| SE4 | section constrained ⊥ plane (A3 regression) | `EXACT_SERVED` | SERVED  | {"q1": "7√2/8"} | REGISTERED_DECOMPOSITION | 0 | 0 | 3 | 0 | 0 |
| RE1 | orthocenter (B1 regression) | `EXACT_SERVED` | SERVED  | {"q1": "2"} | REGISTERED_DECOMPOSITION | 24 | 17 | 6 | 4 | 0 |
| RE2 | circumcenter (B2 regression) | `EXACT_SERVED` | SERVED  | {"q1": "√3"} | REGISTERED_DECOMPOSITION | 24 | 20 | 9 | 4 | 0 |
| RE3 | orthocenter of tetrahedron face ABC | `EXACT_SERVED` | SERVED  | {"q1": "6/7"} | REGISTERED_DECOMPOSITION | 24 | 17 | 6 | 4 | 0 |
| RE4 | projection onto line (described) to plane | `EXACT_SERVED` | SERVED  | {"q1": "√2/2"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| RE5 | orthocenter to plane | `EXACT_SERVED` | SERVED  | {"q1": "2"} | REGISTERED_DECOMPOSITION | 25 | 18 | 6 | 4 | 0 |
| RE6 | circumcenter to line (definition + foot) | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | REGISTERED_DECOMPOSITION | 25 | 21 | 9 | 4 | 7 |
| RE7 | circumcenter of an equilateral face | `EXACT_SERVED` | SERVED  | {"q1": "2√3/3"} | REGISTERED_DECOMPOSITION | 24 | 20 | 9 | 4 | 0 |
| RE8 | orthocenter of an equilateral face to base | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | REGISTERED_DECOMPOSITION | 25 | 18 | 6 | 4 | 0 |
| RE9 | described line–plane intersection | `EXACT_SERVED` | SERVED  | {"q1": "1"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| MG7 | goal-only foot reused by a described-point goal | `EXACT_SERVED` | SERVED  | {"q1": "2√6/3", "q2": "2√3/3"} | REGISTERED_DECOMPOSITION | 10 | 5 | 0 | 2 | 1 |
| MG8 | orthocenter and circumcenter of one triangle | `EXACT_SERVED` | SERVED  | {"q1": "2√3/3", "q2": "2"} | REGISTERED_DECOMPOSITION | 48 | 39 | 15 | 4 | 2 |
| RE10 | projection of a defined point (nested definition) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| MG9 | three property-defined points in one problem | `SEARCH_BUDGET_EXCEEDED` | REFUSED PLAN_TOO_LARGE | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| MG1 | multi-goal shared described point | `EXACT_SERVED` | SERVED  | {"q2": "1", "q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 8 | 4 | 0 | 2 | 1 |
| MG2 | multi-goal three quantities | `EXACT_SERVED` | SERVED  | {"q2": "2/3", "q3": "√2", "q1": "2√6/3"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| MG3 | reuse of a source-named foot | `EXACT_SERVED` | SERVED  | {"q2": "1", "q1": "√2"} | REGISTERED_DECOMPOSITION | 5 | 3 | 0 | 2 | 1 |
| MG4 | multi-goal two described points sharing an inner point | `EXACT_SERVED` | SERVED  | {"q1": "1", "q2": "√6"} | DISCOVERED_FUNCTION_COMPOSITION | 10 | 5 | 0 | 2 | 1 |
| MG5 | distance between two described points | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| MG6 | triangle area with a described vertex | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 2 | 0 | 2 | 0 |
| N1 | missing dimension | `CORRECT_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N2 | contradictory dimensions | `CORRECT_REFUSAL` | REFUSED INCONSISTENT_FACTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N3 | quote not in source | `CORRECT_REFUSAL` | REFUSED QUOTE_NOT_IN_SOURCE | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N4 | ambiguous wording (clarification) | `CORRECT_CLARIFICATION` | REFUSED AMBIGUOUS_FACT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N5 | described centroid of a collinear triple | `CORRECT_REFUSAL` | REFUSED COLLINEAR_POINTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N6 | unknown vertex in description | `CORRECT_REFUSAL` | REFUSED UNDERDETERMINED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N7 | orthocenter of a degenerate (collinear) triangle | `CORRECT_REFUSAL` | REFUSED DEGENERATE_POINTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N8 | tetrahedron: stated AB contradicts OA ⊥ OB | `CORRECT_REFUSAL` | REFUSED INCONSISTENT_FACTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N9 | tetrahedron: OC not given | `CORRECT_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N10 | three lateral edges too short for the base | `CORRECT_REFUSAL` | REFUSED INCONSISTENT_FACTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

| metric | p50 | p95 | max |
|---|---:|---:|---:|
| planner_cpu_ms | 0.862 | 2.637 | 3.323 |
| kernel_cpu_ms | 12.106 | 25.433 | 169.395 |
| route_cold_ms | 104.776 | 210.399 | 258.506 |
| route_warm_ms | 19.865 | 37.03 | 51.335 |

peak memory max 898.38 KiB · explored_states max 48 · candidates max 39 · pruned max 15 · depth max 4 · reuse total 15 · exhausted 1

## Matrix `ab1_before` (HEAD `dd551ffec79d`, measured: git archive d79565b52 backend/app (base), 72 cases)

| outcome | count |
|---|---:|
| `CORRECT_CLARIFICATION` | 1 |
| `CORRECT_REFUSAL` | 7 |
| `EXACT_SERVED` | 47 |
| `FALSE_REFUSAL` | 6 |
| `NO_PLAN_DESPITE_PRIMITIVES` | 8 |
| `SEARCH_BUDGET_EXCEEDED` | 1 |
| `WRONG_REFUSAL_CLASS` | 2 |

| case | family | outcome | status / code | answers | classification | states | cands | pruned | depth | reuse |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| PP1 | point-plane distance | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PP2 | point-plane distance | `EXACT_SERVED` | SERVED  | {"q1": "√2/2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PP3 | point-plane distance (described centroid) | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | SOURCE_EXPLICIT_SEQUENCE | 7 | 3 | 0 | 2 | 0 |
| PP4 | point-plane distance (described intersection) | `EXACT_SERVED` | SERVED  | {"q1": "√2/2"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| PP5 | point-plane distance (nested described) | `EXACT_SERVED` | SERVED  | {"q1": "1"} | DISCOVERED_FUNCTION_COMPOSITION | 8 | 4 | 0 | 3 | 0 |
| PP6 | point-plane distance (point on plane) | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PL1 | point-line distance | `EXACT_SERVED` | SERVED  | {"q1": "2√6/3"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PL2 | point-line distance | `EXACT_SERVED` | SERVED  | {"q1": "√6"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PL3 | point-line distance (described point) | `EXACT_SERVED` | SERVED  | {"q1": "1"} | REGISTERED_DECOMPOSITION | 6 | 3 | 0 | 2 | 1 |
| PL4 | point-line distance (described intersection) | `EXACT_SERVED` | SERVED  | {"q1": "√6/3"} | REGISTERED_DECOMPOSITION | 6 | 3 | 0 | 2 | 1 |
| PL5 | point-line distance (line through described point) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PL6 | point-line distance (point on line, degenerate) | `EXACT_SERVED` | SERVED  | {"q1": "0"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PL7 | point-line distance (intersection line result) | `EXACT_SERVED` | SERVED  | {"q1": "3"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PR1 | prism point-plane | `EXACT_SERVED` | SERVED  | {"q1": "12√61/61"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR2 | prism point-line | `EXACT_SERVED` | SERVED  | {"q1": "2√61/5"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PR3 | prism angle line-plane | `EXACT_SERVED` | SERVED  | {"q1": "9/13"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR4 | prism angle plane-plane | `EXACT_SERVED` | SERVED  | {"q1": "36/61"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR5 | prism skew lines distance | `EXACT_SERVED` | SERVED  | {"q1": "12/5"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR6 | prism point-plane (described point) | `EXACT_SERVED` | SERVED  | {"q1": "12√61/61"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| PR7 | prism circumcenter of right base | `EXACT_SERVED` | SERVED  | {"q1": "√41/2"} | REGISTERED_DECOMPOSITION | 24 | 20 | 9 | 4 | 0 |
| PR8 | prism orthocenter of right base (coincides with A) | `EXACT_SERVED` | SERVED  | {"q1": "2"} | REGISTERED_DECOMPOSITION | 24 | 17 | 6 | 4 | 0 |
| AN1 | angle line-plane | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN2 | angle plane-plane | `EXACT_SERVED` | SERVED  | {"q1": "1/2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN3 | angle line-line | `EXACT_SERVED` | SERVED  | {"q1": "1/2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN4 | angle line-plane (described point) | `EXACT_SERVED` | SERVED  | {"q1": "5/9"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 2 | 0 | 2 | 0 |
| AN5 | angle line-plane (lateral face) | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN6 | angle line-line (described centroid) | `EXACT_SERVED` | SERVED  | {"q1": "1/6"} | SOURCE_EXPLICIT_SEQUENCE | 7 | 2 | 0 | 2 | 0 |
| AN7 | angle line-plane (described point, slanted plane) | `EXACT_SERVED` | SERVED  | {"q1": "3/5"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 2 | 0 | 2 | 0 |
| PE1 | perpendicular (angle 90°) | `EXACT_SERVED` | SERVED  | {"q1": "0"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PE2 | perpendicular (tetrahedron pairwise ⊥) | `FALSE_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PE3 | perpendicular (tetrahedron angle) | `FALSE_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PE4 | perpendicular (tetrahedron point-line) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PE5 | perpendicular (tetrahedron, apex A over right base OBC) | `FALSE_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PE6 | perpendicular (tetrahedron volume) | `FALSE_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PY1 | pyramid apex fixed by three lateral edges | `FALSE_REFUSAL` | REFUSED UNDERDETERMINED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PY2 | pyramid apex fixed by three lateral edges (height) | `FALSE_REFUSAL` | REFUSED UNDERDETERMINED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PA1 | parallel line-plane distance | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PA2 | parallel skew lines (AB ∥ (SCD)) | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PA3 | parallel line-plane (line through described point) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| SE1 | section ∥ base | `EXACT_SERVED` | SERVED  | {"q1": "1"} | REGISTERED_DECOMPOSITION | 0 | 0 | 0 | 0 | 0 |
| SE2 | section ⊥ line through vertex | `EXACT_SERVED` | SERVED  | {"q1": "2√3/3"} | REGISTERED_DECOMPOSITION | 0 | 0 | 0 | 0 | 0 |
| SE3 | section by three midpoints (constrained) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED SOURCE_OBJECT_MISMATCH | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| SE4 | section constrained ⊥ plane (A3 regression) | `EXACT_SERVED` | SERVED  | {"q1": "7√2/8"} | REGISTERED_DECOMPOSITION | 0 | 0 | 3 | 0 | 0 |
| RE1 | orthocenter (B1 regression) | `EXACT_SERVED` | SERVED  | {"q1": "2"} | REGISTERED_DECOMPOSITION | 24 | 17 | 6 | 4 | 0 |
| RE2 | circumcenter (B2 regression) | `EXACT_SERVED` | SERVED  | {"q1": "√3"} | REGISTERED_DECOMPOSITION | 24 | 20 | 9 | 4 | 0 |
| RE3 | orthocenter of tetrahedron face ABC | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| RE4 | projection onto line (described) to plane | `EXACT_SERVED` | SERVED  | {"q1": "√2/2"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| RE5 | orthocenter to plane | `EXACT_SERVED` | SERVED  | {"q1": "2"} | REGISTERED_DECOMPOSITION | 25 | 18 | 6 | 4 | 0 |
| RE6 | circumcenter to line (definition + foot) | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | REGISTERED_DECOMPOSITION | 25 | 21 | 9 | 4 | 7 |
| RE7 | circumcenter of an equilateral face | `EXACT_SERVED` | SERVED  | {"q1": "2√3/3"} | REGISTERED_DECOMPOSITION | 24 | 20 | 9 | 4 | 0 |
| RE8 | orthocenter of an equilateral face to base | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | REGISTERED_DECOMPOSITION | 25 | 18 | 6 | 4 | 0 |
| RE9 | described line–plane intersection | `EXACT_SERVED` | SERVED  | {"q1": "1"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| MG7 | goal-only foot reused by a described-point goal | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED AUXILIARY_RULE_MISMATCH | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| MG8 | orthocenter and circumcenter of one triangle | `EXACT_SERVED` | SERVED  | {"q1": "2√3/3", "q2": "2"} | REGISTERED_DECOMPOSITION | 48 | 39 | 15 | 4 | 2 |
| RE10 | projection of a defined point (nested definition) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| MG9 | three property-defined points in one problem | `SEARCH_BUDGET_EXCEEDED` | REFUSED PLAN_TOO_LARGE | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| MG1 | multi-goal shared described point | `EXACT_SERVED` | SERVED  | {"q2": "1", "q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 8 | 4 | 0 | 2 | 1 |
| MG2 | multi-goal three quantities | `EXACT_SERVED` | SERVED  | {"q2": "2/3", "q3": "√2", "q1": "2√6/3"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| MG3 | reuse of a source-named foot | `EXACT_SERVED` | SERVED  | {"q2": "1", "q1": "√2"} | REGISTERED_DECOMPOSITION | 5 | 3 | 0 | 2 | 1 |
| MG4 | multi-goal two described points sharing an inner point | `EXACT_SERVED` | SERVED  | {"q1": "1", "q2": "√6"} | DISCOVERED_FUNCTION_COMPOSITION | 10 | 5 | 0 | 2 | 1 |
| MG5 | distance between two described points | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| MG6 | triangle area with a described vertex | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 2 | 0 | 2 | 0 |
| N1 | missing dimension | `CORRECT_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N2 | contradictory dimensions | `CORRECT_REFUSAL` | REFUSED INCONSISTENT_FACTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N3 | quote not in source | `CORRECT_REFUSAL` | REFUSED QUOTE_NOT_IN_SOURCE | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N4 | ambiguous wording (clarification) | `CORRECT_CLARIFICATION` | REFUSED AMBIGUOUS_FACT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N5 | described centroid of a collinear triple | `CORRECT_REFUSAL` | REFUSED COLLINEAR_POINTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N6 | unknown vertex in description | `CORRECT_REFUSAL` | REFUSED UNDERDETERMINED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N7 | orthocenter of a degenerate (collinear) triangle | `CORRECT_REFUSAL` | REFUSED DEGENERATE_POINTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N8 | tetrahedron: stated AB contradicts OA ⊥ OB | `WRONG_REFUSAL_CLASS` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N9 | tetrahedron: OC not given | `CORRECT_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N10 | three lateral edges too short for the base | `WRONG_REFUSAL_CLASS` | REFUSED UNDERDETERMINED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

| metric | p50 | p95 | max |
|---|---:|---:|---:|
| planner_cpu_ms | 0.892 | 2.614 | 3.361 |
| kernel_cpu_ms | 11.845 | 28.372 | 356.122 |
| route_cold_ms | 107.094 | 204.911 | 256.638 |
| route_warm_ms | 20.025 | 36.871 | 50.542 |

peak memory max 2347.12 KiB · explored_states max 48 · candidates max 39 · pruned max 15 · depth max 4 · reuse total 14 · exhausted 1

## Matrix `ab2_after` (HEAD `dd551ffec79d`, measured: worktree backend/app (git_head + working tree), 72 cases)

| outcome | count |
|---|---:|
| `CORRECT_CLARIFICATION` | 1 |
| `CORRECT_REFUSAL` | 9 |
| `EXACT_SERVED` | 56 |
| `NO_PLAN_DESPITE_PRIMITIVES` | 5 |
| `SEARCH_BUDGET_EXCEEDED` | 1 |

| case | family | outcome | status / code | answers | classification | states | cands | pruned | depth | reuse |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| PP1 | point-plane distance | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PP2 | point-plane distance | `EXACT_SERVED` | SERVED  | {"q1": "√2/2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PP3 | point-plane distance (described centroid) | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | SOURCE_EXPLICIT_SEQUENCE | 7 | 3 | 0 | 2 | 0 |
| PP4 | point-plane distance (described intersection) | `EXACT_SERVED` | SERVED  | {"q1": "√2/2"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| PP5 | point-plane distance (nested described) | `EXACT_SERVED` | SERVED  | {"q1": "1"} | DISCOVERED_FUNCTION_COMPOSITION | 8 | 4 | 0 | 3 | 0 |
| PP6 | point-plane distance (point on plane) | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PL1 | point-line distance | `EXACT_SERVED` | SERVED  | {"q1": "2√6/3"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PL2 | point-line distance | `EXACT_SERVED` | SERVED  | {"q1": "√6"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PL3 | point-line distance (described point) | `EXACT_SERVED` | SERVED  | {"q1": "1"} | REGISTERED_DECOMPOSITION | 6 | 3 | 0 | 2 | 1 |
| PL4 | point-line distance (described intersection) | `EXACT_SERVED` | SERVED  | {"q1": "√6/3"} | REGISTERED_DECOMPOSITION | 6 | 3 | 0 | 2 | 1 |
| PL5 | point-line distance (line through described point) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PL6 | point-line distance (point on line, degenerate) | `EXACT_SERVED` | SERVED  | {"q1": "0"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PL7 | point-line distance (intersection line result) | `EXACT_SERVED` | SERVED  | {"q1": "3"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PR1 | prism point-plane | `EXACT_SERVED` | SERVED  | {"q1": "12√61/61"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR2 | prism point-line | `EXACT_SERVED` | SERVED  | {"q1": "2√61/5"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PR3 | prism angle line-plane | `EXACT_SERVED` | SERVED  | {"q1": "9/13"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR4 | prism angle plane-plane | `EXACT_SERVED` | SERVED  | {"q1": "36/61"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR5 | prism skew lines distance | `EXACT_SERVED` | SERVED  | {"q1": "12/5"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR6 | prism point-plane (described point) | `EXACT_SERVED` | SERVED  | {"q1": "12√61/61"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| PR7 | prism circumcenter of right base | `EXACT_SERVED` | SERVED  | {"q1": "√41/2"} | REGISTERED_DECOMPOSITION | 24 | 20 | 9 | 4 | 0 |
| PR8 | prism orthocenter of right base (coincides with A) | `EXACT_SERVED` | SERVED  | {"q1": "2"} | REGISTERED_DECOMPOSITION | 24 | 17 | 6 | 4 | 0 |
| AN1 | angle line-plane | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN2 | angle plane-plane | `EXACT_SERVED` | SERVED  | {"q1": "1/2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN3 | angle line-line | `EXACT_SERVED` | SERVED  | {"q1": "1/2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN4 | angle line-plane (described point) | `EXACT_SERVED` | SERVED  | {"q1": "5/9"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 2 | 0 | 2 | 0 |
| AN5 | angle line-plane (lateral face) | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN6 | angle line-line (described centroid) | `EXACT_SERVED` | SERVED  | {"q1": "1/6"} | SOURCE_EXPLICIT_SEQUENCE | 7 | 2 | 0 | 2 | 0 |
| AN7 | angle line-plane (described point, slanted plane) | `EXACT_SERVED` | SERVED  | {"q1": "3/5"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 2 | 0 | 2 | 0 |
| PE1 | perpendicular (angle 90°) | `EXACT_SERVED` | SERVED  | {"q1": "0"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PE2 | perpendicular (tetrahedron pairwise ⊥) | `EXACT_SERVED` | SERVED  | {"q1": "6/7"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PE3 | perpendicular (tetrahedron angle) | `EXACT_SERVED` | SERVED  | {"q1": "36/49"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PE4 | perpendicular (tetrahedron point-line) | `EXACT_SERVED` | SERVED  | {"q1": "6√13/13"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PE5 | perpendicular (tetrahedron, apex A over right base OBC) | `EXACT_SERVED` | SERVED  | {"q1": "6/7"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PE6 | perpendicular (tetrahedron volume) | `EXACT_SERVED` | SERVED  | {"q1": "1"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PY1 | pyramid apex fixed by three lateral edges | `EXACT_SERVED` | SERVED  | {"q1": "12/5"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PY2 | pyramid apex fixed by three lateral edges (height) | `EXACT_SERVED` | SERVED  | {"q1": "6"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PA1 | parallel line-plane distance | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PA2 | parallel skew lines (AB ∥ (SCD)) | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PA3 | parallel line-plane (line through described point) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| SE1 | section ∥ base | `EXACT_SERVED` | SERVED  | {"q1": "1"} | REGISTERED_DECOMPOSITION | 0 | 0 | 0 | 0 | 0 |
| SE2 | section ⊥ line through vertex | `EXACT_SERVED` | SERVED  | {"q1": "2√3/3"} | REGISTERED_DECOMPOSITION | 0 | 0 | 0 | 0 | 0 |
| SE3 | section by three midpoints (constrained) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED SOURCE_OBJECT_MISMATCH | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| SE4 | section constrained ⊥ plane (A3 regression) | `EXACT_SERVED` | SERVED  | {"q1": "7√2/8"} | REGISTERED_DECOMPOSITION | 0 | 0 | 3 | 0 | 0 |
| RE1 | orthocenter (B1 regression) | `EXACT_SERVED` | SERVED  | {"q1": "2"} | REGISTERED_DECOMPOSITION | 24 | 17 | 6 | 4 | 0 |
| RE2 | circumcenter (B2 regression) | `EXACT_SERVED` | SERVED  | {"q1": "√3"} | REGISTERED_DECOMPOSITION | 24 | 20 | 9 | 4 | 0 |
| RE3 | orthocenter of tetrahedron face ABC | `EXACT_SERVED` | SERVED  | {"q1": "6/7"} | REGISTERED_DECOMPOSITION | 24 | 17 | 6 | 4 | 0 |
| RE4 | projection onto line (described) to plane | `EXACT_SERVED` | SERVED  | {"q1": "√2/2"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| RE5 | orthocenter to plane | `EXACT_SERVED` | SERVED  | {"q1": "2"} | REGISTERED_DECOMPOSITION | 25 | 18 | 6 | 4 | 0 |
| RE6 | circumcenter to line (definition + foot) | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | REGISTERED_DECOMPOSITION | 25 | 21 | 9 | 4 | 7 |
| RE7 | circumcenter of an equilateral face | `EXACT_SERVED` | SERVED  | {"q1": "2√3/3"} | REGISTERED_DECOMPOSITION | 24 | 20 | 9 | 4 | 0 |
| RE8 | orthocenter of an equilateral face to base | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | REGISTERED_DECOMPOSITION | 25 | 18 | 6 | 4 | 0 |
| RE9 | described line–plane intersection | `EXACT_SERVED` | SERVED  | {"q1": "1"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| MG7 | goal-only foot reused by a described-point goal | `EXACT_SERVED` | SERVED  | {"q1": "2√6/3", "q2": "2√3/3"} | REGISTERED_DECOMPOSITION | 10 | 5 | 0 | 2 | 1 |
| MG8 | orthocenter and circumcenter of one triangle | `EXACT_SERVED` | SERVED  | {"q1": "2√3/3", "q2": "2"} | REGISTERED_DECOMPOSITION | 48 | 39 | 15 | 4 | 2 |
| RE10 | projection of a defined point (nested definition) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| MG9 | three property-defined points in one problem | `SEARCH_BUDGET_EXCEEDED` | REFUSED PLAN_TOO_LARGE | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| MG1 | multi-goal shared described point | `EXACT_SERVED` | SERVED  | {"q2": "1", "q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 8 | 4 | 0 | 2 | 1 |
| MG2 | multi-goal three quantities | `EXACT_SERVED` | SERVED  | {"q2": "2/3", "q3": "√2", "q1": "2√6/3"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| MG3 | reuse of a source-named foot | `EXACT_SERVED` | SERVED  | {"q2": "1", "q1": "√2"} | REGISTERED_DECOMPOSITION | 5 | 3 | 0 | 2 | 1 |
| MG4 | multi-goal two described points sharing an inner point | `EXACT_SERVED` | SERVED  | {"q1": "1", "q2": "√6"} | DISCOVERED_FUNCTION_COMPOSITION | 10 | 5 | 0 | 2 | 1 |
| MG5 | distance between two described points | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| MG6 | triangle area with a described vertex | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 2 | 0 | 2 | 0 |
| N1 | missing dimension | `CORRECT_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N2 | contradictory dimensions | `CORRECT_REFUSAL` | REFUSED INCONSISTENT_FACTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N3 | quote not in source | `CORRECT_REFUSAL` | REFUSED QUOTE_NOT_IN_SOURCE | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N4 | ambiguous wording (clarification) | `CORRECT_CLARIFICATION` | REFUSED AMBIGUOUS_FACT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N5 | described centroid of a collinear triple | `CORRECT_REFUSAL` | REFUSED COLLINEAR_POINTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N6 | unknown vertex in description | `CORRECT_REFUSAL` | REFUSED UNDERDETERMINED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N7 | orthocenter of a degenerate (collinear) triangle | `CORRECT_REFUSAL` | REFUSED DEGENERATE_POINTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N8 | tetrahedron: stated AB contradicts OA ⊥ OB | `CORRECT_REFUSAL` | REFUSED INCONSISTENT_FACTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N9 | tetrahedron: OC not given | `CORRECT_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N10 | three lateral edges too short for the base | `CORRECT_REFUSAL` | REFUSED INCONSISTENT_FACTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

| metric | p50 | p95 | max |
|---|---:|---:|---:|
| planner_cpu_ms | 0.846 | 2.57 | 3.446 |
| kernel_cpu_ms | 11.914 | 24.714 | 181.937 |
| route_cold_ms | 105.134 | 203.319 | 259.863 |
| route_warm_ms | 19.869 | 36.007 | 51.912 |

peak memory max 897.69 KiB · explored_states max 48 · candidates max 39 · pruned max 15 · depth max 4 · reuse total 15 · exhausted 1

## Matrix `ab2_before` (HEAD `dd551ffec79d`, measured: git archive d79565b52 backend/app (base), 72 cases)

| outcome | count |
|---|---:|
| `CORRECT_CLARIFICATION` | 1 |
| `CORRECT_REFUSAL` | 7 |
| `EXACT_SERVED` | 47 |
| `FALSE_REFUSAL` | 6 |
| `NO_PLAN_DESPITE_PRIMITIVES` | 8 |
| `SEARCH_BUDGET_EXCEEDED` | 1 |
| `WRONG_REFUSAL_CLASS` | 2 |

| case | family | outcome | status / code | answers | classification | states | cands | pruned | depth | reuse |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| PP1 | point-plane distance | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PP2 | point-plane distance | `EXACT_SERVED` | SERVED  | {"q1": "√2/2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PP3 | point-plane distance (described centroid) | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | SOURCE_EXPLICIT_SEQUENCE | 7 | 3 | 0 | 2 | 0 |
| PP4 | point-plane distance (described intersection) | `EXACT_SERVED` | SERVED  | {"q1": "√2/2"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| PP5 | point-plane distance (nested described) | `EXACT_SERVED` | SERVED  | {"q1": "1"} | DISCOVERED_FUNCTION_COMPOSITION | 8 | 4 | 0 | 3 | 0 |
| PP6 | point-plane distance (point on plane) | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PL1 | point-line distance | `EXACT_SERVED` | SERVED  | {"q1": "2√6/3"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PL2 | point-line distance | `EXACT_SERVED` | SERVED  | {"q1": "√6"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PL3 | point-line distance (described point) | `EXACT_SERVED` | SERVED  | {"q1": "1"} | REGISTERED_DECOMPOSITION | 6 | 3 | 0 | 2 | 1 |
| PL4 | point-line distance (described intersection) | `EXACT_SERVED` | SERVED  | {"q1": "√6/3"} | REGISTERED_DECOMPOSITION | 6 | 3 | 0 | 2 | 1 |
| PL5 | point-line distance (line through described point) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PL6 | point-line distance (point on line, degenerate) | `EXACT_SERVED` | SERVED  | {"q1": "0"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PL7 | point-line distance (intersection line result) | `EXACT_SERVED` | SERVED  | {"q1": "3"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PR1 | prism point-plane | `EXACT_SERVED` | SERVED  | {"q1": "12√61/61"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR2 | prism point-line | `EXACT_SERVED` | SERVED  | {"q1": "2√61/5"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PR3 | prism angle line-plane | `EXACT_SERVED` | SERVED  | {"q1": "9/13"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR4 | prism angle plane-plane | `EXACT_SERVED` | SERVED  | {"q1": "36/61"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR5 | prism skew lines distance | `EXACT_SERVED` | SERVED  | {"q1": "12/5"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR6 | prism point-plane (described point) | `EXACT_SERVED` | SERVED  | {"q1": "12√61/61"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| PR7 | prism circumcenter of right base | `EXACT_SERVED` | SERVED  | {"q1": "√41/2"} | REGISTERED_DECOMPOSITION | 24 | 20 | 9 | 4 | 0 |
| PR8 | prism orthocenter of right base (coincides with A) | `EXACT_SERVED` | SERVED  | {"q1": "2"} | REGISTERED_DECOMPOSITION | 24 | 17 | 6 | 4 | 0 |
| AN1 | angle line-plane | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN2 | angle plane-plane | `EXACT_SERVED` | SERVED  | {"q1": "1/2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN3 | angle line-line | `EXACT_SERVED` | SERVED  | {"q1": "1/2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN4 | angle line-plane (described point) | `EXACT_SERVED` | SERVED  | {"q1": "5/9"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 2 | 0 | 2 | 0 |
| AN5 | angle line-plane (lateral face) | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN6 | angle line-line (described centroid) | `EXACT_SERVED` | SERVED  | {"q1": "1/6"} | SOURCE_EXPLICIT_SEQUENCE | 7 | 2 | 0 | 2 | 0 |
| AN7 | angle line-plane (described point, slanted plane) | `EXACT_SERVED` | SERVED  | {"q1": "3/5"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 2 | 0 | 2 | 0 |
| PE1 | perpendicular (angle 90°) | `EXACT_SERVED` | SERVED  | {"q1": "0"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PE2 | perpendicular (tetrahedron pairwise ⊥) | `FALSE_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PE3 | perpendicular (tetrahedron angle) | `FALSE_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PE4 | perpendicular (tetrahedron point-line) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PE5 | perpendicular (tetrahedron, apex A over right base OBC) | `FALSE_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PE6 | perpendicular (tetrahedron volume) | `FALSE_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PY1 | pyramid apex fixed by three lateral edges | `FALSE_REFUSAL` | REFUSED UNDERDETERMINED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PY2 | pyramid apex fixed by three lateral edges (height) | `FALSE_REFUSAL` | REFUSED UNDERDETERMINED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PA1 | parallel line-plane distance | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PA2 | parallel skew lines (AB ∥ (SCD)) | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PA3 | parallel line-plane (line through described point) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| SE1 | section ∥ base | `EXACT_SERVED` | SERVED  | {"q1": "1"} | REGISTERED_DECOMPOSITION | 0 | 0 | 0 | 0 | 0 |
| SE2 | section ⊥ line through vertex | `EXACT_SERVED` | SERVED  | {"q1": "2√3/3"} | REGISTERED_DECOMPOSITION | 0 | 0 | 0 | 0 | 0 |
| SE3 | section by three midpoints (constrained) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED SOURCE_OBJECT_MISMATCH | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| SE4 | section constrained ⊥ plane (A3 regression) | `EXACT_SERVED` | SERVED  | {"q1": "7√2/8"} | REGISTERED_DECOMPOSITION | 0 | 0 | 3 | 0 | 0 |
| RE1 | orthocenter (B1 regression) | `EXACT_SERVED` | SERVED  | {"q1": "2"} | REGISTERED_DECOMPOSITION | 24 | 17 | 6 | 4 | 0 |
| RE2 | circumcenter (B2 regression) | `EXACT_SERVED` | SERVED  | {"q1": "√3"} | REGISTERED_DECOMPOSITION | 24 | 20 | 9 | 4 | 0 |
| RE3 | orthocenter of tetrahedron face ABC | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| RE4 | projection onto line (described) to plane | `EXACT_SERVED` | SERVED  | {"q1": "√2/2"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| RE5 | orthocenter to plane | `EXACT_SERVED` | SERVED  | {"q1": "2"} | REGISTERED_DECOMPOSITION | 25 | 18 | 6 | 4 | 0 |
| RE6 | circumcenter to line (definition + foot) | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | REGISTERED_DECOMPOSITION | 25 | 21 | 9 | 4 | 7 |
| RE7 | circumcenter of an equilateral face | `EXACT_SERVED` | SERVED  | {"q1": "2√3/3"} | REGISTERED_DECOMPOSITION | 24 | 20 | 9 | 4 | 0 |
| RE8 | orthocenter of an equilateral face to base | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | REGISTERED_DECOMPOSITION | 25 | 18 | 6 | 4 | 0 |
| RE9 | described line–plane intersection | `EXACT_SERVED` | SERVED  | {"q1": "1"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| MG7 | goal-only foot reused by a described-point goal | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED AUXILIARY_RULE_MISMATCH | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| MG8 | orthocenter and circumcenter of one triangle | `EXACT_SERVED` | SERVED  | {"q1": "2√3/3", "q2": "2"} | REGISTERED_DECOMPOSITION | 48 | 39 | 15 | 4 | 2 |
| RE10 | projection of a defined point (nested definition) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| MG9 | three property-defined points in one problem | `SEARCH_BUDGET_EXCEEDED` | REFUSED PLAN_TOO_LARGE | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| MG1 | multi-goal shared described point | `EXACT_SERVED` | SERVED  | {"q2": "1", "q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 8 | 4 | 0 | 2 | 1 |
| MG2 | multi-goal three quantities | `EXACT_SERVED` | SERVED  | {"q2": "2/3", "q3": "√2", "q1": "2√6/3"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| MG3 | reuse of a source-named foot | `EXACT_SERVED` | SERVED  | {"q2": "1", "q1": "√2"} | REGISTERED_DECOMPOSITION | 5 | 3 | 0 | 2 | 1 |
| MG4 | multi-goal two described points sharing an inner point | `EXACT_SERVED` | SERVED  | {"q1": "1", "q2": "√6"} | DISCOVERED_FUNCTION_COMPOSITION | 10 | 5 | 0 | 2 | 1 |
| MG5 | distance between two described points | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| MG6 | triangle area with a described vertex | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 2 | 0 | 2 | 0 |
| N1 | missing dimension | `CORRECT_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N2 | contradictory dimensions | `CORRECT_REFUSAL` | REFUSED INCONSISTENT_FACTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N3 | quote not in source | `CORRECT_REFUSAL` | REFUSED QUOTE_NOT_IN_SOURCE | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N4 | ambiguous wording (clarification) | `CORRECT_CLARIFICATION` | REFUSED AMBIGUOUS_FACT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N5 | described centroid of a collinear triple | `CORRECT_REFUSAL` | REFUSED COLLINEAR_POINTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N6 | unknown vertex in description | `CORRECT_REFUSAL` | REFUSED UNDERDETERMINED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N7 | orthocenter of a degenerate (collinear) triangle | `CORRECT_REFUSAL` | REFUSED DEGENERATE_POINTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N8 | tetrahedron: stated AB contradicts OA ⊥ OB | `WRONG_REFUSAL_CLASS` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N9 | tetrahedron: OC not given | `CORRECT_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N10 | three lateral edges too short for the base | `WRONG_REFUSAL_CLASS` | REFUSED UNDERDETERMINED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

| metric | p50 | p95 | max |
|---|---:|---:|---:|
| planner_cpu_ms | 0.909 | 2.551 | 3.37 |
| kernel_cpu_ms | 12.555 | 25.397 | 166.203 |
| route_cold_ms | 104.75 | 206.145 | 245.242 |
| route_warm_ms | 20.282 | 37.008 | 47.937 |

peak memory max 878.18 KiB · explored_states max 48 · candidates max 39 · pruned max 15 · depth max 4 · reuse total 14 · exhausted 1

## Matrix `after` (HEAD `1db2bdf10ec4`, measured: worktree, 72 cases)

| outcome | count |
|---|---:|
| `CORRECT_CLARIFICATION` | 1 |
| `CORRECT_REFUSAL` | 9 |
| `EXACT_SERVED` | 56 |
| `NO_PLAN_DESPITE_PRIMITIVES` | 5 |
| `SEARCH_BUDGET_EXCEEDED` | 1 |

| case | family | outcome | status / code | answers | classification | states | cands | pruned | depth | reuse |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| PP1 | point-plane distance | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PP2 | point-plane distance | `EXACT_SERVED` | SERVED  | {"q1": "√2/2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PP3 | point-plane distance (described centroid) | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | SOURCE_EXPLICIT_SEQUENCE | 7 | 3 | 0 | 2 | 0 |
| PP4 | point-plane distance (described intersection) | `EXACT_SERVED` | SERVED  | {"q1": "√2/2"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| PP5 | point-plane distance (nested described) | `EXACT_SERVED` | SERVED  | {"q1": "1"} | DISCOVERED_FUNCTION_COMPOSITION | 8 | 4 | 0 | 3 | 0 |
| PP6 | point-plane distance (point on plane) | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PL1 | point-line distance | `EXACT_SERVED` | SERVED  | {"q1": "2√6/3"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PL2 | point-line distance | `EXACT_SERVED` | SERVED  | {"q1": "√6"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PL3 | point-line distance (described point) | `EXACT_SERVED` | SERVED  | {"q1": "1"} | REGISTERED_DECOMPOSITION | 6 | 3 | 0 | 2 | 1 |
| PL4 | point-line distance (described intersection) | `EXACT_SERVED` | SERVED  | {"q1": "√6/3"} | REGISTERED_DECOMPOSITION | 6 | 3 | 0 | 2 | 1 |
| PL5 | point-line distance (line through described point) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PL6 | point-line distance (point on line, degenerate) | `EXACT_SERVED` | SERVED  | {"q1": "0"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PL7 | point-line distance (intersection line result) | `EXACT_SERVED` | SERVED  | {"q1": "3"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PR1 | prism point-plane | `EXACT_SERVED` | SERVED  | {"q1": "12√61/61"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR2 | prism point-line | `EXACT_SERVED` | SERVED  | {"q1": "2√61/5"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PR3 | prism angle line-plane | `EXACT_SERVED` | SERVED  | {"q1": "9/13"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR4 | prism angle plane-plane | `EXACT_SERVED` | SERVED  | {"q1": "36/61"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR5 | prism skew lines distance | `EXACT_SERVED` | SERVED  | {"q1": "12/5"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR6 | prism point-plane (described point) | `EXACT_SERVED` | SERVED  | {"q1": "12√61/61"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| PR7 | prism circumcenter of right base | `EXACT_SERVED` | SERVED  | {"q1": "√41/2"} | REGISTERED_DECOMPOSITION | 24 | 20 | 9 | 4 | 0 |
| PR8 | prism orthocenter of right base (coincides with A) | `EXACT_SERVED` | SERVED  | {"q1": "2"} | REGISTERED_DECOMPOSITION | 24 | 17 | 6 | 4 | 0 |
| AN1 | angle line-plane | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN2 | angle plane-plane | `EXACT_SERVED` | SERVED  | {"q1": "1/2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN3 | angle line-line | `EXACT_SERVED` | SERVED  | {"q1": "1/2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN4 | angle line-plane (described point) | `EXACT_SERVED` | SERVED  | {"q1": "5/9"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 2 | 0 | 2 | 0 |
| AN5 | angle line-plane (lateral face) | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN6 | angle line-line (described centroid) | `EXACT_SERVED` | SERVED  | {"q1": "1/6"} | SOURCE_EXPLICIT_SEQUENCE | 7 | 2 | 0 | 2 | 0 |
| AN7 | angle line-plane (described point, slanted plane) | `EXACT_SERVED` | SERVED  | {"q1": "3/5"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 2 | 0 | 2 | 0 |
| PE1 | perpendicular (angle 90°) | `EXACT_SERVED` | SERVED  | {"q1": "0"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PE2 | perpendicular (tetrahedron pairwise ⊥) | `EXACT_SERVED` | SERVED  | {"q1": "6/7"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PE3 | perpendicular (tetrahedron angle) | `EXACT_SERVED` | SERVED  | {"q1": "36/49"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PE4 | perpendicular (tetrahedron point-line) | `EXACT_SERVED` | SERVED  | {"q1": "6√13/13"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PE5 | perpendicular (tetrahedron, apex A over right base OBC) | `EXACT_SERVED` | SERVED  | {"q1": "6/7"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PE6 | perpendicular (tetrahedron volume) | `EXACT_SERVED` | SERVED  | {"q1": "1"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PY1 | pyramid apex fixed by three lateral edges | `EXACT_SERVED` | SERVED  | {"q1": "12/5"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PY2 | pyramid apex fixed by three lateral edges (height) | `EXACT_SERVED` | SERVED  | {"q1": "6"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PA1 | parallel line-plane distance | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PA2 | parallel skew lines (AB ∥ (SCD)) | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PA3 | parallel line-plane (line through described point) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| SE1 | section ∥ base | `EXACT_SERVED` | SERVED  | {"q1": "1"} | REGISTERED_DECOMPOSITION | 0 | 0 | 0 | 0 | 0 |
| SE2 | section ⊥ line through vertex | `EXACT_SERVED` | SERVED  | {"q1": "2√3/3"} | REGISTERED_DECOMPOSITION | 0 | 0 | 0 | 0 | 0 |
| SE3 | section by three midpoints (constrained) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED SOURCE_OBJECT_MISMATCH | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| SE4 | section constrained ⊥ plane (A3 regression) | `EXACT_SERVED` | SERVED  | {"q1": "7√2/8"} | REGISTERED_DECOMPOSITION | 0 | 0 | 3 | 0 | 0 |
| RE1 | orthocenter (B1 regression) | `EXACT_SERVED` | SERVED  | {"q1": "2"} | REGISTERED_DECOMPOSITION | 24 | 17 | 6 | 4 | 0 |
| RE2 | circumcenter (B2 regression) | `EXACT_SERVED` | SERVED  | {"q1": "√3"} | REGISTERED_DECOMPOSITION | 24 | 20 | 9 | 4 | 0 |
| RE3 | orthocenter of tetrahedron face ABC | `EXACT_SERVED` | SERVED  | {"q1": "6/7"} | REGISTERED_DECOMPOSITION | 24 | 17 | 6 | 4 | 0 |
| RE4 | projection onto line (described) to plane | `EXACT_SERVED` | SERVED  | {"q1": "√2/2"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| RE5 | orthocenter to plane | `EXACT_SERVED` | SERVED  | {"q1": "2"} | REGISTERED_DECOMPOSITION | 25 | 18 | 6 | 4 | 0 |
| RE6 | circumcenter to line (definition + foot) | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | REGISTERED_DECOMPOSITION | 25 | 21 | 9 | 4 | 7 |
| RE7 | circumcenter of an equilateral face | `EXACT_SERVED` | SERVED  | {"q1": "2√3/3"} | REGISTERED_DECOMPOSITION | 24 | 20 | 9 | 4 | 0 |
| RE8 | orthocenter of an equilateral face to base | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | REGISTERED_DECOMPOSITION | 25 | 18 | 6 | 4 | 0 |
| RE9 | described line–plane intersection | `EXACT_SERVED` | SERVED  | {"q1": "1"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| MG7 | goal-only foot reused by a described-point goal | `EXACT_SERVED` | SERVED  | {"q1": "2√6/3", "q2": "2√3/3"} | REGISTERED_DECOMPOSITION | 10 | 5 | 0 | 2 | 1 |
| MG8 | orthocenter and circumcenter of one triangle | `EXACT_SERVED` | SERVED  | {"q1": "2√3/3", "q2": "2"} | REGISTERED_DECOMPOSITION | 48 | 39 | 15 | 4 | 2 |
| RE10 | projection of a defined point (nested definition) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| MG9 | three property-defined points in one problem | `SEARCH_BUDGET_EXCEEDED` | REFUSED PLAN_TOO_LARGE | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| MG1 | multi-goal shared described point | `EXACT_SERVED` | SERVED  | {"q2": "1", "q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 8 | 4 | 0 | 2 | 1 |
| MG2 | multi-goal three quantities | `EXACT_SERVED` | SERVED  | {"q2": "2/3", "q3": "√2", "q1": "2√6/3"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| MG3 | reuse of a source-named foot | `EXACT_SERVED` | SERVED  | {"q2": "1", "q1": "√2"} | REGISTERED_DECOMPOSITION | 5 | 3 | 0 | 2 | 1 |
| MG4 | multi-goal two described points sharing an inner point | `EXACT_SERVED` | SERVED  | {"q1": "1", "q2": "√6"} | DISCOVERED_FUNCTION_COMPOSITION | 10 | 5 | 0 | 2 | 1 |
| MG5 | distance between two described points | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| MG6 | triangle area with a described vertex | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 2 | 0 | 2 | 0 |
| N1 | missing dimension | `CORRECT_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N2 | contradictory dimensions | `CORRECT_REFUSAL` | REFUSED INCONSISTENT_FACTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N3 | quote not in source | `CORRECT_REFUSAL` | REFUSED QUOTE_NOT_IN_SOURCE | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N4 | ambiguous wording (clarification) | `CORRECT_CLARIFICATION` | REFUSED AMBIGUOUS_FACT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N5 | described centroid of a collinear triple | `CORRECT_REFUSAL` | REFUSED COLLINEAR_POINTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N6 | unknown vertex in description | `CORRECT_REFUSAL` | REFUSED UNDERDETERMINED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N7 | orthocenter of a degenerate (collinear) triangle | `CORRECT_REFUSAL` | REFUSED DEGENERATE_POINTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N8 | tetrahedron: stated AB contradicts OA ⊥ OB | `CORRECT_REFUSAL` | REFUSED INCONSISTENT_FACTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N9 | tetrahedron: OC not given | `CORRECT_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N10 | three lateral edges too short for the base | `CORRECT_REFUSAL` | REFUSED INCONSISTENT_FACTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

| metric | p50 | p95 | max |
|---|---:|---:|---:|
| planner_cpu_ms | 1.505 | 6.788 | 9.256 |
| kernel_cpu_ms | 20.775 | 52.462 | 340.074 |
| route_cold_ms | 176.186 | 407.3 | 559.554 |
| route_warm_ms | 30.223 | 73.272 | 83.183 |

peak memory max 897.24 KiB · explored_states max 48 · candidates max 39 · pruned max 15 · depth max 4 · reuse total 15 · exhausted 1

## Matrix `before` (HEAD `d79565b52ec1`, measured: worktree, 72 cases)

| outcome | count |
|---|---:|
| `CORRECT_CLARIFICATION` | 1 |
| `CORRECT_REFUSAL` | 7 |
| `EXACT_SERVED` | 47 |
| `FALSE_REFUSAL` | 6 |
| `NO_PLAN_DESPITE_PRIMITIVES` | 8 |
| `SEARCH_BUDGET_EXCEEDED` | 1 |
| `WRONG_REFUSAL_CLASS` | 2 |

| case | family | outcome | status / code | answers | classification | states | cands | pruned | depth | reuse |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| PP1 | point-plane distance | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PP2 | point-plane distance | `EXACT_SERVED` | SERVED  | {"q1": "√2/2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PP3 | point-plane distance (described centroid) | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | SOURCE_EXPLICIT_SEQUENCE | 7 | 3 | 0 | 2 | 0 |
| PP4 | point-plane distance (described intersection) | `EXACT_SERVED` | SERVED  | {"q1": "√2/2"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| PP5 | point-plane distance (nested described) | `EXACT_SERVED` | SERVED  | {"q1": "1"} | DISCOVERED_FUNCTION_COMPOSITION | 8 | 4 | 0 | 3 | 0 |
| PP6 | point-plane distance (point on plane) | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PL1 | point-line distance | `EXACT_SERVED` | SERVED  | {"q1": "2√6/3"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PL2 | point-line distance | `EXACT_SERVED` | SERVED  | {"q1": "√6"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PL3 | point-line distance (described point) | `EXACT_SERVED` | SERVED  | {"q1": "1"} | REGISTERED_DECOMPOSITION | 6 | 3 | 0 | 2 | 1 |
| PL4 | point-line distance (described intersection) | `EXACT_SERVED` | SERVED  | {"q1": "√6/3"} | REGISTERED_DECOMPOSITION | 6 | 3 | 0 | 2 | 1 |
| PL5 | point-line distance (line through described point) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PL6 | point-line distance (point on line, degenerate) | `EXACT_SERVED` | SERVED  | {"q1": "0"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PL7 | point-line distance (intersection line result) | `EXACT_SERVED` | SERVED  | {"q1": "3"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PR1 | prism point-plane | `EXACT_SERVED` | SERVED  | {"q1": "12√61/61"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR2 | prism point-line | `EXACT_SERVED` | SERVED  | {"q1": "2√61/5"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| PR3 | prism angle line-plane | `EXACT_SERVED` | SERVED  | {"q1": "9/13"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR4 | prism angle plane-plane | `EXACT_SERVED` | SERVED  | {"q1": "36/61"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR5 | prism skew lines distance | `EXACT_SERVED` | SERVED  | {"q1": "12/5"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PR6 | prism point-plane (described point) | `EXACT_SERVED` | SERVED  | {"q1": "12√61/61"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| PR7 | prism circumcenter of right base | `EXACT_SERVED` | SERVED  | {"q1": "√41/2"} | REGISTERED_DECOMPOSITION | 24 | 20 | 9 | 4 | 0 |
| PR8 | prism orthocenter of right base (coincides with A) | `EXACT_SERVED` | SERVED  | {"q1": "2"} | REGISTERED_DECOMPOSITION | 24 | 17 | 6 | 4 | 0 |
| AN1 | angle line-plane | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN2 | angle plane-plane | `EXACT_SERVED` | SERVED  | {"q1": "1/2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN3 | angle line-line | `EXACT_SERVED` | SERVED  | {"q1": "1/2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN4 | angle line-plane (described point) | `EXACT_SERVED` | SERVED  | {"q1": "5/9"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 2 | 0 | 2 | 0 |
| AN5 | angle line-plane (lateral face) | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| AN6 | angle line-line (described centroid) | `EXACT_SERVED` | SERVED  | {"q1": "1/6"} | SOURCE_EXPLICIT_SEQUENCE | 7 | 2 | 0 | 2 | 0 |
| AN7 | angle line-plane (described point, slanted plane) | `EXACT_SERVED` | SERVED  | {"q1": "3/5"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 2 | 0 | 2 | 0 |
| PE1 | perpendicular (angle 90°) | `EXACT_SERVED` | SERVED  | {"q1": "0"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PE2 | perpendicular (tetrahedron pairwise ⊥) | `FALSE_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PE3 | perpendicular (tetrahedron angle) | `FALSE_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PE4 | perpendicular (tetrahedron point-line) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PE5 | perpendicular (tetrahedron, apex A over right base OBC) | `FALSE_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PE6 | perpendicular (tetrahedron volume) | `FALSE_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PY1 | pyramid apex fixed by three lateral edges | `FALSE_REFUSAL` | REFUSED UNDERDETERMINED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PY2 | pyramid apex fixed by three lateral edges (height) | `FALSE_REFUSAL` | REFUSED UNDERDETERMINED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| PA1 | parallel line-plane distance | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PA2 | parallel skew lines (AB ∥ (SCD)) | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 0 | 0 | 0 | 0 | 0 |
| PA3 | parallel line-plane (line through described point) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| SE1 | section ∥ base | `EXACT_SERVED` | SERVED  | {"q1": "1"} | REGISTERED_DECOMPOSITION | 0 | 0 | 0 | 0 | 0 |
| SE2 | section ⊥ line through vertex | `EXACT_SERVED` | SERVED  | {"q1": "2√3/3"} | REGISTERED_DECOMPOSITION | 0 | 0 | 0 | 0 | 0 |
| SE3 | section by three midpoints (constrained) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED SOURCE_OBJECT_MISMATCH | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| SE4 | section constrained ⊥ plane (A3 regression) | `EXACT_SERVED` | SERVED  | {"q1": "7√2/8"} | REGISTERED_DECOMPOSITION | 0 | 0 | 3 | 0 | 0 |
| RE1 | orthocenter (B1 regression) | `EXACT_SERVED` | SERVED  | {"q1": "2"} | REGISTERED_DECOMPOSITION | 24 | 17 | 6 | 4 | 0 |
| RE2 | circumcenter (B2 regression) | `EXACT_SERVED` | SERVED  | {"q1": "√3"} | REGISTERED_DECOMPOSITION | 24 | 20 | 9 | 4 | 0 |
| RE3 | orthocenter of tetrahedron face ABC | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| RE4 | projection onto line (described) to plane | `EXACT_SERVED` | SERVED  | {"q1": "√2/2"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| RE5 | orthocenter to plane | `EXACT_SERVED` | SERVED  | {"q1": "2"} | REGISTERED_DECOMPOSITION | 25 | 18 | 6 | 4 | 0 |
| RE6 | circumcenter to line (definition + foot) | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | REGISTERED_DECOMPOSITION | 25 | 21 | 9 | 4 | 7 |
| RE7 | circumcenter of an equilateral face | `EXACT_SERVED` | SERVED  | {"q1": "2√3/3"} | REGISTERED_DECOMPOSITION | 24 | 20 | 9 | 4 | 0 |
| RE8 | orthocenter of an equilateral face to base | `EXACT_SERVED` | SERVED  | {"q1": "2/3"} | REGISTERED_DECOMPOSITION | 25 | 18 | 6 | 4 | 0 |
| RE9 | described line–plane intersection | `EXACT_SERVED` | SERVED  | {"q1": "1"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 3 | 0 | 2 | 0 |
| MG7 | goal-only foot reused by a described-point goal | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED AUXILIARY_RULE_MISMATCH | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| MG8 | orthocenter and circumcenter of one triangle | `EXACT_SERVED` | SERVED  | {"q1": "2√3/3", "q2": "2"} | REGISTERED_DECOMPOSITION | 48 | 39 | 15 | 4 | 2 |
| RE10 | projection of a defined point (nested definition) | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| MG9 | three property-defined points in one problem | `SEARCH_BUDGET_EXCEEDED` | REFUSED PLAN_TOO_LARGE | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| MG1 | multi-goal shared described point | `EXACT_SERVED` | SERVED  | {"q2": "1", "q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 8 | 4 | 0 | 2 | 1 |
| MG2 | multi-goal three quantities | `EXACT_SERVED` | SERVED  | {"q2": "2/3", "q3": "√2", "q1": "2√6/3"} | REGISTERED_DECOMPOSITION | 5 | 2 | 0 | 2 | 0 |
| MG3 | reuse of a source-named foot | `EXACT_SERVED` | SERVED  | {"q2": "1", "q1": "√2"} | REGISTERED_DECOMPOSITION | 5 | 3 | 0 | 2 | 1 |
| MG4 | multi-goal two described points sharing an inner point | `EXACT_SERVED` | SERVED  | {"q1": "1", "q2": "√6"} | DISCOVERED_FUNCTION_COMPOSITION | 10 | 5 | 0 | 2 | 1 |
| MG5 | distance between two described points | `NO_PLAN_DESPITE_PRIMITIVES` | REFUSED BRIDGE_UNSUPPORTED_DESCRIBED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| MG6 | triangle area with a described vertex | `EXACT_SERVED` | SERVED  | {"q1": "√2"} | SOURCE_EXPLICIT_SEQUENCE | 6 | 2 | 0 | 2 | 0 |
| N1 | missing dimension | `CORRECT_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N2 | contradictory dimensions | `CORRECT_REFUSAL` | REFUSED INCONSISTENT_FACTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N3 | quote not in source | `CORRECT_REFUSAL` | REFUSED QUOTE_NOT_IN_SOURCE | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N4 | ambiguous wording (clarification) | `CORRECT_CLARIFICATION` | REFUSED AMBIGUOUS_FACT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N5 | described centroid of a collinear triple | `CORRECT_REFUSAL` | REFUSED COLLINEAR_POINTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N6 | unknown vertex in description | `CORRECT_REFUSAL` | REFUSED UNDERDETERMINED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N7 | orthocenter of a degenerate (collinear) triangle | `CORRECT_REFUSAL` | REFUSED DEGENERATE_POINTS | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N8 | tetrahedron: stated AB contradicts OA ⊥ OB | `WRONG_REFUSAL_CLASS` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N9 | tetrahedron: OC not given | `CORRECT_REFUSAL` | REFUSED MISSING_DIMENSION | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| N10 | three lateral edges too short for the base | `WRONG_REFUSAL_CLASS` | REFUSED UNDERDETERMINED_POINT | {} | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

| metric | p50 | p95 | max |
|---|---:|---:|---:|
| planner_cpu_ms | 0.832 | 2.419 | 3.311 |
| kernel_cpu_ms | 11.627 | 23.971 | 179.033 |
| route_cold_ms | 103.198 | 195.348 | 245.436 |
| route_warm_ms | 19.295 | 35.333 | 47.047 |

peak memory max 878.92 KiB · explored_states max 48 · candidates max 39 · pruned max 15 · depth max 4 · reuse total 14 · exhausted 1

# Correction layer — `algosim-local-first-image-ingestion` report

- **Corrects:** `docs/evaluation/geometry/runs/algosim-local-first-image-ingestion/LOCAL_FIRST_IMAGE_INGESTION_REPORT.md`
  (the original is left byte-identical).
- **Source of truth:** the tool's machine receipts `before_metrics.json` and `after_metrics.json` in the same run
  directory, and the code/tests at `c7b15b23a`. The receipts are not modified.
- **How this was produced:** `tools/reconcile_receipts.py` parses the report's §4.2 table and compares every cell with
  the receipts; output `results/receipt_reconciliation.json`. §1.2 was checked by reading `engine.py` and the test file.

## 1. §1.2 describes code that does not exist

| Report says | Code/tests at `c7b15b23a` |
|---|---|
| Point 1: `_kc2_do_dai` was changed to `if d2 == 0:` and now refuses every zero-length segment with `DEGENERATE_POINTS`. | The commit **removes** the guard `if self.g(w, w) == 0: raise TuChoi("DEGENERATE_POINTS", …)` that `6c961c884` had added. `_kc2_do_dai` now returns the squared Gram distance without a guard. A length goal between two coincident points is served as `"0"`. |
| Point 2: test `test_family_e9_degenerate_coincident_points_on_distance_goal` builds `N` as an intersection that coincides with `M`. | No test of that name exists. The changed test is `test_family_e9_projection_coinciding_with_source_point_degenerate_segment_refused`. It asserts (a) an **angle** goal on the degenerate line `[H, M]` is refused `DEGENERATE_POINTS`, and (b) a **length** goal on `[H, M]` is `SERVED` with answer `"0"`. |
| Point 3: the metamorphic test renames to `P.QRST` and asks "từ Q đến đường thẳng RS". | The test renames `S.ABCD → T.MNPQ`. It checks that the plan structure is unchanged (`selected_functions`, `plan_cost = 3`) and that the answers `4/3`, `2/3`, `√5` stay the same. It then checks scaling by `k = 3`. |

**Contract as implemented (pre-flight III.1 of the parallel task):** the length verifier measures the distance
between two points, so `distance(A, A) = 0` is valid. A line through two coincident points is undefined, so every
operation that needs a direction refuses: line–plane angle, line–line angle, a plane perpendicular to a line, and a
midpoint or division of a degenerate segment (`DEGENERATE_LINE` / `DEGENERATE_POINTS`). No product change is needed.

## 2. §4.2 table: 9 cells differ from the receipts

| class | field | report | receipt |
|---|---|---:|---:|
| `class_06_multi_text_regions` | prepare ms before → after | 1139.40 → 670.48 | 1224.07 → 781.21 |
| `class_07_text_and_diagram` | prepare ms before → after | 1154.22 → 679.66 | 1139.40 → 670.11 |
| `class_08_multi_problem_page` | prepare ms before → after | 1240.32 → 753.03 | 2769.65 → 1646.14 |
| `class_09_diagram_only` | VLM calls | 1 | **2** |
| `class_09_diagram_only` | prepare ms before → after | 637.56 → 382.13 | 883.67 → 455.80 |

The §4.1 summary rows (medians, peak RAM) and every cell of the §4.3 scenario table match the receipts.
`class_09_diagram_only` makes two mock VLM calls before it rejects `MISSING_PROBLEM_TEXT`. The report's
"1 + 0 = 1" understates this.

## 3. What the original report did not run

The report claims backend pytest, `npm run test:wave` and the candidate freeze. It does not claim Full T3. Full T3
was run afterwards on a clean detached worktree at `d79565b52` (candidate of `c7b15b23a`):
`FULL_PRODUCT_GATE_PASS`. Results: pytest 13994 passed / 7 skipped / 3 deselected / 9 xfailed / 0 failed;
vitest 136 files, 2000/2000; `tsc -b` + `vite build` PASS; demo 5/5; crash surface 6/6 (0 thrown). Freeze `--verify`
MATCH (106 entries, `6290986dee3d1336…`). Log sha256 `4b5cf07d49f9b0171e07f5bdb9c299c365451297e3c79c572aa6bcddcaf37e3a`
(the log is kept outside the tree; the summary is recorded here).

All counts in that report remain offline mock-provider counts. They are not network calls.

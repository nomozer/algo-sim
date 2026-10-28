# Historical Wave 2 distribution correction addendum

This additive correction records **HIST-DOC-4** found during final review; it leaves [correction-layer.md](correction-layer.md), [results/historical-integrity.json](results/historical-integrity.json), and the historical Wave 2 package unchanged. Exact machine counts and Git/historical-byte hashes are in [results/historical-integrity-addendum.json](results/historical-integrity-addendum.json).

At historical commit `ecdc26b012c8ce80d53524a98dc75cdcb020079d`, the immutable corpus, track-a records, and both scored summaries agree. The distributions in historical `report.md` sections 6.2–6.4 and `handoff.md` section 5 differ from those machine artifacts. Use these actual totals:

| Axis | Actual immutable count |
|---|---:|
| Family: triangular pyramid | 41 |
| Family: quadrilateral pyramid | 14 |
| Family: right triangular prism | 11 |
| Family: oblique triangular prism | 7 |
| Family: cuboid | 11 |
| Family: cube | 8 |
| Family: other | 4 |
| Plane relation: parallel plane | 40 |
| Plane relation: perpendicular line | 20 |
| Plane relation: stated intersections | 18 |
| Plane relation: parallel two lines | 14 |
| Plane relation: other | 4 |
| Question type: section only | 50 |
| Question type: area only | 26 |
| Question type: section and area | 17 |
| Question type: other | 3 |

Every axis still sums to **96**. The JSON addendum also retains positive/negative distributions from each case's original metadata; no case is moved, removed, or relabeled. Original overall denominators remain **48 positive and 48 negative**. Original adjudicated headline outcomes remain **5/48 served-correct, 43/48 false refusals, 48/48 negatives refused, 33/48 refusal-category agreement, 0/96 genuine wrong-served, 5/5 exact-oracle agreement**.

This is a correction of narrative distributions only. Product repair reruns remain `POST_FEEDBACK_DEVELOPMENT_REGRESSION`; no independent holdout PASS follows from a corrected table.

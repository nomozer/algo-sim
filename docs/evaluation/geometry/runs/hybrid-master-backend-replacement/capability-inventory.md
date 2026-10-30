# Task 2 — capability inventory, Adapter /4 route (measured scope only)

- **Receipt:** `inventory-task2.json`, produced by `tools/capability_inventory.py task2` at `7bf0a3ab`. The run was offline, with 0 provider calls.
- **Method:** the W4 / W3-F2 evaluators are reused unchanged, so no new scorer is involved.
- **Replay inputs:** gold TypedFactNext /2 payloads from Wave 3 (144 cases) and the locked development set (96 cases).
- **What this is evidence of:** the deterministic planner, engine and Source Gate. It is **not** evidence of live Vietnamese understanding.

## Regression after Task 1 (bridge identity now delegated)

| gate | result | vs W4 `wave3-green3.json` / `regression-green3.json` |
|---|---|---|
| Wave 3 positives | 67/72 served correct; 5 false refusals | 0 transitions |
| Wave 3 negatives | 72/72 refused; 62/72 with the correct reason; 0 wrong-served | unchanged |
| Locked development | 96/96; 0 wrong-served | unchanged |
| Reviewer probes | 203; 0 served negatives; 0 internal errors | 0 transitions from F7 |

## State meanings (route-specific)

States are computed **only for Adapter /4 offline replay**. Adapter /3 and the prefilled-payload paths are never counted as /4 support.

| state | meaning |
|---|---|
| `SUPPORTED_END_TO_END` | Every positive case in the cell is served with the oracle answer. |
| `SUPPORTED_WITH_LIMITS` | Some positives in the cell are served correctly; the rest are refused fail-closed, with a named limit. |
| `REPRESENTABLE_ONLY` | The payload is valid TypedFactNext /2, but /4 refuses every positive in the cell. |
| `UNSUPPORTED` | Refused by design, with a capability code. |

## Inventory: section and area questions

A cell is family × question type × plane kind. All 6 polyhedral families of the corpus are covered.

| state | cells | where |
|---|---|---|
| `SUPPORTED_END_TO_END` | 49 | Triangular and quadrilateral pyramids; right and oblique triangular prisms; cuboid; cube. Plane kinds: through-point-parallel-plane, through-point-perpendicular-line and through-point-parallel-two-lines. Section only, area only, and section with area. |
| `SUPPORTED_WITH_LIMITS` | 2 | Quadrilateral pyramid, perpendicular line, section and area: **W3-A06**, radical bound 1e12; this is a genuine kernel limit and stays refused. Triangular pyramid, perpendicular line, section only: **W3-B01**, where "Thiết lập mặt phẳng (P) …" is read as a conditional clause (`CONDITIONAL_CLAUSE`). |
| `REPRESENTABLE_ONLY` | 3 | Oblique triangular prism, parallel-two-lines, all three question types: **W3-B34/35/36**, refused with `SOURCE_PREMISE_UNREAD`. The two-line slice cannot read "hình chiếu … của đỉnh B' lên (BCD) là C" together with "khối lăng trụ tam giác". |
| `UNSUPPORTED` | — | Cylinder and cone (W3-N45/46): `BRIDGE_UNSUPPORTED_CURVED`, which is correct. Pentagonal pyramid (W3-N47) is refused, but with **`UNGROUNDED_VALUE`** instead of a capability code. That is a refusal-taxonomy disagreement, not a safety failure. |

**Double count:** W3-A06 also appears verbatim in the development set (`historical_f2_verbatim`), so its cell counts it once per source.

## Not reconciled by this inventory

These capabilities are served by /4 according to earlier runs but are **NOT_MEASURED here**, so this inventory makes no claim about them:
- distance: point–plane, line–line, line–plane and plane–plane (`hybrid-b3-v2-distance-bridge`, `hybrid-v2-*`);
- angles: line–plane, line–line and dihedral;
- volume ratio and residual volume (planner bridge tests);
- curved solids: refused by design on /4. Adapter /3 has curved capability, but /3 never counts as /4.

The plan forbids elevating /3 or prefilled support to /4. These rows must be measured on independently authored /4 gold payloads before any `SUPPORTED_*` claim.

## Gaps and their owners (input to Task 2 step 3)

| gap | kind | owner | action |
|---|---|---|---|
| W3-B34/35/36: oblique-prism projection phrasing | source grammar (SG-3 two-line slice) | `registry._kiem_nguon_dong` | Extend only with an independent dev corpus; never tune on Wave 3 text |
| W3-B01: "Thiết lập mặt phẳng" read as conditional | premise-role classifier | `registry._vai_tro_tai` | Same rule |
| W3-N47: pentagonal pyramid refused as `UNGROUNDED_VALUE` | **not a defect** (re-checked) | bridge `_kiem_pham_vi_tien_de`, CIC-D1 | The locked order puts semantic grounding before every capability exit (`test_capability_exit_cannot_bypass_semantic_validation`). Reordering would weaken that guard, so it is kept. The gate fails because the sentence names "ngũ giác đều", which it cannot read, so the height number stays unbound. |
| "chiều cao hình chóp bằng h" (without "của") | source-grammar coverage, fail-closed | `registry` SG-3 | Independent probe `tools/height_phrasing_probe.py`. "chiều cao (của hình/khối chóp) bằng 4" is served with the oracle answers (square side 6 at SM = SA/3 gives area 4; equilateral side 6 gives √3); the form without "của" is refused `UNGROUNDED_VALUE`. Recorded only, because it is not a safety gap. |
| W3-A06: radical bound | genuine limit | `geometry/radical.py` | Keep the refusal |
| distance/angle/volume rows | measurement gap | this run | Independent /4 gold payloads plus an exact oracle |

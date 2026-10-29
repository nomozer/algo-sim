# Pre-freeze independent adversarial review — `NOT_READY`

Reviewer: new separate-context agent, read-only, offline (0 provider calls), on HEAD `1d44746d` (product `1262fbd5`),
compared with the previous product `9772ea37` and main `996f114b`. 203 own probes (147 negative, 56 control) × 3 routes
(Adapter /3 `a3`, planner route `pl`, Adapter /4 `a4`) × 3 versions, plus 6 spot mutations. Raw material:
`pre-freeze-review/` (`probes1.py`–`probes5.py`, `harness.py`, `mutate.py`, `out*_{head,9772ea37,996f114b}.*`,
`served_neg_summary.txt`, `mutation-spot.out`, `inventory_list.txt`). The implementer re-reproduced N1–N3:
`pre-freeze-review/implementer-repro.py` → `implementer-repro.out`.

## Findings (all 34 served negatives at HEAD are served identically on 9772ea37 and main: pre-existing, unregistered)

| # | sev | repro | HEAD a3 / pl / a4 | root cause |
|---|---|---|---|---|
| N1 | MAJOR | control + distance goal `target:{solid_id:'s1', segment:'TA'}` (also `point`/`plane:'TBC'`, `line:'TC'`, `polygon:'TBC'`, `target.solid` s1 / `S.ABCD`) | **SERVED (4 = \|TA\| of s2)** / capability / `INVALID_MATH_GOAL` | S11 accepts a bare string for list operands; `scope_records` reads `'TA'` as one unowned label so S7/S8 skip it; Adapter /3 iterates the string per character and scopes with `mg.solid_id` only, ignoring `target.solid_id`/`target.solid` (`adapter3_simulation.py` measurement compile) |
| N2 | MAJOR | A3-DEV-02 (non-identity bindings) + midpoint `M` of SB in `pyr1`; goal `target:{solid_id:'pyr2', segment:['M','B']}` or containment `{container_ref:'pyr2', member_ref:'M'}` | **SERVED** / `BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY` ×2 | Bridge raises the capability refusal before `_kiem_pham_vi_tien_de` (S8), so the Adapter /3 legacy fallback (E1c) never gets constructed-point ownership; the coverage claim "Bridge S8 on E1b" did not hold for E1c |
| N3 | MAJOR | kind-inapplicable fields: ratio/residual with `target.solid_id`/`target.solid`/`goal_type`/`parent`/`cut`/`denominator`; measurement with `parent_solid_id`/`numerator_solid_id`/`cut_solid_id` of another solid; `construct_object.derived_solid_id:'ghost'` | **SERVED** (several on all three routes) | S4 / D-D (no silent ignore) applied only to `solid_id` on ratio/residual and `parent_solid_id`/`target_solid_id` on simulation goals; inventory has no per-kind applicability for MathGoalSpec fields or `derived_solid_id` |
| N4 | MAJOR (borderline) | curved two-cone payload with `shared_vertices` `cone_main::Z` (no such vertex), containment member `cone_main::Z`, `cone_main::S ≡ cone_b::T`, relation quote absent from text | **SERVED** (polyhedral routes refuse `UNKNOWN_VERTEX_REF`) | schema checks qualified namespaces, not label existence; `_check_qualified_refs` and relation reading never run on the curved route |
| N5 | MINOR | unknown open `target` keys (`solid_b`, `solids`) | silently ignored, SERVED ×3 | `MathGoalSpec.target` is an open dict without a closed key set |
| N6 | MINOR | census: AST misses keys read via `partial(_operand, t)` / `set(t)=={…}` | `target.plane1/plane2` absent from the inventory; comment "no route reads them" false (Bridge reads them) | census walker blind to indirect reads; product guard still covers the keys (probe refused ×3) |
| N7 | note (regression vs main since 9772ea37) | `highlight_geometry.target_solid_id` = declared derived solid, `target_refs:['M']` | a3 `UNKNOWN_SOLID_ID` (main serves) | Adapter /3 legacy `resolve_ref` scopes by primary solids only |

## Clean

F1–F7 independently rebuilt (24 probes) and closed, incl. the exact F7 class on hyphenated ids; hyphenated ids of many
shapes keep outcomes; every relation kind and simulation-goal kind contradiction refused; 0 internal errors at HEAD
(8–10 on the baselines); 6/6 spot mutations killed; product diff limited to the three allowed files; no hardcoded case
data; no `Co-Authored-By` trailer.

## Consequence

Per Owner GO §12: `NOT_READY`. No freeze, no Wave 3 replay, no T0–T2, no Full T3 for this product; no product change
after the review.

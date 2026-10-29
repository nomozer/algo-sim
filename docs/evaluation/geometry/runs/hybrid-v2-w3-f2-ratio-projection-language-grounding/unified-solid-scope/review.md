# Independent exhaustive scope audit — verdict NOT_READY

Reviewer: new separate-context agent with no implementer context, read-only, offline (0 provider calls). Reviewed
HEAD `7c3d202d` (candidate `cd8de398`, product `9772ea37`) against main `996f114b` and pre-change `3cdba8eb`.
It built 117 of its own probes (82 negative, 32 control, 3 info) plus 5 plane-pair probes, starting from committed
fixtures, and ran each on Adapter /3 (A3), the planner route (PL) and Adapter /4 (A4), on the candidate and on main.
Raw material: `review/` (`harness.py`, `probes.py`, `probes_plane_pair.py`, `baseline.py`, `probes-candidate.out`,
`probes-main.out`, `probes-3cdba8eb-C1.out`, `diff-main-vs-candidate.txt`, `pytest-targeted.out`). The implementer
re-reproduced F1–F3 independently: `review/implementer-repro.py` → `review/implementer-repro.out`.

## Findings

| # | sev | repro | candidate | main | root cause |
|---|---|---|---|---|---|
| F1 | **MAJOR, regression of `9772ea37`** | valid control with ids `pyr-1`/`pyr-2` and a qualified `pyr-1::S` operand | A3, PL, A4 REFUSED `UNKNOWN_SOLID_ID` (false refusal) | SERVED ×3 | `typed_fact_next.py::_qualified_refs` splits every string on `-` to read edge keys, but `IdentifierStr` and `_QUALIFIED_REF_RE` allow `-` in ids; `pyr-1::S` reads as namespace `1`. Committed corpus has 0 hyphenated ids, so no test caught it. |
| F2 | MAJOR (pre-existing) | `perpendicular` relation with `solid_id`/`solid_a` = s2 and operands owned only by s1 (qualified or not); `shared_vertices` with sides s2 and pairs `s1::A` | A3 REFUSED; PL, A4 SERVED (some variants served on all three) | SERVED | `_validate_declared_solid_scope` checks only existence for relation kinds other than `shared_faces`/`coordinate_frame` and scopes their refs with `None`; Bridge drops the relation's `solid_id`. |
| F3 | MAJOR (pre-existing) | `highlight_geometry` with `target_solid_id` s2 and refs of s1; `construct_plane_section`/`construct_derived_solid` whose `target_solid_id` is another declared solid than the section's; `construct_object` with `parent_solid_id` ≠ `target_solid_id` | PL, A4 (and A3 for some) SERVED | SERVED | R3 covers only derived-solid parent vs section; simulation-goal refs are scoped with `None`; highlight is a no-fact goal on the Bridge. |
| F4 | MAJOR (pre-existing, curved) | two cones: derived solid `apex_ref` = the other cone's apex; contradicting `perpendicular` relation; highlight scoped to one cone with refs of the other | A3 SERVED | SERVED | Bridge ownership validator covers premises and measurement goals only; the curved route ignores `apex_ref` and silently drops unresolved highlight refs. |
| F5 | MINOR (pre-existing) | curved `target.solid` given as notation alias; curved `target.section_id` 5 / unknown; polyhedral `target.point` a dict | `ADAPTER_INTERNAL_ERROR` | same | untyped failures on the curved route and Adapter /3 operand parsing |
| F6 | MINOR | area goal `target.solid` = valid notation alias on A4; D2 operand keys omit `plane1`/`plane2` (unreachable today) | wrong code `UNKNOWN_SOLID_ID` on A4 | same | Bridge area branch is id-only; key list incomplete |
| note | — | two solids sharing base labels, all premises unscoped | `AMBIGUOUS_REFERENCE` on all routes | SERVED | from the earlier recovery wave (`3cdba8eb` behaves the same) |

## Clean

Every census finding (review #1–#6, NEW-1..3) stays closed; foreign/contradicting scope in premise `solid_id` /
`args.solid`, section refs and `named_intersections`, frame anchors, `shared_faces` sides (incl. qualified swap),
measurement `solid_id`/`target.solid`/`target.solid_id`/`section_id`, ratio/residual `solid_id`, wrong-parent derived
solids (polyhedral and curved) all refuse. Aliases (`D.ABC`, `D1.ABC`, `S.ABCD`), derived solids (`s_top`,
`cone_upper`), absent scope and valid multi-solid relations are served. Semantic refusals stay terminal on Adapter /3.
Product diff limited to `typed_fact_next.py`, `typed_fact_next_bridge.py`, `adapter3_simulation.py`; no hardcoded
case data; cache 130. Freeze/T3: receipt fields, freeze hash before/after, log hash and size all verified; no product
drift after `cd8de398`; evidence diff since `3cdba8eb` is additions only plus `EVALUATION_CANDIDATE.json`.

## Consequence

F1 is a false refusal introduced by this task; F2–F4 show the census did not list every scope-bearing slot (relation
kinds beyond two, simulation-goal targets/refs, derived-solid `apex_ref`). Per Owner GO §14: no READY claim, STOP,
checkpoint, `NOT_READY`. No product change was made after this review; Full T3 was not repeated.

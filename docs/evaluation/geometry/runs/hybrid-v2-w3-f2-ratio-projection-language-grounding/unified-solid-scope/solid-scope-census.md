# Solid-scope entry-point and field census

Owner GO `HYBRID_V2_W3_F2_UNIFIED_SOLID_SCOPE_VALIDATION`, 2026-10-29, read-only, before any product edit.
Baseline: main = origin/main = remote `996f114b`; research HEAD `3cdba8eb` (product `c4d7b759`), clean tree; main
and candidate `55bdd332` are ancestors. Machine table: `solid-scope-entrypoint-matrix.json`. Probes (0 provider
calls): `census-probe-output.txt` from `tools/census_probe.py` and `tools/census_payloads.py`.

## Method

1. Fields: every attribute of the TypedFactNext models (`typed_fact_next.py`: `SolidSpec`, `PremiseSpec` with the
   `_ARGS_LOI` shape table, `/1` and `/2` sections, `GeometricRelationSpec`, `SimulationGoalSpec`, `MathGoalSpec`,
   `TypedFactNextPayload`) whose meaning is a solid id, a solid name or a solid-qualified vertex. Non-solid fields
   (`section_id`, `goal_id`, `frame_id`, values, quotes) are not solid references and get no scope rule.
2. Entry points: every caller of `parse_typed_fact_next[_v2]`, `bridge[_v2]`, `run_typed_fact_next_route`,
   `run_typed_fact_next_v2_route`, `run_typed_fact_next_planner_route`, `convert_v1_to_v2`, then the dispatch inside
   `_Adapter3Compiler.run` (curved vs polyhedral) and each `except` that can turn a refusal into a different path.
3. Reads: for each route, the payload fields it actually reads (the curved route reads solids, sections, simulation
   goals and math goals only — premises and relations are never read).
4. Data: 1234 committed TypedFactNext payloads in 28 files: `premise.solid_id` 4411, `premise.args.solid` 7,
   `sim.parent_solid_id` 114, `measurement.solid_id` 266, `target.solid` 17, `target.section_id` 526,
   `target.solid_id` 0, ratio/residual `solid_id` **0**, relation `solid_id` 11 / `solid_a` 6 / `solid_b` 6; 13 curved
   payloads, one with premises.

## Structural conclusion

Every TypedFactNext entry point parses through `TypedFactNextPayload._validate_payload` (E0) before it dispatches —
including the curved route, which no other check reaches. E0 already enforces cross-reference existence for section
targets, simulation targets and ratio/residual operands, with the `UNKNOWN_SOLID_ID` code. It is therefore the one
place where a declared-scope policy runs before every capability refusal, fallback and route dispatch (I7) without
any route having to remember to call it. Vertex ownership that depends on constructed points cannot be decided from
declarations alone; its existing authority is the Bridge `_kiem_pham_vi_tien_de` (owner propagation through
constructed outputs), which Adapter /4, the planner route and the Adapter /3 gate already run, and which the curved
route does not.

## Findings (all reproduced in `census-probe-output.txt`)

| id | sev | path | observed |
|---|---|---|---|
| review #1 | MAJOR | E2 distance/angle goal `solid_id` s2/foreign | SERVED |
| review #2 | MAJOR | E1a curved goal / premise / relation scope | SERVED |
| review #3 | MAJOR | ratio/residual goal `solid_id` foreign | SERVED |
| review #4 | MINOR | E2 relation with foreign solid | SERVED |
| review #5 | MINOR | E2 volume goal on declared derived solid | wrong `UNKNOWN_SOLID_ID` |
| review #6 | MINOR | nested `target.solid_id` contradicting scope | SERVED (E1, E2) |
| NEW-1 | MAJOR | `construct_derived_solid.parent_solid_id` = another declared solid (demo1) | SERVED |
| NEW-2 | MAJOR | E2 `shared_faces` face not of `solid_b`; `coordinate_frame` anchors of another solid | SERVED |
| NEW-3 | MINOR | E1a foreign `parent_solid_id` / `target.solid` | `ADAPTER_INTERNAL_ERROR` (crash, not a data refusal) |

Checked and refused already: foreign namespace in `highlight_geometry.target_refs`, premise scoped s1 with a
qualified `s2::A` operand (E1, E2), polyhedral foreign `parent_solid_id`.

## Locked scope of this repair

In: E0 schema-level declared-scope policy; Bridge goal-operand ownership; Adapter /3 curved dispatch; removal of the
now-redundant Bridge goal check that misjudges derived solids. Out (unchanged): Registry, Planner, engine/kernel,
radical, Adapter /4 code, Scene3D/UI, default routing, TypedFact (route D) contract, any new capability (a derived-
solid volume goal on the Bridge stays a capability refusal; a notation `target.solid` on the Bridge stays a
capability refusal — neither is served wrongly, Adapter /3 serves both).

Known limitation kept: the curved route still does not use premises/relations to build geometry (its data come from
`SolidSpec` radius/height); after this repair their scope is validated, but their content is not consumed. That is a
capability question, not a scope fail-open.

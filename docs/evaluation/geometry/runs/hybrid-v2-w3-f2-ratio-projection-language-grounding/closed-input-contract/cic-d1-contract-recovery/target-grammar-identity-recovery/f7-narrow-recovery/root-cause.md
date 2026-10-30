# F7 root cause and impact report: read-only, before any product edit

Owner GO `W3-F2 F7 NARROW RECOVERY & FINAL SAFETY PREPARATION`, decision D1, 2026-10-30. Research HEAD `1b1a9ed2`.
0 provider calls.

## Reproduction

`prism-f7-{main,pre,head}.json` show `ADAPTER_INTERNAL_ERROR`, `KeyError 'ask2'` on `main` `996f114b`, on pre-CIC
`5e44d5da` and on `5c4b743f`. I reproduced it again at `1b1a9ed2` using the scratch traceback probe. The failing
frame is:

```
_Adapter3Compiler.run  -> _compute_certified_math_goals  (adapter3_simulation.py:1784)  kq_var = hoi[cid]
```

## Root cause

The owner is `backend/app/ai/adapter3_simulation.py::_Adapter3Compiler._compile_derived_solids_and_goals`.

1. For every `measurement` goal, the function allocates `cid` and stores `math_call_ids[goal_id] = cid` (lines 1163–1164).
2. It then dispatches on `goal_type`, but only for `volume`, `distance`, `area` and `angle`.
3. `radius` and `lateral_area` are registered goal types (`GOAL_TARGET_ALTERNATIVES`), but they have no branch and no
   `else`. So no `ask_*` call is emitted, yet the id stays registered.
4. `_Dung.bien_dich()` builds `hoi` only from the emitted calls. `_compute_certified_math_goals` then looks up
   `hoi[cid]` for an id that has no call, which raises `KeyError`.
5. The run boundary in `run_typed_fact_next_route` records that `KeyError` as `ADAPTER_INTERNAL_ERROR`.

**Classification:** an internal invariant failure caused by an incomplete dispatch, not invalid input. The input is
schema-valid and registered.

**Capability:** unsupported. Neither the Registry nor the Planner has a polyhedral radius or lateral-area question.
Contract §5 states that "schema validity does not promise route capability".

**Why a3 reached the gap:** on the Bridge routes (`pl`, `a4`) the same inputs are refused as the typed
`BRIDGE_UNSUPPORTED_MEASUREMENT`. On a3, `_shared_source_gate` treats that code as a legacy capability gap and
continues into the Adapter /3 compiler. The compiler then has no mapping either.

## Impact inventory (scratch probes; frozen into `cases.json`)

| input | a3 at HEAD | after fix (preregistered) |
|---|---|---|
| prism `radius` / `lateral_area`: `{solid}`, notation, goal-level `solid_id` (8 matrix cells) | `ADAPTER_INTERNAL_ERROR` | `BRIDGE_UNSUPPORTED_MEASUREMENT` |
| pyramid `radius {solid}`, `radius {section_id}`, `lateral_area {solid}` | `ADAPTER_INTERNAL_ERROR` (not in the earlier matrix) | same |
| a served multi-goal payload with an appended `radius` / `lateral_area` | `ADAPTER_INTERNAL_ERROR` | whole payload refused, same code |
| polyhedral `area {solid}` | `INVALID_MATH_GOAL` (typed, pre-existing) | **unchanged**, recorded limitation L-AREA |
| curved `radius` / `lateral_area` / `volume` | SERVED by `_run_curved_route` (separate path) | unchanged |
| distance / angle / volume / section-area controls | SERVED | unchanged |

Other `hoi[...]` reads were checked: line 1736 is guarded by `parent_ask_call`, line 3173 iterates over emitted calls,
and line 3206 is guarded by `if cid in hoi`. Curved solids never reach this compiler (`run()` routes any non-prism or
non-pyramid payload to `_run_curved_route`).

## Repair decision

The repair adds one terminal `else` to the existing `goal_type` dispatch. It raises the typed capability refusal
`BRIDGE_UNSUPPORTED_MEASUREMENT` with the goal id, before the id is ever read:
- **One code on every route.** It is the code `pl` and `a4` already return for the same inputs.
- **Already classified.** `hybrid_preview._NHOM` lists it as `capability_gap`.
- **Terminal.** Fallback is only decided at the source gate, before this compiler, so the refusal ends the route.

Scope of the change:
- One module, `adapter3_simulation.py`. It is one of the three originally authorized modules, so the scope does not widen.
- No Registry, Planner, kernel, schema, API or frontend change, and no new capability.
- No `except` is added. The boundary still records real internal faults as `ADAPTER_INTERNAL_ERROR`; a planted-`KeyError` test guards this.

Disclosed ordering effect: the refusal occurs during goal compilation. That is after the schema, S8 ownership, solids,
premises and derived sections, but before the engine's `kiem()` checks. A payload that combines an engine-level data
contradiction with an unsupported polyhedral `radius` therefore gets the capability code. `pl` and `a4` behave the same
way today.

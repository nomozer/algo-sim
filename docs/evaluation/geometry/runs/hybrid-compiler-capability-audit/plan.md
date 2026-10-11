# Implementation plan for design option B (only after approval)

This plan follows [`design.md`](design.md). It starts only after the user approves option B. Until then, nothing here is built.

## Slice 1: point→line distance by decomposition (B26)

1. **RED tests first** in `tests/geometry/test_hybrid_compiler_selection.py`:
   - mutants: auxiliary leaks into premises; auxiliary without a rule; label collision; negated goal;
   - grounding negatives: point not quoted, line not quoted, goal inside "nếu … thì".
   The strict xfail on B26 in the benchmark flips to failing when the gap closes, so the benchmark record is updated in the same commit.
2. **`planner.py`:**
   - a decomposition table with one row, `distance(point, line)` → `orthogonal_projection_line` + `ask_length`;
   - an auxiliary label from a reserved namespace;
   - a trace entry `goal → rule → calls`.
3. **Source gate (`registry.kiem_nguon`):** accept an auxiliary label only when the call came from a registered rule and its non-auxiliary operands are grounded in the goal's quote.
4. **Scene/trace:** check that the auxiliary foot is shown as an auxiliary object. The `function_route` presentation already draws projection feet; reuse that.
5. **Gates:**
   - the hybrid/function-route cluster;
   - the benchmark (B26 served in both evaluations, the other 29 unchanged);
   - the full backend in a clean worktree;
   - candidate refreeze in its own commit;
   - T3.

## Slice 2: anonymous derived operand (B27)

This slice needs its own approval, because it changes the Typed Facts schema and prompt and therefore the hash of B's extraction surface.

1. RED tests for the schema, grounding and the fake provider.
2. Extend `TypedFact` in `planner.py`. The provider schema is derived from it in `fact_extraction.build_request`, so B's surface hash changes; record that.
3. Map the placeholder through the existing `point_def` path. No new geometry.
4. Re-check A/B pilot readiness: the frozen token ceiling no longer matches, so pilot readiness stays NO-GO until it is re-registered.

## Out of plan

- B28 ("tâm" cue): this is a separate grounding decision, which needs a context-restricted cue list and negatives for "tâm đường tròn ngoại tiếp/nội tiếp".
- General search (option C).
- Live runs.

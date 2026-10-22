# TypedFactNext → Planner bridge — implementation plan

> Inline execution; gates in order; independent review before freeze. Owner brief "Backend Hybrid Architecture Integration,
> Session 1" (P0–P6) is the spec. LOCAL ONLY, no merge/push, `ALLOW_LIVE_AI=0`, `LLM_ONLY` / `flat` / Hybrid NO-GO /
> `CACHE_VERSION=127` unchanged. Backend + backend tests + architecture docs only. Sequential focused pytest; one Full T3 on
> the frozen candidate at the end.

**Goal:** one source-gated, planner-driven path for the polyhedral subset of TypedFactNext, with one new planner
capability (section vertices on stated cut edges + derived sub-solid) composed from existing trusted Registry functions,
and the two reported Source Gate / preview defects fixed at their real root causes.

**Non-goals (Session 1):** LLM extractor for TypedFactNext; curved solids on the planner; plane by equation / ratio from
apex; prism derived solids; changing Adapter /3 behaviour; any frontend change; product enablement.

## Gates

### G0 — audit (done)
`BACKEND_INTEGRATION_BASELINE_AUDIT.md`: refs, ancestry, component map, fragmentation, defects re-checked.

### G1 — target architecture and decision
`docs/architecture/HYBRID_BACKEND_TARGET_ARCHITECTURE.md` (+ architecture README row): layer responsibilities, bridge vs
contract change, decision `BRIDGE_FEASIBLE` for the polyhedral relation-plane subset with fail-closed bridge refusals for
the rest.

### G2 — P3 defects, RED first
1. `divide_segment` premise number: regression test RED on current code (`SOURCE_PREMISE_UNREAD` on "SM = 1/3 SA"), and a
   control that a number NOT read by the ratio equation still refuses ("SM = 1/3 SA, AB = 5" with no AB call).
   Fix: the ratio-equation reader that already solves t (`_ty_so_dung_nguon`) credits exactly the occurrences it read.
2. Preview dependency: regression test RED (route-B SERVED scene with group-event edges ⇒ `PREVIEW_DEPENDENCY_INVALID`),
   control that a genuine early dependency still fails. Fix: `_validate_scene` births objects from `event["objects"]`
   as the frontend timeline does.

### G3 — P2 planner slice: section vertices on stated cut edges + derived sub-solid
- TypedFact internal fields hidden from the provider schema (`SkipJsonSchema`): `plane_ref` (a section fact id) on
  `point_def intersect_line_plane` and on a derived `solid`; `cut_edges` on a relation-plane `section`. Provider schema and
  every frozen fingerprint byte-identical (existing fingerprint tests).
- Planner: section vertices resolved per stated cut edge by bounded candidate selection — reuse the plane's through-point
  when its producer lies on that edge (cost 0), reuse an identical intersection already planned (cost 0), a source-named
  intersection (cost 1), else a fresh `I…` (cost 1); plane reused from the existing derived-plane memo; derived pyramid
  over the cycle; budgets (`MAX_EFFECT_NEEDS`, `MAX_RESULT_FEET`, `MAX_CALLS`), cycle/dangling via existing ordering.
- Registry gate: one certificate rule; the cut clause "cắt (các cạnh) E₁, E₂… (lần lượt tại P₁, P₂…)" read by closed grammar
  bound to the declared plane, its solid's lateral edges, named points; derived-solid phrase "khối chóp đỉnh S cắt bởi (α)"
  closed grammar. Unread wording still refuses.
- Engine: each vertex on its edge with 0 < t ≤ 1, edge not contained in the plane, ≥ 3 distinct vertices; reused points
  re-verified; derived pyramid built in the root chart (existing composite path).
- Bridge `typed_fact_next → TypedFact` (pure translation, no inference) + `run_typed_fact_next_planner_route` reusing
  `run_fact_route`. Unsupported constructs refuse with typed `BRIDGE_UNSUPPORTED_*` codes.

### G4 — P4 development evaluation (`DEVELOPMENT_EVALUATION_NOT_BLIND`)
Generated variants (relabeling, clause/goal order, ratio inversion, value scaling, symbolic values, shared-label solids,
construction-only, contradictory / missing / degenerate / out-of-scope) checked against an independent closed-form oracle
and metamorphic relations; metrics per brief §P4; comparison with Adapter /3 and TypedFact route on comparable cases.
Sealed holdouts untouched.

### G5 — tests, review, commit, freeze, T3, handoff
Focused sequential pytest of affected modules; docs gate; independent whole-change review (fix BLOCKER/IMPORTANT);
explicit-file commits; freeze in a clean detached worktree; Full T3 there with raw logs; post-T3 freeze MATCH; deliverables
`PLANNER_COMPOSITION_EVALUATION.md`, `SOURCE_GATE_INTEGRATION_REPORT.md`, `BACKEND_SESSION1_HANDOFF.md`, receipts;
canonical doc sync. Stop after Session 1.

## Decisions

- Bridge, not new IR: TypedFactNext → existing `TypedFact` with schema-hidden internal fields keeps ONE planner, ONE gate,
  ONE engine path and the frozen provider surface.
- Composition is proved by the planner's own trace (choices, costs, reuse) and by metamorphic tests, not by naming.
- Adapter /3 is not modified; differences are measured, not hidden.

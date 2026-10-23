# PLANNER_COMPOSITION_EVALUATION — P4

Classification **`DEVELOPMENT_EVALUATION_NOT_BLIND`**. Inputs are authored TypedFactNext JSON + Vietnamese text generated
by one closed template family ([`evaluate.py`](evaluate.py)); this measures the planner / gate / engine path, **not**
natural-language extraction. 60 cases, offline, 0 provider calls, no sealed holdout read. Raw output:
[`planner-composition-evaluation.json`](planner-composition-evaluation.json) (per-case rows + aggregate).

## 1. What the planner now composes

For a relation-defined plane cutting a pyramid, the planner (`planner._dinh_cat_canh`, `_khoi_tren_thiet_dien`) solves
one typed need **SectionVertex(edge, plane)** per lateral edge and chooses, by cost, among:

| candidate | cost | effect already established by |
|---|---|---|
| `reuse_through_point` | 0 | the plane's through-point, whose validated producer (`midpoint` / `divide_segment`) lies on that edge |
| `reuse_intersection` | 0 | an identical `intersect_line_plane` already planned |
| `named_intersection` | 1 | a NEW `intersect_line_plane` labelled as the source names the cut ("lần lượt tại N, P") |
| `fresh_intersection` | 1 | a NEW `intersect_line_plane` with a collision-free `I…` label (hidden from the learner) |

An unstated edge admits only cost-0 reuse: the planner never asserts a cut the source did not state. The plane comes from
the existing relation-plane decompositions (`MAT_SONG_SONG` / `MAT_VUONG_DUONG`) and their memo, so ONE plane serves the
section, every vertex and the derived pyramid. A derived pyramid ("khối chóp đỉnh S cắt bởi (α)" or "khối chóp S.MNP")
is registered as a solid, so Wave 3A ratio / residual asks compose on it. Every choice is written to the plan trace
(`effect_resolution`, `need`, `selection`, `cost`, `candidates`); every vertex is re-verified by the engine
(`kiem_dinh_cat`: on the edge line and plane, not parallel, 0 < t ≤ 1).

**What this is, precisely (review round 1, IMPORTANT 3):** a **bounded, cost-ranked case analysis over typed
candidates**, not a search. For each edge the candidate set is enumerated from what the plan and source already establish
and the cheapest is taken; with today's inputs this is effectively deterministic (stated + named → named, stated → fresh,
otherwise reuse). The 7 distinct patterns observed (§3) are the input configurations {∥ plane, ⊥ line} × {3, 4 lateral
edges} × {named, unnamed}; selections over the served cases: 77 `named_intersection`, 14 `fresh_intersection`, 40
`reuse_through_point` (always the through-point M on SA). `reuse_intersection` is never selected by the generated family —
it is exercised only by `test_an_identical_intersection_already_planned_is_reused_at_cost_zero`. What the slice does
demonstrate is composition across trusted functions inside ONE planner: relation-plane decomposition (memoised) →
per-edge intersections → derived pyramid registered as a solid → Wave 3A ratio / residual asks on it, each step a
Registry function re-checked by the gate and the engine. It is not a general goal-directed search over effects.

## 2. Results (bridge route: TypedFactNext → bridge → planner → Source Gate → engine)

| metric | value |
|---|---|
| goal coverage (expected-served) | **40/49**; the 9 not covered are all `IR_MEMORY_BUDGET_EXCEEDED` (quadrilateral base, plane ⊥ SA, residual) — a typed resource refusal |
| exact mathematical correctness | **34/34** served cases with numeric goals equal the independent closed-form oracle (V = ⅓·S·h, ratio t³ for a cut ∥ base / ⊥ SA at SM/SA = t) |
| wrong-served | **0** |
| refusal correctness | **11/11** (6 invalid problems + 5 bridge-scope constructs, each with the expected code family) |
| Scene3D structural validity | **40/40** (operator-preview dependency/birth/metric validator) |
| fresh section-vertex labels (`I…`) in learner text | **0** (scope: only the labels this slice introduces) |
| visible duplicate operand planes (`derived_*_plane`) | **0** (each cut's IR operand plane is marked `non_visual`) |
| planner's point-built plane name ("(MHH1)") or "mặt phẳng qua …" in learner text | **0** (review round 2; the source name (α) is used; the plane object's own notation is not counted) |
| served scenes showing relation-plane auxiliary points `H`, `H1` by label | **40/40** — **pre-existing** route B policy: a plain relation-plane section with no cut certificate shows them identically; not changed here |
| quotes of every planned call found verbatim in the source | **40/40** |
| planner-selected operations per served case | mean 5.92 (min 5, max 8) |
| dependency DAG depth (longest producer chain) | 4–5 |
| vertex needs solved by reuse (cost 0) | 40/131 — always the through-point M on SA; plane constructions per served case: exactly 1 |
| planner calls per plan | mean 14.15 (11–17) |
| route time (bridge → Scene3D) | p50 0.029 s, max 0.094 s (local CPU, single process) |

Metamorphic relations (all **hold**): relabeling invariance; premise-order invariance; goal-order invariance; ratio
inversion gives the reciprocal; scaling dimensions by k leaves the ratio and multiplies the residual by k³; a plane ∥ (base)
and a plane ⊥ SA (SA ⊥ base) give the same answers.

Case families: base 36 (6 shapes/sizes incl. equilateral, square, rectangle, right triangle; t ∈ {1/2, 1/3, 2/3}; ∥ and ⊥
planes; symbolic `a` and numeric) · metamorphic 7 · construction-only with unnamed vertices 6 · invalid 6 (contradictory
length, missing height, edge parallel to the plane, swapped cut names, ratio whose operand order the source does not state,
contradictory unread condition) · bridge scope 5 (shared label with distinct identity, plane equation, curved solid, cut
edges absent from the payload, open cycle).

## 3. Comparison with Adapter /3 on the same cases

Adapter /3 received each payload in **its own** convention (`cut_edges` omitted ⇒ every lateral edge; see §4).

| | bridge route | Adapter /3 |
|---|---|---|
| served / 60 | 40 | 55 |
| exact when served (comparable numeric goals) | 34/34 | 43/43 |
| served an **invalid** problem | 0 | **3**: swapped cut names, ratio whose order the source never states, an unread contradictory condition ("sao cho NP = BC") |
| crash | 0 | **1** `AssertionError` (plane equation on a pyramid, `_compile_derived_sections`) instead of a coded refusal |
| bridge-scope constructs | refused (typed) | 3 served legitimately (shared-label identity, payload without cut edges, unstated edge) |

Composition patterns produced by the bridge route (from the JSON): ∥ plane with 3 or 4 vertex needs and named or fresh
intersections (4 patterns), ⊥ line with 3 or 4 needs and named or fresh intersections (3 patterns).

## 4. Contract finding: `cut_edges` means two different things

The TypedFactNext contract does not define `DerivedPlaneSectionSpec.cut_edges`. The bridge reads it as **the edges the
source states are cut** ("cắt SB, SC, SD"; SA is reached through M). Adapter /3 reads it as **the complete section cycle**
and does **not** check closure: given the bridge's payload for a quadrilateral base it builds the tetrahedron S.NPQ as
"the derived solid" and serves exact numbers for it (ratio 1/16 and residual 5a³/16 where the oracle is 1/8 and 7a³/24) —
**18 such cases** ("same_payload_wrong_served" in the JSON). Recommendation for Session 2: pin the meaning in the contract
and make Adapter /3 verify that its cycle closes the section (not changed here: Adapter /3 is out of this slice).

## 5. Limits

- Development evaluation, not blind; one template family; authored JSON — no claim about natural-language E2E.
- Pyramids only for derived solids; relation planes ∥ plane / ⊥ line (the two-lines variant is not wired to the cut
  clause); quadrilateral base + ⊥ line + residual exceeds the IR budget of 32 declarations (typed refusal).
- The oracle covers SA ⊥ base configurations; other altitude configurations were not generated.
- SwiftShader / browser rendering was not run (backend-only campaign); Scene3D validity is structural.
- Section-vertex plans whose teaching expansion alone exceeds the IR budget are built unexpanded (recorded as
  `formation_budget` in the trace); all other route B plans keep `main`'s behaviour (`ENGINE_EXECUTION_FAILED`).

# Hybrid simulation capability and semantic safety audit

Status: `HYBRID_SIMULATION_AUDIT_AWAITING_DECISION`.

**Scope and limits of this run**
- LOCAL, on branch `research/hybrid-simulation-capability-audit` from `main` = `origin/main` = `a6e27a78`. The handoff state was verified:
  - 27 Registry functions;
  - `CACHE_VERSION` 125;
  - candidate `dda3a884…` (product `62f0b18e`);
  - default `LLM_ONLY`.
- No product code changed. LIVE GEMINI CALLS = 0.
- Executable evidence: `backend/tests/geometry/test_hybrid_simulation_capability_probes.py` (27 passed, 5 strict xfail).

**Evidence classes used** — never pooled into one accuracy figure:

| Class | Used here |
|---|---|
| Unit / IR tests of the shared engine | existing tests, cited by file count |
| Offline typed-fact probes through the Hybrid route | this run |
| Fake-provider pipeline | the 30-case benchmark of earlier runs |
| Real Gemini | **none** |
| Browser / human visual review of Hybrid scenes | **none** |

## 1. Hybrid data-flow audit (what each layer actually does)

| Layer | Code | Actual responsibility | Not done here |
|---|---|---|---|
| AI extraction | `app/ai/fact_extraction.py` | structured output `TypedFact[]` (11 kinds, roles premise/prove/condition/question, `negated`, `ambiguous`, quotes) | no geometry, no function choice |
| Planner (inside the compiler) | `geometry_functions/planner.py` | one fact → one Registry call by kind and operand type; definition expansion depth 1; **one** goal decomposition rule (distance point→line, B26); trace | no search, no alternatives, no construction goals |
| Source grounding | `registry.kiem_nguon` (+ `_kiem_phu`) | quote ⊂ text, labels ⊂ text, clause role, negation, predicate cue, plane/role/value binding, construction binding | role is read at the **start** of the quote (§4, Critical) |
| Engine | `geometry_functions/engine.py` | layout chart (affine + Gram), fixed-point dependency resolution, exact re-check of **every** fact (`INCONSISTENT_FACTS`), IR emission | emits only points, operand lines/planes, solids, polygons, measures |
| IR + interpreter + kernel | `semantic_program/*`, `geometry/*` | exact ℚ(√) execution; **also** sections, plane–plane intersection, curved solids, translate, divide_segment, plane ⊥ line | the Hybrid engine never emits these |
| Scene3D | `semantic_program/scene3d.py`, `app/ai/function_route.py` | scene JSON: typed objects, events, formation, `occludes_edges`, projection witness | camera-dependent hidden lines happen in the frontend renderer; route D is not wired to the UI |

There is one canonical semantic state: the Typed Facts become Registry calls, the calls become engine points and IR, and provenance flows through traces. There is no second fact graph, and none is needed for what the evidence shows.

## 2. Inventory of the 27 Geometry Functions

How to read the columns:
- **Planner:** the TypedFact kind that reaches the function. All 27 are reachable.
- **Verified by:**
  - `TF` = `test_text_to_geometry_functions.py`
  - `LX` = `test_geometry_library_expansion.py` (independent oracle)
  - `HS` = `test_hybrid_compiler_selection.py`
  - `BM` = the 30-case benchmark
  - `GD` = `test_hybrid_goal_decomposition.py`
- **Scene** = what reaches Scene3D.

| # | Function | Kind | Mathematical role, in → out | Preconditions / limits | Planner | Verified by | Scene |
|---|---|---|---|---|---|---|---|
| 1 | `regular_polygon` | fact | vertices (+side) → regular base | k ∈ {3, 4, 6} chart | polygon_shape; regular/cube definitions | TF HS BM | base face of the solid |
| 2 | `rectangle` | fact | vertices → rectangle base | "chữ nhật" cue | polygon_shape; cuboid | TF HS | base face |
| 3 | `right_angle` | fact | vertex, rays → right angle | — | right_angle | TF | constraint only |
| 4 | `segment_length` | fact | segment, value → length | value anchored to the segment label | length (segment / lateral / edge) | TF BM | constraint only |
| 5 | `perpendicular_line_plane` | fact | line ⊥ plane → apex placement | foot on the plane | perpendicular (line, plane) | TF BM | constraint (apex) |
| 6 | `altitude` | fact | apex, foot, solid → height foot | foot in base | altitude | TF HS | constraint |
| 7 | `orthogonal_projection` | fact | point, plane, image | image ≠ point; forward or inverse | projection (plane) | LX BM | foot point + witness |
| 8 | `orthogonal_projection_line` | construct | point, line → foot | 2 wordings only (§5) | projection (line); goal decomposition | LX BM GD | foot point + witness |
| 9 | `intersect_line_line` | construct | 2 lines → point | coplanar, not parallel or skew | point_def | LX BM | point + operand lines |
| 10 | `intersect_line_plane` | construct | line, plane → point | not parallel | point_def | LX BM | point + operand line/plane |
| 11 | `perpendicular_lines` | fact | line ⊥ line | — | perpendicular (line, line) | TF | constraint only |
| 12 | `equal_length` | fact | segment = segment | — | equal_lengths | TF | constraint only |
| 13 | `height` | fact | solid, value → height | foot unknown ⇒ apex undetermined | length (height) | TF BM | constraint |
| 14 | `face_perpendicular_base` | fact | face ⊥ base → derived foot | face = edge of base + apex | perpendicular (plane, plane) | TF | constraint |
| 15 | `midpoint` | construct | segment → point | — | point_def | TF BM | point |
| 16 | `centroid` | construct | polygon → point | **triangle only** (`UNSUPPORTED_CENTROID`) | point_def | TF; probe P05/P05b | point |
| 17 | `pyramid` | construct | apex, base → solid | — | solid | TF BM | mesh + edges |
| 18 | `regular_pyramid` | construct | apex, base → solid | regular base declared; centre named O/I/O1/O2 (exhaustion crash, §4) | solid (regular) | TF BM | mesh |
| 19 | `prism` | construct | base, top, right → solid | right or regular | solid | TF BM | mesh |
| 20 | `ask_volume` | ask | solid → V | figure unique | question | BM | readout |
| 21 | `ask_length` | ask | segment → length | — | question | BM GD | readout |
| 22 | `ask_distance_point_plane` | ask | point, plane → d | **no question check** (§4) | question | BM | readout |
| 23 | `ask_distance_lines` | ask | 2 lines → d | skew/parallel | question | TF | readout |
| 24 | `ask_angle_line_plane` | ask | → cos² | — | question | BM | readout |
| 25 | `ask_angle_plane_plane` | ask | → cos² | — | question | TF | readout |
| 26 | `ask_area` | ask | polygon → S | polygon given by named vertices | question | TF | polygon + readout |
| 27 | `unsupported` | escape | reason → `OUT_OF_SCOPE` | — | unsupported | BM | none |

- **What this does not claim:**
  - "Constraint only" means the function shapes or checks the layout and emits no object of its own. No dedicated relation marker (e.g. a right-angle marker for `perpendicular_lines`) was verified in this audit.
  - No Hybrid scene has been rendered in the product UI or reviewed by a human.
- **The two kernel functions with no consumer:** `plane_through_point_parallel_to` and `line_through_point_parallel_to` exist in `geometry/kernel.py`. Neither has an IR expression and both have one test. They count as primitives available to the kernel, not as Hybrid capabilities.

## 3. Simulation coverage matrix (Hybrid route)

Classification: IMPLEMENTED_AND_VERIFIED · IMPLEMENTED_PARTIAL · COMPOSABLE_WITH_EXISTING_FUNCTIONS · BLOCKED_BY_PLANNER · BLOCKED_BY_COMPILER_OR_SEMANTICS · MISSING_GEOMETRY_PRIMITIVE · BLOCKED_BY_RENDERER · UNSUPPORTED.

The column **Shared engine/IR** says whether the layer *under* the Hybrid Registry already builds the object. This is what separates *"the engine cannot build it"* from *"the engine can, but Hybrid has no way to ask"*.

| Group | Simulation request | Hybrid route | Shared engine/IR | Class | Evidence |
|---|---|---|---|---|---|
| 1 Points/lines/planes | named point by midpoint / intersection / projection | served, scene point | yes | IMPLEMENTED_AND_VERIFIED | P01 P03 P11, LX |
| 1 | draw a line or segment through named points as an object ("vẽ đường thẳng AM") | no fact kind → `OUT_OF_SCOPE` | `construct_line` / `construct_segment` | BLOCKED_BY_COMPILER_OR_SEMANTICS | P02 |
| 1 | ray | not representable | not in IR | UNSUPPORTED | — |
| 2 Relations | perpendicular line–plane / line–line, face ⊥ base | served as constraints, re-checked | yes | IMPLEMENTED_AND_VERIFIED | TF, BM |
| 2 | parallel line / plane relation as given | no fact kind, no Registry function | kernel primitives unused; composable in IR via `translate` | BLOCKED_BY_COMPILER_OR_SEMANTICS | §2 |
| 2 | incidence / intersection of lines and planes | served (unique intersection); parallel → `PARALLEL_NO_INTERSECTION` | yes | IMPLEMENTED_AND_VERIFIED | P11 P17 LX |
| 3 Derived and auxiliary | midpoint, centroid of a triangle, projection onto line/plane | served | yes | IMPLEMENTED_AND_VERIFIED (narrow wording, §5) | P01 P05 P03 E01 E04 |
| 3 | centroid of a polygon with more than 3 vertices | `UNSUPPORTED_CENTROID` | arithmetic exists (divide_segment) | MISSING_GEOMETRY_PRIMITIVE (Hybrid engine rule) | P05b |
| 3 | point dividing a segment in a ratio ("SM = 2MC") | no fact kind | `divide_segment` | BLOCKED_BY_COMPILER_OR_SEMANTICS | §2 |
| 3 | unnamed auxiliary objects | only the foot for distance point→line (B26) | yes | IMPLEMENTED_PARTIAL / BLOCKED_BY_PLANNER | GD, B27 |
| 4 Solids | pyramid, regular pyramid, prism, cube, cuboid, tetrahedron | served | yes | IMPLEMENTED_AND_VERIFIED | BM, HS |
| 4 | other polyhedra (non-convex, oblique prism by angle) | not representable | non-convex volume in kernel | BLOCKED_BY_COMPILER_OR_SEMANTICS | product_capability |
| 5 Sections | **section of a polyhedron by a plane** | no fact kind/function → `OUT_OF_SCOPE` | **`construct_section` executes and renders** (probe) | **BLOCKED_BY_COMPILER_OR_SEMANTICS** | P09 + `test_shared_engine_builds_a_section_hybrid_cannot_request` |
| 5 | intersection line of two planes (giao tuyến) | not representable | `intersect_plane_plane` (11 test files) | BLOCKED_BY_COMPILER_OR_SEMANTICS | §2 |
| 5 | point = line ∩ plane | served | yes | IMPLEMENTED_AND_VERIFIED | P11, B09 |
| 6 Reusable constructions | plane through a point parallel to a plane; line through a point parallel to a line | no way in | kernel only; IR via `translate` | COMPOSABLE_WITH_EXISTING_FUNCTIONS (IR) / BLOCKED (Hybrid) | §2 |
| 6 | plane through a point perpendicular to a line | no way in | `plane_perpendicular_to_line` | BLOCKED_BY_COMPILER_OR_SEMANTICS | §2 |
| 7 Curved | sphere, cylinder, cone, curved sections | no way in | `construct_curved_solid`; product `foundation_only` (model unmeasured) | BLOCKED_BY_COMPILER_OR_SEMANTICS | product_capability |
| 7 | solids of revolution, composite (CSG) | — | — | UNSUPPORTED (product decision) | product_capability |
| 8 Constraint constructions | apex from ⊥ + length, from altitude + foot, from regular base + lateral edge | served | yes | IMPLEMENTED_AND_VERIFIED | BM B01 B02 B30 |
| 8 | apex from a **given angle** ("góc giữa SC và đáy bằng 60°") | no fact kind | no "place from angle" construction in IR | MISSING_GEOMETRY_PRIMITIVE + semantics | B24 |
| 8 | height without foot | refused (`FIGURE_NOT_UNIQUE` / `UNDERDETERMINED_POINT`), never sampled | — | IMPLEMENTED_AND_VERIFIED (fail-closed) | B21 B22 |
| 9 Topology / order | declared solid topology, operand-before-result order, construction events | topology and witness checked in tests; trace order (points → solid → measure) observed in a probe (B09), not asserted by a test | yes | IMPLEMENTED_PARTIAL | test_projection_scene_topology; probe |
| 9 | hidden edges by camera, animation in the product UI | not exercised for Hybrid (route not wired) | product renderer | BLOCKED_BY_RENDERER (wiring), not a renderer defect | §6 |

## 4. Semantic and grounding safety

| Risk | Status | Evidence |
|---|---|---|
| **The AI types a conditional or proof goal as a premise, and the quote carries its own "Nếu … thì" / "Chứng minh"** | **CRITICAL, NEW.** The shared gate reads the clause role *before* the quote, so the clause is used as a given. With no ⊥ given the apex is undetermined (control: `UNDERDETERMINED_POINT`); with "Nếu SA ⊥ (ABCD) thì SC = 5" typed as a premise, SC = √17 is **served** (the clause itself says 5). Same result for "Chứng minh rằng SA ⊥ (ABCD)" and in route A (shared `kiem_nguon`). A quote that starts after "Nếu" is refused correctly. The default `LLM_ONLY` route does not use this gate, so no user is affected today | 3 strict xfail tests; `ISSUE-ARCH-GATE-CLAUSE-ROLE-INSIDE-QUOTE` |
| `ask_*` answers a clause that does not ask (e.g. "Hãy chỉ ra rằng khoảng cách … bằng 3") | OPEN (known) | strict xfail; `ISSUE-ARCH-ASK-GATE-NO-QUESTION-CHECK` |
| Negated premise | refused `NEGATED_CLAUSE` | P21 |
| Proof goal with `role: prove` | checked as a configuration observation only; never presented as proven | P19; `can_present_as_proven: False` |
| Wrong object bound (quote says A, facts say B) | refused `ROLE_NOT_IN_QUOTE` | P23 |
| LINE vs SEGMENT | lines served (P15: I outside segment AB, correct for the line reading). The "đoạn thẳng" wording fails closed (P16). There are no segment semantics, and the convention is undecided | `ISSUE-ARCH-LINE-SEGMENT-SEMANTIC-DISTINCTION` |
| Auxiliary treated as GIVEN; auxiliary label collision | closed for slice 1 (review fixes) | GD |
| Subscript labels (M₁) | fail-closed `UNKNOWN_LABEL` | E10 |
| Centre label exhaustion | crash (`StopIteration`) | strict xfail; `ISSUE-ARCH-ENGINE-CENTRE-LABEL-EXHAUSTION` |
| B27 unnamed derived operand / B28 "tâm" cue | false refusals, fail-closed | benchmark |
| A valid model of the wrong object | bounded by construction binding (P23) and the fact re-check; no general semantic verifier — not measured beyond the probes | — |

**The Critical issue comes first.** It is the only hole found where a served answer depends on a clause that is not a given. The fix is bounded: read the clause role at the predicate position *inside* the quote for every premise call. This generalises the special case the gate already has for constructions, and is the same pattern the slice 1 review applied to the auxiliary path.

## 5. Goal-directed planning gaps

| Question | Answer (code + probes) |
|---|---|
| B26 decomposition | one bounded rule (distance point→line), declared auxiliary, gate-checked |
| Multi-step chains | yes, through the engine's fixed-point resolution of **stated** constructions (B09–B16) |
| Reuse of intermediate objects | yes, by label (P11, B12) |
| Own dependency graph | the engine derives the order (trace: operands before results); the planner does not |
| Unnamed objects | only the B26 foot; otherwise not representable (B27) |
| Construction goal vs answer goal | **not distinguished.** Constructions enter only as premises (`point_def`, `projection`); a "Dựng …" goal has no representation (E03, P02, P09) |
| Alternative plans when the first fails | none: refusal with a code |
| Narrow rule list | yes. Rules are per fact kind; wording grammar admits two projection phrasings, and "Kẻ AH ⊥ SB tại H", "chân đường vuông góc" and "Dựng hình chiếu" are refused (E02 E03 E05) |

**Main conclusion.**
- **For the important missing simulations, the engine already knows how to build them; the Hybrid layer has no way to ask for them.** This covers sections, giao tuyến, plane ⊥ line, divide_segment, curved solids, and drawing a line or segment as an object. The probe appends one `construct_section` to IR the Hybrid route produced, and the existing interpreter and Scene3D build the oracle trapezoid A, B, mid(SC), mid(SD).
- **The genuinely missing geometry primitives are few:**
  - placing an apex from a given angle;
  - centroid of more than 3 vertices in the Hybrid engine;
  - parallel constructions without an IR expression of their own (composable through `translate`).

## 6. Geometry verification vs scene verification

| Layer | What exists | What does not |
|---|---|---|
| Geometry | exact kernel; engine re-checks every fact on the built figure; `relation_verified` for each construction; preconditions (parallel, degenerate, foot in plane); independent oracles in LX/BM/GD | no general check that "the model is the object the user meant" |
| Scene (Hybrid) | scene JSON per served case: typed objects, label = geometry id, derived operand lines/planes, projection witness checked equal to the foot; trace order observed in a probe only | **no** product-UI rendering of Hybrid scenes; no camera hidden-line check; no animation timeline check; no human review. The 2026-10-11 screenshots used a harness |
| Product renderer (`LLM_ONLY`) | orbit gate v3, vitest scene tests | orbit gate red on p1 (`ISSUE-ARCH-ORBIT-P1-SECTION-SCENE-DOES-NOT-SETTLE`, P1, not fixed) |

## 7. Metamorphic and negative test plan (executed part marked ✓)

| Transformation | Probe | Result |
|---|---|---|
| ✓ Consistent renaming (T.MNPQ) | `test_renamed_projection_is_invariant` | invariant |
| ✓ Reordering of independent facts and sentences | GD, BM B13 B14 | invariant |
| ✓ Paraphrase of a construction (midpoint ×3, projection ×5) | E01–E08 | midpoint 3/3; projection 2/5 served, 3/5 fail-closed |
| ✓ Irrelevant extra fact | E09 | invariant |
| ✓ Equivalent representations of one relation (projection "là H" / "H là") | E01 E04 | invariant |
| ✓ Negation, condition, proof | P19 P21 + 3 strict xfail | negation and role-prove safe; **prefix inside quote unsafe** |
| ✓ Subscript labels | E10 | fail-closed |
| ✓ LINE vs SEGMENT | P15 P16 | line served; segment wording refused |
| ✓ Degenerate (point on line, parallel lines, BB) | E13 P17, GD | 0 / coded refusals |
| ✓ Coinciding auxiliaries | GD, review | served; redundant foot recorded |
| Scaling (lengths × k ⇒ length × k) | GD (point→line) | invariant; extend to new slices |
| Real-model paraphrase robustness | — | **not run** (no live calls) |

## 8. Next slices (at most three)

**S0. Prerequisite safety fix** — not a new capability, but it should come before any new slice.
- **Problem:** the Critical issue in §4.
- **Change:** in `registry.kiem_nguon`, for every premise call, read the clause role at each predicate or label position inside the quote, not only at its start. Reuse `_vai_tro` and the construction special case.
- **Optionally:** the same "is it asked" allow-list for all `ask_*` (`ISSUE-ARCH-ASK-GATE-NO-QUESTION-CHECK`).
- **Impact:**
  - shared gate of A and B;
  - no provider-surface, Registry or IR change;
  - candidate refreeze;
  - historical results unchanged but re-read.
- **Tests:** the 4 strict xfail flip; negatives and mutants; the benchmark must stay 19/9/0/2.

**Slice 1 — RECOMMENDED: section and intersection line on the Hybrid route.**
- **Problem:** "Dựng thiết diện của hình chóp cắt bởi mặt phẳng (MAB)" and "giao tuyến của (SAB) và (SCD)" are refused (`OUT_OF_SCOPE`), although the shared engine builds and renders them. Section is a *supported* product capability on `LLM_ONLY`.
- **Root cause:** there is no way in. There is no Registry function or TypedFact kind, the planner has no rule, the source grammar has no cue, and the Hybrid engine never emits `construct_section` or `intersect_plane_plane`.
- **Functions:**
  - new Registry entries `section(solid, plane)` and `intersection_line(plane1, plane2)`, built on the existing `construct_section` and `intersect_plane_plane`;
  - `ask_area` of a section as an optional consumer.
- **Planner/compiler:** a TypedFact kind with a construction-goal role (e.g. `construct` as a goal, never a premise), mapped one-to-one; planes by three named points.
- **Verification:**
  - an independent oracle for the section polygon (vertices on the plane and on solid edges, closed, ordered);
  - the existing `section.py` certification;
  - scene object `section` with its vertex sources.
- **Impact:**
  - Registry, which changes A's provider surface: needs your approval, and pilot readiness stays NO-GO;
  - Typed Facts schema, which changes B's surface: needs approval;
  - IR, kernel and Scene3D **unchanged**.
- **Before/after tests:** P09 flips. New section cases:
  - plane through 3 named points, including a derived midpoint;
  - plane through an edge;
  - a plane that misses the solid (refused);
  - a plane through one vertex only (degenerate);
  - renamed, reordered.
- **Acceptance:**
  - the section polygon equals the oracle;
  - the scene has a `section` object;
  - benchmark 19/9/0/2 unchanged;
  - T3 PASS;
  - S0 merged first.
- **Risks:** a "section by a parallel plane" needs slice 2; a curved section stays out.

**Slice 2: parallel constructions.**
- **Problem:** "mặt phẳng qua M song song với (SBC)" and "đường thẳng qua M song song với AB", the usual input to sections in Grade 11.
- **Engine:**
  - kernel primitives exist but have no consumer;
  - IR composition via `translate`, or one new IR expression;
  - plus Registry, Typed Facts and gate wording.
- **It depends on slice 1** to be visible as a section.

**Slice 3: construction wording breadth.**
- **Problem:** "Kẻ AH vuông góc với SB tại H", "chân đường vuông góc hạ từ A", "Dựng …" and subscript labels.
- **Change:** grounding grammar and label scanner only. No new geometry and no provider change.
- **Effect:** higher served rate on existing constructions, but **no new simulation**. A real-model measurement is needed to know how often these wordings occur.

**Deferred and why:**
- **B27** (anonymous operand): Typed Facts schema, and it adds no new kind of object.
- **B28:** one cue, low simulation impact.
- **Curved solids on Hybrid:** product `foundation_only`; the model is unmeasured.
- **General goal-directed search / CEGIS / DSL / FactGraph:** no evidence of need; every gap found has a one-to-one mapping.
- **LINE/SEGMENT semantics:** needs a convention decision and a case first.
- **Orbit p1:** renderer defect on `main`, separate.

## 9. GO / NO-GO

- **S0: GO**, after your approval of a shared-gate change.
- **Slice 1 (section and intersection line): GO for design and implementation** after S0, conditional on approving the Registry and Typed Facts surface change.
- **Real-model claims: NO-GO.**

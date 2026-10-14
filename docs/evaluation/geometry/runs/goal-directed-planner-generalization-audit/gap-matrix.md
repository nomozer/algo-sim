# Generalization gaps — source and measured diagnostics

Source locations are pinned to main2a3c0787 in `source-map.json`; measured cases in `baseline.json`. The new transport probes
are intentionally outside today's TypedFact schema and cannot alone demonstrate a Planner search failure.

| Capability | Current mechanism / evidence | Limitation / root cause | Reuse opportunity / proposed intervention |
|---|---|---|---|
| Goal representation | TypedFact quantity + point arrays; `_cau_hoi`, planner.py:380 | No first-class reference to a constructed line output. `line_ref` probes stop at schema | One optional semantic producer reference for distance/projection; no model program |
| Fact/state | `KeHoach` calls/goals/auxiliary/derived_planes; Engine `_Dung` owns coordinates/Gram | Symbolic call proposal, not a verified semantic FactGraph at planning time | Extend existing plan bindings and Engine entity table; no second FactGraph |
| Function signatures | FunctionSpec registry.py:248; projection.line is Seg, intersection returns IR line3 | Producer output cannot be a consumer argument; no declared planning effects | Small internal planning contracts and a typed line reference on existing functions |
| Preconditions/postconditions | Pydantic/Registry source checks; Engine `_construction_relation`:620 and `kiem` | Actual geometric checks are executable, but not queryable producer-selection metadata | Descriptor metadata names existing checks; Engine remains truth authority |
| Dependency closure | Engine `giai_phu_thuoc`:383; reordered/nested midpoint probes SERVED | Resolves supplied point producers; does not discover new functions | Reuse closure; extend to the referenced line producer before its projection consumer |
| Function discovery | `_anh_xa`, `_cau_hoi` switch by kind/operand arity; fixed function names | Adding a Registry member alone does not make Planner use it | Index registered effect descriptors in the existing Planner, narrowly for point–line distance |
| Candidate generation | `_phan_ra`:489 always foot→length; `_mat_qua_diem`:426 always two translates→section | One chosen recipe, no alternative candidate plan | Resolve typed needs with effects; reuse a supplied foot or derive one |
| Search/alternatives | No search, depth1 rule expansion; source docstring explicit | No generic backward/forward function-chain search; numeric invalidity refuses | Bounded typed need resolution; no A*/PDDL or numeric backtracking needed here |
| Type checking | TypedFact/doc_ke_hoach/Pydantic; static IR validation | Arity encodes point/line/plane, not output identities | Keep validators, enforce reference producer kind and exactly one line representation |
| Grounding/provenance | `kiem_nguon`:880; `_kiem_phu`:655 trusts only declared rule certificates | Proof/condition never given; new composition cannot reuse broad quote permissions | Source-bound result-reference certificate in same Registry; closed-premise authority reused |
| Deterministic verification | Existing metric/Kernel/interpreter, independent oracle fixtures | Does not prove arbitrary theorem goals or arbitrary figure layouts | Reuse exact predicates, unique intersection and projection; no Kernel changes |
| Refusal | Typed/grounding/Engine codes; 4 negative probes all REFUSED | Nonunique/unsupported preserved; wording false refusal observed | Keep explicit structured refusals; new reference/type/budget errors fail closed |
| Trace/formation | Engine.bien_dich:728; existing formation and Scene3D consumers | Current point blocks cannot consume an intersection line emitted later in IR | One DAG-compatible line-before-foot emission change, not a frontend timeline |

**Selected bottleneck:** no composable, source-bound function-result operands/effect metadata across existing Registry
functions. It prevents the evidenced intersection-line → projection → measurement chain. Lack of a search algorithm
is downstream of this contract gap; adding a generic search without usable operands/effects cannot remove it.

Alternatives rejected: one more hand-written distance-to-intersection recipe would repeat the coupling for each next goal;
an unrestricted search/new state DSL would add scope without solving the first contract obstruction. A narrow effect-driven
resolver for existing functions is the next experiment, not a claim that all planning can be generalized this way.

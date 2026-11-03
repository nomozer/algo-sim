# Architecture capability audit (fourth continuation, 2026-10-31)

**Basis.** This audit is read from the code at this branch's HEAD and from probes run in this epic. 0 provider calls. Every probe here is `DEVELOPMENT_DIAGNOSTIC`: the implementer wrote it, so it says nothing about held-out or live performance. It extends `architecture-consolidation.md` (Phase B) and the 18-group baseline in `../hybrid-v2-planner-generalization/capability-gap-matrix.md` (`386d2149`). Neither earlier file is edited.

**Status vocabulary:**
- `IMPLEMENTED_AND_VERIFIED`: executed and checked against an exact oracle in this epic or in locked tests.
- `PARTIALLY_IMPLEMENTED`
- `REPRESENTABLE_BUT_NOT_EXECUTABLE`
- `UNSUPPORTED`
- `NOT_MEASURED`

## New development evidence: `tools/topology_probe.py` → `topology-probe.json`

**What it covers:**
- **4 topologies:** a regular S.ABC; a cube written as a right square prism; S.ABC with a right angle at B and SA ⊥ the base; S.ABCD with an equilateral face perpendicular to the base, a radical chart.
- **36 questions,** each with an oracle computed by hand beforehand: volume; 6 kinds of distance; 3 kinds of angle; goals over constructed points (midpoint, centroid, intersection, projection, two chained projections).

**Results:**
- Before the fix below: **35/36 served exactly correct, 0 wrong-served.**
- **After the fix: 36/36.** The one refusal was T3.HK. Splitting its clause showed the planner already composes HK correctly; the gap was in source grounding. See "Improvement implemented".

## Components A–J

| component | status | evidence | remaining gap |
|---|---|---|---|
| A. Typed FactGraph (`typed-fact-next/2`) | PARTIALLY_IMPLEMENTED | Closed premise kinds (`typed_fact_next._ARGS_LOI`), 6 solid types, and goal shapes (`GOAL_TARGET_ALTERNATIVES`); 36 probe payloads all validate | No pyramid frustum. Curved solids are representable only, see C/F. No general Oxyz input: the coordinate frame is a root marker only. |
| B. Semantic grounding (Source Gate `registry.kiem_nguon`) | IMPLEMENTED_AND_VERIFIED for its closed grammar | 9 bypass mutations refused (architecture review); probe T4 refused an under-quoted plane (`PLANE_NOT_IN_QUOTE`) | Grammar is closed by design. **Fixed here:** respectively projection lists. Not detected: paraphrase outside the grammar, so it fails closed. |
| C. Canonical identity | IMPLEMENTED_AND_VERIFIED (single solid, parent-chart namespaces) | `canonical_vertex_ref` is the sole authority (Task 1); M-1 pinned | Qualified identities across several solids: refused `BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY` |
| D. Construction planner | PARTIALLY_IMPLEMENTED: a bounded effect planner | Typed needs/effects (`PlanningContract`), producer selection by effect (`_EffectResolver`, depth ≤ 3), auxiliary producers marked DERIVED, shared intermediates, `DEPENDENCY_CYCLE` / `DANGLING_DEPENDENCY`. Probe: two chained projections then a length (HK); a constructed point plus an auxiliary foot (d(N, SC)) | Decomposition is shallow: at most 3 derived steps. No theorem-level search, e.g. choosing a common perpendicular from a theorem. See the classification below. |
| E. Geometry Function Registry | IMPLEMENTED_AND_VERIFIED for polyhedra | `REGISTRY` functions for points, lines, planes, projections, intersections, sections, and every measurement kind; registry `/22` | No curved-solid functions; Adapter /3 owns those |
| F. Construction IR compiler (`ir_builders`) | IMPLEMENTED_AND_VERIFIED | One interpreter and one kernel for all three producers (Phase B) | none found |
| G. Exact kernel | IMPLEMENTED_AND_VERIFIED | Rationals plus square roots; radical charts (T4, S(1, 0, √3)); 36/36 exact | Nested radicals are refused (A06, Task 2) |
| H. Geometry and scene verification | IMPLEMENTED_AND_VERIFIED | Engine cross-checks of executed answers, section certificates, adapter scene/metric/proof validation; M-3 closed (a fault of ours is never a 500) | none found in this audit |
| I. Pedagogical construction trace | PARTIALLY_IMPLEMENTED | Calls carry source quotes, `depends_on`, `binding = AUXILIARY` / `provenance = DERIVED`, and closure and section certificates; exact source spans reach the receipt | Not checked here as a learner-facing order of steps. Missing `annotation.kind` on line–plane / plane–plane targets is D-10, a frontend-owned finding. No WHY text is generated without a certificate, and none is added here. |
| J. Composite geometry | REPRESENTABLE_BUT_NOT_EXECUTABLE beyond explicit shared faces | `relations` (`shared_faces`, `containment` …) are in the schema; derived solids resolve through the parent chart | Mixed solids, inscribed/circumscribed, tangency: no /4 executor |

## Planner: what kind of planning (Owner's distinction)

| kind | present? | where |
|---|---|---|
| Genuine generalized planning (open-ended goal search) | **No** | none |
| Bounded rule composition by typed needs and effects | **Yes** | `_EffectResolver`; `AUXILIARY_RULES` (for example, distance(point, line) → `orthogonal_projection_line` then `ask_length`); producers are chosen by effect, not by family |
| Hardcoded section orchestration | Yes, scoped to sections | engine section closure, `DINH_CAT_CANH` |
| Family-specific dispatch | Only in compiler C (disabled) | `SUPPORTED_FAMILY*` |
| Schema transformation | Yes, most of each plan | premise → call, 1:1 |

**Honest bound.** The planner recomposes primitives across topologies, which the 36/36 probe on four new topologies confirms. Its decomposition depth is bounded, though, and it does not discover constructions that the source does not name. No probe in this epic shows a goal that the current primitives could reach but the planner fails to find. Every refusal found traced to grounding (fixed) or to absent families (C/E/J). So **no planner change is justified by evidence.** Deepening it now would be a feature without a failing case.

## Improvement implemented: respectively projection lists (registry /22)

The case "Gọi H, K lần lượt là hình chiếu vuông góc của A trên SB, SC" was refused with `SOURCE_OBJECT_MISMATCH`.
- Production LLM_ONLY grounding reads this phrasing (W18), and Route D already reads it for midpoints and centroids. This is therefore a **parity gap** with the arm to be retired.
- **Fix:** `construction_source_bound` reads ordered respectively lists for point–line projections, with the discipline of `_dinh_nghia_diem_dung_nguon`. That means at least 2 names only with "lần lượt", equal counts, and in-order pairing.
- **Tests:** `test_respectively_projection_grounding.py`, 8 tests. They cover the exact HK² = 4096/1025 and five misbindings refused: swapped, count mismatch, no "lần lượt", wrong source point, extra operand. A mutant that pairs any name with any line fails them.
- **Plane projections** ("… trên (SBC), (SCD)") use a different checker and are **not** extended, because no failing development case asks for them.

## 18 registered groups: delta against the `386d2149` baseline

These are **delta rows only**; every other cell keeps the baseline value.

| group | baseline | now | basis |
|---|---|---|---|
| 1 line–plane / three perpendiculars, 2 skew lines | PARTIAL | PARTIAL, with exact development evidence on 4 new topologies | probe T1–T4: d(line, line), d(point, line), line–plane angle |
| 3–6 pyramid families (metric subset) | PARTIAL | PARTIAL; the metric subset is development-verified | probe T1, T3, T4: volume, distances, angles, dihedral |
| 11 cuboid / cube | PARTIAL | PARTIAL | probe T2: cube metrics, skew diagonals, intersection-point goal |
| 7–9, 14–16 curved and curved composites | REFUSED | **REFUSED, unchanged.** The bridge raises `BRIDGE_UNSUPPORTED_CURVED` (`typed_fact_next_bridge.py:412`). | Adapter /3 (legacy IR) is the only curved executor |
| 10 pyramid frustum | REFUSED | REFUSED | no enum (`solid_type` has `cone_frustum` only) |
| 17–18 Oxyz | REFUSED | REFUSED | the frame is a root marker only |

Inscribed and circumscribed spheres (groups 3–5) are not bridged either: `UNSUPPORTED` on /4.

## The decisive remaining capability gap (cutover-relevant)

The pre-registered corpus admits **curved solids as expected-serve**, because LLM_ONLY serves them (protocol §2). Hybrid /4 refuses every one of them. Criterion 2 allows a net served-correct loss of at most 2 of 45. **A corpus with three or more curved serve cases therefore forces `HYBRID_CUTOVER_NO_GO` under the current product.**

Curved solids on /4 are the highest-reuse gap: 6 of the 18 groups, plus the composite rows. They need a real multi-layer slice:
- Registry functions for cylinder, cone and sphere, with exact ℚ³ anchors (`geometry/curved.py` already exists);
- Source Gate grammar;
- planner effects;
- engine certificates that π-exact answers are correct;
- an adapter scene.

This must not become a second compiler and must not bridge into Adapter /3. It is **justified offline work that is not done in this continuation.** It is recorded as the next architecture action, `HYBRID_MASTER_EPIC_CURRENT_STATE.md` → Next.

---

## Addendum through Ninth Continuation (`fa1ed277` / candidate `17e4a326`, 2026-11-01)

The curved and composite architecture actions identified above were implemented across Continuations 5–9 inside the single Route D `/4` pipeline (`Registry /26`, `Planner /22`, `Engine /18`, `geometric-relation-certificate/1`), without creating a fourth compiler or expanding legacy Adapter `/3`:

- **Continuations 5–7 (`4074e8b9`, `bfe8912f`, `d9d11b60`):** standalone cylinder/cone/sphere measures, parallel/axial/sphere sections, general cone apex ratio $k$, residual volume, and closed base-centre grammar (`curved-capability.md` §§5–7, `curved-generalization-audit.md`).
- **Continuation 8 (`44a0b79e`):** polyhedral role-phrase Source Gate parity, exported machine-verified `preconditions` and `postconditions` on `construction_trace`, and certified circumscribed spheres of polyhedra (`curved-capability.md` §8, `circumscribed-spheres-review.md`).
- **Continuation 9 (`fa1ed277`):** 16-dimension multi-object FactGraph audit (`multi-object-factgraph-audit.md`); additive `typed-fact-next/2` `GeometricRelationSpecV2` (`circumscribes`, `inscribed_in`, `tangent_to` + `contact_ref`) and `SolidSpec.inscribed_in`; certified sphere inscribed in a convex polyhedron across all boundary faces (`_tam_noi_tiep_da_dien` over exact `Fraction` + `_QField`); certified sphere–plane tangency (`_chan_tiep_xuc_mat`); dual named/unnamed spheres, polyhedron section + sphere coexistence, multi-polyhedron `shared_faces` + sphere, and axial cylinder/cone + circumscribed/inscribed spheres (`_dung_cong_ghep`); explicit multi-object planner dependency DAG + `composition_classification`; and 4-layer `relation_certificates` (`curved-capability.md` §9, `composite-relations-review.md` Round 3 `READY`).

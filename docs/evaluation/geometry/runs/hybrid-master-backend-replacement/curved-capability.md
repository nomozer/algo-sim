# Curved solids on Route D /4: capability, parity and limits (fifth continuation, 2026-10-31)

**Revision after independent review round 1 (`NOT_READY`).** The reviewer found three blockers. B1: the centre, top and rim roles were not grounded. B2: a value did not have to end its clause. B3: a role phrase or height belonging to another object was accepted. Each one served a WRONG exact value. All are fixed, and each reproduction is a locked negative (`ADVERSARIAL` in the probe). M1, the certificate's scope, is corrected in the table below.

**Basis.** This record is read from the code at the branch HEAD and from the development probe `tools/curved_probe.py` → `curved-probe.json`. 0 provider calls. The implementer wrote the probe cases, so this is `DEVELOPMENT_DIAGNOSTIC` evidence, never held-out. The oracles were computed by hand, before the implementation. At `23c20679` every case was RED, refused with `BRIDGE_UNSUPPORTED_CURVED`.

## What is now served, and how (one route, no new compiler)

The path is: bridge → the **one** planner → Source Gate → engine → the **existing** curved IR (`construct_curved_solid`, `measure`, `intersect_plane_curved`, `arith`) → interpreter → exact kernel (`geometry/curved.py`) → Adapter /4.

The only new layout code is the engine's canonical pose (`_dung_cong`), which sits beside the polygon chart (`_Dung`). It shares the Source Gate, the IR validator, the interpreter, the kernel and `KetQuaTuyen`.

| capability | status on /4 | evidence |
|---|---|---|
| Cylinder, cone and sphere declared with centre, top/apex and rim, radius and height | **IMPLEMENTED_AND_VERIFIED** | 15/15 probe positives exact; `test_route_d_curved_solids.py` |
| Volume: πr²h, πr²h/3, 4πr³/3 | **IMPLEMENTED_AND_VERIFIED** | cylinder 45π and 6π, cone 12π and 8π/3, sphere 36π |
| Lateral area: 2πrh, πrl | **IMPLEMENTED_AND_VERIFIED** | 30π, 15π, 4π√2, 6π√2 |
| Sphere surface, 4πR² (= its curved surface) | **IMPLEMENTED_AND_VERIFIED** | 36π |
| Total area of a cylinder or cone, **composed**: lateral area + base circle(s) | **IMPLEMENTED_AND_VERIFIED** where the sum is one exact term; a typed refusal otherwise | 48π and 24π. 6π√2 + 4π ⇒ `EXACT_DOMAIN_EXCEEDED`, never rounded. |
| Radius | **IMPLEMENTED_AND_VERIFIED** | 3 |
| **Derived dimension:** cone height from a stated slant, h² = SA² − OA² | **IMPLEMENTED_AND_VERIFIED.** This is recomposition over named points. | 12π and 15π from SA = 5; traced as `derive_dimension` / `pythagoras_axis_rim` |
| Symbolic unit a | **IMPLEMENTED_AND_VERIFIED** | V = 2πa³. A defect was found and fixed here: the learner answer had dropped π and showed "2a³". |
| Source grounding | **IMPLEMENTED_AND_VERIFIED** | `_khoi_cong_dung_nguon` checks four things:<br>• the quote describes one solid of this kind and no other object;<br>• every named point is bound by its role phrase (centre, top/apex, rim on ITS base circle or on the sphere);<br>• the notation agrees with those roles;<br>• each dimension is the one number of its own role clause, and that number ends the clause.<br>A height assertion counts only inside the solid's own quote. The question must name the solid's kind (`_cong_khop`). Unnamed points are allowed (canonical pose) and never invented. Refused, each with the expected code: 12 adversarial cases plus 11 reproductions from the independent review. |
| Exactness certificate | **IMPLEMENTED_AND_VERIFIED, for arithmetic only** | Each answer equals both the executed kernel value and an independent closed form (`_chung_chi_cong`), written from the geometry by `KHOI_CONG` attribute. A tampered closed form gives `ENGINE_SELF_CHECK_FAILED`. **Scope (review M1):** the certificate receives the same solved (r², h²) as the IR. It certifies the formula and the kernel's execution, **not the grounding**. Grounding belongs to the Source Gate (next row). |
| Pedagogical trace | **PARTIALLY_IMPLEMENTED** | Steps recorded: `choose_pose` (LAYOUT_DERIVED, not a given), `derive_dimension`, `construct_solid`, `compose_quantity`, `certify_answer`. The learner sees only the asked target; the parts stay intermediates. |

**Negatives, each refused for the right reason:**

| case | code |
|---|---|
| slant ≤ radius | `INCONSISTENT_FACTS` |
| r, h and slant stated but disagreeing | `INCONSISTENT_FACTS` |
| radius/height swapped against the text | `UNGROUNDED_VALUE` |
| a value the text does not state | `UNGROUNDED_VALUE` |
| a question naming a cone for a cylinder | `SOURCE_OBJECT_MISMATCH` |
| no height stated | `MISSING_DIMENSION` |
| the lateral area of a sphere | `CURVED_MEASURE_UNDEFINED` |
| "diện tích của hình trụ" without "toàn phần" | `PREDICATE_NOT_IN_QUOTE` |
| a curved solid together with a pyramid | `BRIDGE_UNSUPPORTED_CURVED_COMPOSITE` |
| a segment to a point the cone does not own | `SOURCE_OBJECT_MISMATCH` |
| a stated height dropped by the extraction | `SOURCE_PREMISE_UNREAD` |
| an undeclared solid id | `UNKNOWN_SOLID_ID` |
| "đường kính bằng 6" read as a radius | `UNGROUNDED_VALUE` (not guessed) |

## Planner: what changed, honestly

- **Plan branch.** `_ke_hoach_cong` maps one curved declaration and its questions to calls; any other fact is refused. This is **schema transformation plus bounded dispatch**, not search.
- **The real recomposition happens in the engine's exact dimension solve.**
  - Every stated length among {centre, top, rim} is one linear equation in (r², h²).
  - The slant, centre–top or centre–rim distance thereby becomes an intermediate the solver derives and checks.
  - The total area is composed from three primitives already in the IR: `lateral_area`, the base circle (`intersect_plane_curved`), and `area(circle)`.
- **No failing case showed a gap in the polyhedral planner.**

## Parity: Adapter /3 → /4 (read from `adapter3_simulation._run_curved_route`)

| capability | Adapter /3 | /4 now |
|---|---|---|
| Declaration, volume, lateral area, radius | yes | **yes** |
| Height from a slant | no: height required (`MISSING_CURVED_DIMENSION`) | **yes** |
| Total area of a cylinder or cone | not offered | **yes**, composed and exact or refused |
| Section parallel to the base (a circle) and its area | yes | **no** |
| Axial section | yes | **no** |
| Cone volume ratio / remaining (frustum) volume | yes | **no** |
| Standalone frustum | refused | refused |
| Composite curved + polyhedron | refused | refused |

**Parity is therefore PARTIAL.** Adapter /3 must stay until curved sections and the cone ratio are on /4, and LLM_ONLY cannot be retired on curved problems. Ported next, all on existing kernel primitives (`intersect_plane_curved`, `phan_xu_conic`, `measure area`):
- parallel and axial sections;
- the cone ratio / remaining volume.

## Not supported, and why

| capability | why |
|---|---|
| Diameter, circumference or base-area phrasings | No role grammar exists for them yet. They are refused, never guessed. |
| Inscribed / circumscribed spheres; any curved–polyhedral relation | No relation type in the schema, and no certificate (all vertices on one sphere, tangency) |
| Pyramid frustum | No declaration |
| Curved solids in Oxyz | Coordinates are a root marker only |
| Total area that is a sum of unlike radical terms | Outside the exact single-term domain a·π·√b |

## Evaluation consequence (protocol unchanged)

The scorer and the thresholds are untouched. The authoring package (`heldout-authoring/README.md`) now states rules that apply identically to both arms:
- π is written before √;
- a sphere's surface and every lateral area go under `lateral_area`;
- the total area of a cylinder or cone is not asked, because neither arm shows it under a scorable producer kind.

Each rule follows from the kernel both arms share. None of them favours Hybrid.

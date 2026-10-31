# Curved solids on Route D /4: capability, parity and limits (fifth continuation, 2026-10-31)

**Revisions after the independent review.** Round 1 and round 2 were `NOT_READY`; round 3 was **READY** (`curved-slice-review.md`).

**Round 1.** The reviewer found three blockers. B1: the centre, top and rim roles were not grounded. B2: a value did not have to end its clause. B3: a role phrase or height belonging to another object was accepted. Each one served a WRONG exact value. All are fixed, and each reproduction is a locked negative (`ADVERSARIAL` in the probe). M1, the certificate's scope, is corrected in the table below.

**Basis.** This record is read from the code at the branch HEAD and from the development probe `tools/curved_probe.py` → `curved-probe.json`. 0 provider calls. The implementer wrote the probe cases, so this is `DEVELOPMENT_DIAGNOSTIC` evidence, never held-out. The oracles were computed by hand, before the implementation. At `23c20679` every case was RED, refused with `BRIDGE_UNSUPPORTED_CURVED`.

## What is now served, and how (one route, no new compiler)

The path is: bridge → the **one** planner → Source Gate → engine → the **existing** curved IR (`construct_curved_solid`, `measure`, `intersect_plane_curved`, `arith`) → interpreter → exact kernel (`geometry/curved.py`) → Adapter /4.

The only new layout code is the engine's canonical pose (`_dung_cong`), which sits beside the polygon chart (`_Dung`). It shares the Source Gate, the IR validator, the interpreter, the kernel and `KetQuaTuyen`.

| capability | status on /4 | evidence |
|---|---|---|
| Cylinder, cone and sphere declared with centre, top/apex and rim, radius and height | **IMPLEMENTED_AND_VERIFIED** | 18/18 probe positives exact, including the canonical pose (no named point), a rim on the second base, and "chiều cao của hình nón"; `test_route_d_curved_solids.py` (55 tests) |
| Volume: πr²h, πr²h/3, 4πr³/3 | **IMPLEMENTED_AND_VERIFIED** | cylinder 45π and 6π, cone 12π and 8π/3, sphere 36π |
| Lateral area: 2πrh, πrl | **IMPLEMENTED_AND_VERIFIED** | 30π, 15π, 4π√2, 6π√2 |
| Sphere surface, 4πR² (= its curved surface) | **IMPLEMENTED_AND_VERIFIED** | 36π |
| Total area of a cylinder or cone, **composed**: lateral area + base circle(s) | **IMPLEMENTED_AND_VERIFIED** where the sum is one exact term; a typed refusal otherwise | 48π and 24π. 6π√2 + 4π ⇒ `EXACT_DOMAIN_EXCEEDED`, never rounded. |
| Radius | **IMPLEMENTED_AND_VERIFIED** | 3 |
| **Derived dimension:** cone height from a stated slant, h² = SA² − OA² | **IMPLEMENTED_AND_VERIFIED.** This is recomposition over named points. | 12π and 15π from SA = 5; traced as `derive_dimension` / `pythagoras_axis_rim` |
| Symbolic unit a | **IMPLEMENTED_AND_VERIFIED** | V = 2πa³. A defect was found and fixed here: the learner answer had dropped π and showed "2a³". |
| Source grounding | **IMPLEMENTED_AND_VERIFIED** (independent review **READY**, round 3, `curved-slice-review.md`) | `_khoi_cong_dung_nguon` / `_doc_cau_cong` require the WHOLE solid quote to parse in a closed clause grammar, an allowlist. The grammar has: the kind word and a written notation; the base-centre pair; the base circle; the sphere centre; the apex; the rim on ITS base circle or on the sphere; radius and height clauses, whose value ends the clause. Any unread word ⇒ `SOURCE_OBJECT_MISMATCH`. Each named point is bound by its role, and the notation agrees with the roles. A height assertion counts only inside the solid's own quote. The question must name the solid's kind (`_cong_khop`). Unnamed points are allowed (canonical pose) and never invented. Refused: 12 adversarial cases and 17 reproductions from review rounds 1–2, every one of which had served a wrong or unfounded value before its fix. |
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

---

## Sixth continuation: curved sections and the cone volume ratio (registry /24, planner /20, engine /16)

**Development probe:** `tools/curved_section_probe.py`, with oracles computed by hand before the code. At `9f4f61d2` every case was refused at the bridge. Now **10/10 positives are served exactly** and **10/10 negatives are refused for the right reason** (`test_route_d_curved_sections.py`).

### What is served, and how

| capability | how (existing primitives only) | oracle examples |
|---|---|---|
| Section parallel to the base, cylinder | plane z = d → kernel `intersect_plane_curved` → `measure area` / `measure radius` | d = 2: S = 9π, r′ = 3 |
| Section parallel to the base, cone, at a distance from the base | the same; certificate r′ = r·(h − d)/h | d = 1: r′ = 9/4, S = 81π/16 |
| The same, through the midpoint of the axis (ratio from the apex = 1/2) | z = (1 − k)·h | S = 9π/4 |
| Axial section of a cylinder (rectangle) or a cone (isosceles triangle) | a polygon through the axis plus its named plane → `measure area` | 30; 12 |
| Volume ratio small cone : original cone, in either order | the kernel builds the small cone from the apex and the radius it **measures** on the section circle; ratio by cross-multiplication (q·V₁ − p·V₂ = 0) | 1/8; inverse 8 |
| Remaining volume (frustum) | V − V_small, by IR subtraction | 21π/2 |

**Scorer-facing output:** one target per question — `measure.area`, `measure.radius`, `assign.volume_ratio` or `assign.residual_volume`.

### Typed refusals

| case | code |
|---|---|
| a plane outside the solid | `CURVED_PLANE_DOES_NOT_CUT` |
| a plane through the apex | `CURVED_PLANE_TANGENT` |
| a plane on a base | `CURVED_SECTION_IS_A_BASE` |
| an irrational cut | `CURVED_SECTION_OUTSIDE_V1_CLOSURE` |
| a distance the text does not state | `UNGROUNDED_VALUE` |
| a distance "cách đỉnh"; an unread qualifier; a plane not parallel; an inverted ratio; a section sentence about another kind | `SOURCE_OBJECT_MISMATCH` |
| a section "volume" | `INVALID_MATH_GOAL` |
| sphere sections | `BRIDGE_UNSUPPORTED_CURVED` |

### Recomposition (honest classification)

The dependency chain is **original cone → section circle (kernel) → its measured radius → small cone (kernel) → its volume → ratio / remaining volume**. The trace records it in order: `construct_section` → `derive_dimension` (similar cones) → `construct_subsolid` (reusing the section circle) → `compose_quantity` → `certify_answer`, and it is test-locked.

This is **bounded composition of existing primitives**, not open-ended planning. No polyhedral planner change was needed.

### Parity Adapter /3 → /4

| capability | status |
|---|---|
| Cylinder, cone, sphere: volume, lateral area, radius | `SUPPORTED_BOTH` |
| Section parallel to the base, cylinder and cone (distance from the base) | `SUPPORTED_BOTH` |
| Ratio from the apex: /3 takes any k in (0, 1); /4 reads only the midpoint wording (k = 1/2) | `PARTIAL` |
| Axial section of a cylinder or cone | `SUPPORTED_BOTH` |
| Cone volume ratio, remaining volume | `SUPPORTED_BOTH` |
| Height from slant; total area of a cylinder or cone; canonical pose | `SUPPORTED_ONLY_V4` |
| Plane by equation (`plane_equation`); ellipse sections | `SUPPORTED_ONLY_V3` (the /4 schema path would need coordinates from the LLM, which R0 forbids) |
| Sphere section at a distance from the centre / through the centre | `UNSUPPORTED` on /4 (needs a new contract field) |
| Standalone frustum; curved composites | `UNSUPPORTED` on both |

**Parity is therefore still PARTIAL.** Adapter /3 cannot be retired yet.

### Registered controls (explicit layer, not a silent re-pin)

`registered-curved-control-transitions.json` records 32 Owner-registered control cells. Each moved from REFUSED `BRIDGE_UNSUPPORTED_CURVED` to REFUSED `SOURCE_OBJECT_MISMATCH`.
- **Why:** these controls now pass the bridge, and their wording lies outside the closed grammar: "tâm đáy O", "tâm đáy dưới/trên", "A trên đường tròn đáy dưới", "cắt trục SO theo tỉ lệ 1/2 tính từ đỉnh S", "thiết diện qua trục SAB".
- **Guarantee:** the layer can only move a cell between REFUSED codes, and the tests assert that. The registered oracle files are not edited.
- **These wordings are the next grammar gaps.**

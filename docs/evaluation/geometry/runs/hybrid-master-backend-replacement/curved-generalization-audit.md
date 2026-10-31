# Curved generalization audit: planner, FactGraph, certificates, trace (seventh continuation, 2026-10-31)

This audit extends `architecture-capability-audit.md` (fourth continuation, polyhedral planner) to the curved path on /4. It
uses the Owner's classes. Evidence comes from code at the working tree of this continuation and the development probes
`base_center_probe`, `apex_ratio_probe` and `sphere_section_probe`. Offline, 0 provider calls.

## Composition kinds on the curved path

| Component | Class | Evidence |
|---|---|---|
| Bridge `_phan_cong` (typed-fact-next/2 → planner facts) | SCHEMA_TRANSLATION | One section, derived solid or goal becomes one fact (`curved_part`). It reads nothing from the text. Which plane kinds are allowed is decided by the attribute `co_truc` (an axis): axial solids get `_MAT_CAT_CONG`, a solid without an axis (a sphere) gets `_MAT_CAT_TAM`. It never branches on a kind name. |
| Planner `_ke_hoach_cong` + `_HOI_PHAN_CONG` | SCHEMA_TRANSLATION + BOUNDED_RULE_COMPOSITION | Facts map to calls through a fixed table (ask → function). The planner does no goal search. |
| Engine `_dung_phan_cong` | BOUNDED_RULE_COMPOSITION over GENERALIZED_PRIMITIVE_COMPOSITION | See the details below this table. |
| Source Gate curved grammar (`_CAU_CONG`, `_CAU_MAT_CAT`, `_CUM_HOI`) | Closed allowlist; not planning | Unread wording refuses with `CURVED_WORDING_UNSUPPORTED`. A parsed clause whose roles disagree with the call refuses with `SOURCE_OBJECT_MISMATCH` or `UNGROUNDED_VALUE`. |
| FAMILY_SPECIFIC_DISPATCH | **None on /4 curved** | Kind-name dispatch exists only in `geometry/curved.py`. Tests A4 / 04c enforce this. The sphere branch dispatches on the *plane* kind, not on the solid kind. |

Details of the engine `_dung_phan_cong`:

- **Shared primitive.** Every section of every solid uses two primitives: `construct_plane_from_equation` and the kernel's
  `intersect_plane_curved`. The kernel routes that call to `_giao_cau` for a sphere and to `_giao_tron_xoay` for a cylinder
  or cone.
- **Small cone.** It is composed from three parts: the cone's apex, the section circle, and the radius the kernel *measures*
  on that circle.
- **Ratio and residual.** They reuse the polyhedral `ask_volume_ratio` cross-multiplication and the subtraction mechanism.
- **The bound.** The composition rules themselves are a fixed set:
  - parallel at a distance;
  - parallel at a ratio;
  - axial;
  - sphere at a distance from its centre;
  - through the centre;
  - the small cone.

## Changes made, each backed by a failing case

- **Planner /21: `through_point` is carried to the section call.**
  - Failing case: `apex_ratio_probe` `k.13.*`. "cắt SO tại M sao cho SM/SO = 1/3" names M, and without the point the call
    could not be grounded (`n.point_dropped` must refuse; `k.13.*` must serve).
- **Engine /17: the named point on the axis is the section circle's centre and the small cone's base centre.**
  - It is kernel cross-checked together with the solid's named points.
  - Failing case: `test_a_named_point_on_the_axis_is_the_small_cones_base_centre`, which was RED before the change (M was
    missing from `points`).
- **Binder: `CURVED_MULTI_SECTION_UNSUPPORTED`.**
  - Failing case: the registered controls `K.*.area.section*`, where the refusal reason was false (R2 in
    `registered-curved-controls-audit.md`).
- **Sphere sections.**
  - Failing case: `sphere_section_probe`. It was RED at the contract (`INVALID_TYPED_FACT_NEXT`) and GREEN after:
    - 8 / 8 served exactly;
    - 11 / 11 refused with the exact code.

No other planner change is justified. As in the fourth continuation, no probe shows a goal that the primitives can reach but
the planner fails to find. The remaining curved refusals trace to two causes:

1. question grammar (P-1 coordinated lists, P-2 multi-section binding);
2. absent families (curved composites, oblique conic sections, Oxyz spheres).

## Certificates

Each served curved answer equals **both** values below, or the plan is refused (`ENGINE_SELF_CHECK_FAILED`):

- the kernel-executed value;
- an independent closed form.

| Quantity | Independent form | Kernel path |
|---|---|---|
| Parallel section of a cylinder or cone | r' = k·r with k = (h − d)/h for a cone and k = 1 for a cylinder; S = π r² k² | plane z = d ∩ solid |
| Small cone, ratio, residual | V' = k³ V; q·V₁ − p·V₂ = 0; V − V' | kernel cone from the apex and the measured circle |
| **Sphere section** | r' = √(R² − d²); S = π(R² − d²). d = R ⇒ `CURVED_PLANE_TANGENT` (a point, no area); d > R ⇒ `CURVED_PLANE_DOES_NOT_CUT` | `_giao_cau`: centre = exact projection of the sphere's centre, radius² = R² − d², in ℚ³ |

## Pedagogical trace (no frontend change)

Status: **EXPORTED ON BACKEND (`/4`)** as of Continuation 8 (`44a0b79e`; frontend consumer remains deferred under D-10).

What each step carries:

- `step` (a typed kind such as `construct_section`, `derive_dimension`, `construct_subsolid`, `place_point` or
  `compose_quantity`);
- `rule` (for example `sphere_plane_at_distance`, `point_on_axis_at_ratio`, `perpendicular_bisector_intersection`, or
  `canonical_origin_center` for axisless spheres);
- dependencies through `dependencies`, `calls` and `parts`;
- provenance (`SOURCE_NAMED` / `DERIVED` / `LAYOUT_DERIVED`, `binding: AUXILIARY`);
- machine-verified `preconditions` and `postconditions` exported on `KetQuaTuyen.trace` and `route_d.construction_trace`
  (`_gan_dieu_kien_vet`), with post-execution kernel claims (`kernel_point_matched`, `kernel_line_matched`,
  `closed_section_verified`) stripped on every `REFUSED` path;
- a learner `note`.

## Unsupported (typed refusals, exact domain kept)

| Case | Refusal code |
|---|---|
| Two solids of revolution | `BRIDGE_UNSUPPORTED_CURVED_COMPOSITE` |
| Oblique / conic sections | `CURVED_SECTION_OUTSIDE_V1_CLOSURE` |
| Sphere plane given by an equation without centre coordinates (`plane_equation`) | `BRIDGE_UNSUPPORTED_CURVED` |
| Tangent wording ("tiếp xúc") | `CURVED_WORDING_UNSUPPORTED` |
| Irrational section distance | `CURVED_SECTION_OUTSIDE_V1_CLOSURE` |
| Coordinated question lists (P-1) and several sections in one run (P-2) | Owner proposals in `registered-curved-controls-audit.md` |

## Sphere-section contract change: model-surface impact

- **Schema.** `typed-fact-next/2` gains:
  - two plane kinds: `at_distance_from_center` and `through_center`;
  - one optional field: `distance_from_center`, required by `at_distance_from_center`.
- **Compatibility.** The change is additive. Every valid /2 payload stays valid with the same meaning, so `schema_version`
  is unchanged.
- **Provider surface.** The provider-facing response schema (`TransportExtractor`, `TypedFactNextPayloadV2.model_json_schema()`)
  widens, so the model surface **changed** for the /4 arm.
- **Measured-system identity.** It changes through the `measured_system` hash (`backend/app` is measured). The harness
  records it in `runtime_identity`, and a new candidate is frozen.
- **Cache.** `CACHE_VERSION` is unchanged. It keys the /api/analyze LLM_ONLY response cache, whose prompt, policy and
  schema are untouched. /4 has no cache.
- **Live readiness.**
  - The corpus is not pre-registered yet: no Owner GO, and the authorized budget is 0. So no amendment file is needed.
  - The Owner's approval packet must bind the new candidate and harness hashes, which is the next request.
- **Status.** Sphere sections are **IMPLEMENTED_AND_VERIFIED** (`curved-generalization-review.md` Round 3 `READY` and Full T3 `FULL_PRODUCT_GATE_PASS` at `cb06635e`), and certified circumscribed spheres of polyhedra (`SolidSpec.circumscribes`) are added in Continuation 8 (`44a0b79e`, `circumscribed-spheres-review.md` Round 2 `READY`).

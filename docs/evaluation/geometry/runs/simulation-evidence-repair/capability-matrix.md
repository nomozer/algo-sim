# Corrected simulation capability matrix

Version: `simulation-evidence-repair-w01`, 2026-10-21. Product `3298b901d2246650535aa4028845ddc2a44892c4`, frozen candidate `5f4ee58c48011e9e5d38d3209f7c97250032a976` (measured hash `4d11a91790422b9508bc90921f4352687a4b8616c0f855886e76649d3a7dcf68` across `114` files). This matrix supersedes the residual-mesh and browser-scope claims in the preserved original campaign matrix/report; historical files and numerical outcomes remain unchanged.

| Capability | Analytical kernel | Offline TypedFactNext / Adapter /3 | Scene3D objects | Nine-demo browser group | Default natural-language product |
|---|---|---|---|---|---|
| Parent polyhedral solids, derived pyramids and exact sections | Existing exact polyhedral operations | Supported within existing contract | Parent solid, derived pyramid, plane and closed cutting polygon | Demos 1–5 exercise the specific pyramid scenarios in the authoritative inventory | No new live claim established by prepared payloads |
| Residual polyhedral solid mesh | Generic polyhedral operations do not establish a residual construction feature | **NOT_IMPLEMENTED**: no `DerivedSubSolidSpec` / `frustum_like`; derived goal emits `pyramid(apex, section cycle)` | No independently constructed residual mesh | **NOT_IMPLEMENTED**; `demo2` renders parent + upper pyramid + section and scalar residual volume | No supported residual-mesh claim |
| Right circular cylinder | Exact volume/lateral area, circles and finite ellipses | Supported offline | `curved_solid`, `circle3`, axial `polygon3`; `ellipse3` in separate backend cases | `demo6a`: parallel circular section and axial rectangle; no ellipse | Not independently verified live NL E2E |
| Right circular cone | Exact finite cone, circle and admissible ellipse operations | Supported offline | Parent cone, derived upper cone, `circle3` and axial `polygon3` | `demo6b`: parent/upper cone and parallel circle visible (`ownPixels > 0`); axial triangle `td_sec_axial` `ownPixels = 0` in new audit (OPEN renderer occlusion finding — interior `polygon3` uses `depthTest: true` behind `curved_solid` opaque depth prepass and `updateCanonicalEdgeVisibility` excludes `curved_solid` from `occluders`); no ellipse | Not independently verified live NL E2E |
| Sphere | Exact sphere and circle-plane intersection | Supported offline; non-cutting/tangent planes refuse | `ball` `curved_solid`, `plane3` and `circle3`, or `null` scene on refusal | `demo6c`: $R=5, z=3, r=4$. `demo7`: $z=7$ outside sphere, `REFUSED` | Not independently verified live NL E2E |
| Cone-frustum residual volume | Certified parent-minus-upper-cone volume with direct formula check | Supported scalar certificate for parallel cut | Parent/upper cone, cutting circle/plane, scalar residual; no residual frustum mesh | `demo6b` verifies parent/upper cone and parallel cutting circle; axial triangle `td_sec_axial` visibility remains OPEN | No standalone frustum-mesh claim |
| Standalone `cone_frustum` | **BLOCKED_BY_KERNEL** | Explicit refusal; unchanged | No scene | No standalone frustum demo | **BLOCKED_BY_KERNEL** |
| Cylinder/cone oblique ellipse | Finite-solid cap/boundary restrictions enforced; parabola/hyperbola/clipped ellipse refused | Backend positive corpus cases `pos_09` / `pos_10` produce `ellipse3` | Existing `ellipse3` output | **BACKEND_ONLY** in this repair; optional `ADDITIONAL_BROWSER_VALIDATION` omitted | No new live NL or browser ellipse claim |

## Residual object distinction

- **A** = original pyramid/solid mesh.
- **B** = constructed upper sub-solid.
- **C** = exact cutting polygon/plane.
- **D** = certified scalar residual volume.
- **E** = actual independently constructed residual polyhedral mesh.

A–D are present in relevant existing demonstrations. **E is `NOT_IMPLEMENTED`**. Neither a scalar volume nor overlaying parent/cut solids qualifies as E. The cone case likewise has no standalone or residual frustum mesh.

`typed_fact_next.py::SimulationGoalSpec` offers `construct_derived_solid` with `apex_ref` and `section`; `adapter3_simulation.py::_compile_derived_solids_and_goals` compiles it as `fn="pyramid"`. No `DerivedSubSolidSpec` or `frustum_like` exists in `backend/app`. This corrects a documentation claim without removing supported derived pyramids or sections.

The authoritative inventory is eight positive Scene3D demos and one fail-closed refusal (`demos/demo1..demo7*.json`). The original development corpus has ten positive and five negative cases, including the two backend ellipse cases (`pos_09`, `pos_10`). `OFFLINE_SIMULATION_E2E` does not establish `LIVE_NATURAL_LANGUAGE_PRODUCT_E2E`. All earlier scientific classifications, including SGH/BH2A/BH2C limitations, remain unchanged.

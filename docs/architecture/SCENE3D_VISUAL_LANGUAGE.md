# Scene3D semantic visual language

Local product candidate, 2026-10-22; human visual approval **NOT_GRANTED**. Evidence: [run plan](../evaluation/geometry/runs/scene3d-unified-visual-language/plan.md) and [source token audit](../evaluation/geometry/runs/scene3d-unified-visual-language/SCENE3D_DESIGN_TOKEN_AUDIT.md).

Root [DESIGN.md](../../DESIGN.md) defines UI colors/type, not WebGL materials. This explicit Scene3D extension uses its quiet canvas, structural ink and simulation sticker palette. Light amber section fill and deep teal auxiliary ink are additional semantic tokens. Original DESIGN.md values remain unchanged.

`scene3d-roles.ts` owns existing causal roles (`MAU_VAI_TRO`) and typed Scene3D styles (`PHONG_CACH_SCENE3D`). CSS role copies are checked against that source; Three.js receives numeric sRGB colors, not CSS custom properties. No product theme selector is introduced.

| Role | Rule |
|---|---|
| Primary / secondary solid | Common lit shell policy across polyhedra, cylinder, cone and sphere; sky / teal from DESIGN. First constructed solid in the complete scene is primary; subsequent solids secondary. Ties use stable machine ids. Visibility, isolation, array order and step never reassign colors. Existing labels/tree/notation/topology identify each solid independently of color. |
| Visible / hidden structural edge | Charcoal solid line / quieter dashed ink; existing camera classifier and one visual owner. Highlight changes emphasis, never dash semantics. |
| Given / derived point | Neutral charcoal / deep purple; screen-sized markers and learner notation retain their existing owners. |
| Base region / structural face | Structural sky fill, separate from section amber; metadata and formation roles decide meaning. |
| Constructed plane / auxiliary line | Light purple sheet with deep outline / deep teal line. Infinite objects remain subordinate and excluded from camera bounds. |
| Section fill / outline | Common unlit light amber / orange across polygon, circle, ellipse and Adapter /3 auxiliary section polygons. BASE_REGION or CONSTRUCT_BASE takes precedence; otherwise every region type, including a metadata-free `polygon3` from a pre-metadata envelope, falls back to section alike. |
| Selected / newly constructed | DESIGN primary blue plus existing marker/width/inspector/step cues. Numerical given/intermediate causal roles retain their distinct oranges. |
| Context / faded / hidden | Existing neutral context; unrelated objects fade; explicitly hidden objects are omitted. Isolation changes visibility, not palette. |
| Hover | Existing pointer/UI affordances; no new WebGL hover state. |

Flat fills and rim ribbons need one draw submission. This does not claim every two-pass flat sheet double-blends: culling matters. Lit closed shells retain existing two-sided rendering. Alpha is per role; two independently overlapping layers at alpha a compose to 1-(1-a)^2, not to a global opacity correction.

The [occlusion contract](OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md) remains authoritative: back depth prepass 5, section fill 7, curved front depth prepass 7.5, lines 8, section rim 10. Normal respects solid depth; X-ray is explicit. Auxiliary/section fills never become solid occluders. Camera safe-area logic, coordinates, triangulation, topology and mathematical authority remain unchanged.

Line materials belong to each visual owner. Orbit changes span geometry but reuses encountered semantic material styles. Owner rebuild/unmount releases both attached and inactive pooled resources. First use of an unseen style can allocate; there is no global material cache.

Automated technical results, independent code review and Owner visual acceptance are separate. Offline authored scenes do not establish live NLU E2E; SwiftShader does not establish physical-device FPS.

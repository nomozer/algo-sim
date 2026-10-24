# Scene3D semantic visual language

Local product candidate, 2026-10-22; **amended 2026-10-24 (SGK_REFERENCE)** to port the owner's reference `matphanghinhchot.html`; human visual approval **NOT_GRANTED**. Evidence: [run plan](../evaluation/geometry/runs/scene3d-unified-visual-language/plan.md), [source token audit](../evaluation/geometry/runs/scene3d-unified-visual-language/SCENE3D_DESIGN_TOKEN_AUDIT.md), and the SGK port run [`scene3d-html-visual-port`](../evaluation/geometry/runs/scene3d-html-visual-port/FINAL_OWNER_HANDOFF.md).

Root [DESIGN.md](../../DESIGN.md) defines UI colors/type, not WebGL materials. This explicit Scene3D extension follows the owner's SGK visual reference: ivory canvas, slate ink, terracotta section, violet cutting plane, teal auxiliary ink. Original DESIGN.md values remain unchanged; only the 3D canvas background changes.

`scene3d-roles.ts` owns existing causal roles (`MAU_VAI_TRO`) and typed Scene3D styles (`PHONG_CACH_SCENE3D`). CSS role copies are checked against that source; Three.js receives numeric sRGB colors, not CSS custom properties. No product theme selector is introduced.

| Role | Rule |
|---|---|
| Primary / secondary solid | Common **unlit** shell policy across polyhedra, cylinder, cone and sphere: porcelain `#7C8B9E` (secondary teal-slate). Polyhedra draw a BackSide pass at `shellBackRatio` (0.75) × opacity then a FrontSide pass (reference `addPolyhedronShell`, default 0.12); curved shells one unlit DoubleSide pass. First constructed solid in the complete scene is primary; subsequent solids secondary. Ties use stable machine ids. Visibility, isolation, array order and step never reassign colors. Existing labels/tree/notation/topology identify each solid independently of color. |
| Visible / hidden structural edge | Slate `#1E293B` solid / `#64748B` dashed (opacity 0.78); existing camera classifier and one visual owner. Screen-space widths (`fatPx`, 3.6 / 3 px at a 720 px canvas, scaled by canvas height ×0.62–1.25). Highlight changes emphasis, never dash semantics. |
| Given / derived point | Neutral charcoal / terracotta; screen-sized markers and learner notation retain their existing owners. Label style by role only (`.geo3d-label` haloed ink; `.vai-thiet-dien` terracotta box for points at a section vertex; `.vai-phu` teal box for other derived points) — never a new name for an unnamed point. |
| Base region / structural face | Structural porcelain fill, separate from section terracotta; metadata and formation roles decide meaning. |
| Constructed plane / auxiliary line | Violet `#6D28D9` sheet at 0.065 with an **always dashed** violet border (0.55), with or without a closed section — the finite patch is a representation of an infinite plane, never a solid edge / deep teal line. Infinite objects remain subordinate and excluded from camera bounds. |
| Right-angle mark | Two-segment square from the backend-certified unit directions; per-frame screen size ≈ 0.014 × canvas height clamped to 8–12 px, capped at 0.3 × the related segment; duplicates at the same foot and direction pair are hidden. |
| Section fill / outline | Common unlit terracotta `#C85A32` fill (0.32 — reference 0.27 measures ΔE76 ≈ 17 < 20 on `SECTION_FILL_DISTINGUISHABLE`; owner chose the smallest passing value) / outline across polygon, circle, ellipse and Adapter /3 auxiliary section polygons. BASE_REGION or CONSTRUCT_BASE takes precedence; otherwise every region type, including a metadata-free `polygon3` from a pre-metadata envelope, falls back to section alike. |
| Selected / newly constructed | DESIGN primary blue plus existing marker/width/inspector/step cues. Numerical given/intermediate causal roles retain their distinct oranges. |
| Context / faded / hidden | Existing neutral context; unrelated objects fade; explicitly hidden objects are omitted. Isolation changes visibility, not palette. |
| Hover | Existing pointer/UI affordances; no new WebGL hover state. |

Flat fills and rim ribbons need one draw submission. This does not claim every two-pass flat sheet double-blends: culling matters. Closed polyhedral shells are two unlit passes with bounded compound alpha (front a, back 0.75a); no lighting enters any Scene3D color. Alpha is per role; two independently overlapping layers at alpha a compose to 1-(1-a)^2, not to a global opacity correction.

Camera: the scored view selector is unchanged (thresholds still measured from `HUONG`); its familiarity pull targets `HUONG_SGK` (azimuth of `HUONG`, elevation 22.4° = the reference "Góc SGK") with weight 2. The reference's fixed camera, sheared base coordinates and face-normal visibility heuristic are not adopted.

The [occlusion contract](OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md) remains authoritative: back depth prepass 5, section fill 7, curved front depth prepass 7.5, lines 8, section rim 10. Normal respects solid depth; X-ray is explicit. Auxiliary/section fills never become solid occluders. Camera safe-area logic, coordinates, triangulation, topology and mathematical authority remain unchanged.

Line materials belong to each visual owner. Orbit changes span geometry but reuses encountered semantic material styles. Owner rebuild/unmount releases both attached and inactive pooled resources. First use of an unseen style can allocate; there is no global material cache.

Automated technical results, independent code review and Owner visual acceptance are separate. Offline authored scenes do not establish live NLU E2E; SwiftShader does not establish physical-device FPS.

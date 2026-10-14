# Bounded Scene3D reuse inventory

Source inspected at2a3c0787. No browser rerun or UI changes. Existing product features are not judged by what one research
harness happens to display. Current issue `ISSUE-ARCH-SCENE3D-CONSTRUCTION-READABILITY` and orbit issues remain OPEN.

| Requirement/component | Classification | Existing owner / consumer / connection |
|---|---|---|
| Workspace and Explorer | REUSE | `scene3d-view.tsx::Scene3DWorkspace`, `Scene3DExplorer.tsx` passes scene/frame/selection; research TSX harness imports the same Workspace |
| Exact chart→world transform | REUSE | `scene3d-chart.ts`, renderer qHienThi/Gram mapping; never change coordinates/Kernel for visual choices |
| Orbit/zoom/reset | REUSE | view.tsx OrbitControls:1520, camera/reset helpers near595; Explorer controls connect through workspace; old orbit instability remains |
| Default camera from above | ADAPT | Existing initial/fit/reset pose in view.tsx; adjust policy only in future presentation scope, not one fixed angle for all families |
| Reference background | ADAPT | Explorer:466 passes gridShown={luoi}; view.tsx:1859–1876 creates GridHelper. Toggle already exists; current square grid differs from sparse faint diagonal reference |
| Point labels | REUSE / ADAPT | `scene3d-presentation.ts::locNhanChongNhau` real label boxes; view label layer uses notation; placement/overlap tuning uses existing path |
| Plane name `(P)` on canvas | MISSING glyph / ADAPT metadata | Named plane notation/picker metadata exists; canvas labels are point anchors. Add an anchored caption later, not a new plane renderer |
| Selection/highlight | REUSE / ADAPT | `highlightSet`, `tangNhanManh`, selected_id in view:1417–1437 and2038; adjust attenuation for H/H1, reuse interaction owner |
| Dimming/opacity | ADAPT | view.tsx materials and scene3d causal colors/presentation; current dimming exists, no new mechanism needed |
| Hidden lines | REUSE | Existing scene3d occlusion/view segment owners and tests; preserve solid occlusion and representative orbit acceptance |
| Plane/section meshes | REUSE / ADAPT style | view.tsx:893,1204–1213 draws planes/section fill/progressive boundaries; use visual hierarchy, not new geometric entities |
| Auxiliary vector arrows | MISSING drawable | scene3d-model.ts:105 explicitly says vector3 is present but not drawn. IR vector capability exists; dedicated arrows are future presentation work |
| Projection foot/witness | REUSE | `function_route._gan_nhan_chung_hinh_chieu`, quantity_annotations `_nhan_chung`; matches projected point coordinates and supplies perpendicular witness |
| Playback/learner steps | REUSE | model::objectsAt, geometryTimeline:1090, next/prevGeometryStep; player/Explorer read frame k=trace[k] and formation visibility |
| Browser evidence | REUSE | `hybrid-section-visual*.tsx/mjs`, existing Playwright setup; can load future scene package, test every step/selection/forward-backward |
| Duplicate implementation | DUPLICATED: none established | Multiple harness entry points reuse product Workspace; differing evidence scopes are not a proven duplicate renderer. No consolidation proposed |

Next Planner slice requires no frontend implementation. Acceptance must render the existing derived line and projection foot
after dependencies using current harness, plus a refusal scene. This inventory does not implement camera, grid, captions or arrows.

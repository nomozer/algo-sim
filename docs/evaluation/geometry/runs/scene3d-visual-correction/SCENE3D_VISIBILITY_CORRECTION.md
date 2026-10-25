# Scene3D visibility correction

What changed in the renderer, why, and how each change is locked. Codex (C) and Claude (Cl) parts are marked. Frontend
presentation only: no backend fact, coordinate, name or entity is created; the scene JSON is unchanged by building,
selecting or rotating (`leaves scene geometry and authoritative data unchanged…`, and the browser matrix's
`geometry_unchanged` check).

## 1. Curved occlusion is now exact (C)

`scene3d-edge-visibility.ts::diemVanhCongBiChe` replaced sampled heuristics with closed-form tests along the ray from the
point to the eye, `t ∈ [0, 1]`, no fixed fraction discarded:

| Solid | Before | After |
|---|---|---|
| Ball | "near-surface" band `|d − r| ≤ 0.08 r` plus a 15 % view-angle threshold; ray clamped to `t ∈ [0.01, 0.985]` | closest approach of the segment to the centre, strict `< r²` |
| Cylinder | 4 samples along the ray; radius shrunk by 0.4 %; height trimmed by 0.2 % | clip to the finite axial slab, then the minimum of the radial quadratic on that interval |
| Cone | same samples with `r(1 − z/h)` | the same quadratic with the radius varying along the ray (axial slope included) |
| Transformed scenes | ray in world coordinates against volumes in local coordinates | `worldToLocal` applied to both the point and the eye |

The same classifier now serves polyhedron edges (`classifySolidEdgeVisibility`), free segments
(`classifyWorldSegmentVisibility`, including a zero-length rim sample) and the curved rims. One authority, no second
visibility rule.

Locks (`scene3d-unified-materials.test.ts`, "curved visibility follows the ray and finite solid"):
sphere point just beyond the perspective silhouette; a small sphere far along the ray; cylinder and cone sides against an
independent outward normal over 3 × 48 camera positions; cylinder caps including axial and bottom views; a line split
VISIBLE/HIDDEN/VISIBLE by a ball and reversing with the camera.

## 2. Camera-tangent silhouettes for curved solids (C)

`updateCurvedSolidSilhouette`: the sphere outline is the true perspective tangent circle (not an equator); cylinder and
cone get two tangent generators in any axis orientation (cone: `cos = r(1 − axial/h)/d`, from projecting the eye through
the apex onto the base plane), plus their physical cap rims. Locks: `sphere outline is the camera tangent circle…`,
`%s renders its physical rims and camera-tangent generators without inventing scene entities` (asserts
`normal · (eye − p) = 0` at three cameras and that the scene object is not mutated).

## 3. Selected rim drawn over solid outlines (Cl)

Found in the browser: on the p6 oblique cylinder cut, the navy cylinder generator overdrew the cobalt boundary of the
selected ellipse near tangency (role-aware probe, `BOUNDARY_NOT_COBALT` on front chords 44–46 at the "high" camera).

Root cause: three.js draws the whole opaque queue before the transparent one, and `renderOrder` orders only within a
queue. Solid outlines are deliberately in the transparent queue (`canonicalEdgeMaterial`: "opacity 1, so renderOrder
places lines after fills"). The front rim mesh was the only opaque stroke, so it was drawn first and lost to every
outline regardless of `THU_TU_VE_THIET_DIEN = 10 > THU_TU_DUONG = 8`.

Fix: the front rim material joins the same queue (`transparent: true`, opacity stays 1) in both the circle and the
ellipse builders. Lock: `queues the front curve rim with the solid outlines so it is drawn over them` (RED before: the
rim's `transparent` was `false`).

## 4. Curve rims no longer vanish when seen obliquely (Cl)

Found in the browser: at the "quarter" camera (390 px) the hidden arc of the p6 ellipse had 19/499 cobalt samples. The
renderer's own hidden flags and the oracle's agreed chord for chord (checked by importing the product modules into the
page), so classification was right and the ink was missing.

Root cause: a circle/ellipse rim is a flat ribbon lying in the region's own plane. When that plane is seen nearly
edge-on, the ribbon's screen width falls below one pixel and rasterizes nothing; the dashed hidden arc (every other
pair of chords) went first. Polygon section borders are 1 px GL lines and never had this problem. The Owner HTML
reference avoids it by drawing tubes (`HTML_REFERENCE_COMPARISON.md` §3).

Fix: `themNetVanh` adds a 1 px `LineSegments` stroke along the outer curve for the front and hidden parts. It **shares
the ribbon's material** (colour, opacity, depth state, selection/hover colour cannot diverge) and is filled in the same
in-place buffer pass (`capNhatHinhHocVanhCong`, preallocated, `setDrawRange`), so camera moves allocate nothing new.
Lock: `strokes every drawn rim chord with a 1px line…` (stroke shares both materials; stroke chord count equals ribbon
chord count before and after two camera updates with a curved occluder; some chords are hidden in the side view).

## 5. Hover vs selection (C)

Hover emphasis is a distinct state (`"hover"`): neutral line colour, unchanged terracotta fill opacity, no cobalt.
Hover is cleared when the scene changes and is never applied to the selected object or a target. Lock:
`hover is distinct from selection and preserves the neutral section fill`, plus `scene3d-focus-mode.test.tsx`.

## 6. Fixes from the internal review (`REVIEW_REPORT.md`)

Codex's curved-solid additions had four side effects. All four were fixed with RED-first tests in `093c0b4c` and
`78aaef2f`:

- **Stray unit ring at the origin.** A secondary sphere's silhouette was never placed. It is now placed, and every
  silhouette stays hidden until a camera update places it.
- **Duplicate cap rims.** A curved solid's own cap rims duplicated the backend's base circles, and in family 10 one was
  drawn over the selected section. The solid's own rim is now dropped when a visible backend circle has the same
  centre, radius, axis and translation.
- **Polyhedron edges dashed by a curved solid.** An enclosing sphere dashed every edge of an inscribed polyhedron.
  Polyhedron edges now follow solid faces only, as at base and in the Owner reference.
- **Crashes on the cap-rim path.** A cylinder or cone axis with fractional coordinates threw in the coordinate parser,
  and a cylinder given by height lost its top rim.

One related convention is left to the Owner: free segments and section borders inside a sphere are still dashed.

## 7. Results

| Check | Result |
|---|---|
| Geometry-domain vitest at `78aaef2f` | 839/839 |
| Role-aware baseline, 3 shapes × 2 widths × 5 cameras, before §3–§4 (`verification/role-baseline-before-rim-fix`) | 18 PASS · **4 FAIL** (all p6 ellipse) · 8 UNCERTIFIABLE |
| Same, final code `78aaef2f` (`verification/role-aware-final`) | 19 PASS · **0 FAIL** · 11 UNCERTIFIABLE; 0 retries, 0 error rows |

Per-view transitions of the four p6 FAILs:

| View | Before → after |
|---|---|
| 390 low | FAIL → PASS |
| 1440 quarter | FAIL → UNCERTIFIABLE |
| 390 quarter | FAIL → UNCERTIFIABLE |
| 390 half | FAIL → UNCERTIFIABLE |

The p6 ellipse is certified in 4 of 10 views (1440: default, high, low; 390: low). An UNCERTIFIABLE view is one where
DOM labels cover part of the boundary: every unscored chord had zero visible samples. Such a view is not counted as a
pass. In the unfaulted runs, no view that was UNCERTIFIABLE had a scored part failing.

Fault matrix results: `OFFICIAL_VISUAL_SUITE_RESULTS.md` §3.

# Internal separate-context review — round 1 (verbatim)

Reviewer: a Claude agent with a fresh context, spawned by the author session. **Internal, not independent.** Brief:
`internal-review-brief.md`. Scope: `git diff fe5f40b7` of the working tree, before the review fixes. Read-only. Its
scratch probes are outside the repository and were not committed.

---

**Internal separate-context review** of `git diff fe5f40b7` (working tree), in the scoped files only. This is not an
independent review. I edited no repo files and ran no state-changing git. Baseline checks: the geometry domain vitest
passes 834/834, and `node --test scripts/section-role-oracle.node-test.mjs` passes 21/21.

## Critical

**C1. A secondary ball draws a stray unit circle at the scene origin.** `scene3d-view.tsx:1873-1882` together with
`:3533-3534`.
- In the workspace, a secondary curved solid that shares the primary's translation has its `curvedSolidVolume` deleted.
- `updateCanonicalEdgeVisibility` only calls `updateCurvedSolidSilhouette` for nodes that still have that metadata. The
  new `sphere_silhouette` ring therefore never gets positioned and stays visible: radius 1, centred at local (0,0,0),
  facing +z.
- Scenario: `scene3d-circumsphere-fixture.json` (real backend output, OABC is listed before the circumsphere). The ring
  lands on vertex O, while the sphere centre is (1,1,1). That is invented geometry on the canvas.
- **Reproduced** (probe3, which mirrors line 3534): `ring visible true world centre [0,0,0] scale [1,1,1] true sphere
  centre ["1","1","1"]`. Not checked in a browser.

## Important

**I1. The curved solid now draws its own cap rims, which duplicate rims the backend already emits and can cover a
selected section's cobalt boundary.** `scene3d-view.tsx:1883-1893`.
- Route D (`adapter3_simulation.py:2239+`) already emits `duong_tron_day_*` and `duong_tron_day_tren_*` as circle3
  objects with the same centre, normal and r². With this change every base and top circle is drawn twice. Each logical
  boundary should have one visual owner.
- Worse case, `family10_cone_frustum_cut`: `khoi_cone_upper` (scene object 17) gets a navy base rim at exactly the
  selected section circle `td_sec_cut` (object 12). Both rims are built at centre (0,0,2), outer radius 1.5,
  renderOrder 10, transparent queue, depthWrite true, LessEqual depth.
- The later-built navy rim is therefore drawn over the outer band of the cobalt ribbon and over its 1px stroke, which
  breaks F2.
- The frontend rim also appears at the solid's step, before the backend circle's own step. That cuts against invariant
  #31 (frame k ⇔ trace[k]).
- **Reproduced** structurally (probe2): `td_sec_cut … outerR 1.5000 … color 2563eb renderOrder 10` and
  `khoi_cone_upper … outerR 1.5000 … color 1e293b renderOrder 10`. The draw order is reasoned from how three.js sorts
  transparent objects, not measured in pixels.
- None of family09, family10 or family12 is covered by the default `--audit` regex in `browser-matrix.mjs:26`, nor by
  the role probe's cases.

**I2. A curved solid now hides every edge of a polyhedron inscribed in it.** `scene3d-view.tsx:985`, which passes
`curved_occluders` into `classifySolidEdgeVisibility`; segments get the same treatment at `:784` and `:851`.
- A ball is opaque to the new classifier, so every chord of an inscribed tetrahedron becomes dashed.
- **Reproduced** (probe on the circumsphere fixture, camera (12,9,10)): without the ball, AB, AC, BC visible; with the
  ball, all six edges hidden.
- In the workspace this is masked only when the curved solid comes after the polyhedron, at the same translation (the
  deletion at line 3534). It shows up when the curved solid is primary or is displaced. The owner needs to decide the
  convention.

**I3. The supplemental oracle passes a frame that is missing most of a hidden curve arc.**
`section-role-oracle.mjs:147-163`.
- Hidden ink is scored per maximal hidden arc, against `hiddenCoverage` 0.4, which leaves a lot of slack.
- **Reproduced** with a synthetic 96-chord curve using the renderer's 2-on/2-off dash pattern, removing one contiguous
  piece of the hidden arc: 0 %, 25 %, 40 %, 50 %, 55 % missing → PASS; 60 % → PASS (coverage 0.45); 65 % → FAIL.
- Real browser arcs measure 0.7–0.9, so the practical tolerance is roughly 45–55 % missing.

**I4. "0 FAIL after §3–§4" is partly FAIL turning into UNCERTIFIABLE.**
- From the receipts: three of the four p6 FAILs before the fix (1440 quarter, 390 quarter, 390 half) are UNCERTIFIABLE
  in `role-aware-final`; only 390 low became PASS. That includes 390 quarter, the frame that motivated §4.
- 7 of 10 p6 views are uncertifiable, and 55 fault rows were excluded.
- I found no case where UNCERTIFIABLE hides a failing scored part, because FAIL dominates. But one unscored chord is
  enough to make a view UNCERTIFIABLE, and the exit code accepts a single certified view per case.

## Minor

- **M1.** `scene3d-view.tsx:1889`: the `!` on the recursive `buildObject3D` result crashes when an envelope carries
  `rim_point` without `radius_sq`. The guard at line 1824 allows that combination. **Reproduced**: `TypeError: Cannot
  set properties of null (setting 'raycast')`. The current backend always emits `radius_sq`, so this is latent.
  Separately, `rim.raycast = () => {}` on a Group does not stop its children from being picked; they resolve to the
  solid's id, so this is harmless today.
- **M2.** Hover is distinct by colour only. `"hover"` is truthy, so it still gets the selected widths. Reasoned.
- **M3.** At `scene3d-view.tsx:1044`, each rim midpoint goes through `classifyWorldSegmentVisibility(wPt, wPt, …)`. On
  the zero-length path that rebuilds `occludingTriangles` for every solid: 96 times per rim, on every camera change.
  Per-move JS allocation; the orbit gate only counts GPU buffers. Reasoned.
- **M4.** Oracle self-description no longer matches the code (threshold history, hard-coded RGB); `FILL_NOT_TERRACOTTA`
  and `FILL_COLOR_DISTANCE` test the identical condition; the oracle shares the renderer's discretisation and ring
  frame; `otherBoundaries` skips samples inside the selected boundary's band, so it cannot see the I1 overlap.
- **M5.** `browser-matrix.mjs` `mode_b_once` only inspects the first analysis item, and ignores values printed elsewhere
  in the inspector or in the quantity table. Line 85 is a ternary whose two branches are identical.
- **M6.** Camera inside a ball → everything hidden and the silhouette disappears; grazing rays along a cap plane count as
  visible. Acceptable edge cases.

## Areas with nothing found

- Occlusion and silhouette maths: ball closest approach, cylinder/cone slab clipping, the radial quadratic (signs of
  `qa`, `qb`, `dr`; concave case falling back to endpoints), the cone tangent formula with the eye above the apex, the
  cylinder case with the eye inside the infinite cylinder, `worldToLocal` composition. The oracle's ellipse frame
  matches the renderer's `(M, m)`.
- Mode A/B: no leak found.
- Disposal: no double dispose or leak (`disposeScene3DObject` dedups materials and geometries).
- Render order: the `transparent: true` change touches only the front rim material.
- R0 and hard-coding: none found; no scene mutation.

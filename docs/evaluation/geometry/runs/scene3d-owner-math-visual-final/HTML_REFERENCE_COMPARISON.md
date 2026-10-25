# Owner HTML reference — what was learned and what was rejected

## Source actually read

- **Read:** `C:\Users\Bunny\Downloads\matphang.html`, 207 567 bytes, 2026-10-24 17:36.
- **Hash:** SHA-256 `279216192b09d6e12c8b8d444dcb0bf943419e6c52078fe04107684f0d9e8af1`, byte-identical to the repository copy
  `docs/evaluation/geometry/runs/visual-closure-hybrid-readiness/reference/matphang.html` (after CRLF→LF).
- **Attachment:** the document attached to this brief has the same functions and structure; its bytes are not on disk,
  so it is not hashed separately.
- **Not found:** no file named `matphang(3).html` exists on this machine. If it differs from the file above, it was not
  read, and nothing here is claimed about it.

The reference is an authority on **presentation** only. It is not an authority on mathematical correctness.

## Table

| Reference does | Taken / Rejected | Why | AlgoSim instead |
|---|---|---|---|
| `addRepresentedPlane`: border segments drawn solid where visible, dashed where a 3D solid hides them (`addSolidOccludedLine`, `ignorePlanes`) | **Taken** (F1) | The Owner's own rule ("don't dash the whole border") and the reference agree. An earlier AlgoSim port had wrongly read "always dashed" from `addCuttingPlanePatch` | The same classifier as real edges decides each border span; the border keeps a thin, light violet stroke |
| Visibility of border/line samples: `isPointOccludedBySceneSolids` with fixed margins (0.016, 0.02) and, for cylinders and cones, 8–11 sampled ray parameters | **Rejected** | Sampled and margin-based; misses thin crossings; scale-dependent | Exact ray–finite-volume test (`diemVanhCongBiChe`) and the polyhedron classifier |
| Polyhedron edges: solid iff an adjacent face faces the camera | Equivalent for convex solids; **kept AlgoSim's** classifier | — | Partial spans are split per segment instead of one style per edge |
| `addRightAngleMarker`: fixed world size (0.28–0.36), drawn wherever the scene code chooses | **Rejected** | A fixed world size is tiny far away and huge up close (the Owner forbids it); and the marks are placed by hand-written scene code, not by a verified relation | Screen-sized 12–18 px (F2), drawn only from backend witnesses (`u ⊥ v` exact), one per relation by default (F3) |
| Many marks per figure (e.g. at A on both SB and SD, at K, at B) | **Rejected** as a default | Too many marks (Owner P3) | One representative per relation; others when selected or emphasised |
| Section polygon: exact plane ∩ faces, edges bound to host faces | Same principle; **kept AlgoSim's** backend sections | The backend computes the section exactly; the frontend only draws it | — |
| `pointOnSegmentWithPlane` clamps `t` into [0.05, 0.95] | **Rejected** | It forces the intersection onto the segment, a fake point when the plane misses it | Backend sections; a plane that doesn't cut is refused (`PLANE_DOES_NOT_CUT`) |
| Arcs: per-mode shortcuts (`cylinder_top`: `camera.y > center.y`; `lateral_split`) and a cone silhouette with the cylinder's tangent formula | **Rejected** | They assume a vertical axis; the cone formula is wrong (it ignores camera height) | Exact tangent generators and classification for any axis |
| Camera: hand-written spherical orbit, `mousemove` on window, no damping, full `updateViewDependentVisibility` on every move event | **Rejected** (Owner P5) | The jerky rotation and label motion the Owner reported | AlgoSim's OrbitControls kept unchanged |
| Labels: offset radially from the model centroid by a fixed push, every frame, no collision handling | Idea "push away from the figure" already in AlgoSim; **rejected** the rest | No collision handling; labels overlap | AlgoSim's scored placement, now with frame-to-frame hysteresis (F5) |
| Shell 12 %, terracotta sections, violet planes, cobalt lines | **Taken** (already in AlgoSim) | Matches the Owner's colour policy (P7) | Unchanged; the selected boundary is cobalt, the fill stays terracotta |
| Final values shown at once as decimals on side cards | **Rejected** | Mode A/B policy and exact values | Unchanged |
| Geometry sliders (move vertices, the plane, radii) | **Rejected** | The frontend must not change geometry (R0, invariant #31) | Unchanged |
| Background, sidebars, page layout | **Not touched** | Owner P1: the web UI is being rebuilt separately | — |

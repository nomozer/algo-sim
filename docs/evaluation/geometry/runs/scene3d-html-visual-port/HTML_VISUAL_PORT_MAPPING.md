# HTML reference → AlgoSim renderer mapping

Reference: owner file `matphanghinhchot.html` (on-disk copy SHA-256 `9f09b7f412d13371…`, 2256 lines, rendered unmodified). It is a **visual** authority only. Its geometry is hand-built (`SHAPES_DB`) and not used.

| Reference function / value | What it does | AlgoSim counterpart | Ported? |
|---|---|---|---|
| `PALETTE` inkSolid `#1E293B`, inkDashed `#64748B`, porcelainShell `#7C8B9E`, tealAccent `#0F766E`, terracotta `#C85A32`, violetPlane `#6D28D9` | Semantic colors | `scene3d-roles.ts::PHONG_CACH_SCENE3D.colors` (`canh`, `hiddenEdge`, `mesh`, `line`, `polygon`/`sectionOutline`/`derived`, `surface`/`planeOutline`) | Yes, identical hex |
| `addPolyhedronShell` | Two `MeshBasicMaterial` passes, BackSide at `opacity×0.75`, then FrontSide at `opacity`, `depthWrite:false` | `scene3d-view.tsx::voKhoiHaiLuot` (renderOrder −1 / 0); depth prepass `lopChieuSau` kept for occlusion | Yes; default opacity 0.12, back ratio 0.75 |
| Curved shells (`opacity×1.15`, MeshBasic) | Unlit sphere/cone/cylinder | `curved_solid` branch → `MeshBasicMaterial`, DoubleSide | Unlit yes; the ×1.15 factor not ported (single shell opacity) |
| `addPolygonSection` | Terracotta fill 0.27 (DoubleSide, unlit) + 0.035-radius outline, vertex dots | Section fill/outline in `buildObject3D` (already unlit), color `#C85A32` | Color yes; fill **0.32**, owner decision so `SECTION_FILL_DISTINGUISHABLE` passes (reference 0.27 gives ΔE76 ≈ 17 < 20) |
| `addCuttingPlanePatch` | Fixed 6.2×5 rectangle around a hand-placed centre, violet 0.065, dashed border 0.55 | Data-derived plane patch (`daGiacMatPhang` / `moRongDaGiacMatPhang`), violet 0.065, border always dashed `LineDashedMaterial` 0.55 | Look yes; shape stays engine-derived (a finite representation of an infinite plane) |
| `addFixedEdge` / cylinder segments, radius 0.026–0.035 | World-space thick lines | `Line2` screen-space strokes (`dongBoNetDayManHinh`), widths `PHONG_CACH_SCENE3D.fatPx` × `heSoNetTheoKhung(canvasHeight)` | Thickness ratio yes (edge ≈ 0.008 × figure height); world-space cylinders not used |
| `addDynamicPolyEdge` + `updateViewDependentVisibility` (`n·v > −0.02` on adjacent faces) | Solid/dashed switch by face normals | `classifySolidEdgeVisibility` + per-span CPU occlusion (unchanged) | **No**: the heuristic is wrong for section edges and non-convex cases; the product classifier stays authoritative |
| Dash 0.17 / gap 0.12 | Dash cycle | `dash.relative` 0.044, `gapRatio` 0.72 | Ratio yes |
| `addRightAngleMarker` (two segments, size 0.34–0.36 world, stroke 0.021) | Right-angle square | `dauGocVuong` + `datCoGocVuong` (per-frame 8–12 px, capped by 0.3 × related segment, duplicate suppression) | Shape yes; size screen-adaptive instead of world 0.34 (owner: markers were too large) |
| `addViewSplitCircle` (`sin(angle) ≥ −0.05` in world space) | Front/back arc split for circles | Existing curved-rim CPU/GPU visibility | **No**: camera-independent split is wrong after any orbit |
| `pointOnSegmentWithPlane` (parameter clamped to [0.14, 0.86]) | Fake section points | Engine-certified section polygons | **No** (not geometry) |
| `updateFloatingLabels` + `.vertex-label.*` CSS | Projected DOM labels pushed outward from the centroid | Existing `tinhViTriNhanDiem` placement; new role classes `.vai-thiet-dien` / `.vai-phu` in `global.css` | Styles yes; placement algorithm stays AlgoSim's (it already avoids markers and edges) |
| `.academic-stage-light` radial gradient `#FFF → #F8F6F1 → #EFECE4` | Canvas background | `.geo3d-canvas` background only (page theme unchanged) | Yes |
| `camSpherical` θ 0.56, φ 1.18, r 11.8, FOV 40 ("Góc SGK") | Fixed camera | Scored view selector unchanged; familiarity pull → `HUONG_SGK` (elevation 22.4°), weight 2 | Elevation target yes; fixed camera no (would degenerate on other figures) |
| Base shear `sk = 0.85` baked into vertex coordinates | Fakes an oblique-projection drawing by distorting the 3D model | — | **No**: changes geometry; AlgoSim renders true coordinates |
| Bottom toolbar toggles (faces, labels, altitude, section, sphere, axes) and opacity slider | Demo UI | Existing "Hiển thị" menu (x-ray, measurements, "Hình phụ", grid) | Not ported (no website/UI redesign in scope) |

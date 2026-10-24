# Scene3D visual spec (from the owner's visual reference)

Status: `SCENE3D_VISUAL_SPEC_ONLY` for product code. No renderer, token or CSS file was changed in this run. Browser previews are runtime material overrides (see BROWSER_VISUAL_COMPARISON.md).

Source read in full: owner file `matphanghinhchot.html` (Three.js r128, Tailwind CDN, 12 hand-built shapes in `SHAPES_DB`) and the eight owner screenshots (S.ABCD with SA ⊥ base, regular S.ABCD, Oxyz intercept plane, cylinder, cone, sphere ∩ plane, oblique prism, S.ABC). This is a **visual reference, not a geometry authority**.

## 1. Two separate layers

| Layer | Owner | Rule |
|---|---|---|
| A. Website/UI (layout, type, sidebar, buttons, forms) | `DESIGN.md` / `tokens.css` brand tokens | Out of scope here; unchanged |
| B. Geometry visualization (edges, hidden edges, sections, planes, auxiliary, labels, transparency, camera) | `scene3d-roles.ts` + `scene3d-view.tsx` material tables | Colors carry mathematical meaning and must not follow brand color changes |

## 2. Reference values, read from the file (not from the brief)

| Role | Reference (file) | Product C0 `5ee97340` | Uncommitted WIP in root checkout (`PHONG_CACH_SCENE3D`) |
|---|---|---|---|
| Canvas | `#F8F6F1`, radial gradient `#FFF -> #F8F6F1 -> #EFECE4` | `#f8fafc` radial from `#fff`; comment deliberately rejects a warm tint on translucent faces | not changed |
| Visible solid edge | `#1E293B` | `#1E293B` (`MAU.canh`) | `#1E293B` |
| Hidden edge | `#64748B`, dashed, opacity 0.78 | same ink color, dashed, opacity 0.75 | `#475569`, opacity 0.56 |
| Section | `#C85A32` edges, fill opacity **0.27** (MeshBasic) | amber `#F59E0B`, fill **0.45** (MeshStandard, lit); locked by browser gate `SECTION_FILL_DISTINGUISHABLE` | fill `#F59E0B` 0.28, outline `#D97706` |
| Altitude / auxiliary | `#0F766E` | `#0F766E` (`MAU.line`) | `#0F766E` |
| Cutting plane | `#6D28D9`, fill **0.065**, dashed border 0.55 | `#7C3AED`, fill 0.11 / extended 0.09 | fill `#C4B5FD`, outline `#6D28D9`, 0.045 |
| Solid shell | `#7C8B9E`, front **0.12** + back 0.09 (`0.75×`), depthWrite off | `#647A96`, one DoubleSide mesh **0.22**, lit | `#647A96`, **0.16** |
| Derived point | section vertex: terracotta label box | `#DC2626` | `#C85A32` |
| Opacity slider | min 0.04, default 0.12, max 0.38, step 0.01 | none | none |

Reference sphere/curved shells use `opacity × 1.15`; cone/cylinder base discs `× 0.7–0.8`.

## 3. Contrast, measured with WCAG relative luminance (single-layer alpha model)

Front+back shell blend of `#7C8B9E` on `#F8F6F1`:

| Shell opacity | Edge `#1E293B` on shell | Hidden `#64748B` on shell | Section edge `#C85A32` on shell | Section fill 0.27 vs shell |
|---|---|---|---|---|
| 0.04 | 12.70:1 | 4.13:1 | 3.67:1 | 1.38:1 |
| **0.12** | 11.13:1 | **3.62:1** | 3.22:1 | **1.35:1** |
| 0.20 | 9.80:1 | 3.19:1 | 2.83:1 | 1.32:1 |
| 0.30 | 8.40:1 | **2.73:1** | 2.43:1 | 1.28:1 |

Consequences:
- At 0.12 every line role stays ≥3:1 (WCAG 1.4.11 non-text); at 0.30 hidden edges and section edges fall below 3:1. Default 0.12 is defensible; the slider should cap at ≤0.20 unless hidden ink darkens (WIP `#475569` gives 7.02:1 on bare canvas).
- A 0.27 section fill alone is barely distinguishable from the shell (~1.35:1). In the reference it reads by hue plus a 0.035 thick terracotta outline. That is why the product raised fill to 0.45 behind a measured gate. Lowering it requires re-running that gate, not editing its threshold.
- Amber `#F59E0B` (C0) is 1.99:1 on canvas as a line color; terracotta `#C85A32` is 3.92:1. Switching section **outline** to terracotta is a pure legibility gain.
- Model difference: the reference uses unlit `MeshBasicMaterial`; the product uses lit `MeshStandardMaterial` (ambient + directional). Numerical opacities do not transfer 1:1; compare in the browser, not by copying numbers.

## 4. What must not be copied

The reference creates geometry by hand. AlgoSim must not take that over:
- `pointOnSegmentWithPlane` clamps the parameter to `[0.14, 0.86]` and iterates on `x` only. Its section points are not plane intersections. Product sections come only from engine-certified polygons.
- Hidden/visible edges: the reference decides per edge with "any adjacent face front-facing (`n·v > -0.02`)". This is correct for convex solids with exact topology only. It is wrong for section edges: each one gets a single adjacent face index, so a section edge lying inside the solid is drawn solid. The product already uses `classifySolidEdgeVisibility` with per-span occlusion and certified edge ownership. That classifier stays authoritative.
- Curved shapes: the reference splits circles front/back by `sin(angle) ≥ -0.05` in world space, which is independent of the camera. That is wrong after any orbit. Adapter /4 does not serve curved solids (PLANNER_GENERALIZATION_GAP_REPORT.md), so no sphere/cone/cylinder support may be implied.
- `SHAPES_DB`, case-specific labels (`I₁, I₂, I₃`), Tailwind CDN, Three.js r128 CDN, Font Awesome: none are imported.

## 5. Recommended deltas, in priority order (not applied)

1. Section outline `#F59E0B -> #C85A32`; keep the fill hue family; re-run `SECTION_FILL_DISTINGUISHABLE` before changing fill opacity.
2. Solid shell default opacity 0.12, color `#7C8B9E`, rendered as BackSide (×0.75) + FrontSide passes so overlap stays bounded. It must not change depth layers (`lopChieuSau`), which decide edge occlusion.
3. Shell opacity slider 0.04–0.20 (not 0.38, see §3), applied to shell materials only, never to edges, labels or section fill.
4. Cutting-plane fill `#6D28D9` at ≈0.06 with dashed border; the plane must never sit above section fill in render order (current `THU_TU_TO_THIET_DIEN` keeps this).
5. Label classes: given points dark text with canvas halo; derived/section vertices terracotta boxed; auxiliary feet teal boxed; plane name violet italic. Product already distinguishes origin `free`/`derived` and provenance `DERIVED_FRESH`, so this is styling only.
6. Canvas warm tint `#F8F6F1`: **owner decision**. The product comment rejects warm tint under translucent faces; the reference uses it.

Items 1–4 overlap one-for-one with the uncommitted `PHONG_CACH_SCENE3D` rework in the root checkout (same constants, same files). They should be applied **inside that rework by its owner**, not as a parallel branch.

## 6. Camera

Reference "Góc SGK": spherical θ=0.56 rad, φ=1.18 rad, r=11.8, FOV 40°, target slightly above base. The product already fits the camera from scene bounds (`scene3d-camera.ts`). A preset only adds value if expressed relative to fitted bounds; copying absolute radius would break scenes of other sizes. Not implemented.

# Scene3D — Checkpoint C (Claude resume)

Status: **SCENE3D_VISUAL_PARTIAL_WITH_GAPS**. Author review only — not Owner visual approval
(`HUMAN_VISUAL_APPROVED = PENDING`), not an independent review.

## Starting point

Frontend `domains/geometry` was byte-identical from Claude `f3ae506c` to Codex `e336e0df`
(`../visual-source-continuity.json`), so the 204-frame matrix and 60 P0 frames in
`../../scene3d-to-hybrid-v2-replacement/` describe the inherited renderer. Those frames were re-read
for the Owner's list A–F (MNP pyramid, right-angle pyramids, standalone sphere, sphere ∩ (P),
cylinder ellipse, cone axial section). Nothing there was redone.

## Changes (each with a RED test first, then GREEN)

| commit | Owner item | what | test |
|---|---|---|---|
| `c5d65c7f` | C, F | Witness foot that **is** a drawn named point (foot A of SA ⊥ (ABCD)) no longer gets a second, orange "derived point" dot over the vertex and the mark's corner | `scene3d-right-angle-witness.test.ts` "chấm chân không chồng lên một điểm có tên" |
| `21af55bc` | F | Analysis panel: one row per coordinate assumption shared by several points (`Điểm A, B, C, D, S — …`) instead of five identical rows | `final-quality.test.tsx` "giả định dùng chung không lặp từng điểm" |
| `b12e93a0` | F | Non-clickable analysis rows (`<div>`) used the inherited 16 px while clickable rows (`<button>`) used the UA 13.3 px; one scoped declaration (`.geo3d-dai-luong .geo3d-tree-item`) | visual only |
| `3f42b52a` | C | Right-angle mark 12–18 px → **16–22 px** screen size (`perCanvasHeight` 0.022 → 0.026), still anchored in 3D and capped at 0.3 × the witnessed segment. At 390 px a 12 px mark at vertex A was mostly under the vertex dot | `scene3d.test.tsx` SGK size test (18.72 px at 720 px) |

No change to background, theme, home page, navigation, layout, camera controller, F2 colour policy
(terracotta fill, cobalt selected border) or any locked oracle.

## Evidence (0 provider calls, product store, `/api/*` stubbed)

- `p0-after/` (40 frames, tree `21af55bc`, clean), `p0-after-css/` (20), `p0-after-size/` (60, all three
  right-angle scenes × Mode A/B × 5 gestures × 1440/390): 0 page errors.
- Geometry domain vitest 866/866; geometry + components 1255/1255 before the size change; build PASS.
- `scene3d-orbit-gate` on `dist/`: **ĐẠT** (`docs/evaluation/geometry/scene3d-orbit-gate/v3/ORBIT_GATE.json`,
  0 GPU reallocations while orbiting).

## Seen and deliberately not changed (Owner decision)

1. Standalone sphere: the non-authoritative reference great circle's front arc is drawn heavier than the
   sphere's own silhouette. Mathematically correct (centre I, front solid / back dashed); a weight choice.
2. `vuong-goc-chop`: the measured line BC is drawn slightly beyond B and C in "đang xét" teal to show it
   is a line. Not an invented intersection; SGK figures usually stop at the endpoints.
3. `vuong-goc-chop` quarter orbit in Mode B: B and its mark leave the bottom of the canvas. Existing camera
   behaviour (Owner: keep the camera); "Xem lại toàn hình" refits.
4. Point markers on a heavy curve (sphere point A on the reference circle) are hard to see.
5. Official Visual Suite remains **7/8** (`cross_section`, locked F2 hue oracle vs the Owner's terracotta/
   cobalt policy) — inherited; not re-run here and not converted to 8/8.

## Not certified

Tangent / no-intersection sphere–plane browser rows, oblique-prism cutting planes, non-ellipse cone conics
(backend refuses), complete all-label overlap oracle, label-jump flags on cuboid/multi-solid (seven
heuristic flags from Codex #1 remain for visual review).

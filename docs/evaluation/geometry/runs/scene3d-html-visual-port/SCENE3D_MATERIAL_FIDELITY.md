# Scene3D material fidelity (SGK_REFERENCE)

All values are read from the reference file, not from the brief. Single authority: `scene3d-roles.ts::PHONG_CACH_SCENE3D`.

## Shell

| | Reference | AlgoSim before (V6.2 checkpoint) | AlgoSim after |
|---|---|---|---|
| Material | `MeshBasicMaterial` (unlit), BackSide `0.75×` then FrontSide | `MeshStandardMaterial` (lit, ambient 1.45 + directional 0.28), FrontSide only | `MeshBasicMaterial` ×2 (`voKhoiHaiLuot`), BackSide `opacity × shellBackRatio (0.75)` at renderOrder −1, FrontSide at 0 |
| Color / default opacity | `#7C8B9E` / 0.12 | `#647A96` / 0.16 | `#7C8B9E` / 0.12 (secondary solid 0.10, selected 0.20) |
| Depth | `depthWrite:false`, no prepass | depth prepass `lopChieuSau` | unchanged prepass `lopChieuSau`; both shell passes `depthWrite:false` |
| Curved shells | unlit, `×1.15` | lit DoubleSide | unlit DoubleSide (the `×1.15` factor is not ported) |

**Unlit for color-keeping layers: yes.** Every Scene3D region (shells, section, plane, faces) is now unlit, so lighting no longer shifts any semantic color. Light settings remain only for point markers.

**Does 12 % look like the reference?** Yes, within the limits of the screenshot comparison (HTML_VS_ALGOSIM_SCREENSHOTS.md). The shell is light porcelain. Front-over-back overlap is bounded (≈ 0.12 + 0.09 single-layer compound, about 20 %). Edges and dashed hidden edges stay legible. A 0.04–0.30 study is in the earlier B1/B2 run (`hybrid-primary-b1-b2-offline/verification/visual-reference/`). At 0.30, hidden edges fell to ≈ 2.7:1 contrast, which is why no larger default is used.

## Section

| | Reference | After |
|---|---|---|
| Fill | `#C85A32`, 0.27, unlit DoubleSide | `#C85A32`, **0.32**, unlit (owner decision) |
| Outline | `#C85A32`, radius 0.035 | `#C85A32`, Line2 4.5 px solid / 3.7 px dashed @720 px canvas |

Why 0.32. The repository's pre-registered gate `SECTION_FILL_DISTINGUISHABLE` requires mean ΔE76 ≥ 20 and min ≥ 12 between fill-on and fill-off in the same frame. Measured with the gate's own `deltaE76` and thresholds on 6 scenes:

| alpha | 0.27 | 0.30 | 0.31 | **0.32** | 0.34 |
|---|---|---|---|---|---|
| ΔE76 | 16.9–17.2 | 19.2 | 19.7–19.9 | **20.4–20.6** | 21.8 |

The layers under the section are porcelain shell 12 %, violet plane 6.5 % and the ivory canvas. That is the reference's own layering, so the reference HTML at 0.27 would also miss this gate. This is not a renderer difference that a material change could fix. The owner chose the smallest passing value. The selected state is 0.38.

## Cutting plane

- Fill `#6D28D9` at 0.065 (standalone 0.085, selected 0.16), unlit, as in the reference.
- Border: violet `LineDashedMaterial`, opacity 0.55, Line2 2.2 px. It is **always dashed** and **shown with or without a closed section**. Previously V6.2 removed the border whenever a closed section existed.
- The patch is the engine-derived plane region (`daGiacMatPhang` / `moRongDaGiacMatPhang`): a finite representation of an infinite plane, never read as a solid edge. Finished auxiliary planes stay behind the learner's "Hiển thị → Hình phụ" toggle (or selection), unchanged ("shown when requested").

## Edges and dashes

| Role | Reference (world radius → px at its 1440×900 default) | AlgoSim Line2 px @720 px canvas (× canvas-height factor 0.62–1.25) |
|---|---|---|
| Visible edge `#1E293B` | 0.028 → 5.9 px | 3.6 |
| Hidden edge `#64748B` (0.78) | 0.0235 → 5.0 px | 3.0 |
| Section edge | 0.035 → 7.4 px | 4.5 / 3.7 dashed |
| Auxiliary / right-angle stroke `#0F766E` | 0.021–0.026 → 4.4–5.5 px | 2.7 / 2.4 dashed |
| Plane border | 0.017 → 3.6 px | 2.2 |

The reference strokes are world-space, so they change with framing. AlgoSim matches the stroke-to-figure ratio measured on screenshots at matched framing: ≈ 0.008 × figure height. The previous ratio was ≈ 0.0063. Dash cycle follows the reference: dash/figure ≈ 3.8 %, gap ratio 0.72 (reference 0.71).

## Canvas

`.geo3d-canvas` uses `radial-gradient(circle at 50% 44%, #FFFFFF 0%, #F8F6F1 68%, #EFECE4 100%)`, the reference `.academic-stage-light`. Page/website theme is unchanged. The earlier objection to a warm tint was about lit shells multiplying it; shells are now unlit.

# HTML original vs AlgoSim after the port

Status: `SCENE3D_HTML_VISUAL_FIDELITY_READY_FOR_OWNER_REVIEW`. **HUMAN_VISUAL_APPROVED is not claimed.**

## Method

- **HTML side.** The owner's file is unmodified (`C:\Users\Bunny\Downloads\matphanghinhchot.html`, SHA-256 in `verification/html-reference/receipt.json`). It is rendered in headless Chrome (SwiftShader, DPR 1) at its official "Góc SGK" camera (θ 0.56, φ 1.18) and construction step 4. For the side-by-side views the radius is widened from 11.8 to 15.5 so the whole figure is in frame; the receipt records this.
- **AlgoSim side.** The freeze commit `13d28b84` (product `852f6501`) runs on a clean worktree with a dev server. Its inputs are the actual B1/B2 service wrappers (`fixtures.json` SHA in the receipts) and one offline sample. Each scene is at the final construction step, with the learner action "Hiển thị → Hình phụ" applied where the scene offers it, because the HTML always shows (α) at step 4.
- **Same view direction.** The HTML camera direction is expressed in an orthonormal frame on the labelled base triangle A, B, C (z toward the apex), then re-expressed in AlgoSim's frame of the same labels. Elevation is 22.39° on both sides. Each renderer keeps its own framing distance.
- **Same viewports.** 1440×900 and 390×844.
- **Where to find it.** Side-by-side composites are `verification/html-vs-algosim/SIDE-*.png`. The raw captures and per-image SHA-256, camera, step and Line2 widths are in `receipt.json` next to them. Product-default-camera captures are in `verification/default-camera/`.

| Pair | HTML shape | AlgoSim scene | Topology match |
|---|---|---|---|
| S.ABCD, SA ⊥ base, section | `chop_sa_vuong_day_vuong` | `PERP-square-third` | Same solid and relation; HTML section points are clamped fakes |
| S.ABC, SA ⊥ base, section | `chop_sa_vuong_abc` | `CORPUS-DEV03-construct` | Same; base triangles differ in shape |
| Right prism + section | `lang_tru_tam_giac_deu` | `CORPUS-DEV10-prism-area` | Same family; different section plane |
| S.ABCD + section MNPQ | `chop_tu_giac_deu` | offline sample `thiet-dien-chop` | Same solid; AlgoSim apex not over the base centre |

The geometry is not identical on the two sides and cannot be made identical. The reference shears its base (`sk = 0.85` added to B and C) to imitate an oblique textbook drawing, and it places section points by a clamped parameter. AlgoSim renders exact engine coordinates and must not distort them. So the comparison judges **materials, colors, strokes, labels and markers**, and topology only coarsely.

## Assessment against the owner's criteria (Claude, not the owner)

| Criterion | Result |
|---|---|
| Shell looks like the reference | Yes. Same porcelain `#7C8B9E`, unlit, front 0.12 / back 0.09; overlap brightness matches |
| Section color | Same terracotta `#C85A32`. Fill is 0.32 (owner decision, gate), so AlgoSim is slightly denser |
| Section outline clear, hidden part dashed | Yes. Terracotta 4.5 px solid / 3.7 px dashed; hidden section edges read as dashes, which were near-invisible in amber before |
| Hidden edges distinguishable | Yes. Slate `#64748B` dashes, cycle ≈ reference; thickness ratio ≈ reference |
| Right-angle marks compact | Yes. 8–12 px target (RIGHT_ANGLE_MARKER_VALIDATION.md); reference marks are ≈ 36 px at its default framing, so AlgoSim's are deliberately smaller |
| Violet plane shown when requested | Yes, with "Hình phụ" or selection: violet 0.065 fill + dashed 0.55 border. AlgoSim's patch is the engine plane region, so its outline differs from the reference's fixed rectangle |
| Labels by role | Yes. Haloed dark vertex names; terracotta boxed section-vertex points; teal boxed derived points; violet plane names. Unnamed section vertices stay unlabeled (the reference prints invented names M, I₁…) |
| Camera suitable | Elevation matches the reference (22°) in the forced comparison. The product default keeps its scored view (elevation 15–35°, pull toward 22.4°) and refuses degenerate views; the forced HTML direction produces one for `CORPUS-DEV03` (C hidden behind S), which the scorer avoids |
| Canvas | Ivory radial gradient, identical stops |

## Remaining differences and why

1. **Figure shape** (shear, fake section points): not portable; it would change geometry.
2. **Stroke scale.** The reference strokes are world-space (thicker when zoomed in). AlgoSim uses screen-space strokes scaled by canvas height, at the reference stroke/figure ratio for the default framing.
3. **Figure size.** The AlgoSim canvas spans the full workspace width, so the figure occupies less of the width than in the HTML's three-column layout.
4. **Plane visibility.** The HTML always shows (α). AlgoSim hides finished auxiliary planes until requested, which is the owner's criterion "shown when requested".
5. **Default camera.** AlgoSim's scored view, not the fixed preset (see above).
6. **Section fill 0.32 vs 0.27** (gate).

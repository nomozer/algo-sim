# Current material inventory — before product edits

Complete line-level inventory: `material-inventory-before.json`, extracted from the seven owner-prioritized modules at `f95596716912e5550ed079287221274b2d70f24c`. Entries preserve file/line/source, including opacity, width, dash, order, depthTest/depthWrite, transparency and literals. Actual styles outside the renderer are in tokens.css/global.css; Scene3D model, interaction state and pick-target do not own palettes.

| Role | Baseline | Defect class / decision |
|---|---|---|
| given / derived points | #374151 / #dc2626, MeshStandard, screen-sized 6/7.5/9 px | scattered color; preserve marker/pick sizes |
| polyhedron / curved shell | #647a96, MeshStandard DoubleSide, .22, depthWrite false; highlighted curved .36 but polyhedron .22 | semantic inconsistency; shared lit shell policy |
| secondary solid | post-build #0d9488/.18 and #0f766e edge based on visible array index | unstable role on hide/isolate/step; no scene-specific id branch found |
| visible / hidden edge | #1e293b both; widths 1/3 selected; hidden .9, dash .16 or scene-scaled .022, gap .75 | hidden competes with visible; retain CPU ownership and dash classification |
| auxiliary line / witness | teal #0f766e, auxiliary fade .45, numerical witness .92/.96; hidden .75 or canonical .9 | centralize styles; do not touch witness geometry |
| plane | #7c3aed lit fill .055/.11/.07 or .16/.22/.28 highlighted; border .32/.48 | color + lighting overlap; unlit region, one semantic plane policy while retaining clipping branches |
| base | circular slate fill .12/.24 with dark rim; polygon amber .16/.35 | same base meaning has different colors |
| section | polygon amber .45, circle/ellipse .28/.42, MeshStandard; rim #f59e0b | color + material/lighting inconsistency, not geometry error; common unlit fill and distinct outline |
| face | amber .14/.55 unless hit proxy | ambiguous section/base/face color; structural face uses shell role |
| sphere depth contours | structural ink .18/.13/.13 | preserve contour geometry; central style |
| background grid | #94a3b8/.24/.14, #b0bec5/.06, renderOrder -2 | decorative literals -> semantic grid styles |
| selection / causal | blue #2563eb, numerical given #c2410c, intermediate #fb923c, context #6b7280/#cfd6df; fade .3 | reuse existing authority roles.ts, preserve numeric meaning; UI focus blue alignment |
| hover | no WebGL recolor; cursor + existing UI hover styles | no invented theme-dependent hover behavior |
| depth | back depth prepass 5; curved front prepass 7.5; section fill 7, lines 8, section rim 10 | engineering invariant, not palette; preserve all flags/orders |
| material allocation | rebuild on object/state change; edge span updates can replace material on changed spans | separate performance issue; measure orbit after warmup before deciding fix |

Do not classify existing face darkening as wrong geometry. Lit normals, overlap, double-sided transparent passes, opaque depth and CPU edge classification are separate mechanisms. Existing multi-solid occlusion/shared-edge suppression and adaptive safe-area framing are baseline invariants and remain owned by their existing modules.

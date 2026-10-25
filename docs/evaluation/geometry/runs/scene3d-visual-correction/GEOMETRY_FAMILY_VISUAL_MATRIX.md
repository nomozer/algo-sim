# Geometry family visual matrix

**Rendering a family is not Hybrid support.** This matrix records what the renderer draws for envelopes and scenes that
already exist offline. Whether a family is supported end to end by route D Hybrid (facts → planner → exact engine →
Adapter /4) is recorded separately in `../visual-b3-sphere-integration/UPDATED_18_FAMILY_CAPABILITY_MATRIX.md`.
Nothing here changes that matrix.

## 1. Final browser matrix (`verification/after-b8b3311b/`, tool `tools/browser-matrix.mjs`)

Same result at `78aaef2f` in `verification/after-final/`, before the Mode B reveal fix. In that run `mode_b_once` still
forbade canvas result labels.

| Item | Value |
|---|---|
| Browser | Real Chrome (SwiftShader) |
| Model calls | 0 |
| Non-local requests | every one aborted (0 attempted) |
| Source | commit `b8b3311b` (product of freeze `c84e8620`), served by a freshly started Vite on `:3161` |
| Command | `--phase after --audit '.' --extra-scene frontend/src/simulations/domains/geometry/scene3d-circumsphere-fixture.json` |

Each row has 7 frames:
- Mode A, default camera;
- five cameras: default, quarter, half, high, low;
- Mode B, with the first final result selected from the analysis panel (it was a final result in every rendered row).

| Family / scene | Source | 1440 | 390 |
|---|---|---|---|
| triangular_pyramid, triangular_prism, rectangular_pyramid, cuboid, regular_square_pyramid, regular_triangular_pyramid, cross_section | offline backend envelopes (`visual-closure-hybrid-readiness/visual/final-inputs`) | 7/7 PASS | 7/7 PASS |
| cau-cat-mat-phang, tru-truc-xien, tru-thiet-dien-tron, non-duong-sinh, non-thiet-dien-truc | legacy offline samples, not Hybrid envelopes | 5/5 PASS | 5/5 PASS |
| family01–family12 (incl. 07 multi-solid, 08 unnamed section vertices, 09 cylinder sections, 10 cone frustum cut, 11 sphere cut, 12 cylinder ellipse section) | display-only authored scenes (`geometric-visual-correctness-framing/demos/audit_scenes.json`) | 13/13 PASS | 13/13 PASS |
| family13_invalid_geometry_refusal | same file; a **refusal record without a scene** (`served: false`, `CURVED_PLANE_DOES_NOT_CUT`) | NOT_APPLICABLE | NOT_APPLICABLE |
| scene3d-circumsphere-fixture (tetrahedron in its circumsphere) | frontend test fixture scene | PASS | PASS |

**52/52 rendered rows pass; 364 frames.** The tool reports 52/54 because it loaded family 13 with an empty scene and
waited for a canvas that a refusal never has. That is a tool input-selection gap, not a product result, and it is not
counted as a pass. The refusal path itself is covered by backend tests, not by this matrix.

Checks per row:

| Check | Meaning |
|---|---|
| `mode_a_hidden` | no result label on the canvas, and no analysis result in the DOM |
| `mode_b_once` | each result listed once in the panel; the inspector does not repeat the selected result. The selected result's canvas annotation is expected in Mode B, per the locked suite |
| `geometry_unchanged` | scene JSON byte-identical after all interactions |
| `no_duplicate_edge_owners` | each logical edge has one visual owner |
| `no_overflow` | no horizontal page scroll |
| `multiple_cameras` | at least 4 distinct camera positions |

## 2. Frames inspected by eye (Claude; not Owner approval)

| Frame | Observation |
|---|---|
| `scene3d-circumsphere-fixture-1440-default-unselected` | No stray ring at O (round-1 C1). Front edges AB, BC, CA solid; OA, OB, OC dashed (round-1 I2) |
| `family10_cone_frustum_cut-1440-default-unselected` / `-high-` | The section circle keeps its terracotta rim; no navy cap rim over it (round-1 I1). The mid-height dashed arc is the hidden back half of the base circle, which the top view confirms |
| `tru-truc-xien-1440-quarter-unselected`, before vs after | Before: uniformly grey silhouette with no outline. After: tangent generators and both cap rims, hidden halves dashed |
| `cross_section-390-default-selected-mode-b` | Selected solid's edges cobalt, section stays terracotta, inspector shows the link "Xem giá trị trong Phân tích toán học" instead of the value |

## 3. Before / after

`verification/before/` (Codex: the `fe5f40b7` renderer served through a source-substituting Vite plugin) covers the
three curved samples. `verification/after-claude-pre-review/` is the same tool on the code before the internal review
fixes, kept for traceability.

## 4. What the matrix does not show

- It does not judge appearance. `HUMAN_VISUAL_APPROVED = PENDING`.
- No automated check in this run asserts the placement of right-angle marks or labels. The locked official suite checks
  labels for the 7 polyhedron families (`OFFICIAL_VISUAL_SUITE_RESULTS.md`).
- Curved families come from legacy samples and display-only scenes, not from backend envelopes of the current pipeline.
- During the `78aaef2f` run, a 30-second single-page repro probe overlapped the matrix. The final `b8b3311b` run had no
  overlap.

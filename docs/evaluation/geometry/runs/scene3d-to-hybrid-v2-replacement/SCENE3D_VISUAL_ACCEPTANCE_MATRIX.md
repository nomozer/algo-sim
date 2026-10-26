# Scene3D visual acceptance matrix

Product `f3ae506c` (+ relock `1beb3d0f`). Two captures, both through the product store on a dev server of this tree, with
0 provider calls:

- `visual-matrix/`: 17 fixtures × 6 orbit gestures × 1440/390 = 204 frames, 0 page errors. Same tool, fixtures and
  gestures as the Codex takeover (`../scene3d-codex-takeover/tools/capture-final.mjs`, unchanged), so a frame-by-frame
  before/after comparison is available.
- `p0-capture/`: 60 frames of the three right-angle scenes in Mode A and Mode B.

Review aid: `tools/sheet.py` builds one contact sheet per fixture.

**Status of this table:** an author review of every frame plus the automated tests named. It is **not** Owner visual
approval (`HUMAN_VISUAL_APPROVED = PENDING`) and not an independent review. Gesture names follow the takeover:
`half` is the rear view (about 180°); `back` is a full turn (about 360°), not a rear view.

| Scene | Geometry / identity | Solid vs hidden strokes (all gestures) | Annotation | Invented facts | Verdict |
|---|---|---|---|---|---|
| thiet-dien-chop (MNP) | M, N, P on SA, SB, SC; section MNP + base | Section front edges solid, rear dashed; base hidden edges dashed; consistent across all 6 gestures | Section vertices in section style | none | PASS |
| mat-cheo-sac (SAC) | diagonal plane through S, A, C | SA / AC dashed when behind, SC solid; flips correctly on half/low | S, A, C as section vertices | none | PASS |
| vuong-goc-chop (BC ⟂ (SAB)) | backend `angle` witness at B (new) | edges as solid; no mark drawn over edges | Mode A: no mark (the mark is the answer); Mode B: one mark at B between BA and BC | none (frontend inference removed) | PASS (G1 closed) |
| mp-vuong-goc-duong | (α) = plane through B ⟂ SC; foot H exact on SC | base (ABCD) and (α) borders: front solid, rear dashed | one mark at H between HS and the witness leg HB; labels (ABCD), (α) | none | PASS (Owner P0) |
| the-tich-chop | SA ⟂ (ABCD) | standard | one mark at A, sides AS and AB (both edges, not redrawn) | none | PASS; redundant foot dot on A (cosmetic) |
| cau-the-tich (sphere) | centre I (source), point A given | reference great circle: front solid, rear dashed; fully dashed in the high view, which is correct because the equator lies beyond the limb; limb solid | — | reference circle marked `authoritative:false` | PASS |
| cau-cat-mat-phang (sphere ∩ (P)) | real circle of intersection, (P) labelled | circle front solid / rear dashed; fully solid from above; mostly dashed from below; no reference circle | — | none | PASS |
| tru-truc-xien (oblique cylinder) | O, O′, A | two silhouette generators solid; rear rim arcs dashed; switch with gesture | — | none | PASS |
| tru-thiet-dien-tron | circle section of plane ⟂ OO′ through M, plane now (α) | section front solid, rear dashed; base rims correct | — | none | PASS |
| family12 cylinder ellipse | oblique ellipse | front arc solid / rear dashed; fully dashed under the top cap from above | — | none | PASS (desktop/mobile low certified only as noted by the takeover) |
| non-duong-sinh, non-thiet-dien-truc | cone, axial triangle SAB | SA solid; SB and the base chord AB dashed (inside / behind); base rim front solid | B in derived-point style | none | PASS |
| cuboid_positive | box ABCD.A′B′C′D′ | hidden-edge sets change correctly, including the low view | one representative mark per relation (lateral ⟂ base) | none | PASS |
| triangular_prism_positive | right prism | consistent | one mark per relation, moves with the most open view | none | PASS |
| family01_triangular_pyramid, cross_section_positive | official fixtures | consistent | section + foot mark | none | PASS |
| w18_projection_line | H = projection of S onto BD | consistent | no mark: this FROZEN fixture predates witnesses (SH is a plain segment `doan_SH`). Policy: no witness ⇒ no mark. The current route D emits a projection witness (`function_route._gan_nhan_chung_hinh_chieu`) | none | PASS under policy; fixture not regenerated |

## Not certified by this matrix

- Tangent and no-intersection sphere–plane browser variants: backend refusals `CURVED_PLANE_TANGENT` /
  `CURVED_PLANE_DOES_NOT_CUT` exist, but no browser row.
- Oblique-prism cutting planes; a cone cut producing a non-ellipse conic (backend refuses; no browser row).
- A complete all-label overlap oracle. Label stability: see `OFFICIAL_VISUAL_SUITE_RESULTS.md` and the motion run when
  it is recorded.
- Official Visual Suite: separate, locked (`OFFICIAL_VISUAL_SUITE_RESULTS.md`).

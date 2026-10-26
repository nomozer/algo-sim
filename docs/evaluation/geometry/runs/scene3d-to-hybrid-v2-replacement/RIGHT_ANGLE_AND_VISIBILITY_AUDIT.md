# Right-angle and visibility audit

Part 1 (right angle) is complete at product `f3ae506c`. Part 2 (solid/hidden strokes) is filled in after the visual
matrix run.

## 1. Right-angle mark — Owner P0

### What the Owner saw

Scene `mp-vuong-goc-duong`: "dựng mặt phẳng qua B và vuông góc với SC, rồi tính khoảng cách từ S đến mặt phẳng vừa
dựng". The mark appeared to lie on the plane, or not to sit clearly at the foot, next to the only plane label on the
figure, "(ABC)".

### End-to-end trace (backend → envelope → presentation → renderer)

| Step | Finding |
|---|---|
| Relation | distance S → `mpb` (plane through B ⟂ SC); witness from `quantity_annotations._nhan_chung` |
| Foot | H = (5/3, 5/3, 2/3), exact. H ∈ SC, and n·(H − B) = 0 for `mpb`'s normal n = (2, 2, −4) |
| Directions | v = S − H = (−5/3, −5/3, 10/3) ∥ n; u = B − H = (1/3, −5/3, −2/3); u·n = 0, u·v = 0, exactly |
| Renderer anchor | `dauGocVuong` draws foot + s·u → foot + s·(u+v) → foot + s·v; `datCoGocVuong` scales about the foot (`position = foot·(1 − k)`), so the foot is a fixed point. No world- or screen-space offset |
| **Root cause** | Identification, not coordinates: (1) `mpb` had `notation: null`, so nothing named the plane the mark belongs to; (2) the base was labelled "(ABC)" although the program declares "(ABCD)"; (3) the mark's in-plane side ran along HB, which was not drawn; (4) the step read "Ghi nhận mpb = Plane3(point=Vec3(x=Fraction(2, 1)…" as a MEASUREMENT |

The mark was therefore mathematically right but read as "S ⟂ (ABC) at a point near C", a false relation.

### Fix (one authority each)

| Layer | Change |
|---|---|
| `display_names.ten_hien_thi` | A plane with no notation is called (α), (β)… (Owner decision 2026-10-26), only if every parenthesised name the problem writes is already shown. Otherwise it gets none: in `p6` the problem writes (α) and the model calls the plane "mặt phẳng alpha", and assigning (β) would contradict the problem. A declared multi-point name (ABCD) is kept only if `simulation_state` proves every named point lies on the plane, exactly. A false name is not trusted and is not shortened |
| `quantity_annotations._nhan_chung` | u points at a NAMED point on the target, and `marker.u_to` names it (Owner decision: draw the witness leg) |
| `quantity_annotations._goc_vuong` | An angle measured exactly 90° (cos² = 0) gets an `angle` annotation with a right-angle witness at the line–plane / line–line intersection. Skew lines: none. This closes G1 (BC ⟂ (SAB)) without frontend inference |
| `scene3d._ke_lai` | Geometry built by `assign` is a CREATE step ("Gọi (α) là mặt phẳng qua B và vuông góc với SC."); no internal repr in `learner_text` or `explanation` |
| `scene3d-witness-gate.ts` (new, boolean-only) | Before any mark is drawn: u, v ≠ 0 and u ⟂ v; v ∥ (from − foot); foot on the `on` plane/line; u in the plane / along the line; v ∥ normal / v ⟂ line; `u_to − foot` ∥ u. Fail-closed |
| `scene3d-annotations.ts` | Removed the inference that drew line ⟂ plane marks from '⊥'/'90°'/cos = 0 text and float coordinates (`tuDuongMp`) |
| `scene3d-view.tsx` | Witness leg H → B drawn unless it is already a drawn edge; Mode A hides an angle answer's mark; a solid's own face plane counts as present for its witness; the chart transform keeps `u_to` |

### Regression and fault injection (`scene3d-right-angle-witness.test.ts`, real samples)

| Injected fault | Caught by |
|---|---|
| ① foot moved within the plane | gate: v no longer ∥ from − foot |
| ② foot off the plane | gate: n·(foot − p) ≠ 0 |
| ③ not perpendicular (u tilted; `u_to` off u; tampered envelope foot) | gate; `projectionWitnessesAt` returns nothing |
| ④ renderer shifts the anchor by 0.01 | implied foot p(1,0) + p(0,1) − p(1,1) no longer equals H |
| ⑤ the same relation drawn twice | `datCoGocVuong` shows one mark |
| ⑥ camera orbit, 7 azimuths | implied foot = H and both sides keep their world direction at every azimuth |

RED on the v129 baseline (same probe file, copied in and removed): 5/6 fail there, 6/6 pass here
(`verification/red-baseline.txt`). R6 does not discriminate: the baseline drew BC ⟂ (SAB) through the removed text
inference.

Also found: an existing test fixture drew a mark from a wrong witness (K = (3/8, 3/8, 1/4) lies on (BCS) but AK is not
normal to it, and u·v ≠ 0). The gate now rejects it, and the fixture uses the true foot (1/3, 1/3, 1/3).

### Browser evidence (`p0-capture/`, 60 frames, 0 page errors)

Three scenes × Mode A/B × 5 orbit gestures × 1440/390. Witnesses drawn (from `receipt.json`):

| Scene | Mode A | Mode B | Plane labels |
|---|---|---|---|
| mp-vuong-goc-duong | `perpendicular:kc` (foot H, leg HB) | same | (ABCD), (α) |
| the-tich-chop | `perpendicular:d` (SA ⟂ (ABCD) at A; leg AB = base edge, not redrawn) | same | — |
| vuong-goc-chop | none (the mark is the answer) | `perpendicular:goc` at B | — |

`p0-capture-attempt1/` is the first run, superseded: it showed no mark for the-tich-chop and vuong-goc-chop, because a
face plane hidden as "measurement-only" removed the witness's subject. That was fixed before the final run.

Not done: the orange foot dot is drawn even when the foot coincides with a named vertex (A in the-tich-chop). It is
redundant but not misleading.

## 2. Solid/hidden strokes

Pending — see SCENE3D_VISUAL_ACCEPTANCE_MATRIX.md.

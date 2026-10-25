# Open gaps

Each gap names why it was not fixed here. "Needs backend" means the frontend would have to invent a point, relation or
text to fix it, which R0 forbids.

| # | Gap | Where | Why not fixed here | Next |
|---|---|---|---|---|
| G1 | No right-angle mark for BC ⊥ (SAB), although the expected answer is 90° | sample `vuong-goc-chop` | The scene carries no witness for that relation, and the renderer draws marks only from backend witnesses. Drawing one would be a frontend-invented relation | Backend: emit a `perpendicular_witness` (BC ⊥ (SAB) at B) for this sample |
| G2 | Learner step text leaks an internal representation: "Ghi nhận mpb = Plane3(point=Vec3(x=Fraction(2, 1)…". The same event is a MEASURE, not a CREATE, so the timeline groups the plane with the preceding "Dựng SC" step: the plane, now drawn (F4), appears in that step | sample `mp-vuong-goc-duong`, formation step 3 | Backend-generated sample text and event kind (`geometry-samples.json` via `build_geometry_samples.py`); out of this frontend scope | Backend: emit the plane as a construction (CREATE) with learner-facing text; rebuild the sample |
| G3 | The constructed plane `mpb` has no name and no label; it is "Mặt phẳng qua B và vuông góc với SC" with `notation: null` | `mp-vuong-goc-duong` | The label must come from backend notation; the frontend does not invent names | Backend: give it a notation such as (P) |
| G4 | The scene in your image (A, H ⊥ (α), line d, projection d′, angle φ) has no product counterpart | only the reference HTML (`quan_he_dt_mp`) | No sample, fixture or backend family produces "angle between a line and a plane" with a projection line. The nearest fixture, `w18_projection_line`, is the projection of S onto BD | A backend family; then the renderer's existing angle/witness primitives |
| G5 | Ellipse front/back transition: the renderer splits a curve rim per 96-chord midpoint; an analytic check finds a ~4 px front interval near the switch drawn as hidden | `p6` cylinder ellipse, 1440 low (`scene3d-final-acceptance` report) | The cause is not established. A finer split is a wider visibility change with its own regression; not done blind | A reproducible math regression first, then the rim split |
| G6 | Official Visual Suite **7/8**: `cross_section` fails the locked role-hue gate | `canvas_role_hues.cam` | **Policy gate, not a renderer defect.** The locked gate counts the selected section's terracotta fill, which F2 keeps. Not edited, not worked around | Owner decision: amend the gate or adopt a role-aware check |
| G7 | A hard-coded scene id `o.id === "day"` in `scene3d-auxiliary.ts` (earlier code) | `auxiliaryObjects` | Pre-existing; AGENTS.md forbids hard-coding. Changing it alters which planes hide in other scenes, beyond this campaign's evidence | Separate change with its own scene sweep |
| G8 | No automatic placement check of every label against every line; label checks are the locked suite's (`labels`, `annotations_rotated`/`resized`) plus the jump heuristic | all | A full overlap oracle was not built in this run | — |
| G9 | Curved scenes are legacy offline samples, not backend envelopes of the current pipeline | `cau-*`, `tru-*`, `non-*` | Unchanged corpus | — |
| G10 | `INDEPENDENT_REVIEW_PENDING`; `HUMAN_VISUAL_APPROVED = PENDING` | — | Not something this run can grant | Owner |

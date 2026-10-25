# Browser visual acceptance

**`HUMAN_VISUAL_APPROVED = PENDING`.** Everything below is machine evidence plus Claude looking at frames. It is not the
Owner's visual approval.

Common conditions:
- real Chrome with SwiftShader WebGL;
- 0 model calls; every non-local request aborted (0 attempted);
- desktop 1440×900 (DPR 1) and mobile 390×844. Mobile uses DPR 2 in the role-aware probe and DPR 1 in the family
  matrix.

**Final source: commit `b8b3311b`**, the product commit of candidate freeze `c84e8620`. It was served by a freshly
started Vite (`frontend/src` unchanged after `b8b3311b`). The locked official suite was run separately on the built
`dist/` of `c84e8620` (`OFFICIAL_VISUAL_SUITE_RESULTS.md`).

## 1. Family matrix (`verification/after-b8b3311b/`)

**52/52 rendered rows pass at both widths**, 364 frames. Rows covered:
- 7 backend polyhedron families;
- 5 legacy curved samples;
- 12 display-only audit families;
- the circumsphere fixture.

One refusal record without a scene is NOT_APPLICABLE. Per-row checks and frames: `GEOMETRY_FAMILY_VISUAL_MATRIX.md`.

## 2. Mode A / Mode B (answer privacy)

The contract is the locked one (Owner policy `aa458cc3`, suite `mode_b_reveal` / `selection_per_quantity`):

| Mode | Contract |
|---|---|
| A (analysis panel closed) | no final answer anywhere: no «Kết quả» value, no canvas result annotation, no analysis result |
| B (learner opens «Phân tích toán học») | each final answer in exactly one «Kết quả» row with its value; stated in the analysis panel; the selected result's canvas annotation shown. The inspector links to the panel instead of repeating the value (kept from Codex) |

| Check | Evidence | Result |
|---|---|---|
| Mode A, family matrix `mode_a_hidden` | no canvas result label, no analysis result in the DOM | 52/52 |
| Mode B, family matrix `mode_b_once` | panel results unique; inspector does not repeat the selected result (the selected item was a result in 52/52) | 52/52 |
| Mode B, every final result of 4 scenes (`tools/inspector-probe.mjs` → `verification/mode-b-inspector-b8b3311b/current.json`) | inspector open 9/9; value repeated **0/9**; link "Xem giá trị / công thức trong Phân tích toán học" 9/9; selected result annotation on the canvas for the 4 polyhedron selections (the curved samples carry no result annotation) | PASS |
| Negative control (inspector duplication) | the same probe on the `fe5f40b7` renderer: inspector repeated the result 8/9 (`verification/mode-b-inspector-pre-review/baseline-fe5f40b7.json`) | detected |
| Negative control (over-hiding) | the locked suite on `3c6d1e65`, where Codex's change hid Mode B results: 0/8, every family `mode_b_reveal` + `selection_per_quantity` | detected |

## 3. Selected section boundary (supplemental role-aware check, not the locked oracle)

`verification/role-aware-b8b3311b/`: 180 rows (3 shapes × 2 widths × 5 cameras × (unfaulted + 5 faults)).

| Item | Result |
|---|---|
| Unfaulted views | 19 PASS · 0 FAIL · 11 UNCERTIFIABLE (DOM labels cover part of the boundary) |
| Certified views per shape | polygon 10/10 · circle 5/10 · ellipse 4/10 |
| Faults on certified views | **95/95 detected**: boundary→terracotta, boundary→magenta, fill→grey, fill hidden, wrong object |
| Faults on uncertifiable views | 55/55 also FAIL |
| Retries, error rows | 0, 0 |

The same verdicts were obtained at `78aaef2f` (`verification/role-aware-final/`).

## 4. Negative controls required by P6

| Fault | Where it is proven to be caught | Real code/DOM path? |
|---|---|---|
| Wrong hidden line | locked suite library tests (`HIDDEN_DASHED`); oracle node test "does not aggregate away a missing hidden edge"; the locked suite's human hidden-line oracle (`human_expected_visibility`) runs on every family | library tests are synthetic; the hidden-line oracle runs on the real product |
| Missing section edge | oracle node tests (a missing quarter of one edge, a missing edge, 40 % of a hidden arc); browser `boundary_terracotta` removes the cobalt boundary in the real WebGL program | yes (browser) + synthetic |
| Wrong object selected | browser `wrong_object`: the learner clicks another point after selecting the target | yes |
| Wrong boundary colour | browser `boundary_magenta` / `boundary_terracotta` (WebGL uniform swap) | yes |
| Missing fill | browser `fill_hidden` (product harness hook) and `fill_grey` | yes |
| Wrong point name | locked suite `labels` assertion against the oracle labels on every family; library test `SELECTED_LABEL_MISSING` | suite yes; **no injected wrong name in this run** |
| Wrong plane | locked suite fixture `cross_section_wrong_plane` (and `wrong_centre` / `wrong_centroid`), which must be refused; all refusal negatives pass in `official-run-c84e8620` | yes (refusal path) |
| Answer leak | inspector probe on `fe5f40b7` (8/9 caught); the locked suite caught the opposite error at `3c6d1e65` | yes |
| Labels covering key information | library tests `ANNOTATION_OVER_POINT_LABEL`, `ANNOTATION_OVERLAP`; locked suite `annotations_rotated` / `annotations_resized` per family | synthetic + suite |

## 5. Looked at by eye (Claude)

See `GEOMETRY_FAMILY_VISUAL_MATRIX.md` §2. Frames checked:
- circumsphere: no stray ring, correct dashing;
- family 10: section rim not covered;
- oblique cylinder: before vs after;
- `cross_section` in Mode B on mobile.

## 6. Not covered / open

- Owner visual approval (`PENDING`).
- No wrong-point-name fault was injected in the browser in this run.
- Mobile in the family matrix uses DPR 1.
- Two earlier long role-aware runs stopped on a canvas that never appeared (`verification/aborted-stale-hmr/`). The
  stop did not reproduce in 15 fresh loads, and both final runs needed 0 retries.
- During the `78aaef2f` family-matrix run, a 30 s single-page repro overlapped it. The `b8b3311b` runs had no overlap.

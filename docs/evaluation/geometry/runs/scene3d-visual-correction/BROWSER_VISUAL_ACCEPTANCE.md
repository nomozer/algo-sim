# Browser visual acceptance

**`HUMAN_VISUAL_APPROVED = PENDING`.** Everything below is machine evidence plus Claude looking at frames. It is not
the Owner's visual approval.

Every browser check ran under these conditions:

| Condition | Value |
|---|---|
| Browser | real Chrome, SwiftShader WebGL |
| Model calls | 0 |
| Network | non-local requests aborted (0 attempted) |
| Viewports | desktop 1440×900 (DPR 1) and mobile 390×844 (DPR 2 in the role-aware probe; DPR 1 in the family matrix) |
| Source | commit `78aaef2f` (the product commit of candidate freeze `3c6d1e65`), served by a freshly started Vite |

## 1. Family matrix (`verification/after-final/`)

52/52 rendered rows pass at both widths: 7 backend polyhedron families, 5 legacy curved samples, 12 display-only audit
families and the circumsphere fixture. One refusal record without a scene is NOT_APPLICABLE. Per-row checks and frames:
`GEOMETRY_FAMILY_VISUAL_MATRIX.md`.

## 2. Mode A / Mode B (answer privacy)

| Mode | Requirement | Evidence | Result |
|---|---|---|---|
| A (analysis panel closed) | no final answer anywhere | family matrix `mode_a_hidden`: no result label on canvas, no analysis result in the DOM | 52/52 |
| B (panel open) | the answer exactly once | family matrix `mode_b_once`: no canvas result label, panel results unique, inspector does not repeat the selected result (selected item was a result in 52/52) | 52/52 |
| B, every result | the same, for every final result of 4 scenes (cross_section, cuboid, cau-cat-mat-phang, non-duong-sinh) | `tools/inspector-probe.mjs` → `verification/mode-b-inspector/current.json`: inspector open 9/9, value repeated 0/9, canvas result labels 0/9, link "Xem giá trị / công thức trong Phân tích toán học" 9/9 | PASS |
| negative control | the probe must catch the old duplication | same probe on the `fe5f40b7` renderer (`tools/baseline-server-claude.mjs`, port 3158), recorded in `verification/mode-b-inspector-pre-review/baseline-fe5f40b7.json`: inspector repeated the result 8/9, canvas result label 4/9 | detected |

The vitest regressions for Mode A/B (`visual-closure.test.tsx`, `simulation-coverage-fixes.test.tsx`,
`scene3d-focus-mode.test.tsx`) pass within the 1377/1377 full suite.

## 3. Selected section boundary (supplemental role-aware check, not the locked oracle)

`verification/role-aware-final/`: 3 shapes (polygon cross-section, circle on a sphere, p6 ellipse on a cylinder) ×
2 widths × 5 cameras × (unfaulted + 5 faults) = 180 rows. 0 retries, 0 error rows.

| | Result |
|---|---|
| Unfaulted views | 19 PASS · 0 FAIL · 11 UNCERTIFIABLE (labels cover part of the boundary) |
| Certified views per shape | polygon 10/10 · circle 5/10 · ellipse 4/10 |
| Injected faults on certified views | **95/95 detected** (boundary→terracotta, boundary→magenta, fill→grey, fill hidden, wrong object selected) |
| Injected faults on uncertifiable views | 55/55 also FAIL (not counted as evidence) |

## 4. What was looked at by eye (Claude)

See `GEOMETRY_FAMILY_VISUAL_MATRIX.md` §2:
- circumsphere: no stray ring, correct dashing;
- family 10: section rim not covered;
- oblique cylinder: before vs after;
- cross_section in Mode B on mobile.

Also the p6 ellipse at the 390 "quarter" camera (`verification/role-aware-final/ellipse-cylinder-p6-390-quarter-none.png`):
the selected boundary is visible as a thin cobalt curve on both arcs.

## 5. Not covered / open

- Owner visual approval (`PENDING`).
- No automated placement check for right-angle marks and labels in this run; the locked suite covers labels for 7
  polyhedron families (`OFFICIAL_VISUAL_SUITE_RESULTS.md`).
- Mobile in the family matrix uses DPR 1. DPR 2 is exercised only by the role-aware probe.
- Two long role-aware runs stopped on a canvas that never appeared (`verification/aborted-stale-hmr/`). It did not
  reproduce in 15 fresh loads, and the final run needed 0 retries. The probe now isolates rows and records any retry.

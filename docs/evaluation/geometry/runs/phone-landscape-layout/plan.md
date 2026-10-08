# phone-landscape-layout — plan

Task: finish the responsive work left after D5 — phone landscape, 360 px phones, the low-screen orbit case — and run the
final acceptance on the last product version. CORE (learner-facing). `LLM_ONLY`, 0 model calls; no new family, no
OCR/DSL/FactGraph/compiler/prompt change.

## Baseline (before the change, scratch build of `f6ebe946`, `diagnostics/baseline_f6ebe946/`)

Probe `check-mobile-layout.mjs` extended BEFORE the baseline with: controls in view at load, no page scroll while
stepping, labels inside the canvas at the last step, «Xem lại toàn hình» restores the initial camera, three panels
(«Các bước dựng», «Đại lượng», «Đề bài») keep figure ≥ 50 % + controls + panel header and no horizontal scroll, phone
rotation keeps step/selection/camera and controls in view. Result: 15/40 (six original viewports) and 0/8 at 667×375.

- 844×390: canvas at the 320 px floor, play bar at y = 392–427 in a 390 px viewport (`CONTROLS_OFFSCREEN`); floating
  «Đại lượng»/«Đề bài» leave the controls off screen. The figure is height-bound and fills ~26 % of the canvas width.
- 667×375 (narrow layout in landscape): 2 × 2 tool grid + float-button row + canvas floor ⇒ controls off screen; every
  panel flows below and pushes the figure out (`PANEL_LOSES_FIGURE:*`).
- 360×640: play controls wrap to three rows (129 px), last row at y = 645–680 (`CONTROLS_OFFSCREEN`). Panels are fine.
- Rotating a portrait phone to landscape ends in the 844×390 / 640×360 problem (`ROTATED_CONTROLS_OFFSCREEN`).
- Low screen: `FIGURE_LEFT_CANVAS_AFTER_ORBIT` on the triangular prism only (pre-existing); «Xem lại toàn hình» restores.

## Decision

Short landscape (`(orientation: landscape) and (max-height: 30rem)`): controls become a 10rem column beside the canvas —
width is the spare dimension there; the canvas keeps its height, so the figure keeps its size, and no control overlays
the figure. The 320 px floor is NOT lowered (instruction); at 667×375 the floor exceeds the available ~299 px, so only the
canvas's bottom blank margin falls below the fold — controls stay in view because they are beside it. View buttons go to
the top of the column. 360 px: narrower button padding so the three play buttons share one row. The low-screen orbit case
is not changed: the only shared fix (fit by the orbit sweep / bounding sphere) shrinks the figure on every screen — an
approved invariant — so it is presented to the user.

Pre-registered checks: the probe verdict above (`assessMobileLayout`); `VIEW_BUTTONS_OFFSCREEN` added after the baseline
(noted as such). Review set: `inputs/REVIEW_SET.json`. Measurement: `diagnostics/measure.sh` at the final candidate, the
whole Tier-A suite in one run. Gates: T3 + identity gates at the documentation commit.

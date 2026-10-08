# mobile-canvas-fit — plan

Task: close D5 (`ISSUE-ARCH-MOBILE-CANVAS-WHITESPACE-AND-PANEL-SCROLL`) on the product route and bring the branch to
human acceptance. Classification: CORE (learner-facing simulation on phones). Default mode `LLM_ONLY`; 0 model calls;
no new family, no DSL/compiler/prompt/IR change.

## Root cause (reproduced before the change, scratch build of 38a19c65, `check-mobile-layout.mjs`)

- `caoKhungKhaDung` gives the canvas all the height left under its top edge (no cap since the W5 answer to W4 R4).
- The camera fits the figure to `TI_LE_LAP_KHUNG` (0.68) of the BINDING dimension (`scene3d-camera.ts`); on a portrait
  phone that is the width, so the extra height is blank: 390x844 canvas 519 px, figure 48-58 % of its height for six
  of eight families, 107 + 137 px blank (regular triangular pyramid).
- Panels flow below the controls (≤ 48rem), and the controls sit at the bottom of the viewport by construction, so
  every opened panel lands below the fold; opening «Các bước dựng» scrolled 338 px and pushed the figure out of view.
- Found on the way: in a long steps panel the current step is not kept in view while stepping — hidden at 19 of 40
  family × viewport runs, desktop included.

## Decision among the recorded options

(a) fixed height ratio — excluded (shrinks the height-bound rectangular pyramid; brief W5). (c) buttons back on the
canvas and (d) one-row toolbar only win ~50 px and do not remove the band. (b) adaptive height is kept: on the narrow
layout only, canvas = width × projected figure aspect (same points, display rotation and view direction as the camera
fit), capped by the available height, floored at 320 px. The aspect depends on the scene alone, so steps, selection,
panels and resize-within-a-layout never move the canvas or the camera. Desktop and low screens are unchanged.

## Pre-registered checks

- Probe thresholds (`NGUONG_D5`, fixed before the baseline): narrow layout, figure ≥ 55 % of canvas height unless the
  canvas is at its floor or the figure is height-bound; figure in viewport + ≥ 120 px of panel body after opening it
  (reported); canvas height and camera unchanged across panels/selection/steps; current step inside the panel body;
  no horizontal scroll; labels inside the canvas after an orbit.
- Review set: `inputs/REVIEW_SET.json` (chosen before the measurement).
- Measurement: `diagnostics/measure.sh` in a clean detached worktree at the final candidate, all eight families,
  regression probes (suite, scene controls, panels, focus mode, occlusion, playback, evidence builder).
- Gates: T3 full gate + identity gates at the documentation commit.

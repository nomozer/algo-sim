You are an INTERNAL code reviewer with a separate context. You are not independent of this campaign: your result is
labelled "internal separate-context review", never "independent review". Do not edit any file. Do not run git commands
that change state (no add/commit/checkout/stash/reset). Read-only: git diff/log/show, Read, Grep, and running tests is
allowed (`cd frontend && npx vitest run <file>`, `node --test scripts/<file>.node-test.mjs`).

Repository worktree: D:\Documents\projects\algo-sim\.superpowers\worktrees\scene3d-visual-correction
Base commit: fe5f40b7. Review `git diff fe5f40b7` (working tree, uncommitted) restricted to:
  frontend/src/simulations/domains/geometry/scene3d-view.tsx
  frontend/src/simulations/domains/geometry/scene3d-edge-visibility.ts
  frontend/src/simulations/domains/geometry/Scene3DExplorer.tsx
  frontend/src/simulations/domains/geometry/*.test.ts(x) changed in the diff
  frontend/scripts/section-role-oracle.mjs, section-role-browser-probe.mjs, section-role-oracle.node-test.mjs
  docs/evaluation/geometry/runs/scene3d-visual-correction/tools/browser-matrix.mjs (new, untracked)

Context (product): AlgoSim renders 3D solid-geometry scenes from a backend envelope. The frontend is presentation
only: it must never compute geometry facts, coordinates, names or answers (rule R0); it must not mutate the scene.
Section regions keep a terracotta fill; a SELECTED section's boundary is cobalt (Owner policy F2). Hidden lines are
dashed. Mode A (analysis panel closed): no final answer anywhere. Mode B (panel open): answer exactly once.

What the diff claims to do:
1. Exact ray / finite-volume occlusion for ball, cylinder, cone (incl. caps, cone slope, worldToLocal transform).
2. Camera-tangent silhouettes: sphere tangent circle, cylinder/cone tangent generators.
3. Hover state distinct from selection.
4. Mode B: canvas never shows result labels; inspector links to the analysis panel instead of repeating a value.
5. Front curve rim material put in the transparent queue so renderOrder draws it over solid outlines.
6. A 1px LineSegments stroke along the outer rim, sharing the ribbon's material, so rims cannot vanish when the
   region's plane is seen edge-on.
7. A supplemental (NOT official) role-aware pixel oracle: curve hidden part scored per maximal hidden arc; samples
   where front and hidden parts of the same boundary overlap on screen are excluded; three-way verdict
   PASS / FAIL / UNCERTIFIABLE; the probe counts a fault as detected only on views certified PASS unfaulted.

Look for, with evidence (file:line and a concrete failing scenario):
- mathematical errors in occlusion/silhouette (sign errors, eye above cone apex, axis not vertical, degenerate radius,
  camera inside a solid, grazing rays, left-handed ellipse frames);
- ways the supplemental oracle can now PASS a wrong frame (e.g. the ambiguity exclusion or the arc grouping hiding a
  missing boundary, UNCERTIFIABLE swallowing a real failure, thresholds that make faults undetectable);
- Mode A/B leaks (a final value printed twice in Mode B, or anywhere in Mode A);
- renderer regressions: disposal of the shared rim material (double dispose / leak), raycast/picking changes,
  allocation per camera move, render-order effects on other objects (fills, planes, labels);
- any frontend reasoning, hardcoded case IDs / labels / expected answers (forbidden).

Report: a list of findings ranked Critical / Important / Minor, each with file:line, the scenario, and whether you
reproduced it (test command + output) or reasoned it. Say plainly when you found nothing in an area. Under 900 words.

# exact-dimensions — handoff

## 1. State

- Branch `feat/regular-square-pyramid`, local only for this run; no push, merge, PR or branch deletion.
- Product `ed3ae208` · candidate `e1927f84…` · `CACHE_VERSION` 117 · `LLM_ONLY` · 0 model calls.
- Measurement `3bbb8052` (fixtures, build, scene controls, panels, focus) / `fe83c46e` (suite, occlusion) /
  `d51db4e2` (playback, builder); evidence `c5cae8af`.
- Full gate (T3) and identity gates: `diagnostics/gate_<sha>.log`, result recorded in §2 after the run.
- User's change kept: `D frontend/public/favicon.svg` (never staged).
- Human review: **NOT_APPROVED**.

## 2. Gate

Recorded after T3 on a clean detached checkout of the final docs commit.

## 3. What the user decides next

1. Review `review.md` (R1–R10) together with `runs/regular-triangular-pyramid-w01/REVIEW.md` and the W5/W4 packages.
2. Pick a D5 option (`ISSUE-ARCH-MOBILE-CANVAS-WHITESPACE-AND-PANEL-SCROLL`).
3. Whether to spend a live budget to measure the model's extraction/layout for this family
   (`ISSUE-ARCH-REGULAR-TRIANGULAR-MODEL-LAYOUT-UNMEASURED`).
4. On approval: merge into `main`, push, delete the branch — in a separate turn with an explicit instruction.

## 4. Open, not hidden

- `ISSUE-ARCH-MISSING-SIZE-REASON-ON-AFFINE-CHART` (new): missing size on a non-Euclidean chart refuses with
  "invariance unproven" instead of "determines the answer".
- The metric is used for the regular triangular pyramid / tetrahedron only; other families keep the Euclidean chart.
- Symbolic sizes and sums of radicals stay refused.
- Wave-coded legacy Informatics scripts keep their names (listed in `RUN_NAMING.md`).

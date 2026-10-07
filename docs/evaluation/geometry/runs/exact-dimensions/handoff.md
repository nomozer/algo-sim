# exact-dimensions — handoff

## 1. State

- Branch `feat/regular-square-pyramid`, local only for this run; no push, merge, PR or branch deletion.
- Product `ed3ae208` · candidate `e1927f84…` · `CACHE_VERSION` 117 · `LLM_ONLY` · 0 model calls.
- Measurement `3bbb8052` (fixtures, build, scene controls, panels, focus) / `fe83c46e` (suite, occlusion) /
  `d51db4e2` (playback, builder); evidence `c5cae8af`.
- Full gate (T3) and identity gates at `4ef0a02e`: §2.
- User's change kept: `D frontend/public/favicon.svg` (never staged).
- Human review: **NOT_APPROVED**.

## 2. Gate

Run once on a clean detached checkout of the docs commit `4ef0a02e` (worktree `D:/tmp/exact pre`, CRLF, path with a
space), 0 model calls:

- **T3 `FULL_PRODUCT_GATE_PASS`** (`diagnostics/t3_4ef0a02e.log`): pytest 7302 passed / 1 skipped / 2 deselected ·
  vitest 1148/1148 (75 files) · typecheck + build · demo 5/5 · crash surface 6/6 — 369.7 s.
- **Identity gates** (`diagnostics/gates_4ef0a02e.log`): candidate verify `e1927f84…` (111 files) · cache lock 117 /
  environment `b1714b56…` · schema export ×2 idempotent, mirrors identical · `LLM_ONLY`, routing unchanged, compiler not
  referenced from the route · model-surface files changed since `4ceadd55`: 0 · evidence outside this run: only the
  living candidate registry, `EVALUATION_CANDIDATE.json` and `RUN_NAMING.md` · `git diff --check` clean · docs audit
  PASS · node harness 95 pass / 2 skipped / 0 fail · working tree clean before and after. The "catalogued reports
  changed: 1" line is the living `EVIDENCE_INDEX.md` (linked from the catalogue header; same line in the rtp-w01 gate
  log), not a historical report.

This commit only records the result (docs); no product, harness or test change after the gate.

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

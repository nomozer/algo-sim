# Review packet — Visual closure + B3 distance bridge + F2 role-aware oracle proposal + sphere source fix

Repository root: `D:\Documents\projects\algo-sim` (Windows, Git Bash available). Do NOT modify any file in the repository,
do not create branches/commits, do not run `git checkout`/`switch`/`reset`/`stash` anywhere, do not start servers or
browsers, do not run the full backend or frontend suites (a measurement is running). You may read any file, run
`git log/show/diff` (read-only), and run small Python probes that IMPORT repository code with the interpreter
`D:/Documents/projects/algo-sim/backend/.venv/Scripts/python.exe` (set `PYTHONIOENCODING=utf-8`, `ALLOW_LIVE_AI=0`,
working directory a worktree's `backend/`). Put any probe script under
`C:/Users/Bunny/AppData/Local/Temp/claude/d--Documents-projects-algo-sim/9b8a0ef4-8ee8-41e6-a541-89ef55bd032b/scratchpad/review/`.
Never call a model/provider/network.

## Candidates (read through the worktrees below; they are clean checkouts)

| Line | Worktree (read here) | Branch / commits | What changed |
|---|---|---|---|
| Visual + B3 + F2 harness | `.superpowers/worktrees/b3-dist` (currently detached at `cb8d7c4a`) | `research/f2-oracle-b3-e2e`: `1a4a0b93..cb8d7c4a` | see below |
| Sphere source fix | `.superpowers/worktrees/sphere-src` (detached at `98d52e90`) | `research/sphere-sample-source-authority`: `de49c592..98d52e90` | see below |

Product diffs to review in full:
1. `git -C .superpowers/worktrees/b3-dist diff 1a4a0b93 53fe3d25 -- frontend/src` — visual closure product (F1 formula
   shown once in analysis panel; inspector keeps identity/link; F2 selected section boundary cobalt `#2563EB` while the
   semantic fill stays terracotta `#C85A32`; transient hover; sphere decorative loops removed).
2. `git -C .superpowers/worktrees/b3-dist diff a2692503~4 3524bec8 -- backend` — B3: `typed_fact_next_bridge.py`
   `_distance_question` maps `typed-fact-next/2` `measurement` goals with `goal_type: "distance"` to planner questions
   (`{point, plane}` → point–plane distance, `{segment}` → length, `{line1, line2}` → line–line distance), anything else
   `INVALID_MATH_GOAL`; `/1` unchanged. Tests: `backend/tests/geometry/test_typed_fact_next_v2_distance_bridge.py`.
3. `git -C .superpowers/worktrees/b3-dist diff 9490bae9~2 3117d513 -- frontend/src` — ellipse rim band orientation fix.
4. `git -C .superpowers/worktrees/b3-dist show 9490bae9 --stat` and the files it adds — PROPOSED role-aware section check
   (`frontend/scripts/section-role-oracle.mjs`, `.node-test.mjs`, `section-role-browser-probe.mjs`) and
   `frontend/scripts/b3-distance-browser-e2e.mjs`. The proposal is meant to replace the locked hue-only gate for section
   targets ONLY after review; judge whether it really reads the boundary of the selected object and cannot be passed by
   a wrong rendering.
5. `git -C .superpowers/worktrees/sphere-src diff de49c592 98d52e90` — sphere sample source authority:
   `formation.py` (curved-section cutting plane → `CONSTRUCT_CUTTING_OBJECT`), `build_geometry_samples.py` (only source
   data free), CACHE_VERSION 128→129 with cache probe/migration test, oracle correction layer
   `docs/evaluation/geometry/runs/sphere-sample-source-authority/oracle_scalar_radius.py` over the hash-locked
   `step-math-validation/oracle.py`.

Context documents: `AGENTS.md`, `docs/RULES.md`, and in b3-dist
`docs/evaluation/geometry/runs/hybrid-b3-v2-distance-bridge/B3_VERTICAL_SLICE_REPORT.md`,
`docs/evaluation/geometry/runs/visual-closure-hybrid-readiness/OFFICIAL_SUITE_F1_F2_REPORT.md`.

Architecture rule to check: the LLM never decides geometry; the bridge is a pure rename; Source Gate, planner and
exact engine re-check everything; refusals fail closed with typed codes; no case-ID or label hardcoding in product.

## Required evaluation (actually probe these against the B3 bridge/route, report observed codes)

Use `from app.ai.adapter4_route import run_typed_fact_next_v2_route` and the payload builder `_prism` in
`backend/tests/geometry/test_typed_fact_next_v2_distance_bridge.py` (you may copy/adapt it in your probe).

1. Plane given by three collinear points although the source text is perfectly valid (e.g. a named midpoint on an edge).
2. Plane given by more than three points that are NOT coplanar.
3. Two lines that are parallel, coincident, intersecting, skew — what does `{line1, line2}` return in each case?
4. Wrong reference types: a plane where a point is expected, a line ref of 3 points, a qualified reference to a
   different/undeclared solid (`xx::A`).
5. Renaming, uniform scale, operand order, and a dependent (described) point such as a midpoint of a top edge.
6. Underdetermined and contradictory inputs.

For each: expected mathematically correct behaviour, observed status/code/answer, verdict (OK / DEFECT / RISK).

## Output

Write `C:/Users/Bunny/AppData/Local/Temp/claude/d--Documents-projects-algo-sim/9b8a0ef4-8ee8-41e6-a541-89ef55bd032b/scratchpad/review/REVIEW_RESULT.md`
with: scope actually read; findings ranked BLOCKER / IMPORTANT / MINOR with file:line and a concrete failure scenario;
the six-item probe table with observed outputs; an explicit verdict on whether the role-aware oracle may replace the
hue gate for section targets (yes / not yet + why); and a final line `REVIEW_VERDICT: PASS | PASS_WITH_FINDINGS | FAIL`.
Be skeptical; do not restate the authors' claims as findings without checking them.

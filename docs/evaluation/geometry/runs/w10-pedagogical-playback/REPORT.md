# Human visual review and pedagogical playback closure (w10)

Status: `READY_FOR_HUMAN_VISUAL_REVIEW` — automation only. The w09 human review
was `FAIL_REQUIRES_PEDAGOGICAL_VISUAL_REPAIR`; this run repairs what it named and
hands the result back to a human. Nothing here is `MERGE_READY`.

## Identity

- Branch `fix/cuboid-visual-semantic-closure`, start `be23e88d`, `origin/main` `a9492ee9`.
- Product commit `f0deaa0d` · candidate `3bc9415b…` → `8539acbc…` (refrozen four
  times in clean worktrees, last at `7f5205ca`; the hash moved twice).
- Measurement commit `40ce889f` (detached clean worktrees, no local venv);
  evidence post-processing `52de6f22` (offline, no browser rerun).
- `CACHE_VERSION` 102 → **103** (user decision: cached `ok` envelopes carry the
  changed scene); provider fingerprint `b1714b566e25c912` unchanged;
  `DEFAULT_MODE = LLM_ONLY`; 0 live Gemini requests; 0 application LLM calls.

## What the reviewer rejected, and what changed

| Area | Root cause (measured) | Repair |
|---|---|---|
| Playback | The interval read a stale closure in controlled mode and stalled at step 1; no replay control at the last step | `scene3d-playback.tsx`: latest state through a ref, stop exactly at the last step, "Xem lại" resets step + selection. Playback never sets `selected_id` (the w09 causal colour came from the harness clicking a readout row: `EXPECTED_HARNESS_ACTION`) |
| Camera | One fixed direction for every scene; fit by bounding sphere left the figure small | Direction chosen on a 10° × 15–40° Z-up grid from projected hull area, depth, vertex/vertex and vertex/edge clearance, face tilt. Clearance thresholds = ½ of the unit cube at the former direction; area/depth ≥ 60 %/50 % of the scene's own best. Distance fits the real projection and recentres. Tests: all six families meet the thresholds and fill 55–80 % of the measured canvases (desktop 1318×464, mobile 340×418) with vertex gaps ≥ 2 label heights and vertex–edge gaps ≥ 1 |
| Hidden edges | A-B and A-D of the rectangular pyramid were classified HIDDEN yet drew no pixel: the dashed span depth-tested against the solid's own depth layer. Visible edges between two front faces lost MSAA samples and read pale. Edges shared the fill colour | Both span layers stop depth-testing (the CPU classification the oracle measures is the authority); lines draw after fills; dedicated edge ink (≥ 7:1); depth layer pushed back; a segment on a solid edge yields to the canonical owner (one edge, one stroke) |
| Learner surface | Solids named "Khối đa diện dựng từ…", an answer shown twice, generic narration, a section-closing step that changed nothing | Solid nouns from topology (fail-closed on unknown shapes), an answer and its aliases are ONE conclusion carrying the source's dependencies, structured narration, section fill appears at the closing step |
| Causal | Flat highlight of the whole closure | Target > intermediates > givens by colour; everything outside the closure dimmed, surviving re-classification on orbit; dashes kept; closing the panel or "Xem lại toàn hình" restores neutral |
| Narrow screens | Detail panel covered the answer row and "Xem lại"; floating buttons covered the top vertex | Panel and buttons flow above/below the stage at ≤ 48rem |
| Reset view | "Xem lại toàn hình" right after a drag kept the damping momentum and drifted away | `datKhungNhin` consumes the momentum before setting the pose |

Found while measuring (all recorded in `diagnostics/MEASUREMENT_ATTEMPTS.json`):
the conclusion event of an alias declared the source's own id as its dependency
(product, `f5a3adf2`); the component tree listed an answer twice (product,
`7a03e50d`) and the first fix of that removed given lengths AD/AA′ of the cube from
the tree (product regression inside this wave, `f0deaa0d`); a blind click under
the sticky navigation bar opened the sign-in overlay (harness, `5e6e1583` →
`40ce889f`); mobile crops were cut at 1× on 2× images (harness, `52de6f22`).

## Measurement discipline

- The frozen human registry stays byte-identical. Because the reviewed camera no
  longer exists, the oracle checks the reviewed sets at the REGISTERED camera on
  the new scene and at the NEW camera; the expectation transfers only if both
  match, the registered scene hash matches and the geometry is unchanged
  (`transfer_expectation`, flag `--declared-camera-change`). All six hold.
- Seven browser attempts and two T3 runs are listed, failures included.

## Final verification

| Gate | Result |
|---|---|
| T3 `full-gate.mjs` from a path WITH a space (`D:/tmp/w10 space/algo-sim`, `40ce889f`) | `FULL_PRODUCT_GATE_PASS` — pytest 6368 passed / 0 failed (1 skipped, 1 deselected) · vitest 946/0 · typecheck + build · demo · crash surface |
| Browser suite, 6 families × desktop 1440×900 + mobile 390×844 | 12/12 positive, 12/12 negative; immutable 120 frames 12/12; causal closure 12/12; orbit 12/12 (planned gesture first, passed first time 12/12); formation 12/12 |
| Occlusion (product ↔ independent oracle) | 24/24 states, product = oracle 24/24; frozen expectations `DECLARED_CAMERA_CHANGE` 6/6 |
| Learner playback (Play pressed once) | 12/12 runs × 17/17 checks; orbit laps 60/60 with state transitions |
| Hidden-edge crops | 60, both endpoints inside 60/60, oracle disagreements 0, duplicate owners 0 |
| Candidate `--verify` · cache lock · schema export ×2 | PASS · `CACHE_VERSION 103`, fingerprint `b1714b56…` · byte-identical |
| Node tests (harness) | 29/29 (main tree); from the spaced path 25 passed + 2 skipped by design (no venv inside the worktree) |

Numbers: `results/VERIFICATION_SUMMARY.json` (generated from the evidence files).

## Limitations (not hidden)

- **No human has approved** the new contact sheet, screenshots or crops.
- Lines are still 1 physical px: WebGL ignores `linewidth`. Thicker lines would
  need the `Line2` path that was removed at the user's request (`1a553b8`); not
  reintroduced.
- Edge visibility is classified per solid; a scene where one solid hides another
  would need `occluders` (marked `ponytail:` in `canonicalEdgeMaterial`). The six
  families have one solid.
- Rotated views are required to keep depth (hull, depth, no face edge-on), not the
  full label-clearance threshold of the default view — crowded scenes meet the
  latter at almost no azimuth (cross-section: 30° and 60° only).
- Browser scripts outside the test graph still build paths with `URL.pathname`
  (they are run by hand); tracked as a residual issue.
- Temporary directories of this wave outside git: `D:/tmp/w10-out`,
  `D:/tmp/w10-build.log`, `D:/tmp/w10-freeze4` (deregistered, delete was refused
  while a process held it), `D:/Documents/projects/tmp-dist-exp`.

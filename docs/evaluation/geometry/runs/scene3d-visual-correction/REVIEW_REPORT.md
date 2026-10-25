# Review report

**Status: `INDEPENDENT_REVIEW_PENDING`.** Nothing in this run is an independent review. `HUMAN_VISUAL_APPROVED = PENDING`.

## 1. Codex's review step

Codex announced `requesting-code-review` and never dispatched a reviewer. Its last action was a checkpoint commit. That
commit was not executed because Codex's automatic approval review failed on quota ("not a determination that the
action is unsafe"). No review output exists from Codex: none in the run directory, none in `.superpowers/`, and none
in Codex's session log after that point. Details: `TAKEOVER_FROM_CODEX.md` §3.

## 2. Internal separate-context review (Claude)

One reviewer agent with a fresh context, briefed only with the diff scope, the product rules (R0, F2, Mode A/B) and
the list of claims. The brief: `review/internal-review-brief.md`. The report, verbatim: `review/internal-review-1.md`.
The reviewer was read-only. It reproduced its findings with scratch probes outside the repository.

It is labelled **internal**: the same campaign wrote and reviewed the code, and the reviewer was spawned by the author.

Scope: `git diff fe5f40b7` of the working tree (Codex + Claude, before the review fixes). Baseline at review time:
geometry vitest 834/834, oracle node tests 21/21.

## 3. Findings and disposition

| # | Severity | Finding | Reproduced by reviewer | Disposition |
|---|---|---|---|---|
| C1 | Critical | A secondary ball sharing the primary's frame lost its volume metadata, so its new silhouette ring was never positioned. A unit ring was drawn at the scene origin (on vertex O of the circumsphere fixture) | yes (unit probe) | **Fixed.** `datKhoiCongKhongChe` keeps the metadata under a presentation-only key: silhouette placed, solid not an occluder. Silhouettes are hidden until first placed. Tests: `never shows a silhouette that no camera update has placed`, `places the silhouette of a curved solid that does not occlude…` (both RED first) |
| I1 | Important | Codex's new cap rims duplicate the backend's `circle3` base/top circles (route-D-style scenes). Family 10: the cone's navy rim sits exactly on the selected cobalt section circle and is drawn after it. The rim also appears before the circle's own step (#31) | structural yes, pixels reasoned | **Fixed.** `boVanhDayTrung` drops the solid's own cap rim when the whole scene has a `circle3` with the same centre, radius and axis. Comparison of backend numbers only. Legacy samples, which have no circles, keep their rims. Test: `lets a backend circle own a cap rim…` (RED first). Confirmed on real data: families 09, 10, 12 match, the six legacy samples have none |
| I2 | Important | Codex passed curved occluders to polyhedron-edge classification, so an enclosing sphere dashes every edge of an inscribed tetrahedron | yes (0→6 hidden) | **Fixed by restoring the base and reference convention.** Polyhedron edges follow solid faces only. Curved solids still dash free segments, as the Owner reference does. Test: `classifies a polyhedron's edges by solid faces only…` (RED first: 3 → 6 hidden). Known remaining gap: a polyhedron standing *beside and behind* a sphere is not dashed by it, the same as at base |
| I3 | Important | The supplemental oracle passed a hidden curve arc with up to ~60 % of it missing (threshold 0.4) | yes (synthetic) | **Fixed.** Arcs get `hiddenArcCoverage` 0.6. Unfaulted browser arcs measured 0.678–0.991, and the threshold was chosen from those, never from faults. Test: `a hidden arc with 40% of its dashes missing fails` (RED at 0.4) |
| I4 | Important | The claim "0 FAIL after the fix" partly hides FAIL→UNCERTIFIABLE transitions; 7/10 p6 views are uncertifiable | from receipts | **Reported precisely**, not hidden: `SCENE3D_VISIBILITY_CORRECTION.md` §6 and `OFFICIAL_VISUAL_SUITE_RESULTS.md` §3 list each view's transition. The reviewer found no case where UNCERTIFIABLE hides a failing scored part |
| M1 | Minor | `!` on the recursive rim build crashes for `rim_point` without `radius_sq` | yes | **Fixed** (`if (!rim) continue`). While fixing it, the new test found a second latent crash in the same lines: fractional axes were passed as `String(1.5)`, which the coordinate parser rejects. Now fixed |
| M2 | Minor | Hover reuses the selected widths; it differs from selection by colour only | reasoned | Accepted. Hover is a weaker emphasis by colour; the widths are deliberate |
| M3 | Minor | Rim visibility goes through the zero-length segment path, which rebuilds the occluder triangles 96× per rim per camera change | reasoned | Not fixed. CPU cost only, and the orbit gate (GPU allocation) still passes in T3 |
| M4 | Minor | The oracle header no longer matched the code; `FILL_COLOR_DISTANCE` duplicated `FILL_NOT_TERRACOTTA`; the oracle shares the renderer's discretisation | — | Header rewritten (threshold history, hard-coded policy RGB, independence limit stated). Duplicate reason removed |
| M5 | Minor | `mode_b_once` looks only at the first analysis item, and only at inspector data attributes | — | Complemented by `tools/inspector-probe.mjs`: every final result of 4 scenes is selected in turn, with a negative control on the pre-fix product (see `BROWSER_VISUAL_ACCEPTANCE.md` §2) |
| M6 | Minor | Camera inside a ball hides everything; grazing rays along a cap plane count as visible | reasoned | Accepted edge cases |

The reviewer found nothing in these areas: occlusion and silhouette mathematics (incl. eye above the cone apex),
disposal (materials and geometries are deduplicated), the render-order change being limited to the front rim, R0, and
hard-coding.

Round-1 fixes: commit `093c0b4c`.

## 3b. Round 2 — on the round-1 fixes (`review/internal-review-2.md`)

A second fresh-context internal reviewer read `093c0b4c` only. It ran no code, because a browser measurement was in
progress, so all of its findings are reasoned. It found no Critical issue and confirmed that C1 is fixed on every path.

| # | Finding | Disposition |
|---|---|---|
| I-A | A cylinder given by height (`apex_or_top: null`) lost its top cap rim, because the round-1 fix used `apex_or_top!` | **Fixed**: the exact backend string when present, else the derived top as a valid fraction. Test `keeps both cap rims of a cylinder given by height…`. RED confirmed on `093c0b4c`'s renderer: 1 rim, expected 2 |
| I-B | The dedupe compared a 1e-6-rounded axis at 1e-9 tolerance, so tilted fractional axes never matched | **Fixed**: the rim records the unrounded centre and axis. Same test, tilted axis (1/3, 2/3, 2/3) |
| I-C | The dedupe ignored user hide/isolate and the display translation, so a cap could vanish with nobody drawing it | **Fixed**: the caller passes only circles the user has not hidden or isolated away, at the solid's translation |
| I-D | Occlusion convention is now split: polyhedron edges ignore curved solids, while free segments and section borders inside a ball are dashed | **Owner decision** (`FINAL_OWNER_HANDOFF.md`, decisions). Not changed: free segments follow the Owner reference, polyhedron edges follow the base and the reference |
| minor | 40 % arc test might fail through a front chord | **Fixed**: the test asserts that the arc fails and every front chord passes. RED at 0.4, GREEN at 0.6 |
| minor | Per-chord 0.4 `pass` still exported for hidden curve chords | **Fixed**: `null`, because those chords are judged in their arc |
| minor | 1 px stroke has no depth bias against coplanar fills | Not changed. Watch item for the human visual review |
| minor | Framing counts unplaced silhouettes | Not changed. Latent, same as before this work |

Round-2 fixes: commit `78aaef2f`.

## 4. After the fixes

Code at `78aaef2f`: geometry vitest 839/839, typecheck 0 errors, oracle node tests 22/22.

Neither review round caught the Mode B over-hiding that Codex introduced. Both reviewers read Codex's own test as the
spec. The locked official suite caught it (0/8 at `3c6d1e65`), and it was fixed in `b8b3311b`, after both rounds.
That fix was not reviewed by an agent. The locked suite on `c84e8620` (7/8, Mode B assertions all pass) is its check.

Final gates on candidate `c84e8620`:
- Full T3 PASS;
- official suite 7/8;
- browser checks: `BROWSER_VISUAL_ACCEPTANCE.md`.

No third review round was run.

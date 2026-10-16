# Scene3D visual correctness — integration review, CONTRACT-BE-1 and branch closure

Run `scene3d-visual-correctness` · 2026-10-17 · LOCAL Windows 11 · branch `integration/scene3d-visual-correctness`
from `main` = `origin/main` = `6d8ead99` · `LLM_ONLY`, `CACHE_VERSION = 125`, Hybrid product enablement NO-GO,
0 live Gemini calls · `HUMAN_VISUAL_REVIEW_PENDING`.

Status words: **IMPLEMENTED** (code exists) · **VERIFIED BY TESTS** (offline test red → green or green) ·
**MEASURED** (browser/replay receipts in this run) · **HUMAN_REVIEWED** (none in this run) · **NOT_MEASURED**.

## Commits

| commit | what |
|---|---|
| `a7388a40` | merge of Gemini `0ef0a20a` (base `140ae4ed`, 5 frontend files) onto `main` `6d8ead99`, no conflicts |
| `08021881` | FE-4 fix 1: on-line span no longer counts the backend anchor point |
| `f07ea069` | CONTRACT-BE-1: route D scenes carry `targets`; integration scenes, harness source, browser receipts |
| `e460cfac` | FE-4 fix 2 (independent review): a witness foot outside the edge stays inside the drawn line span |
| `8f437980` | candidate refreeze at `e460cfac`: `43e877ed…` (110 files), divergence layer `inputs/candidate_divergence.json` |

T3, integration and cleanup: `run.json` and `handoff.md`.

## A. What Gemini changed and what the independent review concluded

Read from the diff of `0ef0a20a`, not from Gemini's report. Gemini's claims re-checked on the merged tree: vitest
1067/1067, `tsc -b` exit 0 (Gemini's 714/714 was the geometry folder on its older base). An independent read-only
reviewer (subagent) then reviewed `6d8ead99..f07ea069`.

| item | change | verdict |
|---|---|---|
| FE-1 plane | `daGiacMatPhang`: plane3 drawn as the convex hull of scene points lying on the plane; < 3 such points or zero area ⇒ previous square patch (`khungMatPhang`) | IMPLEMENTED, accepted with risks: the hull is on the plane (points within 1e-3 projected onto it), but it is a hull of *scene points*, not polyhedron ∩ plane — a plane cutting edges between named points (cube, plane through three edge midpoints with no `section` object) draws a smaller polygon than the true cut. Absolute 1e-3 tolerance. `depthTest:false` tints over front faces (opacity 0.11–0.24). A general polyhedron–plane cut is a contract change and is not opened here. |
| FE-2/3 occlusion | `classifyWorldSegmentVisibility` + `WorldSolidOccluder`: non-canonical segments/lines split into VISIBLE/HIDDEN spans against solid faces; spans colinear with a canonical edge yield to it (drawn once) | IMPLEMENTED, VERIFIED BY TESTS (`scene3d-hidden-lines.test.tsx`). Risks: only polyhedral solids occlude (mixed curved + polyhedral scenes: a curved solid no longer hides these lines); near edge-on faces can flip at the `1e-6` facing test (same as canonical edges); the witness branch (`nhanChungGroup`) is never set, so witnesses are not classified (dead code). The plane hull outline yields only to canonical edges: when the hull equals a section polygon or contains a drawn diagonal (`(SAC)` + `AC`) the two outlines overlap at the same place in two colours — cosmetic, checked in the browser on `section-cube-A1BD` (`visual/receipts/section-cube-aux1.png`). |
| FE-4 line extent | `doanDuongThang` centres on figure points lying on the line | **BUG ×2, fixed.** (1) the on-line range started at 0 = the backend anchor, so a line anchored far from the figure was centred halfway to it (`08021881`, red → green). (2) found by the reviewer: a distance-witness foot is a kernel projection, usually not a scene point, so a foot outside the edge fell past the drawn end (d(A, BC), foot at t = −1.41, span from −0.30). Fixed by `diemChoDuong` (`e460cfac`, red → green). Lines use the whole scene's points, so the span does not jump between steps; later points shape it at earlier steps (accepted). |
| FE-5 highlight | witness colour/dim by causal layer `tang`; out-of-chain witnesses dimmed ×0.3, not hidden | OK. A witness owned by a background object keeps its full colour (minor). |
| FE-6 right angle | `huongChanVuongGoc`: flips the marker's display direction `u → −u` when the foot is at an end of the on-line points | OK: the flip keeps `u ⟂ v`, the mathematical relation is unchanged; display direction only. Plane witnesses effectively never flip. |

No hardcoded case IDs or labels in the added product lines (reviewer + own read).

## B. Fixes added during integration

FE-4 ×2 (above) and CONTRACT-BE-1 (below). Each with a test that is red on the code before the fix.

## C. CONTRACT-BE-1 — closed

**Root cause.** `function_route.run_function_route` called `build_simulation_state(spec, exec_result,
declared_topology)`, but the third parameter is the request contract whose obligations become `state["targets"]`.
Route D therefore had `targets == []`: the asked distance `kq_q` got `role = intermediate` / `category = measurement`,
its event still `FINAL_RESULT` (fallback "last measure"), and the target plane `mp_q` was `display_group =
["construction"]`, hidden at `aux=0` as a measurement-only auxiliary plane.

**Ownership.** The engine knows what the source asks (gate-certified asks → IR measures); `scene3d.py` owns
`display_group`/annotation role from `targets`; the frontend only reads them. Fix at the producer: `KetQuaTuyen.targets`
= each asked measure's answer variable + its named operands, minus the planner's auxiliary labels (a constructed foot
H is never a target; the described point of an effect chain, "trung điểm của SC", is). The route writes it into the
state. No new geometry, no new H, no mass role change, no schema/prompt change.

**Result** (VERIFIED BY TESTS + MEASURED): `kq_q` role `result`, `mp_q` and `M` `target`; FINAL_RESULT subject `kq_q`;
at `aux=0` the target plane and the source point stay visible; selecting the quantity shows the perpendicular witness,
the right-angle marker and `d(M, (SAB)) = 1` (`visual/receipts/pyr-plane-quantity-selected.png`). The default label
policy is kept (result label on selection / "Hiện tất cả"). Tests: `test_function_discovery_planning.py`
(`test_asked_distance_to_a_plane_is_the_result_and_its_plane_is_a_target` ×3 solids,
`test_fresh_foot_is_never_a_target_and_named_operands_are`), `scene3d-auxiliary.test.ts` block "CONTRACT-BE-1"
(FINAL_RESULT, hidden auxiliaries, selected quantity, timeline) on the regenerated scenes.

Route D answers unchanged: the generalized-goal-entry bundle (174 rows) replayed at `e460cfac` is identical to the
recorded production arm in status, code and answers (`results/route-d-replay-*.json`). Reviewer edge cases, not
reachable for distance asks and left as is: a source-stated foot (`fresh=False`) is excluded from targets, but a
distance measure's operands are never the foot; the described point is both `binding: AUXILIARY` (provenance) and a
target (display), which are different axes.

## D. BE-2 / BE-3 / BE-4 — no contract change

| finding | decision | why |
|---|---|---|
| BE-2 canonical-edge association for colinear `line3` | NO CHANGE | The frontend already decides colinearity geometrically from exact world coordinates (`yield_colinear_canonical_edges`); backend `boundary_edge_ids` would be a second authority for the same fact. No failing case found. |
| BE-3 witness marker direction | NO CHANGE | Backend `marker.u` states the mathematical direction along the receiving object; which side the glyph sits on is presentation (camera/figure dependent) and is owned by the frontend (`huongChanVuongGoc`). One rule, one place. |
| BE-4 plane display region | NO CHANGE | Backend emits the mathematical plane (point + normal) and sections; the display region is a frontend choice. A true polyhedron ∩ plane region would be a new contract — not opened (no Typed Facts / schema expansion without evidence). Risk recorded under FE-1. |

## E. Rendering level reached

MEASURED (technical, not pedagogical): Scene3D harness on the 11 integration scenes regenerated from this backend
(`measure_function_discovery.py --integration`: three point–plane, named line, result lines, three derived lines,
goal entry, one refusal) — Intel D3D11 and SwiftShader, before and after the second FE-4 fix:
`PASS_CORE_CAUSAL_RENDERING`, 0 page/console errors, causal order (line before foot), aux toggle, selection, backward
playback, orbit/zoom/reset gestures observed (`visual/receipts/*.json`). The harness reads `scenes.json` CRLF working
bytes `d722b963…` (committed LF bytes `73ed4071…`). Orbit gate on a build of `a7388a40`+fixes: `KHONG_ON_DINH` on
p1/p6/p7, the known `ISSUE-OPS-ORBIT-GATE-UNSETTLED-LOCAL` symptom; not compared against a `main` build in this run, so
no orbit regression signal either way (NOT_MEASURED). Camera/framing: no change; a mid-height default view still makes
both top and bottom faces back-facing on cubes (pre-existing). Hidden/visible strokes, line extension, witness and
auxiliary planes: correct on the inspected screenshots; **not human-reviewed**.

## F. Regressions

None found. Frontend vitest 1072/1072, `tsc -b` clean; backend geometry/route-D suites green (2305 at `f07ea069`);
route D replay identical; Planner, compiler, kernel, interpreter, schema, prompts and `/api/analyze` untouched.
Authoritative numbers: T3 in `run.json`.

## G. Gates

Candidate `43e877ed49e409e48504737edcf010b0b8cad395bb93ad2c0494985347a40ccf` (110 files) frozen at `e460cfac` in a
clean detached worktree, `--verify` MATCH there and on the branch. T3, Playwright, typecheck and build: `run.json`.

## H. Git — see `handoff.md`

## I. What still blocks visual acceptance or Hybrid

- `HUMAN_VISUAL_REVIEW_PENDING` for all of the above.
- FE-1/2/3 risks above (hull ≠ true section, curved occluders, overlapping outlines, dead witness branch).
- Hybrid enablement: unchanged blockers — extraction NOT_MEASURED live, source-grammar residuals
  (`ISSUE-ARCH-LINE-REF-PREMISE-GRAMMAR-CUBE`, `ISSUE-ARCH-HYBRID-GATE-RESIDUAL-FALSE-SERVES`,
  `ISSUE-ARCH-CONSTRUCTION-WORDING-BREADTH`).

## J. Next research step

Source grounding / natural-language understanding before G16. Evidence: every route-D capability measured so far is
on authored Typed Facts; provider extraction is NOT_MEASURED and the open blockers to enablement are source-grammar
and false-serve residuals, not a missing construction family. G16 (distance/angle construction) would add planning
breadth on top of the same unmeasured input stage. This matches the earlier recommendation in the
generalized-goal-entry run; it remains the user's decision.

## Environment residuals (not product)

`.superpowers/worktrees/goal-bounded` (14 083 files) and `.superpowers/worktrees/goal-fixed` (13 625 files): plain
source copies left by a Codex sandbox, no `.git` link, not registered in `git worktree list`, no `node_modules`.
ACL: Codex sandbox SIDs `(M)` inherited, owner `Bunny:(F)`; deletes fail for files created inside the sandbox.
`backend/.tmp/pytest-05045731f8a046b9ba317bc970ecca11`: owned by `CodexSandboxOffline`. Not touched. Owner-run
removal, scoped to these three paths only (elevated prompt, after confirming nothing else is needed from them):
`takeown /F "<path>" /R /D Y`, `icacls "<path>" /grant Bunny:F /T`, `rd /s /q "<path>"`.

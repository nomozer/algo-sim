# Pedagogical timeline + source grounding closure (w12)

Status: `READY_FOR_HUMAN_VISUAL_REVIEW` — automation only. The w11 human review was
`NEEDS_CHANGES` (W11-H1…H5, recorded additively in `inputs/W11_HUMAN_VISUAL_REVIEW.json`);
this run repairs what it named and hands the result back to a human. Nothing here is
`MERGE_READY`.

## Identity

- Branch `fix/cuboid-visual-semantic-closure`, start `a4fd5fec`.
- Product commits: `79eb1e59`, `8aaeae80` (backend grounding) · `98b505ef`, `233f8720`,
  `4014f311` (frontend/src) · `d17550c3` (`CACHE_VERSION`). Red tests first: `1fd55d99`
  (backend), `fb4ea271` (frontend). Last product commit **`4014f311`**.
- Candidate `df04a613…` → **`548f5b3b…`** (103 files), frozen **three** times in the clean
  worktree `D:/tmp/w12-freeze`, each after a product change: `b9c60010` (at `d17550c3`,
  intermediate `8ffd6d46`), `054bc08d` (at `8aaeae80`), **`c243968b`** (at `4014f311`; same
  tree hash, product commit moved). Both intermediates are declared in
  `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`.
- Measurement commit **`c243968b`** (detached clean worktree `D:/tmp/w12-final`, no local
  venv); evidence and T3 commit **`442584cf`**.
- `CACHE_VERSION` 104 → **105**, once (`d17550c3`): a cached `ok` envelope could carry an
  invented GIVEN (served → rejected); provider fingerprint `b1714b566e25c912` unchanged.
  `DEFAULT_MODE = LLM_ONLY`; 0 live Gemini requests; 0 application LLM calls.

## What the reviewer rejected, and what changed

| Finding | Root cause (measured) | Repair |
|---|---|---|
| W11-H1/H2 — the timeline mixes construction with calculation steps; some steps change nothing on screen | The step bar walked every trace event (INIT, GEOMETRY_CONSTRUCTION, MEASUREMENT, FINAL_RESULT). The backend events and formation snapshots were already typed; the presentation ignored the types | `98b505ef`: `geometryTimeline` partitions the events into **geometry steps** — a new step only at a GEOMETRY_CONSTRUCTION event that changes the drawn figure (visible set or section progress); the frame shown is the step's last event, so #31 (`frame k ⇔ trace[k]`) and #32 hold; new invariant #35. Player, explorer and screen-reader text count geometry steps; Play stops at the last one; seeking restores objects, section progress, fill, selection and the solution panel. Steps per family: 3 · 3 · 5 · 5 · 5 · 10 (cross-section: points, base, solid, plane, each section edge, closure, BD) |
| W11-H3 — formulas and results must stay, as a secondary layer in sync | — (presentation requirement) | `98b505ef`, user decision "Bảng dưới thanh bước": one panel under the step bar — **Kết quả** (always visible, the answer exactly once), **Dữ kiện**, **Các bước tính** (formula + "Dựa trên"), in sync with the geometry step; the readout strip on the canvas is gone; narrow screens collapse givens and steps |
| W11-H4 — dark orange meant both "numerical given" and "selected object" | Two hand-written palettes (renderer, readout CSS) drifted apart; the formation highlight was orange too | `233f8720`: one role table (`scene3d-roles.ts`, CSS mirrors it, sync test): **blue = being looked at** (selected; newly built while playing — user decision), dark orange = numerical given, light orange = derived intermediate, gray = context, dimmed = outside the chain; given points neutral dark gray. **`4014f311`** (found while inspecting this run's first sheets): context-tier objects still kept their TYPE colour for strokes, so the cross-section outline stayed amber in the causal state — the colour the legend gives to intermediates. Strokes in the context tier now use the neutral role colour (`net`, the stroke twin of `nen`) |
| W11-H5 — the LLM route could accept a length not in the problem and mark it GIVEN | The grounding gate checked program ↔ contract, never contract ↔ text: a value only the analyze output claimed could ground a GIVEN | `79eb1e59`: a GIVEN length (integer, decimal `.`/`,`, fraction, radical) needs the number in the problem text right after the segment label, with a consistent unit; P1 (`gia_tri_khong_chung_minh_duoc`) is recomputed from the text and shared by the frozen boundary, the gate and the invariant builders; three stable codes `GIVEN_VALUE_NOT_IN_SOURCE` / `SOURCE_SPAN_MISMATCH` / `SOURCE_EVIDENCE_CONFLICT`, never sent to repair; `reason_subjects` + a point- or segment-aware learner message. `8aaeae80` (found while generating the w12 negatives): a point pinned to a coordinate claim whose digits the text does not state is refused; P1's string rule compares under NFKC. `d17550c3`: `CACHE_VERSION` 105 |

No branch on family name, case ID, problem text or vertex name was added; the frontend
presents backend structured data only. The structural negatives (`_negative`, e.g.
`PLANE_DOES_NOT_CUT`) are generated and asserted by the fixture generator; the browser
negatives of this wave are the six **ungrounded** fixtures (one stated value removed from
the text while the fake analyze transport still claims it).

## Measurement

`diagnostics/MEASUREMENT_ATTEMPTS.json` lists every attempt, failures included:

1. **DRY-1** (`054bc08d` + uncommitted harness): all gates green; found the panel crop in
   viewport instead of document coordinates and a stale oracle hash (both fixed in `e115eede`).
2. **BROWSER-1** (`e115eede`): every gate green — **superseded** after reading the sheets:
   the cross-section causal state drew a context-tier outline amber, and no gate measured
   canvas stroke colours. Repaired in `4014f311`; `7b039621` adds the gate
   `CAUSAL_CANVAS_ROLE_HUE` (orange or blue pixels on the causal canvas only when a drawn
   object carries that role; HTML overlays masked). **Known-answer run** before trusting
   it: the new harness on the e115eede product fails exactly the two cross-section frames
   (326 / 1191 orange px) and passes the other ten with 0 / 0.
3. **BROWSER-2** (`7b039621`): every gate green, but the learner runner first **stalled**
   (~20 min in an orbit lap; a DevTools probe showed the page responsive — the runner
   waited for a DevTools response that never came, `ISSUE-EVAL-CDP-SEND-NO-TIMEOUT`);
   rerun under a watchdog passed. `6569ed41` corrected the sheet legend (it called built
   objects "neutral" and was cut at the right edge). **Superseded for provenance**: T3
   at its evidence commit `399fc423` failed 8 candidate-verify tests — the candidate's
   `product_commit_sha` is the last commit touching backend/app or frontend/src, and the
   renderer fix had moved it without a refreeze.
4. **BROWSER-3** (`c243968b`, after the third freeze): authoritative.

## Final verification

| Gate | Result |
|---|---|
| T3 `full-gate.mjs` from a path WITH a space (`D:/tmp/w12 space/algo-sim`, `442584cf`) | `FULL_PRODUCT_GATE_PASS` — pytest **6443 passed / 0 failed** (1 skipped, 1 deselected) · vitest 1010/1010 (67 files) · typecheck + build · demo replay 5/5 · crash surface |
| Browser suite, 6 families × desktop 1440×900 + mobile 390×844 (`c243968b`) | 12/12 positive, 12/12 ungrounded negative (refused at grounding with `GIVEN_VALUE_NOT_IN_SOURCE`, subjects SA · AD · SA · AA′ · AB · S; no canvas, no answer); geometry steps = expected, 0 static frames, 0 measurement/final-result steps, forward/backward and end lock 12/12; solution panel in sync, answer once, never over the canvas; causal tiers and row classes 12/12; role colours on panel and legend 12/12; **canvas role hues 0 orange / 0 blue on all twelve causal frames**; dashes preserved; 0 raw tokens, 0 console errors, 0 uncaught exceptions |
| Occlusion (product ↔ independent oracle) | 24/24 states; frozen expectations `DECLARED_CAMERA_CHANGE` 6/6 (registry byte-identical) |
| Learner playback (Play pressed once) | 12/12 runs × 19 checks; orbit laps 60/60 |
| Hidden-edge crops · family sheets | 64 crops, both endpoints inside, 0 oracle disagreements, 0 duplicate owners; six `images/<family>/SHEET.png` + `images/overview/INDEX.png` |
| Unit and known-answer proofs of the colour fix | context-stroke test red on the section outline, three branch injections red; hue gate reproduces the known answer |
| Candidate `--verify` · cache lock · schema export ×2 · default mode | PASS (`548f5b3b…`, product commit `4014f311`) · `CACHE_VERSION 105`, fingerprint `b1714b56…` · byte-identical, no diff · `LLM_ONLY`, compiler not wired |
| Section regression · `git diff --check` · node tests (harness) | 50 passed (`PLANE_DOES_NOT_CUT` asserted) · clean outside verbatim logs · 38/38 |

Numbers: `results/VERIFICATION_SUMMARY.json` (generated from the evidence files);
backend count 6411 → 6443 per file in `results/BACKEND_COUNT_RECONCILIATION.json`.

## Limitations (not hidden)

- **No human has approved** the new sheets, panels, refusals or films.
- **Type colours in neutral and playback views.** Role colours apply when the causal
  legend is shown. Outside it, built objects keep their type colours: the section
  polygon is amber (`#f59e0b`) and tints each base faintly amber, planes are violet,
  lines teal, derived points red. The sheet legend says so. Please judge whether amber
  for the section still reads as "intermediate quantity" next to the causal legend.
- In these six families every causal target is a number, so the canvas shows only
  neutral context and dimming in the causal state; the target's colour is on its panel
  row. A drawn object selected on the canvas turns blue.
- Residual `ISSUE-ARCH-ASSUMPTION-CHANNEL-UNSTATED-DIMENSION`: a layout or
  `model_assumption` coordinate can still fix a dimension the text does not state (it is
  never labelled GIVEN) — `diagnostics/logs/ASSUMPTION_CHANNEL_PROBE_79eb1e59.log`.
- New `ISSUE-EVAL-CDP-SEND-NO-TIMEOUT`: a lost DevTools response stalls a browser run
  instead of failing it (watchdog used here).
- `ISSUE-OPS-DIST-ACL-OWNERSHIP` and `ISSUE-OPS-OFFLINE-SAMPLES-STALE` remain open.
- Lines are still 1 physical px (WebGL ignores `linewidth`).
- Deviations from the planned commit sequence: a separate cache commit; a second backend
  fix with a second freeze; a frontend fix after the first measurement with a harness
  gate, a legend fix and a third freeze; three measurement rounds. All are listed above.
- Temporary worktrees: all eight removed (`diagnostics/WORKTREE_CLEANUP.json`); empty or
  older unregistered directories under `D:/tmp` are marked `SAFE_TO_DELETE`, not deleted.

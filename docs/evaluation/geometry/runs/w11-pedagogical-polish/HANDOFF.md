# Handoff — w11 pedagogical formula + visual polish

## For the human reviewer

Open, in this order:

1. `images/overview/INDEX.png` — index only: one thumbnail per family, each pointing
   at its sheet.
2. `images/<family>/SHEET.png` — the acceptance sheet of one family, full
   resolution: desktop neutral · causal · rotated, mobile neutral, then EVERY
   formation step with its caption, and the legend (orange = new or under
   consideration · neutral = constructed · dashed = hidden). The six families:
   `triangular-pyramid`, `triangular-prism`, `rectangular-pyramid`, `cuboid`,
   `cube`, `cross-section`.
3. The w10 findings, where to look:
   - W10-H1/H2/H3 — the causal state of `triangular-pyramid` and `triangular-prism`:
     the formula card reads `V = 1/3 × S(ABC) × SA = 10` / `V = S(ABC) × AD = 30`, and
     "Dựa trên" names S(ABC) and the height (sources:
     `images/<family>/desktop/causal_selected.png`, `…/playback/<viewport>/`).
   - W10-H4 — the rotated state of every family (`rotated_neutral`), chosen by the
     planned gesture that passed the perspective gate.
   - W10-H5 — vertex markers: 6 px desktop, 7.5 px mobile, 9 px selected.
   - W10-H6 — causal tiers after selecting the answer: in the readout row the target
     has a blue outline, numerical givens a dark-orange bar, numerical intermediates a
     light-orange bar, everything else is dimmed; in the canvas the solid, base and
     points are structural context (neutral ink, light fill) and dashes are kept.
     In all six families every numerical tier is a readout, so the canvas shows no
     tier colour of its own. A drawn object selected in the canvas turns dark orange,
     the colour a GIVEN has in the readout; the two never appear in the same state,
     but please say whether that reads as one colour code.
   - W10-H7 — `cross-section`: BD is light in the final state and prominent at its
     construction step.
   - W10-H8 — the formation strip of each sheet.
4. `images/<family>/hidden-edges/<viewport>/` — every hidden edge with BOTH
   endpoints; metadata in `results/HIDDEN_EDGE_CROPS.json`.
5. `images/<family>/playback/<viewport>/` — what a learner sees after pressing Play
   once, then `neutral_final`, `rotated_neutral`, `causal_selected`,
   `neutral_restored`.

Questions only a person can answer: does each formula read as the textbook formula
with the right height; are the causal tiers distinguishable at both sizes; are the
markers and the dimmed BD right; does every rotated view read as a solid.

## Required fields

```text
TASK = W11_PEDAGOGICAL_FORMULA_VISUAL_POLISH_AND_HUMAN_REREVIEW
BASE_HEAD = b9193766
END_HEAD = SELF_EXCLUDED_RESOLVE_FROM_GIT (docs commit after the evidence commit)
HUMAN_VISUAL_REVIEW_W10 = FAIL_REQUIRES_TARGETED_PEDAGOGICAL_REPAIR (inputs/W10_HUMAN_VISUAL_REVIEW.json; w10 byte-identical)
MEASUREMENT_COMMIT = 39e54046 (suite, oracle, playback, evidence builder)
FORMULA_PROVENANCE = PASS — base area + height in the numerical closure and the formula for all five volume families; cross-section volume stays structural; missing height never compiles; ambiguous height ⇒ no formula
VERTEX_MARKER_RESULT = PASS — measured through the camera matrix: 6.00 px desktop, 7.50 px mobile (12/12); selected 9 px (token; pick-target.test.ts pins 8–10 px, not measured in the browser); one token DAU_DINH_PX
ROTATED_EVIDENCE_RESULT = PASS — perspective-screen gate 12/12, planned gesture passed first time 12/12, predicted = actual view matrix within 1e-6
CAUSAL_TIERS_RESULT = PASS — observed tiers = independently computed tiers 12/12, readout classes match 12/12, dashes preserved
CROSS_SECTION_LINE_RESULT = PASS — BD at 0.45 opacity when not emphasised, orange at its construction step; "Xem lại toàn hình" ignores its rendered span (60292ecf)
FORMATION_RESULT = PASS — 12/12; measurement steps keep geometry 12/12; every step on the family sheet with its caption and the legend
EVIDENCE_LAYOUT = per-family sheets + overview index; diagnostics outside the sheets
OCCLUSION_RESULT = PASS — product = oracle 24/24; frozen expectations DECLARED_CAMERA_CHANGE 6/6
PLAYBACK_RESULT = PASS — 12/12 runs × 18 checks; orbit laps 60/60
FULL_BACKEND_RESULT = 6411 passed / 0 failed (1 skipped, 1 deselected) — T3 FULL_PRODUCT_GATE_PASS at 5e3dbab4 from `D:/tmp/w11 space/algo-sim`; log diagnostics/logs/T3_FULL_GATE_SPACED_5e3dbab4.log, sha256 6f7c18fd61da093f78d35c41ecb3f8b552b94fd0b1bebe7e4e35bd4655236045
BACKEND_COUNT_RECONCILIATION = 6368 = T3 @ 40ce889f; 6370 = 6368 + 2 tests added by 52de6f22 (b9193766); 6411 = 6370 + 41 tests of w11 (results/BACKEND_COUNT_RECONCILIATION.json)
FRONTEND_RESULT = vitest 958/958 · typecheck + build PASS (inside T3) · node tests 29/29
CACHE_VERSION = 103 -> 104 once (f147dde6); provider fingerprint b1714b566e25c912 unchanged
CANDIDATE = 8539acbc… -> df04a613…, refrozen once (a39028de, clean worktree at 7efdae4a, product commit 60292ecf)
CANDIDATE_VERIFY = PASS (df04a613…, 103 files)
CACHE_VERIFY = PASS (CACHE_VERSION 104, fingerprint unchanged)
SCHEMA_SYNC = PASS (export twice, byte-identical, no diff)
NEW_OPEN_ISSUES = ISSUE-ARCH-LLM-ROUTE-LENGTH-NOT-TEXT-GROUNDED · ISSUE-OPS-OFFLINE-SAMPLES-STALE · ISSUE-OPS-DIST-ACL-OWNERSHIP
LIVE_GEMINI_REQUESTS = 0
PUSH_EXECUTED = NO
MERGE_EXECUTED = NO
USER_FAVICON_DELETION_PRESERVED = YES
HUMAN_VISUAL_REVIEW = NOT_APPROVED (pending)
FINAL_DECISION = READY_FOR_HUMAN_VISUAL_REVIEW
NEXT_ACTION = HUMAN_VISUAL_REREVIEW_OF_PEDAGOGICAL_POLISH_EVIDENCE
```

## If the reviewer rejects again

Record the verdict additively in a new run's `inputs/` (as
`inputs/W10_HUMAN_VISUAL_REVIEW.json` does here); do not edit this run.

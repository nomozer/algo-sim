# Handoff — w10 pedagogical playback

## For the human reviewer

Open, in this order:

1. `images/contact-sheet.png` — one row per family: desktop neutral · causal ·
   rotated, mobile neutral (cropped to the stage, large cells).
2. `images/crops/<family>/<viewport>/<state>__<edge>__hidden.png` — every hidden
   edge with BOTH endpoints; metadata per crop in `images/crops/CROPS_INDEX.json`
   (expected / observed / oracle visibility, owner count, dash signature).
   The edges the w09 review named: rectangular pyramid AB, AD, SA · triangular
   pyramid AB, AC, SA · prism AB, AC, AD · cuboid/cube AA′, AB, AD ·
   cross-section AB, AD, SA.
3. `images/playback/filmstrip/<family>/<viewport>/step-NN.png` — what a learner
   sees after pressing Play once, then `neutral_final`, `rotated_neutral`,
   `causal_selected`, `neutral_restored` in the same folder.
4. `images/contact-sheet-appendix-formation.png` — every formation step.
5. Full-resolution screenshots: `images/screenshots/<family>/<viewport>/`.

Questions only a person can answer: is the default view readable as a textbook
figure; are dashes legible over the fills at both sizes; does the causal colouring
read as target → intermediates → givens; does "Kết luận …" read once and correctly.

## Required fields

```text
TASK = HUMAN_VISUAL_REVIEW_AND_PEDAGOGICAL_PLAYBACK_CLOSURE
START_HEAD = be23e88d
END_HEAD = SELF_EXCLUDED_RESOLVE_FROM_GIT (docs commit after the evidence commit)
MEASUREMENT_COMMIT = 40ce889f · EVIDENCE_POST_PROCESSING = 52de6f22
PLAYBACK_CAUSAL_AUTO_TRIGGER = NO (no_causal_selection 12/12; w09 causal colour = EXPECTED_HARNESS_ACTION)
FINAL_STEP_STOPS_PLAYBACK = YES (stops_at_final_step 12/12)
REPLAY_CLEARS_SELECTION = YES (replay_resets_step_selection_highlight 12/12)
ORBIT_PRESERVES_TIMELINE = YES (orbit_preserves_timeline 12/12)
SIX_FAMILY_CAMERA_RESULT = PASS — default view meets thresholds 12/12, rotated view keeps depth 12/12, fill 55–80 % in unit tests at both canvases
HIDDEN_EDGE_LEGIBILITY = AUTOMATION_PASS — 60 crops with both endpoints, oracle disagreements 0; human legibility PENDING
DUPLICATE_VISUAL_OWNER_COUNT = 0
LEARNER_SURFACE_RESULT = PASS — no machine IDs/generic text, solids named by kind, answer shown once, 6 families (pytest test_scene3d_learner_surface.py)
SPACE_PATH_RESULT = PASS — T3 FULL_PRODUCT_GATE_PASS from `D:/tmp/w10 space/algo-sim` (ISSUE-OPS-FRONTEND-TESTS-SPACE-PATH resolved)
ORBIT_REPEATABILITY_RESULT = PASS — 60/60 laps (5 per family × viewport), suite planned gesture first-time 12/12
FULL_BACKEND_RESULT = 6368 passed / 0 failed (1 skipped, 1 deselected) inside T3
FRONTEND_RESULT = vitest 946/946 · typecheck + build PASS · node tests 29/29
CANDIDATE_VERIFY = PASS (8539acbc…, 103 files)
CACHE_VERIFY = PASS (CACHE_VERSION 103, fingerprint b1714b566e25c912 unchanged)
SCHEMA_SYNC = PASS (export twice, byte-identical)
LIVE_GEMINI_REQUESTS = 0
PUSH_EXECUTED = NO
MERGE_EXECUTED = NO
USER_FAVICON_DELETION_PRESERVED = YES
HUMAN_VISUAL_REVIEW = NOT_APPROVED (pending)
FINAL_DECISION = READY_FOR_HUMAN_VISUAL_REVIEW
NEXT_ACTION = HUMAN_VISUAL_REVIEW_OF_PEDAGOGICAL_PLAYBACK_EVIDENCE
```

## If the reviewer rejects again

Record the verdict additively in a new run's `inputs/` (as
`inputs/W09_HUMAN_VISUAL_REVIEW.json` does here); do not edit this run.

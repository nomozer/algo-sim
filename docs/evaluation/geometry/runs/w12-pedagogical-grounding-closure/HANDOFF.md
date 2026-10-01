# Handoff — w12 pedagogical timeline + source grounding closure

## For the human reviewer

Open, in this order:

1. `images/overview/INDEX.png` — index only: one thumbnail per family, each pointing
   at its sheet.
2. `images/<family>/SHEET.png` — the acceptance sheet of one family, full resolution.
   The two-line legend at the top: blue = being looked at (newly built while playing, or
   selected); built objects keep their type colours (solid gray, plane violet, section
   amber, lines teal, derived points red); dashed = hidden. Causal (after clicking a row
   of the solution panel): blue = target · dark orange = numerical given · light orange
   = derived intermediate · gray = every shape in the chain · dimmed = outside it.
   Cells: desktop neutral · causal · rotated, mobile neutral; the solution panel at the
   last step, with the answer selected, on mobile collapsed and expanded; the refusal of
   a problem with one value removed (desktop, mobile); then EVERY geometry step with
   its caption ("Bước dựng i/n — …"). Families: `triangular-pyramid`,
   `triangular-prism`, `rectangular-pyramid`, `cuboid`, `cube`, `cross-section`.
3. The w11 findings, where to look:
   - W11-H1/H2 — the geometry-step cells of each sheet: 3 · 3 · 5 · 5 · 5 · 10 steps;
     each changes the figure; no step only computes a number or states the result.
   - W11-H3 — the solution-panel cells: Kết quả (the answer once, with formula and
     "Dựa trên"), Dữ kiện and Các bước tính, in sync with the geometry step.
   - W11-H4 — the causal cell: the selected row is blue in the panel, the shapes of the
     chain are neutral gray on the canvas (the cross-section outline is no longer amber
     there), dashes kept; the playback cells: the newly built object is blue.
   - W11-H5 — the refusal cells: the problem text without the removed value, the
     message naming what is missing ("độ dài AD", "toạ độ điểm S"), no 3D scene, no
     answer.
4. `images/<family>/hidden-edges/<viewport>/` — every hidden edge with both endpoints;
   metadata in `results/HIDDEN_EDGE_CROPS.json`.
5. `images/<family>/playback/<viewport>/` — what a learner sees after pressing Play
   once, then `neutral_final`, `rotated_neutral`, `causal_selected`, `neutral_restored`.
6. Before/after of the context colour fix: `diagnostics/attempt-e115eede/` (the amber
   section outline in the causal state that this run's first sheets showed).

Questions only a person can answer: does each step read as one construction step; is
the panel the right secondary layer at both sizes; does one colour now mean one thing
— in particular, does the **amber section in the neutral views** still read as
"intermediate quantity" next to the causal legend; are the refusal messages clear.

## Required fields

```text
TASK = W12_PEDAGOGICAL_TIMELINE_AND_SOURCE_GROUNDING_CLOSURE
START_HEAD = a4fd5fec
END_HEAD = SELF_EXCLUDED_RESOLVE_FROM_GIT (the docs commit that adds this file)
CURRENT_BRANCH = fix/cuboid-visual-semantic-closure
ORIGIN_MAIN = a9492ee98ff9dc3302d1ff64465f1c06e9001bce (local ref, ancestor of HEAD; not re-fetched)
PRODUCT_COMMIT_SHA = 4014f311e1df7082eecbf090d7e62c96217e0ec9 (last commit touching backend/app or frontend/src)
MEASUREMENT_COMMIT_SHA = c243968b1ec263d2ab48040d569eec45efe9cfaa (suite, oracle, playback, evidence builder; detached clean worktree)
EVIDENCE_COMMIT_SHA = 442584cfbbd0fa82674c42c43550429732d3e2c7 (also the T3 commit)
FINAL_DOCS_COMMIT_SHA = SELF_EXCLUDED_RESOLVE_FROM_GIT
HUMAN_REVIEW_INPUT_VERDICT = NEEDS_CHANGES (W11-H1…H5; inputs/W11_HUMAN_VISUAL_REVIEW.json; w11 byte-identical)
SOURCE_GROUNDING_RESULT = CLOSED for GIVEN — lengths (integer, decimal . or ,, fraction, radical) and P1-only atoms need the problem text; coordinate claims with unstated digits refused; never sent to repair (79eb1e59, 8aaeae80). Residual, not GIVEN: ISSUE-ARCH-ASSUMPTION-CHANNEL-UNSTATED-DIMENSION
UNGROUNDED_LENGTH_PROBE = REFUSED — prism text without "Cạnh bên AD = 5", fake analyze still claims 5: unsupported · input_not_grounded · GIVEN_VALUE_NOT_IN_SOURCE · subject AD; same for all six families in the browser (subjects SA · AD · SA · AA′ · AB · S), no canvas, no answer
GROUNDING_ERROR_CODE = GIVEN_VALUE_NOT_IN_SOURCE (closed set: GIVEN_VALUE_NOT_IN_SOURCE · SOURCE_SPAN_MISMATCH · SOURCE_EVIDENCE_CONFLICT)
GEOMETRY_TIMELINE_RESULT = PASS — geometry steps = independently expected 12/12 (3 · 3 · 5 · 5 · 5 · 10); every step changes the figure; Play stops at the last geometry step
STATIC_MEASUREMENT_FRAME_COUNT = 0
FINAL_RESULT_GEOMETRY_STEP_COUNT = 0
FORWARD_BACKWARD_RESULT = PASS — forward and backward seeking restore every step 12/12; end locked 12/12
SOLUTION_LAYER_RESULT = PASS — Kết quả · Dữ kiện · Các bước tính in sync with the geometry step 12/12; answer exactly once 12/12; panel never over the canvas
FORMULA_PROVENANCE_RESULT = PASS — formula references resolve 12/12; 5/5 volume families show base area × height with "Dựa trên" in formula order (V = 1/3 × S(ABC) × SA = 10, S(ABC) × AD = 30, 1/3 × S(ABCD) × SA = 24, S(ABCD) × AA′ = 60 / 64)
CAUSAL_COLOR_RESULT = PASS — one role table for canvas and panel; tiers = independently computed 12/12; panel row and legend colours = tokens 12/12; causal canvas role hues 0 orange / 0 blue 12/12 (gate CAUSAL_CANVAS_ROLE_HUE, known answer reproduced); the context outline fix 4014f311. Reviewer question: amber stays the section's TYPE colour in neutral views
HIDDEN_LINE_REGRESSION = NONE — product = oracle 24/24, frozen expectations DECLARED_CAMERA_CHANGE 6/6, dash signature preserved 12/12, 64 crops with 0 oracle disagreements and 0 duplicate owners
SIX_FAMILY_BROWSER_RESULT = PASS — 12/12 positive, 12/12 negative
DESKTOP_RESULT = PASS — 6/6 positive, 6/6 negative (1440×900, DPR 1)
MOBILE_RESULT = PASS — 6/6 positive, 6/6 negative (390×844, DPR 2)
NEGATIVE_PATH_RESULT = PASS — structured refusal, learner message, no canvas, no answer, no overflow 12/12
RAW_TOKEN_LEAKAGE = 0
CONSOLE_ERRORS = 0
UNCAUGHT_EXCEPTIONS = 0
FULL_BACKEND_RESULT = 6443 passed / 0 failed (1 skipped, 1 deselected) — T3 FULL_PRODUCT_GATE_PASS at 442584cf from `D:/tmp/w12 space/algo-sim`; 6411 → 6443 reconciled per file (results/BACKEND_COUNT_RECONCILIATION.json)
FULL_BACKEND_EXIT_CODE = 0
FRONTEND_TEST_RESULT = vitest 1010/1010 (67 files)
FRONTEND_TYPECHECK = PASS (tsc -b inside T3)
FRONTEND_BUILD_RESULT = PASS (vite build inside T3)
NODE_HARNESS_RESULT = 38/38 (main tree; the T3 worktree skips 2 interpreter tests that need a repo-local venv)
SCHEMA_SYNC = PASS (export twice, byte-identical, no diff)
CANDIDATE_OLD_HASH = df04a613db9c5dd0d97cf3a21e14e01f101ba08ba22373443b95cdd361514650
CANDIDATE_NEW_HASH = 548f5b3b9ff891587fccb61cc59981362543a8f60f7f9917b7c241098bbb096f
CANDIDATE_REFROZEN = YES — three times (b9c60010 at d17550c3 → intermediate 8ffd6d46; 054bc08d at 8aaeae80 → 548f5b3b with product commit 8aaeae80, intermediate identity; c243968b at 4014f311 → 548f5b3b with product commit 4014f311); declared in inputs/CANDIDATE_DIVERGENCE_CORRECTION.json
CACHE_VERSION_BEFORE = 104
CACHE_VERSION_AFTER = 105
CACHE_FINGERPRINT_CHANGED = NO (b1714b566e25c912)
DEFAULT_MODE = LLM_ONLY
LIVE_GEMINI_REQUESTS = 0
TEMP_WORKTREES_FOUND = 8 (2 left by w11, 6 created by w12)
TEMP_WORKTREES_REMOVED = 8 (diagnostics/WORKTREE_CLEANUP.json)
UNIQUE_ARTIFACTS_AT_RISK = 0
LIVING_DOCS_UPDATED = README.md · docs/README.md · AI_CONTEXT_BUNDLE · CURRENT_STATE · CODE_INDEX · ARCHITECTURE_MAP (#35, #36) · CORRECTNESS · ROADMAP §0 · OPEN_ISSUES · STATUS_LEDGER · EVIDENCE_INDEX · THESIS_READINESS · audit_docs_information_architecture.py (allowed actions)
HISTORICAL_ARTIFACTS_BYTE_IDENTICAL = YES (w11, w10, w09 and the occlusion-wave runs: 0 files changed since a4fd5fec)
COMMITS_CREATED = 17 (a4fd5fec..END_HEAD; RUN.json lists the first 16, the 17th is the docs commit)
PUSH_EXECUTED = NO
MERGE_EXECUTED = NO
HISTORY_REWRITTEN = NO
USER_FAVICON_DELETION_PRESERVED = YES
HUMAN_VISUAL_REVIEW = NOT_APPROVED (pending)
FINAL_DECISION = READY_FOR_HUMAN_VISUAL_REVIEW
NEXT_ACTION = HUMAN_VISUAL_REREVIEW_OF_GEOMETRY_TIMELINE_EVIDENCE
```

## If the reviewer rejects again

Record the verdict additively in a new run's `inputs/` (as
`inputs/W11_HUMAN_VISUAL_REVIEW.json` does here); do not edit this run.

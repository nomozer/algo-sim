# Handoff — w16 pre-merge soundness and visual evidence closure

## For the human reviewer

Open, in this order:

1. **`images/cross-section/desktop/neutral_final.png`** and
   **`images/cross-section/mobile/neutral_final.png`**. They show the closed section fill
   with the solid edges drawn over it. S-A (dashed, hidden) and S-C (solid) cross the amber
   region. Compare them with w15's
   `../w15-assumption-closure/images/cross-section/desktop/neutral_final.png`, where the fill
   was drawn after the lines and tinted both edges brown. Are the edges and the fill both
   clear enough now?
2. **`images/cross-section/FILMSTRIP.png`**. The fill appears only at the closing step and
   disappears on rewind. The order changed (W16) but the timing did not.
3. **`images/<family>/SHEET.png`**, one per family. The refusal rows now carry all six panels:
   *dữ kiện không có trong đề*, *đáp số phụ thuộc kích thước đề không cho* and *bảng mặt /
   hình học không dựng được*, each on desktop and mobile. Each panel is the family's own
   `negative/<kind>/<viewport>/refusal.png`. The white band under a desktop panel is the row
   height of the taller mobile capture, not a missing image. Is every refusal message
   readable?
4. **The four scenes W14 changed** (U2 of w15, still pending a person): triangular pyramid,
   triangular prism, rectangular pyramid and cross-section. Their hidden edges are in
   `images/<family>/hidden-edges/desktop/`. The product equals the independent oracle on
   every state, but a person must still confirm them.
5. `images/<family>/playback/` and `FILMSTRIP.png` cover the rest, as in w15.

## Decisions that are yours

| Id | Question | What follows |
|---|---|---|
| W16-H1 | Approve the four W14-changed scenes (carries W15-H1), the section fill under the edges, and the completed refusal panels? | A person records it in a new human-registry layer; automation never writes `APPROVED_BY_USER`. |
| W15-H2 | Extend enforcement beyond the polyhedral vocabulary (U3)? | Unchanged by W16. It is also what would close `ISSUE-ARCH-GROUNDING-GOAL-CLAUSE-AS-DATUM` outside the polyhedral scope. |
| W15-H3 | Widen the closed vocabulary? | Unchanged by W16. A reader for construction relations (`(X) cắt … theo thiết diện (T)`, `M là trung điểm của XY`) belongs here; it is what closes limit A′. |

## Required fields

```text
TASK = W16_PREMERGE_SOUNDNESS_AND_VISUAL_EVIDENCE_CLOSURE
CURRENT_BRANCH = fix/cuboid-visual-semantic-closure
START_HEAD = 8a339d17e9780d4a9df0cb838f11cc26a355e80f
END_HEAD = SELF (the documentation commit that adds this file; resolve with git log -1)
BASE = origin/main a9492ee98ff9dc3302d1ff64465f1c06e9001bce (git fetch --prune origin at Phase 0: equals ls-remote, ancestor of HEAD, ahead 162 / behind 0)
SKILLS_INVOKED_IN_W16 = superpowers:writing-plans (2026-10-03T09:56Z, the W16 plan) · ponytail:ponytail-review (12:20Z, after the evidence; 5 findings, none applied)
SKILLS_APPLIED_FROM_AN_EARLIER_INVOCATION = invoked earlier in this same session and not re-invoked after the W16 brief; their loaded instructions governed the work: superpowers:executing-plans (2026-10-01; inline, ledger, rulings) · superpowers:test-driven-development (2026-09-28; red first for every product change, including the post-freeze fix) · superpowers:systematic-debugging (2026-09-28; browser attempt 1, the page-code redeclaration) · superpowers:verification-before-completion (2026-09-28; every claim here comes from a log of this wave) · andrej-karpathy-skills:karpathy-guidelines (2026-09-28; simplest rule at the right boundary, surgical fixes)
SKILLS_APPLIED_MANUALLY = code-reviewer.md of superpowers:requesting-code-review (read at 11:37Z), performed by the author as the pre-evidence self-review (no subagent)
SKILLS_NOT_USED_WITH_REASON = subagent-driven-development and a fresh-context reviewer (the brief forbids subagents) · brainstorming (scope came from the brief)
PHASE1_PROBES = 34 rows at the RED commit 6d015112 (+2 W16B at 2dc55f1b): plane binding 5 exploitable and served (A1, A2, A6, A6b, A8; A2 showed 9 where the text gives 16), A7 certified but refused by the postcondition, A9 (primed alias) certified at 2dc55f1b; goal clauses 7 exploitable and served (B1, B1b, B2, B3b, B3c, B5, B7), B3/B4 not exploitable, B6b over-refused; guards 4/4 fire from valid specs
PLANE_ENTITY_BINDING = 24161657 + 6b120036: a plane literal is SOURCE_DATUM only for the text plane it binds to, by name (closed Greek table, capitals, prime part of the name) or as unique by counting, with proportional coefficients; equal numbers never bind. 7/7 wrong-entity programs refused, 9/9 valid bindings C0, gold p1/p6/p7 C0. Declared limit A′ (A2b) served
PREMISE_GOAL_SEPARATION = 93d4ec69: goal clauses (chứng minh, chứng tỏ, CMR, kiểm tra, hỏi, clauses ending in ?) masked before every premise reader (NFC cluster map); a goal constraint still blocks the counterexample; 7/7 goal-as-premise programs refused, 4/4 hypothesis rows stay C1
GUARDS = CLOSURE_UNSUPPORTED_KIND (no-op if) · TEMPLATE_CONSTRAINT_VIOLATED (apex moved off the normal) · FRAME_DEPENDENT (an equation plane on a C1 slice, the only failure) · FORMATION_REJECTED (two-vertex face): each UNDETERMINED with ASSUMPTION_INVARIANCE_UNPROVEN and a valid C1 counterpart; FG1–FG4 caught
GOLD_18 = 18/18 PROVEN_SAFE (8 C0, 10 C1) and served; unchanged from W15
CENSUS = round 2 at 7695b967: SHIP; 147 rows (W14 48, W15 49, W15B 14, W16 + W16B 36); 0 status changes on W14/W15/W15B against W15 round 3 and against round 1; W16 rows as labelled except the declared limit A2b; 0 valid cases newly refused (B6b and two guard triggers were refused before W16 too); compiler cross-check 32 / 5 / 0
FAULT_INJECTIONS = backend 13/13 at 7695b967 (FG1–4, FA1–4, FB1–3, FD1–2; baseline 380 passed, 1 xfailed) · frontend 4/4 at cd3a0efa (FL1, FH1–3; attempt 1 FH1 STALE on a CRLF checkout kept apart)
STRICT_XFAIL_REMAINING = 1 (limit A′, ISSUE-ARCH-ASSUMPTION-CONSTRUCTION-RELATION-NOT-SOURCE-BOUND)
SECTION_FILL_EDGE_VISIBILITY = confirmed defect (W15 fill drawn after the lines tinted S-A/S-C); fix: fill renderOrder 7 (after surfaces, before transparent lines). SECTION_FILL_UNDER_EDGES PASS (rho 0.138/0 desktop, 0.485/0.274 mobile < 1; edge contrast 35.5–66.8 ≥ 12); SECTION_FILL_DISTINGUISHABLE PASS 34.20/34.11 desktop, 34.19/33.74 mobile vs 20/12; pre-close and rewound 0 vs 3; W15 thresholds unchanged
NEGATIVE_SHEET_COMPLETENESS = 6 sheets × 6 refusal panels (three kinds × desktop/mobile); root cause: the builder read the W12 shape negative[viewport] while the suite records negative[kind][viewport] since W15 (W15 sheets: blank cells); a missing, wrong, blank or unreadable panel now raises ThieuAnhBangChung; source images were correct
HIDDEN_LINES = occlusion pass, HUMAN_REVIEW_PENDING (the four W14-changed scenes, U2); 64 crops, 0 oracle disagreements, 0 duplicate owners
HUMAN_REVIEW = NOT_APPROVED
TESTS = T3 frontend/scripts/full-gate.mjs from 'D:/tmp/w16 space/algo-sim' at 7f3658b0: exit 0, FULL_PRODUCT_GATE_PASS — pytest 6854 passed / 0 failed / 1 skipped / 2 deselected / 1 xfailed (A′); vitest 1018/1018 (67 files); typecheck + build; demo 5/5 + reduced 1/1; crash surface 6/6 · browser suite exit 0 (12/12 positive, 36/36 negative) · occlusion exit 0 · playback exit 0 (12/12 × 19/19) · builder exit 0 · gates exit 0 (diagnostics/logs/*_7f3658b0.log) · node harness 59 + 2 skipped by design, 0 fail · census round 2 and fault injections exit 0
PRODUCT_COMMITS = 24161657 93d4ec69 29da8e5a 2ec02b3a 6b120036 (+ 6d015112, red tests incl. a frontend/src test file)
PRODUCT_COMMIT_SHA = 6b1200364f83b62fe6ea07d09009638b159e6b25
MEASUREMENT_COMMIT_SHA = 7f3658b00f48dae854e5ab2527ca0ff3f701f828
EVIDENCE_COMMIT_SHA = 705970dd83f267a17da87e5f18906eee829ad955
FINAL_DOCS_COMMIT_SHA = SELF
CANDIDATE_OLD_HASH = b3b7eb79d3c64a2f076ae1dc815abb2273364e2c0374660682be66dbbb0ec60c
CANDIDATE_NEW_HASH = 9bb0aaa7bddecf945f3d0c89632d1c46f3d7be350b350ded96dc0c598b733476
CANDIDATE_INTERMEDIATE_HASH = 8d14469bacee7928bbc407f201ea0e3879cccc26102f404e2382375177396044
CANDIDATE_REFROZEN_COUNT = 2 (2ec02b3a; 6b120036 after the primed-name fix found by the pre-evidence self-review)
CACHE_VERSION_BEFORE = 107
CACHE_VERSION_AFTER = 108 (2ec02b3a: twelve requests served before W16 are refused and would HIT as v107 rows — served → rejected; not bumped again for 6b120036: 108 unreleased, the fix only refuses more)
CACHE_FINGERPRINT_CHANGED = NO (b1714b566e25c912)
SCHEMA_SYNC = PASS (both mirrors d852b47c08b7ac0e2a41155366ac1ff88e7d08875cb1cfe718326c543b2951e7, exported twice, no diff)
MODEL_SURFACE_CHANGED = NO (0 files since 8a339d17)
DEFAULT_MODE = LLM_ONLY
LIVING_DOC_IMPACT = README · docs/README · AI_CONTEXT_BUNDLE · CURRENT_STATE · CODE_INDEX (W16 section; plane-name reader incl. primes) · ARCHITECTURE_MAP (§2e W16, fill order, invariant #37) · CORRECTNESS (what "same entity" and "premise" now mean) · OPEN_ISSUES (two resolved, three opened, one annotated) · ROADMAP §0 · STATUS_LEDGER · EVIDENCE_INDEX · THESIS_READINESS · ASSUMPTION_CERTIFICATE_AMENDMENT §14.1 dated correction · docs-audit allowed actions
TEMP_FILE_INVENTORY = diagnostics/TEMP_FILE_INVENTORY.json: 28 entries (USED 9, RESEARCH_EVIDENCE 9, SUPERSEDED_DIAGNOSTIC 3, REPRODUCIBLE_TEMP 7, UNKNOWN 0); 1 verified duplicate deleted by exact path; 7 worktrees + 5 temp folders/files removed (diagnostics/WORKTREE_CLEANUP.json)
LIVE_GEMINI_REQUESTS = 0
PUSH_EXECUTED = NO
MERGE_EXECUTED = NO
HISTORY_REWRITTEN = NO
USER_FAVICON_DELETION_PRESERVED = YES
FINAL_DECISION = READY_FOR_HUMAN_VISUAL_REVIEW
NEXT_ACTION = HUMAN_VISUAL_REVIEW_OF_PREMERGE_CLOSURE_EVIDENCE
```

## Known leftovers

- **Deferred minors:**
  - a named text equation written twice gives "several text equations", an over-refusal;
  - five behaviour-neutral ponytail findings (`diagnostics/PONYTAIL_REVIEW.json`).
- **Not touched:** directories that earlier waves left in `D:/tmp`. Every w16 worktree and
  temporary folder is removed.

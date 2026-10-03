# Handoff — w15 source-constraint and assumption closure

## For the human reviewer

Open, in this order:

1. **`images/cross-section/FILMSTRIP.png`** shows the closed section fill (the user's own
   request). The section edges are built step by step, and the amber fill appears only at the
   closing step, *"khép thiết diện — Thiết diện khép lại thành tứ giác"*. Then open
   `images/cross-section/desktop/neutral_final.png` and the matching mobile frame to see the
   fill against the violet cutting plane and the grey solid. Compare them with
   `diagnostics/browser-attempt1-c1638891/`, which shows the same scene before the fix: an
   outline with no fill. The fill is drawn after the lines, so it tints any solid edge that
   crosses the section region on screen. Is that acceptable?
2. **The four scenes W14 changed** (U2, still pending a person): the triangular pyramid,
   triangular prism, rectangular pyramid and cross-section. Their hidden edges are in
   `images/<family>/hidden-edges/desktop/`. The independent oracle reproduces the reviewed
   visible/hidden sets at the registered and at the new camera, and the product equals the
   oracle on every state. A person must still confirm them.
3. **`images/<family>/negative/assumption/`** shows the refusal a learner sees when the text
   omits a dimension the answer depends on. The message names the missing quantity, for
   example *"Đề bài chưa cho độ dài AA′, mà đáp số lại phụ thuộc vào số liệu này…"*.
4. `images/<family>/SHEET.png` and `playback/` cover the rest of the acceptance sheet, as in
   w14.

## Decisions that are yours

| Id | Question | What follows |
|---|---|---|
| W15-H1 | Approve the four W14-changed scenes and the new section fill? | Approval is recorded by a person in a new human-registry layer; automation never writes `APPROVED_BY_USER`. |
| W15-H2 | Extend enforcement beyond the polyhedral vocabulary (U3)? | Today a non-polyhedral text keeps the pre-W15 behaviour, with the gate recording only. Enforcing everywhere refuses about 170 currently served, text-determined cases outside C0/C1 (U3 experiment). The way forward is more certificate coverage, not a wider refusal. |
| W15-H3 | Widen the vocabulary (angles, `SA = AB`, `vuông cân`, radical lengths, `thuộc cạnh` ratios)? | Each phrase needs a reader rule and a registered certificate rule. Until then, these determined problems are refused inside the polyhedral scope (fail-closed). |

## Required fields

```text
TASK = W15_SOURCE_CONSTRAINT_AND_ASSUMPTION_CLOSURE
CURRENT_BRANCH = fix/cuboid-visual-semantic-closure
START_HEAD = 4f6a0ab60b964da83b978c8b617e776c318fc7b8
END_HEAD = SELF (the documentation commit that adds this file; resolve with git log -1)
BASE = origin/main a9492ee98ff9dc3302d1ff64465f1c06e9001bce (git fetch --prune origin at Phase 0: unchanged, equals ls-remote, ancestor of HEAD)
SKILLS_USED = writing-plans (plan) · executing-plans (inline, with a ledger and rulings) · systematic-debugging (Track B root causes; the U3 wiring reds; BROWSER-1's section-fill failure) · test-driven-development (red first for every product change, including the two post-freeze fixes) · verification-before-completion (Tasks 9–11) · ponytail:ponytail-review (Task 9) · karpathy-guidelines (applied manually: simplest gate rules, surgical fixes)
SKILLS_SKIPPED_WITH_REASON = subagent-driven-development and a fresh-context reviewer (the brief allows no unrequested subagents; the final whole-branch review is a self-review by the author) · brainstorming (scope came from the brief and the user's answers U1–U5)
CERTIFICATE_SCOPE_DELIVERED = C0 for any measure (every literal is a text datum of the same entity: coordinates, lengths, division ratios, plane coefficients) · C1 for volume/area/distance on templates T1–T6 (right-triangle-base pyramid, rectangle/square-base pyramid, right triangular prism, cuboid, cube, right square prism incl. unnamed) · counterexample only from a valid stretch along a missing required dimension of a fully read text · single reaching definitions (U5 refinement fixed in 41a26f11)
CERTIFICATE_SCOPE_MISSING = angles/cos² · regular and curved solids without coordinates · phrasing outside the closed vocabulary · model-chosen parameters · arithmetic literals (FORMULA_COEFFICIENT empty) · control flow · frame-dependent constructions — all refused UNDETERMINED inside the polyhedral scope · enforcement outside the polyhedral vocabulary (U3: recorded, not refused) · plane equations not entity-bound in C0
AC1 = 3/3 DEPENDENT_ON_UNSTATED_ASSUMPTION (subject AD); route 3/3 refused (2 at assumption ASSUMPTION_DETERMINES_ANSWER, 1 at grounding GIVEN_VALUE_NOT_IN_SOURCE)
AC2 = 18/18 PROVEN_SAFE (8 C0, 10 C1); route 18/18 served; 18/18 oracle-equal and facts verbatim (diagnostics/GOLD_ROW_VERIFICATION.json)
ADVERSARIAL = 7 rows, 7/7 refused, 0/7 PROVEN_SAFE: 6 reach the gate (3 DEPENDENT, 3 UNDETERMINED), adv7 (empty text) refused before it with SOURCE_TEXT_MISSING
FALSE_COUNTEREXAMPLES_W14 = 11 → 0 DEPENDENT: 10 PROVEN_SAFE and served, 1 UNDETERMINED (adv11, one answer is cos² outside C1, refused as registered); root causes RC2/RC4/RC1/RC3/STALE_CONTRACT in diagnostics/TRACK_B_ROOT_CAUSE_TABLE.*
PROBES = W12 LAYOUT_DERIVED probe: refused at assumption (ASSUMPTION_DETERMINES_ANSWER, AD) · W12 model_assumption probe: refused at assumption (ASSUMPTION_DETERMINES_ANSWER, AD) · both were served before W15 and still HIT the 106 cache (diagnostics/PROOF_CACHE_ROW_W15.json)
ROUTES = in scope (polyhedral text): PROVEN_SAFE served, DEPENDENT/UNDETERMINED refused at stage assumption, never sent to repair · out of scope: recorded (assumption_enforced = false), served as before; 2 INVARIANT rows of the census are served this way · multiple definitions (U5): refused in every scope
CENSUS = round 3 at 41a26f11: SHIP, §9 (a)–(f) hold; 111 rows (W14 48, W15 49, W15B 14); 0 PROVEN_SAFE on DEPENDS/MUST_REFUSE; 0 DEPENDENT on INVARIANT; no DEPENDS/MUST_REFUSE row served by the route; compiler cross-check 32 agree / 5 not recognisable / 0 disagree; no row changed status since rounds 1 and 2
STRICT_XFAIL_REMAINING = 0 (the 16 W14 strict xfails were removed where their requirement holds; none left)
FAULT_INJECTIONS = FI1–FI14 at 41a26f11: 13 caught, FI1 masked as registered (stretch maps keep template constraints by construction)
FORMATION = W14 formation kept: six families × desktop/mobile role coverage PASS; forward/backward and playback 12/12 × 19/19; solid_faces gives no prism reading for a non-bijective cap correspondence (characterization unchanged)
SECTION_FILL = SECTION_FILL_DISTINGUISHABLE PASS: closed mean/min ΔE 33.9/25.3 desktop (46 samples), 33.8/25.9 mobile (29) vs registered T_ON 20 / T_ON_MIN 12; pre-close (5 steps) and rewound 0 vs T_OFF 3; root cause of the earlier invisibility: the fill was depth-tested against the solid's opaque depth layer (fixed in 909a3a2d)
HIDDEN_LINES = product = independent oracle 24/24 states; 64 crops, 0 disagreements, 0 duplicate owners; cuboid/cube DECLARED_CAMERA_CHANGE; the four W14-changed scenes HUMAN_REVIEW_PENDING (U2)
HUMAN_REVIEW = NOT_APPROVED
TESTS = T3 frontend/scripts/full-gate.mjs from 'D:/tmp/w15 space/algo-sim' at c57ebd1b: exit 0, FULL_PRODUCT_GATE_PASS — pytest 6757 passed / 0 failed / 1 skipped (test_scalar_obligations.py:95, deliberate) / 2 deselected (opt-in postgres, external_evidence) / 0 xfailed; vitest 1017/1017 (67 files); typecheck + build; demo 5/5; crash surface 6/6 · browser suite exit 0 (12/12 positive, 36/36 negative, 0 raw tokens / console errors / uncaught exceptions / failed API calls / overflow over 48 runs) · occlusion exit 0 · playback exit 0 · builder exit 0 · gates exit 0 (diagnostics/logs/*_c57ebd1b.log) · node harness 55/55 main tree, 53 + 2 skipped by design in the worktree · fault injections and census round 3 exit 0
PRODUCT_COMMITS = 5dd8e7f5 cf57332b 6fa6e582 2305f072 a1b17fef 45d014b0 33b11a79 8239a2a4 0579d559 d41176f2 909a3a2d 41a26f11 (+ ac6687ae, red tests incl. a frontend/src test file)
PRODUCT_COMMIT_SHA = 41a26f11a6c80367c5eff79b86c3e0164f49a4d0
MEASUREMENT_COMMIT_SHA = c57ebd1b4b34abe14947a97d8169dfead99ab622
EVIDENCE_COMMIT_SHA = 23cc880a07b0a95ea502e17f7903bc6ba9f31e6c (supersedes 751169dd, measured at e5b88647 on the intermediate candidate)
FINAL_DOCS_COMMIT_SHA = SELF
CANDIDATE_OLD_HASH = 40263983f97811ada21238a0ff3da634eaa36ef88deb6d07f4c0b3091fb9b5d3
CANDIDATE_NEW_HASH = b3b7eb79d3c64a2f076ae1dc815abb2273364e2c0374660682be66dbbb0ec60c
CANDIDATE_INTERMEDIATE_HASH = aaa5b5bd452321e1ad5130608b27e02a60c55cb487f66dab78563e4dc2f2ca5e
CANDIDATE_REFROZEN_COUNT = 3 (d41176f2; 909a3a2d after the section-fill defect found by the first browser run; 41a26f11 after the final-review soundness fix)
CACHE_VERSION_BEFORE = 106
CACHE_VERSION_AFTER = 107 (0579d559: real pre-W15 ok envelopes of both W12 probes HIT under 106 although W15 refuses them — served → rejected; not bumped again for 41a26f11: 107 unreleased, the fix only refuses more)
CACHE_FINGERPRINT_CHANGED = NO (b1714b566e25c912)
SCHEMA_SYNC = PASS (both mirrors d852b47c08b7ac0e2a41155366ac1ff88e7d08875cb1cfe718326c543b2951e7, exported twice, no diff)
DEFAULT_MODE = LLM_ONLY
LIVING_DOC_IMPACT = README · docs/README · AI_CONTEXT_BUNDLE · CURRENT_STATE · CODE_INDEX (new modules/symbols; w12 _NHAN_TRUOC marked removed) · ARCHITECTURE_MAP (assumption stage, reader family, U2) · CORRECTNESS (what "served" certifies) · OPEN_ISSUES · ROADMAP §0 · STATUS_LEDGER · EVIDENCE_INDEX · THESIS_READINESS · capability matrix note · docs-audit allowed action
TEMP_FILE_INVENTORY = diagnostics/TEMP_FILE_INVENTORY.json: 122 entries (USED 46, RESEARCH_EVIDENCE 15, SUPERSEDED_DIAGNOSTIC 20, REPRODUCIBLE_TEMP 41, UNKNOWN 0); 5 verified duplicates/caches deleted by exact path; 10 worktrees + 3 temp folders removed (diagnostics/WORKTREE_CLEANUP.json)
LIVE_GEMINI_REQUESTS = 0
PUSH_EXECUTED = NO
MERGE_EXECUTED = NO
HISTORY_REWRITTEN = NO
USER_FAVICON_DELETION_PRESERVED = YES
FINAL_DECISION = READY_FOR_HUMAN_VISUAL_REVIEW
NEXT_ACTION = HUMAN_VISUAL_REVIEW_OF_ASSUMPTION_CLOSURE_EVIDENCE
```

## Known leftovers

- Directories left in `D:/tmp` by earlier waves (`w13-verify-c1`, `w10-*`, `w11-*`, `w12-*`,
  `algo-sim-*`) were not inventoried in w15 and were left in place.
- Every w15 worktree and temporary folder is removed (`diagnostics/WORKTREE_CLEANUP.json`).

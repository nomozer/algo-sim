# Handoff — w14 generic formation and assumption foundation

## For the human reviewer

Open, in this order:

1. `images/triangular-pyramid/FILMSTRIP.png` and `images/triangular-prism/FILMSTRIP.png`
   — the answer to W12-H1/H2. Each cell is one formation step, captioned with its role
   names and the learner text:
   - pyramid: points (AB = 3, AC = 4, SA = 5) · base ABC · **SA** ("đường cao, cạnh
     bên": one object, two roles, one visual owner) · lateral edges SB, SC · closed solid;
   - prism: points · lower base ABC · top face DEF · lateral edges AD, BE, CF · closed
     solid.
2. `images/<family>/FILMSTRIP.png` for the other four families. Rectangular pyramid,
   cuboid and cube keep their objects and order (cuboid/cube labels are now capitalised,
   *"Đáy trên …"*, *"Các cạnh bên …"* — the declared Q1 delta). The cross-section gains
   one step, *"Dựng các cạnh bên SA, SB, SC, SD"*, before the pyramid closes; its five
   section steps are unchanged.
3. `images/<family>/SHEET.png` — the acceptance sheet per family, as in w12.
4. Hidden lines of the four scenes S4 changed — `images/{triangular-pyramid,
   triangular-prism, rectangular-pyramid, cross-section}/hidden-edges/desktop/`. The
   frozen human expectations could not be carried over automatically
   (`SCENE_GEOMETRY_CHANGED`: new drawn objects); `diagnostics/OCCLUSION_TRANSFER_DIAGNOSTIC.json`
   shows the independent oracle still reproduces the reviewed visible/hidden sets 4/4.
5. `images/<family>/playback/<viewport>/` — what a learner sees after pressing Play once.

Questions only a person can answer: does every step read as one construction step; does
SA read well as "height and lateral edge" in one step; are the captions and the
capitalised labels right; is the extra lateral step of the cross-section welcome; do the
hidden lines of the four changed scenes still look right.

## Decisions that are yours

| Id | Question | Options and what follows |
|---|---|---|
| W14-D1 | Is a program the product refuses (no formation is ever shown) part of the enforced formation set? Only `n2_khoi_ghep_bu_can_boolean` is affected: its box has no typed base, so the pass leaves it `AMBIGUOUS_TOPOLOGY` by design. | **Yes** (the plan's wording, applied here): the decision stays `FORMATION_FOUNDATION_INCOMPLETE`; completing it needs a typed base for such boxes (contract topology of a composite problem — composite geometry is backlog). **No** (what the pre-product S4 test enforced: served gold p1, p2): the decision becomes `ASSUMPTION_POLICY_INCOMPLETE` with next action `USER_DECISION_ON_ASSUMPTION_CERTIFICATE_SCOPE`. |
| W14-D2 | Assumption certificate scope (Track B stopped) | (a) make C1 reachable: relation facts confirmed as InputFacts (span-checked) for the compiler families, recognition for LLM programs; (b) refuse everything uncertified — today that refuses 18/18 gold answers; (c) keep the channel open and label assumptions instead (D2 chose refusal) |
| W14-D3 | Hidden-line registry for the four changed scenes | re-review them and freeze a new registry layer; the reviewed registry stays byte-identical |

## Required fields

```text
TASK = W14_GENERIC_FORMATION_AND_ASSUMPTION_FOUNDATION
START_HEAD = ce9c672d2328353e3e2b844025040e4ed84163d1
END_HEAD = SELF (the documentation commit that adds this file; resolve with git log -1)
CURRENT_BRANCH = fix/cuboid-visual-semantic-closure
ORIGIN_MAIN = a9492ee98ff9dc3302d1ff64465f1c06e9001bce (git fetch --prune origin at Phase 0: unchanged, equals ls-remote, ancestor of HEAD)
SKILLS_DISCOVERED = superpowers (brainstorming, writing-plans, executing-plans, subagent-driven-development, test-driven-development, systematic-debugging, verification-before-completion, using-git-worktrees, requesting-code-review, finishing-a-development-branch), andrej-karpathy-skills:karpathy-guidelines, ponytail (ponytail, ponytail-review, ponytail-audit, ponytail-debt), mattpocock-skills and the other skills of the session list
SKILLS_USED = writing-plans (plan R2) · karpathy-guidelines (one completion pass instead of per-family planners; deletion in compiler.py) · systematic-debugging (assumption counterexamples RC1-RC5; formation, trust-policy and full-suite failures) · test-driven-development (Tasks 1-8: red first, then green) · executing-plans (inline execution with a ledger and rulings) · ponytail:ponytail-review (Task 9) · verification-before-completion (Tasks 10-12)
SKILLS_SKIPPED_WITH_REASON = brainstorming (design preregistered in w13; the open choices were put to the user as Q1, Q3, Q4) · subagent-driven-development (tightly coupled interfaces; repository rule: no unrequested agents) · using-git-worktrees (the repository's own detached-worktree measurement procedure applies) · requesting-code-review with a fresh reviewer (no unrequested agent; the final whole-branch review is a self-review, reported with the session handoff)
D2 = REFUSE_AND_EXPLAIN_IN_W14 (brief) — applied to SOURCE_TEXT_MISSING; the assumption refusal codes did not ship (Track B STOP)
D3 = EXCLUDE_CURVED_SOLID_FORMATION_FROM_W14 (brief) — curved solids are untouched by the pass
NA05_PORTABILITY = RESOLVED — opt-in marker external_evidence + ALGOSIM_LIVE_RETRY_EVIDENCE_DIR; AST guard on absolute paths (0daa6354)
PYRAMID_LIKE_FORMATION = PASS — triangular and rectangular pyramid families and the cross-section pyramid (gold p1) observed in the browser against an independent expectation, gold p2 in backend tests: BASE < HEIGHT (only where a typed foot exists) <= LATERAL < CLOSE
PRISM_LIKE_FORMATION = PARTIAL — PASS for the triangular prism, cuboid, cube (browser) and square prism (tests): BASE < TRANSLATED_FACE < LATERAL < CLOSE; the refused gold negative n2's box stays AMBIGUOUS_TOPOLOGY (no typed base; decision W14-D1)
FAMILY_ID_BRANCH_GUARD = PASS (AST guard over formation.py and solid_faces.py)
ASSUMPTION_POLICY_RESULT = ASSUMPTION_POLICY_INCOMPLETE (STOP): 0 PROVEN_SAFE on DEPENDS rows, every AC1/adversarial row refused, AC2 0/18 PROVEN_SAFE; no gate shipped; 16 gate tests strict xfail citing the decision
UNGROUNDED_ASSUMPTION_PROBE = STILL_SERVED — the w12 probe's LAYOUT_DERIVED and model_assumption variants reach stage `served` at the measured product (rerun with --runxfail); the strict-xfail tests turn red the day a gate refuses them
SOURCE_GROUNDING_PROBE = AS_REGISTERED — dai_cm reads AB = 5; standalone_wrong_segment refused SOURCE_EVIDENCE_CONFLICT; 23 rows identical; "có độ dài" on the wrong segment refused (test)
TRIANGULAR_PYRAMID_VISUAL = READY_FOR_HUMAN_VISUAL_REVIEW — points · base · SA (height + lateral) · SB, SC · closed solid (images/triangular-pyramid/FILMSTRIP.png)
TRIANGULAR_PRISM_VISUAL = READY_FOR_HUMAN_VISUAL_REVIEW — points · base · top face DEF · AD, BE, CF · closed solid (images/triangular-prism/FILMSTRIP.png)
CROSS_FAMILY_REGRESSION = NONE_MEASURED — product = oracle 24/24; playback 12/12 x 19; cuboid and cube hidden-line expectations transfer; the 4 scenes S4 changed stop at SCENE_GEOMETRY_CHANGED (gate red by design) while the oracle reproduces their reviewed sets 4/4 — human re-review (W14-D3)
PONYTAIL_REVIEW_RESULT = 4 findings applied (net -10 lines), 2 kept with reason, 1 out of scope (diagnostics/PONYTAIL_REVIEW.json)
FULL_BACKEND_RESULT = 6564 passed / 0 failed (1 skipped, 2 deselected opt-in, 16 xfailed) — T3 from a path with a space at 380db58c
FRONTEND_TEST_RESULT = 1010/1010 (67 files)
FRONTEND_TYPECHECK = PASS (tsc -b inside T3)
FRONTEND_BUILD_RESULT = PASS in the measurement and T3 worktrees; the main tree still fails with EPERM on frontend/dist (ISSUE-OPS-DIST-ACL-OWNERSHIP)
NODE_HARNESS_RESULT = 44/44 in the main tree; 42 passed + 2 skipped by design in the worktree (no repo-local venv)
SCHEMA_SYNC = PASS (both mirrors d852b47c08b7ac0e2a41155366ac1ff88e7d08875cb1cfe718326c543b2951e7, exported twice, no diff)
CANDIDATE_OLD_HASH = 548f5b3b9ff891587fccb61cc59981362543a8f60f7f9917b7c241098bbb096f
CANDIDATE_NEW_HASH = 40263983f97811ada21238a0ff3da634eaa36ef88deb6d07f4c0b3091fb9b5d3
CANDIDATE_REFROZEN_COUNT = 1
CACHE_VERSION_BEFORE = 105
CACHE_VERSION_AFTER = 106
CACHE_FINGERPRINT_CHANGED = NO (b1714b566e25c912)
DEFAULT_MODE = LLM_ONLY
LIVE_GEMINI_REQUESTS = 0
PRODUCT_COMMIT_SHA = a2af56e4ec0d2165d6be4a3d7cbef36d7f05eb87
CANDIDATE_COMMIT_SHA = 380db58c37da6088d8dba47647d15ba7ed77cf35
MEASUREMENT_COMMIT_SHA = 380db58c37da6088d8dba47647d15ba7ed77cf35
EVIDENCE_COMMIT_SHA = 54af39a42ab8969a0f8858c7c563d8b7420c9734
FINAL_DOCS_COMMIT_SHA = SELF
PUSH_EXECUTED = NO
MERGE_EXECUTED = NO
HISTORY_REWRITTEN = NO
USER_FAVICON_DELETION_PRESERVED = YES
FINAL_DECISION = FORMATION_FOUNDATION_INCOMPLETE
NEXT_ACTION = COMPLETE_SHAPE_CLASS_FORMATION
```

## Known leftovers

- `D:/tmp/w13-verify-c1` — w13 leftover, unregistered; no unique content by hash
  (`diagnostics/W13_LEFTOVER_INVENTORY.json`): `SAFE_TO_DELETE_MANUALLY`, not deleted.
- Every w14 worktree is removed (`diagnostics/WORKTREE_CLEANUP.json`).

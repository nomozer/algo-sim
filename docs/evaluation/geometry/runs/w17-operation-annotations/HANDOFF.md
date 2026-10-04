# Handoff — w17 operation binding and on-scene annotations

## For the human reviewer

Open, in this order:

1. **`images/cross-section/SHEET.png`**. The refusal rows now include the W17 panel
   *hệ dựng lệch với đề bài* (`construction_mismatch`). The text cuts with (β); the program
   cut with (α). The served row shows the correct plane, area 16, with the area label on the
   section. Is the refusal message clear, and does it avoid telling the learner to fix a
   valid text?
2. **`images/cube/SHEET.png`**. It has the `system_cause` panel: the text is valid, and the
   system's own reading put AB = 0. The message must say the error is the system's. The
   W16 image of a refused "cạnh 4" cube came from a fixture-generator defect, now fixed (see
   `REPORT.md` §C).
3. **The on-figure labels**, in `images/<family>/desktop/neutral_final.png` and
   `mobile/neutral_final.png`:
   - every verified quantity sits beside the segment, region, solid or point it measures;
   - the answer label is bold with a darker border;
   - the "Số đo" and "Kết quả" chips sit in the header bar, both on.

   `annotations_off.png` is the same frame with both chips off; only the labels differ.
   `annotations_resized.png` (desktop) is at 70 % width with the device at DPR 2. Do the
   labels read as part of the figure without hiding it, especially on mobile?
4. **`causal_selected.png` → `causal_restored.png`**, per family and viewport. Selecting
   the answer highlights its chain; "Bỏ chọn" restores the neutral figure at the same camera
   and scroll.
5. **`images/<family>/FILMSTRIP.png`**. The edge-group steps are now named by their action
   ("Các cạnh bên AD, BE, CF"), not "dữ kiện đề cho".
6. **The four scenes W14 changed** (U2 of w15, still pending a person): triangular pyramid,
   triangular prism, rectangular pyramid and cross-section. Their hidden edges are in
   `images/<family>/hidden-edges/desktop/`. The product equals the independent oracle on
   every state.

## Decisions that are yours

| Id | Question | What follows |
|---|---|---|
| W17-H1 | Approve the on-figure labels, the two chips (default on, U-W17-1), the W17 refusal panels and the renamed group steps (carries W16-H1: the four W14-changed scenes, the section fill under the edges, the refusal panels)? | A person records it in a new human-registry layer; automation never writes `APPROVED_BY_USER`. |
| W17-H2 | "(Q) qua M và song song với (ABCD) cắt …" is refused as "chưa chứng minh được" since the final-review fix (W16 served it, without any operation check). Teach the vocabulary to pin a plane through a point parallel or perpendicular to a named plane? | Belongs to W15-H3; `ISSUE-ARCH-CUT-PLANE-BY-POINT-AND-PARALLEL`. |
| W15-H2 | Extend enforcement beyond the polyhedral vocabulary (U3)? | Unchanged by W17. |
| W15-H3 | Widen the closed vocabulary? | Unchanged by W17. Constructions other than section cuts (midpoint, foot of a perpendicular) belong here: `ISSUE-ARCH-CONSTRUCTION-RELATION-BEYOND-SECTION-CUT`. |

## Required fields

```text
TASK = W17_OPERATION_BINDING_AND_ON_SCENE_ANNOTATIONS
CURRENT_BRANCH = fix/cuboid-visual-semantic-closure
START_HEAD = dd6e86b0f6704f5ef5fdf9e2ad4834a42add19ec
END_HEAD = SELF (the documentation commit that adds this file; resolve with git log -1)
BASE = origin/main a9492ee98ff9dc3302d1ff64465f1c06e9001bce (git fetch --prune origin at Phase 0: equals ls-remote, ancestor of HEAD; the feature branch was never pushed)
SKILLS_INVOKED_IN_W17 = superpowers:writing-plans (the W17 plan from the source, C:/Users/Bunny/.claude/plans/w17-operation-annotations.md) · superpowers:executing-plans (that plan, inline, ledger and rulings; 2026-10-03T15:19Z) · superpowers:test-driven-development (loaded by executing-plans at the start of W17, 15:19Z: red first for every product and harness change, including the final-review fix and the restore tolerance) · impeccable (Operate mode; the label overlay and the Số đo/Kết quả chips; bounded visual verification) · ponytail:ponytail-review (the W17 diff before freeze 1; 7 cuts applied in add4afb0)
SKILLS_APPLIED_FROM_AN_EARLIER_INVOCATION = invoked earlier in this same session (2026-09-28) and not re-invoked after the W17 brief; their loaded instructions governed the work: superpowers:systematic-debugging (the Task 7 rounds; browser attempt 1 on the final candidate, diagnosed by filtered reruns before any change) · superpowers:verification-before-completion (every claim here comes from a log of this wave) · andrej-karpathy-skills:karpathy-guidelines (simplest rule at the right boundary, surgical fixes)
SKILLS_APPLIED_MANUALLY = code-reviewer.md of superpowers:requesting-code-review, performed by the author as the final whole-branch self-review after freeze 1 (no subagent)
SKILLS_NOT_USED_WITH_REASON = subagent-driven-development and a fresh-context reviewer (the brief forbids subagents) · brainstorming (scope came from the brief)
ROOT_CAUSES = A′: the certificate pinned literals to their text entities but never compared the construct_section operation with the text's cut relation (producer: the model's program; consumer: the certificate) · goal-only givens: W16 masked goal clauses in the certificate only, while grounding read GIVEN evidence on the whole text · refusal causes: learner messages chose the wording from the stage, not from a structured cause, so system errors told the learner to fix a valid text · the cube "cạnh 4" image: a fixture-generator defect (_zero_ab replaced a string absent from the text) · group label: build_scene_events fell back to a generic label for a statement whose target is not a scene object
A_PRIME_BEFORE_AFTER = before (dd6e86b0): text (β), program (α) → PROVEN_SAFE C0, served, area 9 (text: 16) · after (d63d6fd4): UNDETERMINED CONSTRUCTION_NOT_TEXT_BOUND, subjects (β)/(α), refused at assumption, cause CONSTRUCTION; the correct program (β) PROVEN_SAFE C0, served, area 16; W16 strict xfail now passes
OPERATION_BINDING = shape_constraint.doc_quan_he_cat (closed vocabulary of three phrasings; named, equation or three-point planes; the object of "song song/vuông góc với (X)" is never the cutting plane) + assumption_gate._kiem_phep_dung (same plane identity by source, then name/unique, point-named planes by point set; same solid by vertex set; a definite mismatch needs both identities known, an unpinned identity is ASSUMPTION_INVARIANCE_UNPROVEN)
PREMISE_GOAL = grounding reads GIVEN evidence on che_muc_tieu(text) in every route; a value only in a goal clause → GIVEN_ONLY_IN_GOAL_CLAUSE (G1, G3, G4 — G4 a cylinder outside the polyhedral scope); "Tính …, biết …" (G2), "Chứng minh …, biết …" (G5) and "… bao nhiêu, biết Y?" (G6, G7) are served
REFUSAL_CLASSIFICATION = refusal_cause SOURCE / CONSTRUCTION / UNKNOWN by registered reason code and server text readers; 20/20 negative fixtures reconciled (NEGATIVE_FIXTURE_RECONCILIATION_0b71502b.json); only SOURCE tells the learner to fix the text; the card no longer repeats the backend message
ANNOTATIONS = backend binds (quantity_annotations.gan_so_do: area→region, volume→solid, distance→pair, given length→the text-named segment verified by exact distance; result vs measurement; ANNOTATION_UNBOUND otherwise); frontend projects, places (rings 6/12/18 px, sides then corners, ≤ 24 px), avoids point labels, controls and each other, toggles; nothing before its step
ANNOTATION_RESULTS = binding: every label ≤ 24 px from its independently projected anchor (max 16.97 px), inside the canvas, no overlap with point labels, controls or each other · visibility: every available label shown on desktop (5/5 four families, 3/3 cube and cross-section), also after orbit and after resizing to 70 % width at device DPR 2; on mobile every available label shown too (only the result is required) · nothing early: at every geometry step forward and backward the DOM label ids equal the oracle, 72/72 steps · toggles change only the labels (dash signature, rendered objects, camera within the settle tolerance, selection, step), 12/12 · neutral → causal → restored at the same camera and scroll with a byte-identical canvas, 12/12, camera reset / selection reset / scroll recorded separately
FINAL_REVIEW = self-review (no subagent) after freeze 1: 3 Important — object of "với" read as the cutting plane (a correct program refused with a false message), unpinned identities blamed on the program, ", biết Y?" masked as the goal — fixed in d3817d5f (red 01b0c27c, 8 tests; W17C labels committed before the fix); 2 minor deferred (four-point plane names; equation-plane caption)
CENSUS = round 2 at d3817d5f (3cbe3a1f): SHIP; 167 rows (W14, W15, W15B, W16 + W16B, W17 16, W17C 4); AC2 18/18 PROVEN_SAFE (8 C0, 10 C1); 0 changes against round 1 on 163 rows; the only gate change since W16 round 2 is A2b; W17 + W17C 20/20 as labelled; compiler cross-check 32 / 5 / 0
FAULT_INJECTIONS = backend 23/23 at 6d52ab2f (run 3; runs 1–2: 19/20, 20/20) · frontend 18/18 at 99925723 (run 3: 16 unit + 2 browser; FH2 retargeted after add4afb0, FH3–FH5 for the restore tolerance; runs 1–2: 13/15, 15/15); every source restored byte-identical
CACHE_DECISION = 108 → 109 in fadfd10e: five rows served by dd6e86b0 and refused by W17 (O1, O2, O5, O8, G4) HIT as v108 rows and miss after the bump (PROOF_CACHE_ROW_W17.json); not bumped again for d3817d5f (109 unreleased; the fix serves only correct requests or changes refusal reasons)
MEASUREMENT_ATTEMPTS_ON_FINAL_CANDIDATE = attempt 1 at 83f101e4: one assertion red (cube/mobile causal_restore, CANVAS_NOT_RESTORED), a harness defect — byte comparison read at-rest capture noise (≤ 1 per 8-bit channel) as a change; kept apart (diagnostics/browser-final-attempt1-83f101e4/); harness fix 4e07548e (NHIEU_KHUNG_TOI_DA = 1 registered in §15.5 before re-measuring) · attempt 2 at 99925723: PASS
HUMAN_REVIEW = NOT_APPROVED
TESTS = T3 frontend/scripts/full-gate.mjs from 'D:/tmp/w17 space/algo-sim' at 99925723: exit 0, FULL_PRODUCT_GATE_PASS — pytest 6936 passed / 0 failed / 1 skipped / 2 deselected / 0 xfailed (A′ closed); vitest 1044/1044 (68 files); typecheck + build; demo 5/5 + reduced 1/1; crash surface 6/6 · browser suite exit 0 (12/12 positive, 40/40 negative, 2/2 served; 54 runs with 0 raw tokens, console events, uncaught exceptions or failed API calls) · occlusion exit 0 (HUMAN_REVIEW_PENDING, four W14-changed scenes) · playback exit 0 (12/12) · builder exit 0 (64 crops, 0 oracle disagreements) · gates exit 0 (diagnostics/logs/*_99925723.log) · node harness 65 + 2 skipped by design, 0 fail · census round 2 and fault injections exit 0
PRODUCT_COMMITS = 2678b363 0b71502b ce9a4c1f 8e002028 fa5f8382 2c7d4134 240ecba5 dbb38b95 fadfd10e add4afb0 d3817d5f (+ 288f3616 and 01b0c27c, red tests; 288f3616 includes frontend/src test files)
PRODUCT_COMMIT_SHA = d3817d5f5e6aedbc5b6c140a1503909ecfc8e6cc
MEASUREMENT_COMMIT_SHA = 99925723e6179e9f67852a2aa393db163dd07c4f
EVIDENCE_COMMIT_SHA = 781c14e50327d12aa864426391898f7976442567
FINAL_DOCS_COMMIT_SHA = SELF
INTERMEDIATE_MEASUREMENT = c5592c1a on d4a24eba (evidence f07b0d24): complete PASS, superseded and kept (diagnostics/evidence-intermediate-c5592c1a/)
CANDIDATE_OLD_HASH = 9bb0aaa7bddecf945f3d0c89632d1c46f3d7be350b350ded96dc0c598b733476
CANDIDATE_NEW_HASH = d63d6fd4704ae033ed0e7e32f612b681f421ed7507dafacfd28799d8d0a92b37
CANDIDATE_INTERMEDIATE_HASH = d4a24ebaec48c03d96b94d6915f2c76661959bdf7b0f98311bd3239eff3e731d
CANDIDATE_REFROZEN_COUNT = 2 (add4afb0 → d4a24eba in 4706eb0b; d3817d5f → d63d6fd4 in 921015b6, after the final-review fix)
CACHE_VERSION_BEFORE = 108
CACHE_VERSION_AFTER = 109
CACHE_FINGERPRINT_CHANGED = NO (b1714b566e25c912)
SCHEMA_SYNC = PASS (both mirrors d852b47c08b7ac0e2a41155366ac1ff88e7d08875cb1cfe718326c543b2951e7, exported twice at the measurement commit, no diff)
MODEL_SURFACE_CHANGED = NO (0 files since dd6e86b0)
DEFAULT_MODE = LLM_ONLY
LIVING_DOC_IMPACT = README · docs/README · AI_CONTEXT_BUNDLE · CURRENT_STATE · CODE_INDEX (W17 section, harness restore tolerance, run diagnostics) · ARCHITECTURE_MAP · CORRECTNESS · OPEN_ISSUES (two resolved, three opened) · ROADMAP §0 · STATUS_LEDGER · EVIDENCE_INDEX · THESIS_READINESS · ASSUMPTION_CERTIFICATE_AMENDMENT §15 (dated corrections: Tasks 1–3, Task 7, the final review, the attempt-1 restore tolerance) · docs-audit allowed actions
ARTIFACTS = REPORT.md · HANDOFF.md · RUN.json · MANIFEST.json · results/ (BROWSER_EVIDENCE, OCCLUSION_MEASUREMENT, PLAYBACK_EVIDENCE, HIDDEN_EDGE_CROPS) · images/<family>/ (SHEET, FILMSTRIP, desktop, mobile, negative, served, playback, hidden-edges) · inputs/ (fixtures, FIXTURE_MANIFEST, CANDIDATE_DIVERGENCE_CORRECTION) · diagnostics/ (MEASUREMENT_ATTEMPTS, census rounds 1–2, corpora W17/W17C, fault-injection drivers and logs, cache proof, ponytail review, Task 7 rounds, evidence-intermediate-c5592c1a, browser-final-attempt1-83f101e4, TEMP_FILE_INVENTORY, WORKTREE_CLEANUP, logs)
TEMP_FILE_INVENTORY = diagnostics/TEMP_FILE_INVENTORY.json: 37 rows (USED 5, RESEARCH_EVIDENCE 6, SUPERSEDED_DIAGNOSTIC 7, REPRODUCIBLE_TEMP 19, UNKNOWN 0); 63 paths deleted by exact path in two cleanups after the unique artifacts were copied and verified byte-identical; 10 worktrees created and removed (diagnostics/WORKTREE_CLEANUP.json); git worktree list = the main tree only
LIVE_GEMINI_REQUESTS = 0
PUSH_EXECUTED = NO
MERGE_EXECUTED = NO
HISTORY_REWRITTEN = NO
USER_FAVICON_DELETION_PRESERVED = YES
FINAL_DECISION = READY_FOR_HUMAN_VISUAL_REVIEW
NEXT_ACTION = HUMAN_VISUAL_REVIEW_OF_OPERATION_ANNOTATION_EVIDENCE
```

## Known leftovers

- **Deferred minors:**
  - a plane named by four or more points binds only to a `construct_plane` through exactly
    that point set (an over-refusal);
  - the served correct-plane caption reads "Mặt phẳng cho bằng phương trình", not "(β)".
- **Pre-existing, observed during measurement:** the WebGL renderer keeps pixel ratio 1 at
  every device DPR. The W17 DPR check proves that labels are placed again after a DPR
  change; it says nothing about sharper rendering.
- **Not touched:** directories that earlier waves left in `D:/tmp`.

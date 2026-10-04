# Handoff — w18 construction binding and focused annotations

## For the human reviewer

Open, in this order:

1. **`images/cross-section/SHEET.png`**. The refusal rows now include the three W18 panels:
   - `point_construction_mismatch`: the text says "M là trung điểm của SA", the program built the midpoint of SB;
   - `projection_mismatch`: the text says "H là hình chiếu vuông góc của S lên đường thẳng BD", the program
     projected onto BC;
   - `construction_unverified`: "Gọi M là điểm chính giữa của đoạn SA", a phrasing the system cannot check.

   The two served W18 rows show a distance witness: M on SA to the base plane (answer 3), and S to its foot H on BD
   (3√6). Do the refusal messages say who is at fault (the system, never the text)?
2. **The compact default**, in `images/<family>/desktop/neutral_final.png` and `mobile/neutral_final.png`. It shows
   point names and the given data only. One chip, "Hiện tất cả", replaces the W17 "Số đo"/"Kết quả" pair.
   `show_all.png` is the same frame with the chip on.
3. **Selection**, in `images/<family>/desktop/selected_<kind>.png` with `detail_<kind>.png` (`<kind>` = length,
   area, volume, distance). Selecting a quantity shows its label and its numeric chain. The inspector (right on
   desktop, below on mobile) holds the formula, the given data and the direct inputs. A selected distance draws
   its witness: a dashed segment to the exact foot and a right-angle mark.
4. **The solution**: `solution_neutral_final.png` (collapsed by default: Kết quả shows `symbol = value`) and
   `solution_expanded.png` (opened by the learner; the inspector then drops its formula).
5. **`images/<family>/FILMSTRIP.png`** and `causal_selected.png` → `causal_restored.png`: playback, highlight and
   restore are unchanged from w17.
6. **The four scenes W14 changed** (U2 of w15, still pending a person): triangular pyramid, triangular prism,
   rectangular pyramid and cross-section. Their hidden edges are in `images/<family>/hidden-edges/desktop/`. The
   product equals the independent oracle on every state.

## Decisions that are yours

| Id | Question | What follows |
|---|---|---|
| W18-H1 | Approve the compact default, the "Hiện tất cả" chip, selection with its numeric chain, the inspector as the one explanation place, the collapsed solution, the distance witness and the W18 refusal panels? This carries W17-H1 and W16-H1 (the four W14-changed scenes). | A person records it in a new human-registry layer; automation never writes `APPROVED_BY_USER`. |
| W18-H2 | For a result whose formula has no references ("S(T) = 9", "d(S, BD) = 3√6"), the inspector's line repeats the Kết quả row while the solution is collapsed. §16.5 keeps the value in the inspector on purpose, so that a label hidden by crowding stays readable. Drop that line for results? | A presentation change in `Scene3DExplorer.tsx`, then a refreeze and re-measurement. |
| W18-H3 | "Tính độ dài đoạn MC" with no other clue stops at the scope gate (no clue for "độ dài"). Add the clue? | A routing-policy change: corpus re-run and a `CACHE_VERSION` decision (`ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE`). |
| W17-H2 | "(Q) qua M và song song với (ABCD) cắt …" is refused as "chưa chứng minh được". | Unchanged by W18 (`ISSUE-ARCH-CUT-PLANE-BY-POINT-AND-PARALLEL`). |
| W15-H2 | Extend enforcement beyond the polyhedral vocabulary (U3)? | Unchanged by W18. UNVERIFIED point constructions are recorded only outside U3. |
| W15-H3 | Widen the closed vocabulary? | Now also covers point constructions beyond midpoints and projections: centres, centroids, intersections, unread phrasings (`ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY`). |

New shapes, OCR and several solids in one problem are recorded for later waves (`docs/ROADMAP.md` §0), outside W18.

## Required fields

```text
TASK = W18_CONSTRUCTION_BINDING_AND_FOCUSED_ANNOTATIONS
CURRENT_BRANCH = fix/cuboid-visual-semantic-closure
START_HEAD = 0ec2bbbb105d1aa899b6c292cb3821092fb59b40 (W17 final docs commit)
END_HEAD = SELF (the documentation commit that adds this file; resolve with git log -1)
BASE = origin/main a9492ee98ff9dc3302d1ff64465f1c06e9001bce (git fetch --prune origin at Phase 0: equals ls-remote, ancestor of HEAD; the feature branch was never pushed)
SKILLS_INVOKED_IN_W18 = superpowers:writing-plans (C:/Users/Bunny/.claude/plans/w18-binding-focus.md) · superpowers:executing-plans (inline, ledger and rulings) · superpowers:test-driven-development (red first for every product and harness change: f3edd903/bb9f7004, 9844f83e, 21981005, RED_W18_HARNESS_FIX.log) · superpowers:systematic-debugging (Phase 1, pre-freeze round 1, FA4, the three browser injections missed in run 1) · andrej-karpathy-skills:karpathy-guidelines · impeccable (Operate mode, refinement of the explorer, bounded visual verification) · ponytail:ponytail-review (before the freeze; PONYTAIL_REVIEW_W18.json) · superpowers:verification-before-completion (before this handoff)
SKILLS_APPLIED_MANUALLY = code-reviewer.md of superpowers:requesting-code-review, performed by the author as the final whole-branch self-review (no subagent: the brief asks for one agent)
SKILLS_NOT_USED_WITH_REASON = subagent-driven-development and a fresh-context reviewer (one agent, per the brief) · brainstorming (scope came from the brief)
ROOT_CAUSE = every gate before W18 asked WHERE a point is (coordinate invariants, the W15 literal certificate), never WHICH text point it is; the W17 operation check covered construct_section only; no server reader read projections or "lần lượt" lists. A determined point built on other entities, renamed, or replaced by a same-coordinate twin was served unless its coordinates broke a text invariant
REPRODUCTION_BEFORE_AFTER = bb9f7004 (before): B5 swapped list served (3√6 for 9), B7 renamed target served, B9 same-coordinate twin served, B11 wrong line served (6√2 for 3√6), B13 wrong plane served (3√2 for 2√3), B2/B4 refused only at source_invariant with cause UNKNOWN · 84ce7b70 (after): the seven reachable MUST_REFUSE rows refused at construction_binding, cause CONSTRUCTION, both relations named; every INVARIANT row served except B16 (unread phrasing, UNVERIFIED by design); B18/B19 stop at the pre-existing scope gate (CONSTRUCTION_BINDING_REPRODUCTION_*.json)
CONSTRUCTION_BINDING_SCOPE = closed vocabulary §16.1: "X là trung điểm (của) AB"; "X, Y lần lượt là trung điểm của AB, CD" (in order, counts must match); "X là hình chiếu (vuông góc) của P lên/trên/xuống <line|plane>"; "X là chân đường vuông góc/đường cao (kẻ/hạ) từ P xuống/đến/tới/lên <line|plane>". Identity by aliases, _khoa (A′/A'/A_prime), labels, fact source and the C₁a reconciliation, never by coordinates or values. Statuses: MATCHED; MISMATCHED (refused everywhere, CONSTRUCTION_NOT_TEXT_BOUND); UNVERIFIED (refused in U3, CONSTRUCTION_BINDING_UNVERIFIED, cause UNKNOWN, "chưa đối chiếu được"); AUXILIARY (engine points, provenance AUXILIARY); OUT_OF_SCOPE; NOT_REALIZED
UNVERIFIED_AND_OVER_REFUSALS = B16 "điểm chính giữa" (correct program) refused UNVERIFIED in U3; W15 oov:chia_doan_canh now refused earlier as UNVERIFIED (already refused); a receiver named through other points of the same line or plane is MISMATCHED (by-name identity rule); "Tính độ dài đoạn MC" with no other clue stops at the scope gate (W18-H3)
OPEN_LIMITS = centres, centroids, orthocentres, intersections and symmetric points OUT_OF_SCOPE (ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY); phrasing outside the vocabulary UNVERIFIED; witness only point→line/plane, drawn on top; the highlight dash rule is exercised in the browser by cross_section only (elsewhere by the unit test); display name "(ABC)" for the text's "(ABCD)" in the served witness case
CENSUS = CONSTRUCTION_BINDING_DECISION_W18.json at 84ce7b70: SHIP (§9 rule unchanged); AC2 gold 18/18 PROVEN_SAFE; W14, W15, W15B, W16, W16B, W17, W17C: no served row refused; only route change W15 oov:chia_doan_canh; W18 23/23 as registered; compiler cross-check 32 / 5 / 0
SIX_FAMILIES = triangular pyramid, triangular prism, rectangular pyramid, cuboid, cube, cross-section × desktop 1440×900 and mobile 390×844: 12/12 positives, 46/46 negatives (8 kinds, 3 of them W18), 6/6 served
LABEL_POLICY = default: point names + given data (12/12 = oracle); selected quantity: its label + numeric chain (58/58 selections); "Hiện tất cả": every available label, nothing before its step (72/72 steps = oracle); isolation measured against the state before the first toggle 12/12; no fixed label count; crowded labels hide, values stay in the inspector and the solution
ONE_DETAIL_PLACE = the inspector (geo3d-soi; right on desktop, below on mobile) holds the formula, "Từ dữ kiện đề cho" and "Tính trực tiếp từ"; the full solution is collapsed by default and, when open, carries the formula while the inspector drops it: exactly one region 10/10 collapsed and 10/10 open (selections with a referenced formula); same_as merges by subject, never by value
DISTANCE_WITNESS = backend annotation.witness {from, foot (exact, kernel.project_point_onto_line/plane), on, marker {u, v}}; drawn only while the distance label shows (2/2 on selection, 2/2 under "Hiện tất cả"); no geometry-timeline step; the frontend computes no foot (5D guard)
FAULT_INJECTIONS = backend 12/12 at 8caa8307 (run 3; run 1 11/12 → FA4 guard fixed in 83a0e0c1, run 2 12/12) · frontend 12/12 at 0ca3accf (run 2: unit 8/8, browser 4/4; run 1 at 8caa8307: unit 8/8, browser 1/4 → three harness blind spots fixed in 1d8dfc6f)
TESTS = T3 frontend/scripts/full-gate.mjs from 'D:/tmp/w18 space/algo-sim' at 0ca3accf: exit 0, FULL_PRODUCT_GATE_PASS — pytest 7001 passed / 0 failed / 1 skipped / 2 deselected / 0 xfailed; vitest 1058/1058 (68 files); typecheck + build; demo 5/5 + reduced 1/1; crash surface 6/6 · browser suite exit 0 · occlusion exit 0 (HUMAN_REVIEW_PENDING, four W14-changed scenes) · playback exit 0 (12/12) · builder exit 0 (64 crops, 0 oracle disagreements) · gates PASS (node harness 70 + 2 skipped by design, 0 fail) · pre-freeze full backend at 7a06ee47: 6985 passed / 16 classified failures, all green after 5cfb53a1 and 72be45ce
MEASUREMENT_COMMIT = 0ca3accf7e921797e75aebcbc19e3a05b2557859 (acceptance attempt 2)
ATTEMPT_1 = 8caa8307: every gate passed; superseded by the harness fix 1d8dfc6f; kept in diagnostics/evidence-attempt1-8caa8307/
PRODUCT_COMMITS = 84ce7b70 f2a040f9 b6868e19 1e8c5658 7a06ee47 (+ red tests f3edd903, bb9f7004, 9844f83e, 21981005; 21981005 includes frontend/src test files)
PRODUCT_COMMIT_SHA = 7a06ee473a481a1377d270b9a2318756807da91a
EVIDENCE_COMMIT_SHA = 4a9db1ffd73c9eeefddd377e4c62edb2b3f58064
FINAL_DOCS_COMMIT_SHA = SELF
CANDIDATE_OLD_HASH = d63d6fd4704ae033ed0e7e32f612b681f421ed7507dafacfd28799d8d0a92b37
CANDIDATE_NEW_HASH = d3b4cab96c69a09f6ba1b82ac5ca1ee994abed3430d0f277fa30c6d7f328d57e
CANDIDATE_REFROZEN_COUNT = 1 (7a06ee47 → d3b4cab9 in 8caa8307; no intermediate candidate)
CACHE_VERSION_BEFORE = 109
CACHE_VERSION_AFTER = 110 (1e8c5658: B5, B7, B9, B11, B13, B16 served before W18, refused by W18, HIT under 109 — PROOF_CACHE_ROW_W18.json; the identity lock regenerated in 5cfb53a1)
CACHE_FINGERPRINT_CHANGED = NO (b1714b566e25c912)
SCHEMA_SYNC = PASS (both mirrors d852b47c08b7ac0e2a41155366ac1ff88e7d08875cb1cfe718326c543b2951e7, exported twice at the measurement commit, no diff)
MODEL_SURFACE_CHANGED = NO (0 files since 0ec2bbbb)
DEFAULT_MODE = LLM_ONLY
LIVING_DOC_IMPACT = README (run pointer) · docs/README (current run, decisions) · CURRENT_STATE (base block, W18 table, origin row) · AI_CONTEXT_BUNDLE (§1, §2, §3 W18, §4–§6) · CODE_INDEX (W18 section, W17 symbols removed in W18 marked) · ARCHITECTURE_MAP (W18 block, invariant #39) · CORRECTNESS (what "served" now means) · OPEN_ISSUES (one partially resolved, two opened, one updated) · ROADMAP §0 (new shapes, multi-object and OCR noted as later waves) · STATUS_LEDGER · EVIDENCE_INDEX (W18 entry; W17 corrected and superseded for the human verdict) · THESIS_READINESS · amendment §16 (dated corrections) · docs-audit allowed actions. Not changed, with reason: RULES.md and AGENTS.md (no rule changed), MIGRATION_CHECKLIST.md (compiler-first gates untouched), COVERAGE.md (no coverage claim made), DESIGN_BRIEF.md (the explorer kept its identity; Operate-mode refinement only)
ARTIFACTS = REPORT.md · HANDOFF.md · RUN.json · MANIFEST.json · results/ (BROWSER_EVIDENCE, OCCLUSION_MEASUREMENT, PLAYBACK_EVIDENCE, HIDDEN_EDGE_CROPS) · images/<family>/ (SHEET, FILMSTRIP, desktop, mobile, negative, served, playback, hidden-edges) · inputs/ (fixtures, FIXTURE_MANIFEST, CANDIDATE_DIVERGENCE_CORRECTION) · diagnostics/ (reproductions, corpus, census, fault injections, cache proof, ponytail review, pre-freeze rounds, attempt 1, measurement attempts, temp inventory, worktree cleanup, logs)
REVIEW_IMAGES = images/cross-section/SHEET.png · images/<family>/desktop/{neutral_final,show_all,selected_<kind>,detail_<kind>,solution_neutral_final,solution_expanded,rotated_neutral,causal_selected,causal_restored}.png · images/<family>/mobile/ (same states) · images/<family>/FILMSTRIP.png · images/<family>/negative/<kind>/<viewport>/refusal.png · images/cross-section/served/{point_construction_witness,projection_correct,correct_plane}/<viewport>/served.png · images/<family>/hidden-edges/desktop/ · images/overview/INDEX.png
TEMP_FILE_INVENTORY = diagnostics/TEMP_FILE_INVENTORY.json: 29 rows (USED 9, RESEARCH_EVIDENCE 0, SUPERSEDED_DIAGNOSTIC 6, REPRODUCIBLE_TEMP 14, UNKNOWN 0); 62 paths deleted by exact path (51 under D:/tmp, 11 in the session scratchpad) after the unique artifacts were copied and verified; 7 worktrees created and removed (diagnostics/WORKTREE_CLEANUP.json); the only uncommitted unique outputs removed were the 466 superseded attempt-1 images (their sha256 values are in the committed attempt-1 evidence)
LIVE_GEMINI_REQUESTS = 0
HUMAN_REVIEW = NOT_APPROVED
PUSH_EXECUTED = NO
MERGE_EXECUTED = NO
HISTORY_REWRITTEN = NO
USER_FAVICON_DELETION_PRESERVED = YES
FINAL_DECISION = READY_FOR_HUMAN_VISUAL_REVIEW
NEXT_ACTION = HUMAN_VISUAL_REVIEW_OF_CONSTRUCTION_BINDING_AND_FOCUS_EVIDENCE
```

## Known leftovers

- **Deferred minors (final self-review):**
  - the "một điểm phụ" fallback in a mismatch message can be glued to another symbol ("một điểm phụA");
  - a relation whose target is declared as a literal is neither checked nor recorded NOT_REALIZED (backstops: the
    coordinate invariant for midpoints, the W15 certificate for projections in U3);
  - a receiver named through other points of the same line or plane is MISMATCHED (registered by-name rule);
  - `_xuat_xu_hien_thi` recomputes the binding the route already computed (cost only);
  - `IconFlag` has no user since the "Kết quả" chip was removed;
  - the inspector repeats the value line of a formula-less result (W18-H2).
- **Observed during measurement:** one causal-restore pair (triangular-prism/mobile) differed by at most 1 per 8-bit
  channel, inside the tolerance registered in w17 §15.5; both frames are saved next to the images.
- **Not touched:** directories that earlier waves left in `D:/tmp`.

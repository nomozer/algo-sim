# Operation binding and on-scene annotations (w17)

Status: **`READY_FOR_HUMAN_VISUAL_REVIEW`**. Every required gate passes on the final candidate `d63d6fd4…` at the
measurement commit `99925723`. Human visual review is still `NOT_APPROVED`.
This is automation only; nothing here is `MERGE_READY`.

## Identity

- **Branch and start.** Branch `fix/cuboid-visual-semantic-closure`, start **`dd6e86b0`** (W16
  END). At Phase 0, `origin/main` was fetched and is an ancestor of HEAD; the feature branch
  has never been pushed (`diagnostics/logs/PHASE0_REPOSITORY_GATE.log`).
- **Order of work.**
  1. The rules (amendment §15) and the W17 corpus labels were registered first, in
     `bce0b7bb`.
  2. Then came the red tests (`288f3616`, backend 46 failed / 14 passed for the stated
     reasons) and the A′ reproduction through `run_pipeline`.
  3. Only then were the fixes made.
  4. After the first freeze, the final whole-branch self-review found three Important
     defects. They were fixed red-first, and every acceptance run was repeated on the
     final candidate (brief: "Nếu phát hiện lỗi sau freeze, sửa và tái đo trên candidate
     cuối").
- **Product commits** (touching `backend/app` or `frontend/src`):
  - `2678b363`: operation binding.
  - `0b71502b`: goal-only givens and refusal causes.
  - `ce9a4c1f`: group-step label.
  - `8e002028`: annotation binding.
  - `fa5f8382`: labels and chips, `frontend/src`.
  - `2c7d4134`, `240ecba5` and `dbb38b95`: Task 7 fixes in `frontend/src` (corner and ring
    placement, refusal card, a test).
  - `fadfd10e`: `CACHE_VERSION`.
  - `add4afb0`: ponytail simplifications.
  - `d3817d5f`: the final-review fix; **the last product commit**.
  - `288f3616` and `01b0c27c`: red tests (`288f3616` includes `frontend/src` test files).
- **Candidate.** `9bb0aaa7…` (W16) → **`d63d6fd4…`** (109 files). It was frozen **twice**,
  each time in a clean detached worktree:
  - freeze 1 at `add4afb0` (`4706eb0b`) gave the intermediate candidate `d4a24eba…`;
  - freeze 2 at `d3817d5f` (`921015b6`) gave `d63d6fd4…`, after the final-review fix.
- **Measurement and evidence.**
  - The measurement commit is **`99925723`**. After the last product commit it adds only the
    freeze-2 declarations, run records (census, fault injections, the kept-apart attempts) and
    one harness fix (`4e07548e`, below); all of it lies outside the measured paths.
  - The evidence commit is **`781c14e5`**.
  - Two earlier measurements are kept apart, unchanged:
    - `c5592c1a` (evidence `f07b0d24`) measured the intermediate candidate. It passed
      completely and is superseded, not withdrawn
      (`diagnostics/evidence-intermediate-c5592c1a/`).
    - `83f101e4` was attempt 1 on the final candidate. One assertion was red, a harness
      defect (`diagnostics/browser-final-attempt1-83f101e4/`).
  - The divergence is declared in `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`, a new layer
    that corrects the w16 one, and in the living `CANDIDATE_DIVERGENCE.json`.
- **Cache.** 108 → **109** (`fadfd10e`, proven by rows, below). The fix `d3817d5f` did not
  bump it again: 109 is unreleased, and the fix only serves correct requests (G6, G7) or
  changes refusal reasons. The provider fingerprint is unchanged (`b1714b566e25c912…`); the
  model surface is untouched.
- **Model calls.** `DEFAULT_MODE = LLM_ONLY`. Every run of this wave made 0 model calls.

## Phase 1 — A′ reproduced before any fix

`diagnostics/reproduce_operation_binding.py` ran row O1 through the production boundary
(`run_pipeline`, frozen analyze/program stages, 0 model calls). Row O1 is: "Cho hai mặt
phẳng (α): z = 3 và (β): z = 2. Mặt phẳng (β) cắt khối chóp theo thiết diện (T)." The program
cuts (T) with `alpha_plane`.

The reproduction separates five things:

| What | Value |
|---|---|
| literal with a source | both plane literals pinned by the text (the W16 plane binding holds) |
| semantic entity identity | `alpha_plane` = (α), `beta_plane` = (β) |
| construction the text asks | (β) cuts S.ABCD → (T), area 16 |
| construction the program runs | `construct_section(T, S.ABCD, alpha_plane)` |
| result served | certificate PROVEN_SAFE C0, status ok, **area 9** |

Saved: `diagnostics/OPERATION_BINDING_REPRODUCTION_bce0b7bb.json` (source, request, program,
certificate, envelope).

## A — operation binding (§15.1)

**Root cause (producer → consumer).** The model's program (producer) names the plane in
`construct_section`. The certificate (consumer) pinned every literal on the slice to its
text entity, but no rule compared the *operation* with the text's cut relation. A correctly
pinned (α) could therefore stand where the text says (β).

**Fix, at the authority boundary: source solid → cutting plane → requested section.**
- `shape_constraint.doc_quan_he_cat` reads the text's cut relations on the goal-masked text,
  using a closed vocabulary of three forms:
  - "(X) cắt <khối> theo thiết diện (T)";
  - "thiết diện (T) của <khối> cắt bởi (X)";
  - "cắt <khối> bởi (X) được thiết diện (T)".

  The plane may be named, written as an equation, or "qua ba điểm". The object of "song
  song/vuông góc với (X)" is never read as the cutting plane (final-review fix).
- `assumption_gate._kiem_phep_dung` makes every `construct_section` on the slice an extra
  condition of PROVEN_SAFE:
  - the section must bind to a cut relation (unique, by source, or by name);
  - it must use the **same plane identity**: `danh_tinh_mat_phang` goes by source first
    (`source_fact_id` → verbatim InputFact located once in the text → that plane), and a
    name/source conflict binds nothing; the W16 name/unique rule is the fallback; a plane
    named by points is its point set;
  - it must cut the **same solid** (vertex set).

  Equal equations are never the same entity.
- **Verdicts.**
  - A definite mismatch gives UNDETERMINED + `CONSTRUCTION_NOT_TEXT_BOUND`. A mismatch is
    definite when both identities are known and differ. The request is refused at
    `assumption` and never sent to repair. The learner message names both planes and does
    not blame the text.
  - An identity the server cannot pin gives UNDETERMINED + `ASSUMPTION_INVARIANCE_UNPROVEN`
    (cause UNKNOWN). A program the gate cannot check is never blamed for a mismatch (final
    review).

**Before / after.**

| Row | Before (W16 end, dd6e86b0) | After (W17 final, d63d6fd4) |
|---|---|---|
| O1 / A2b — text (β), program (α) | PROVEN_SAFE C0, served, area 9 | UNDETERMINED `CONSTRUCTION_NOT_TEXT_BOUND`, subjects (β)/(α), refused |
| O1b — text (β), program (β) | served, area 16 | PROVEN_SAFE C0, served, area 16 |
| O2 — another solid (S.ABC for S.ABCD) | served | refused, `CONSTRUCTION_NOT_TEXT_BOUND` |
| O3 — measures another section | refused (other reason) | refused, `CONSTRUCTION_NOT_TEXT_BOUND` |
| O5 — (P) used where the text says (P′) | served | refused |
| O8 — same equation, different identity | served | refused |
| O4, O6, O8b, O9, O10 — valid (P′, alias, same-equation right identity, unique unnamed plane, passive phrasing) | served | PROVEN_SAFE C0, served |
| O7 — machine names p1/p2 with source facts | refused | PROVEN_SAFE C0, served (source binding) |
| Q1 — "(Q) qua M và song song với (ABCD) cắt khối chóp …", right program | served (no operation check) | refused, `ASSUMPTION_INVARIANCE_UNPROVEN` (was `CONSTRUCTION_NOT_TEXT_BOUND` at freeze 1, with the false message "Đề bài nêu mặt phẳng (ABCD)") |
| Q2 — "(Q), song song với (ABCD), cắt …", right program | served | refused, `ASSUMPTION_INVARIANCE_UNPROVEN` (was `CONSTRUCTION_NOT_TEXT_BOUND` at freeze 1) |

Q1 and Q2 are over-refusals: the answer is right, and the closed vocabulary cannot pin a
plane defined by a point and a parallel plane. The learner reads "chưa chứng minh được", not
"the program cut the wrong plane". The issue is recorded as
`ISSUE-ARCH-CUT-PLANE-BY-POINT-AND-PARALLEL`.

The W16 strict xfail `test_w16_gioi_han_A_phay_…` now passes, with its xfail mark removed.
The browser pair on one text gives:
- `cross_section_wrong_plane`: refused with cause CONSTRUCTION;
- `cross_section_correct_plane`: served, area 16, with the area label on the section.

## B — premise versus goal in grounding (§15.2)

**Root cause.** W16 masked goal clauses only inside the certificate. The product grounding
gate still read GIVEN evidence on the whole text. `Chứng minh rằng SA = 5` could therefore
back a GIVEN `SA = 5`. Inside the polyhedral scope the certificate refused it; outside that
scope (the cylinder p4), it was served.

**Fix.**
- `grounding_gate.check_grounding` reads evidence on `che_muc_tieu(text)`, which keeps the
  same length and spans.
- A second pass on the unmasked text only *classifies* the refusal as
  `GIVEN_ONLY_IN_GOAL_CLAUSE`; it never grants evidence.
- `, biết` ends a goal clause, so in "Chứng minh X, biết Y" Y is a datum (dated correction
  §15.2).
- In a question that ends "…, biết Y?", the "biết" clause is a premise and the question is
  the clause before it (final-review fix).

**Results.**
- G1 (SA only in the proof request), G3 (S's coordinates only in it) and G4 (cylinder, A only
  in it) are refused at `grounding` with `GIVEN_ONLY_IN_GOAL_CLAUSE`.
- G2 (`Tính …, biết SA = 5`) and G5 (`Chứng minh …, biết … SA = 5`) are served.
- G6 ("Thể tích … bằng bao nhiêu, biết SA = 5?") and G7 ("Hỏi … bằng bao nhiêu, biết SA =
  5?") are served, C1. At freeze 1 both were refused with `GIVEN_ONLY_IN_GOAL_CLAUSE`: the
  premise was masked instead of the question.

This is a grounding fix, not a certificate expansion.

## C — refusal causes and messages (§15.3)

Every geometry refusal carries `refusal_cause` ∈ {SOURCE, CONSTRUCTION, UNKNOWN}. It is
decided only from structured codes and the server's text readers (`refusal_cause.py`), never
from prose.

**Registered table.**
- SOURCE: `GIVEN_VALUE_NOT_IN_SOURCE`, `ASSUMPTION_DETERMINES_ANSWER`,
  `GIVEN_ONLY_IN_GOAL_CLAUSE`, `SOURCE_TEXT_MISSING`.
- CONSTRUCTION: `CONSTRUCTION_NOT_TEXT_BOUND`, `SOURCE_EVIDENCE_CONFLICT` and
  `SOURCE_SPAN_MISMATCH`. The last two are the system's reading disagreeing with the text,
  per the dated correction of Task 1.
- `NON_POSITIVE_LENGTH` is SOURCE only if the text itself writes a length ≤ 0.
- `PLANE_DOES_NOT_CUT` is SOURCE only if the failing plane is proportional to a text
  equation.
- Everything else is UNKNOWN.

Only a SOURCE cause tells the learner to fix the text. CONSTRUCTION says "đề không cần sửa".
UNKNOWN keeps a conditional "gửi lại".

**Reconciliation of every negative fixture.** `diagnostics/NEGATIVE_FIXTURE_RECONCILIATION_0b71502b.json`
traces source / program / envelope to a class, giving 20/20 MATCH. The W16 image of a cube
"cạnh 4" refused was a **fixture-generator defect**, not a product one. `_zero_ab` replaced
"AB = 3", a string absent from the cube text. The text stayed valid (V = 64) while the
contract carried AB = 0. Class: HISTORICAL_DEFECT, runner-injected wrong program. Now:
- `_zero_ab` writes the zero into the text ("cạnh bằng 0"), and that refusal is SOURCE;
- a separate `cube_system_cause` fixture keeps the text valid, injects AB = 0 into the
  contract only, and is refused with CONSTRUCTION.

**Refusal card (Task 7).**
- For SOURCE and CONSTRUCTION the backend message already states the cause and the next
  step, so the card has no hint that repeats it. The rule matches the out-of-closure branch:
  a hint says something different from `learner_reason`, or nothing.
- A CONSTRUCTION refusal at the source gate is labelled "hệ dựng lệch với đề bài" instead of
  "dữ kiện không truy được về đề bài".

## D — group label and formation

**Root cause.** A group statement ("Các cạnh bên AD, BE, CF") targets a variable that is not
a scene object. `build_scene_events` therefore fell back to "Bước dựng hình", and the player
printed "Đang dựng — (dữ kiện đề cho)" for a construction step.

**Fix.**
- The event uses the statement's own label, never a machine name with `_`.
- The player shows the action name; "dữ kiện đề cho" now belongs to the INIT step only.

**Checks.**
- The provenance audit found the internal display group `given` on LAYOUT_DERIVED vertices
  used only for explode/isolate, never as text.
- A new test checks every section-edge narration against the solid's faces in the payload
  ("mặt SAB" and its two edges).
- The progression (points → base/height/top/edges → close; section edges one by one, then
  the closed fill) is unchanged.

## E — quantities on the figure (§15.4)

**Binding, owned by the backend** (`quantity_annotations.gan_so_do`):
- a measured quantity binds to its IR operand:
  - area → polygon or section (region);
  - volume → solid;
  - distance → pair, where two points make a segment;
- a given length binds to the segment the server's text reader names just before its GIVEN
  evidence span, **verified by the exact distance** in the final memory.

Each quantity carries `annotation = {kind, category, subject_ids, anchor, unit}`, where
`category` is `result` for the problem's target (or what a target aliases) and `measurement`
otherwise. An alias gets no second label. Anything unbindable stays in the details panel with
`ANNOTATION_UNBOUND <id>: <reason>`. Examples: the cube's bare "cạnh bằng 4" names no
segment; curved objects and angles have no registered anchor.

**Presentation, owned by the frontend** (`scene3d-annotations.ts`, `scene3d-view.tsx`).
- Labels are placed per frame beside the projected anchor:
  - the anchor is a segment midpoint, a vertex average, or the point of a pair; there is no
    geometric inference (guard 5D);
  - positions are tried in rings of 6/12/18 px, sides then corners, within 24 px;
  - labels stay inside the canvas and never cover point labels, controls or each other.
- Labels appear only from the step the quantity is available:
  - results from their concluding event;
  - measurements from their measuring event;
  - data from the moment they and their subjects are present.
- Selecting a subject raises the priority of its labels.
- The "Số đo" and "Kết quả" chips sit in the existing header bar (`aria-pressed`), are on by
  default (U-W17-1), and are absent when the scene has no label of that kind.

**Browser results at `99925723`** (`results/BROWSER_EVIDENCE.json`, 6 families × 2 viewports):
- Every label sits ≤ 24 px from its independently projected anchor (the largest distance is
  16.97 px), inside the canvas, with no overlap.
- On desktop, every available label is shown: 5/5 for four families, 3/3 for the cube and the
  cross-section. That still holds after orbit, and after resizing to 70 % width with the
  device at DPR 2. On mobile every available label was shown too, although only the result
  label is required there.
- At every geometry step, forward and backward, the label ids in the DOM equal the oracle:
  72/72 steps over the 12 runs.
- Toggling both chips off and on changes only the labels (12/12). The dash signature,
  rendered objects, camera (within the settle tolerance), selection and step stay the same.
- Neutral → causal → restored ("Bỏ chọn", not "Xem lại toàn hình") returns to the same
  camera, the same scroll position and a byte-identical canvas (12/12). Camera, selection
  and scroll are recorded separately.
- The WebGL renderer keeps pixel ratio 1 at every device DPR; this predates W17. The
  recorded `dpr` is the renderer's own. The DPR check therefore shows that labels are placed
  again after a DPR change, not that the figure renders sharper.

## Final whole-branch self-review (after freeze 1)

The brief allows no subagents, so the author performed the review with `code-reviewer.md` of
`superpowers:requesting-code-review` over the whole branch. It found three Important defects
in `backend/app`:

| # | Defect | What a learner got at freeze 1 |
|---|---|---|
| 1 | The cut-relation reader read the object of "song song/vuông góc với (X)" as the cutting plane: "(Q) qua M và song song với (ABCD) cắt khối chóp …" became "(ABCD) cắt". | A correct parallel-section program was refused with the false message "Đề bài nêu mặt phẳng (ABCD)…". W16 served it. |
| 2 | An identity the gate cannot pin (a text plane with no equation and no point name, a program plane bound to no text plane) was reported as a definite mismatch. | `CONSTRUCTION_NOT_TEXT_BOUND`, cause CONSTRUCTION: the system blamed its own program for something it could not check. |
| 3 | In "… bằng bao nhiêu, biết SA = 5?", the question rule took the ", biết" comma as the clause start and masked the premise. | A valid request was refused with `GIVEN_ONLY_IN_GOAL_CLAUSE` ("chỉ nêu trong yêu cầu"). |

**Fix pass, one pass, red first.**
- `01b0c27c` added the addendum corpus W17C (Q1, Q2, G6, G7), with labels written before the
  fix. It also added the red tests:
  - `test_w17_mat_phang_sau_voi_la_tan_ngu_khong_phai_mat_phang_cat`;
  - `test_w17_mat_phang_cat_khong_ghim_duoc_la_chua_chung_minh_khong_phai_lech_phep_dung`;
  - `test_w17_cau_hoi_ket_bang_biet_menh_de_biet_la_gia_thiet`;
  - `test_w17_cau_hoi_bao_nhieu_biet_van_la_du_kien`.
- `d3817d5f` fixed all three:
  - `_TAN_NGU_VOI` skips the object of "với";
  - a definite mismatch needs both identities known (`mo` vs `loi`);
  - `_MO_BIET` keeps a trailing ", biết …" clause out of the question span.

  The amendment §15.2 carries the dated correction.
- Census round 2 (`3cbe3a1f`): **SHIP**, and 0 of the 163 round-1 rows changed. W17C matches
  its labels: Q1/Q2 are refused `ASSUMPTION_INVARIANCE_UNPROVEN`, and G6/G7 are PROVEN_SAFE C1
  and served.
- Backend fault injections, run 3 (`6d52ab2f`): **23/23** caught. FO2 and FO3 were retargeted
  to the definite-mismatch branches; FO7, FO8 and FG4 are new.
- The full backend run after the fix (`logs/PRE_FREEZE_FULL_BACKEND_d3817d5f.log`) gave 6924
  passed and 12 failures. All 12 are identity or tree-state checks that the refreeze and a
  clean worktree resolve.
- Freeze 2 followed at `d3817d5f` (`921015b6`).

**Deferred minors.**
- A plane named by four or more points ("(MNPQ)") binds only to a `construct_plane` through
  exactly that point set (an over-refusal).
- The served correct-plane caption reads "Mặt phẳng cho bằng phương trình", not "(β)".

## Results

| Check | Result |
|---|---|
| Census round 2 (`diagnostics/ASSUMPTION_MECHANISM_DECISION_W17_R2.json`), 167 rows | **SHIP** (§9 unchanged): 0 PROVEN_SAFE on DEPENDS/MUST_REFUSE, 0 false counterexamples, guards served, metamorphic tests pass; 0 changes against round 1 (`ASSUMPTION_MECHANISM_DECISION_W17.json`, 163 rows) |
| 18 gold rows (AC2), row by row against W16 round 2 | **18/18 unchanged**: PROVEN_SAFE and served (8 C0: n1, n2, p1, p2, p4, p5, p6, p7 · 10 C1: t3, t4, the six family rows, the rigid and rotated rows) |
| Gate changes since W16 round 2 | exactly **one**: A2b (A′) PROVEN_SAFE C0 → UNDETERMINED `CONSTRUCTION_NOT_TEXT_BOUND` |
| W17 corpus (16 rows, labels committed in Task 0) and W17C addendum (4 rows, labels committed with the red tests) | 20/20 as registered |
| Compiler cross-check (C1 rows) | 32 agree / 5 not recognisable / 0 disagree |
| Backend fault injections (`logs/FAULT_INJECTION_W17_R3.log`) | **23/23** caught (run 1: 19/20, FM2 uncaught → test added; run 2: 20/20) |
| Frontend fault injections (`logs/FAULT_INJECTION_W17_FRONTEND_R3.log`, at `99925723`) | **18/18** caught: 16 unit + 2 browser. FH2 was retargeted (`add4afb0` shortened its line); FH3–FH5 cover the restore tolerance. Run 1 (240ecba5) caught 13/15: FE3 was uncaught → test added; FB1 aborted the suite → the toggle polls record a verdict. Run 2 (dbb38b95) caught 15/15 |
| Cache (`diagnostics/PROOF_CACHE_ROW_W17.json`) | **BUMP 108 → 109**: five rows served by dd6e86b0 and refused by W17 (O1, O2, O5, O8, G4) HIT as v108 rows and miss after the bump |
| Ponytail review (`diagnostics/PONYTAIL_REVIEW_W17.json`) | 7 behaviour-neutral cuts applied **before** freeze 1 (`add4afb0`); 3 findings kept on purpose |

## Task 7 — what the browser rounds found

The first real-browser round (4d9eacfb) was red in all six families. Each failure was
classified before any fix (`diagnostics/browser-t7-round1-4d9eacfb/NOTE.md`):

- **Two product defects, fixed in the product:**
  - a crowded base label (S(ABC) between AB = 3 and AC = 4) had all four side positions
    taken and was hidden;
  - the refusal card repeated the backend message.
- **Four measurement defects, fixed in the harness** (dated correction §15.5, no threshold
  changed):
  - the hue census counted the blue "đang xét" border of the selected label as a figure hue;
  - a fill sample sat under the 90 %-opaque area label (min ΔE 2.8);
  - a 1e-14 camera damping difference was compared by bytes;
  - the neutral frame of the causal restore was captured mid-transition, as the cuboid
    mobile diagnostic rerun proved (`diagnostics/browser-t7-diag-cuboid-mobile-4d9eacfb/`).

The confirm round (239efc05) passed 5/6. The last label was half a pixel short of free, which
led to the rings of 6/12/18 px. The rings were verified on that family by the filtered browser
baseline of the frontend fault injections.

## Measurement on the final candidate `d63d6fd4…`

### Attempt 1 at `83f101e4` — failed on one assertion, a harness defect (kept apart)

The attempt passed 11/12 positives, 40/40 negatives and 2/2 served correct planes. The one
red assertion was cube/mobile `causal_restore` = `CANVAS_NOT_RESTORED`: the neutral frame was
`b9c334f7…` and at rest, the restored frame `2090af68…` and not at rest.

The product code and fixtures equalled those of the passing `c5592c1a` run, apart from the
fixtures' identity fields. Two diagnostic runs of the same flow, one under CPU load, passed
with `45e45c71…` at both ends. Their 40-capture series show that at rest, with the same
camera, label boxes, label opacities and scroll, a capture sometimes differs from the at-rest
frame over the whole canvas by at most 1 per 8-bit channel (4 of 160 captures). Comparing
bytes read that capture noise as "not restored". The attempt saved no canvas frames, so its
actual difference is `NOT_RECOVERABLE`. Folder: `diagnostics/browser-final-attempt1-83f101e4/`
(NOTE, evidence, the failing viewport's screenshots, the diagnostic series and patches).

**Harness fix `4e07548e`**, registered in §15.5 before the re-measurement:
- The restored frame equals the neutral one when the bytes match, or when both frames are
  the same size and no channel differs by more than `NHIEU_KHUNG_TOI_DA` = 1.
- Anything larger, a size mismatch, or an unmeasured difference is `CANVAS_NOT_RESTORED`.
- When the bytes differ, the suite saves both frames.

The node test failed against the old library (`logs/RED_CAUSAL_RESTORE_NOISE.log`) and
passes now (60/60). The fault injections FH3–FH5 cover the new check. The candidate is
unchanged.

### Attempt 2 at `99925723` (clean detached worktree) — the authoritative measurement

| Run | Result |
|---|---|
| Identity before measurement | candidate `d63d6fd4…` verify 0; cache lock 109 / b1714b566e25c912 verify 0; tree clean |
| Fixtures | 27, 0 model calls; byte-identical to attempt 1 (same fixture manifest) |
| Browser suite, attempt 2 | **PASS**, 6 families × desktop/mobile:<br>· 12/12 positives (21 assertions desktop, 20 mobile; 23/22 cross-section)<br>· 40/40 negatives, each with its own code and cause<br>· 2/2 served (correct plane, area 16)<br>· every causal-restore pair byte-identical, so the new tolerance was never used; cube/mobile `45e45c71…` at both ends. The cross-section mobile frames did not settle within the window in either attempt, but each pair was byte-identical<br>· 54 runs: 0 raw tokens, 0 console events, 0 uncaught exceptions, 0 failed API calls |
| Section fill | `SECTION_FILL_DISTINGUISHABLE` desktop mean 34.21 / min 34.11 ΔE (34 samples), mobile 34.19 / 33.74 (17), thresholds 20 / 12; pre-close and rewound 0 (≤ 3). `SECTION_FILL_UNDER_EDGES` ρ S-A 0.368 / S-C 0.000 desktop, 0.485 / 0.274 mobile (< 1); edge contrast 42.9 / 66.8 desktop, 35.5 / 49.4 mobile (≥ 12) |
| Occlusion | pass; verdict `HUMAN_REVIEW_PENDING`, 0 failures. Pending: the same four W14-changed scenes as in w15/w16 |
| Playback | 12/12 runs PASS, 5 orbit laps each |
| Builder | 64 crops, endpoints inside, 0 oracle disagreements, 0 duplicate owners. Six sheets with every W15 refusal panel, the W17 panels where declared, the served correct plane, and the toggle-off and causal-restore captures; six filmstrips |
| Frontend fault injections, run 3 (scratch worktree at `99925723`) | 18/18 caught; every source restored byte-identical |

## Measurement on the intermediate candidate `d4a24eba…` (superseded, kept)

The complete acceptance measurement at `c5592c1a` (evidence `f07b0d24`) passed every gate on
the intermediate candidate:
- browser 12/12 + 40/40 + 2/2;
- occlusion `HUMAN_REVIEW_PENDING`;
- playback 12/12;
- builder 64 crops, 0 oracle disagreements;
- T3 `FULL_PRODUCT_GATE_PASS` (pytest 6928/0, vitest 1044/1044);
- identity gates.

Its JSON results and logs are kept unchanged in `diagnostics/evidence-intermediate-c5592c1a/`;
its images are at `f07b0d24`. The final-review fix changes `backend/app`, so these results
describe `d4a24eba…`, not the final candidate.

## Final verification (at `99925723`)

| Gate | Result |
|---|---|
| T3 `frontend/scripts/full-gate.mjs` from `D:/tmp/w17 space/algo-sim` (a path WITH a space) | **exit 0, `FULL_PRODUCT_GATE_PASS`**. pytest **6936 passed / 0 failed**, 1 skipped (deliberate), 2 deselected (opt-in markers), **0 xfailed** (A′ closed); +8 against `c5592c1a`, the final-review tests. vitest **1044/1044** (68 files). Typecheck + build. Thesis demo 5/5 + reduced chain 1/1. Crash surface 6/6, 0 thrown as HTTP 500 |
| Candidate / cache | `freeze_evaluation_candidate.py --verify` exit 0 (`d63d6fd4…`, 109 files); `lock_cache_identity.py --verify` exit 0 (109, `b1714b566e25c912…`) |
| Schema | `export_semantic_program_schema.py` twice: both mirrors `d852b47c…` on both runs, 0 files changed |
| Routing | `CHE_DO_MAC_DINH = "LLM_ONLY"`; `routing.py` unchanged since dd6e86b0; `geometry_compiler` not referenced from `app/ai` or `main.py`; `FIXTURE_TIN_CAY` 0 references in production |
| Model surface | 0 files changed since dd6e86b0 (prompts, grammar card, both schemas, capability table) |
| `git diff --check dd6e86b0..99925723` | exit 0 (captured logs excluded) |
| Node harness | 67 tests: 65 pass, 2 skipped by design (worktree), 0 fail |
| Tree | `git status` 0 before and after (`diagnostics/logs/GATES_99925723.log`) |

## Limitations (not hidden)

- **Operation binding covers section cuts only.** A construction on the wrong entity of
  another kind is still certified when its literals are pinned, for example a midpoint of
  SB where the text says SA. Opened as `ISSUE-ARCH-CONSTRUCTION-RELATION-BEYOND-SECTION-CUT`.
- **Closed vocabulary.** A cut relation outside the three registered phrasings is refused as
  `ASSUMPTION_INVARIANCE_UNPROVEN`, never served. That is an over-refusal, not an error.
  Since the final-review fix, this includes a plane defined by a point and a parallel or
  perpendicular plane (Q1/Q2), which W16 served without any operation check. Recorded as
  `ISSUE-ARCH-CUT-PLANE-BY-POINT-AND-PARALLEL`.
- **Labels the figure does not carry.** There are no on-figure labels for curved objects,
  angles or bare numbers that name no segment (the cube's "cạnh bằng 4"). Those values stay
  in the details panel (`ISSUE-ARCH-ANNOTATION-UNANCHORED-QUANTITIES`).
- **Mobile and resized canvases** guarantee only the result labels. A crowded measurement
  label may be hidden there; it is never misplaced.
- **Causal restore tolerance.** The restored canvas may differ from the neutral one by at most
  1 per 8-bit channel, the measured capture noise. A restore failure that small would pass,
  and no learner can see it. Any larger difference fails, and both frames are saved.
- **The four W14-changed scenes** still need a person (U2), as since w15.
- **"Mặt phẳng cho bằng phương trình".** The served correct-plane caption calls the plane
  this, not (β). Display names for equation planes are not in the W17 brief (deferred
  minor).

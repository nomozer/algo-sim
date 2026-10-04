# Construction binding and focused annotations (w18)

Status: **`READY_FOR_HUMAN_VISUAL_REVIEW`**. Every required gate passes on the final candidate `d3b4cab9…` at the
measurement commit `0ca3accf` (acceptance attempt 2). Human visual review is still `NOT_APPROVED`.
This is automation only; nothing here is `MERGE_READY`.

## Identity

- **Branch and start.** Branch `fix/cuboid-visual-semantic-closure`, start **`0ec2bbbb`** (W17 END). At Phase 0,
  `origin/main` (`a9492ee9`) was fetched and is an ancestor of HEAD; the feature branch has never been pushed; the
  W17 candidate `d63d6fd4` and cache 109 verified before any edit (`diagnostics/logs/PHASE0_REPOSITORY_GATE.log`).
- **Order of work.**
  1. The rules (amendment §16) and the 23 W18 corpus labels were registered first, in `c479f377`.
  2. Then came the Phase 1 reproduction through the production boundary and the red tests (`f3edd903`, `bb9f7004`:
     43 failed / 15 passed, every failure the missing module).
  3. Only then were the fixes made, each red first: binding (`84ce7b70`), presentation data (red `9844f83e` → `f2a040f9`),
     frontend (red `21981005` → `b6868e19`).
  4. Harness, fixtures and fault injections followed (`91f750e6`, `256fdc8e`, `83a0e0c1`, `32f10f69`). Then the cache
     proof and bump, the pre-freeze ponytail review, the pre-freeze full run, ONE freeze, and the measurement.
- **Product commits** (touching `backend/app` or `frontend/src`):
  - `84ce7b70`: construction binding — new `construction_binding.py`, the route stage, learner messages, the refusal
    card's stage label (`frontend/src`).
  - `f2a040f9`: label roles, same-subject merge, exact distance witness, `S(T)`.
  - `b6868e19`: focused labels, one explanation place, the witness layer (`frontend/src`).
  - `1e8c5658`: `CACHE_VERSION` 109 → 110.
  - `7a06ee47`: ponytail cuts, behaviour unchanged; **the last product commit**.
  - `21981005`: red tests (`frontend/src` test files only).
- **Candidate.** `d63d6fd4…` (W17) → **`d3b4cab9…`** (110 files: one new module). It was frozen **once**, at
  `7a06ee47`, in a clean detached worktree (`8caa8307`). There is no intermediate candidate. The two pre-freeze
  browser rounds ran on scratch worktrees with stale identity labels and are diagnostics only
  (`diagnostics/browser-prefreeze-*`).
- **Measurement and evidence.** The measurement commit is **`0ca3accf`**: the freeze commit `8caa8307`, plus the
  harness fix `1d8dfc6f` and records outside the measured paths. Every acceptance run used a clean detached worktree at
  it:
  - `D:/tmp/w18-m2` for fixtures, browser, occlusion, playback and the sheet builder;
  - `D:/tmp/w18 space/algo-sim` (a path with a space) for T3 and the identity gates;
  - `D:/tmp/w18-fe` (scratch) for the frontend fault injections.

  Acceptance attempt 1 at `8caa8307` passed every gate. It is kept apart (`diagnostics/evidence-attempt1-8caa8307/`)
  because the frontend fault injections then found three blind spots of the browser harness (section D). The
  divergence is declared in `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`, a new layer that corrects the w17 one, and
  in the living `CANDIDATE_DIVERGENCE.json`.
- **Cache.** 109 → **110** (`1e8c5658`, proven by rows, below). The bump commit missed the identity lock; it was
  regenerated in `5cfb53a1` (version only). The provider fingerprint is unchanged (`b1714b566e25c912…`); the model
  surface is untouched (0 files of prompts, grammar card, schemas or capability changed since `0ec2bbbb`).
- **Model calls.** `DEFAULT_MODE = LLM_ONLY`. Every run of this wave made 0 model calls.

## Phase 1 — the gap reproduced before any fix

`diagnostics/reproduce_construction_binding.py` ran every W18 corpus row through the production boundary
(`run_pipeline`, frozen analyze/program stages, 0 model calls) and saved, per row, the source, contract, program,
the relation the text requires, the point constructions executed, the certificate and the envelope
(`diagnostics/CONSTRUCTION_BINDING_REPRODUCTION_bb9f7004.json`; `…_f3edd903.json` is an earlier, superseded run
whose two outside-scope rows never reached the route).

Before the fix (`bb9f7004`), on the gold p1 text ("…khối chóp S.ABCD … đáy ABCD là hình vuông … S(0;0;6)"):

| Row | Text says | Program does | Before |
|---|---|---|---|
| B5 | "M, N lần lượt là trung điểm của SA, SB" | M ↔ SB, N ↔ SA | **served**, 3√6 where the correct value is 9 |
| B7 | "Gọi M là trung điểm của SA. Tính độ dài đoạn MC." | builds midpoint(S, A) as `X`, never M | **served** (value right, entity wrong) |
| B9 | "H là hình chiếu của S lên (ABCD). M là trung điểm của SH." | M = midpoint(S, A); H coincides with A | **served** (same coordinates, other entity) |
| B11 | "H là hình chiếu vuông góc của S lên đường thẳng BD" | projects onto BC | **served**, 6√2 where the correct value is 3√6 |
| B13 | "H là hình chiếu vuông góc của A lên mặt phẳng (SBD)" | projects onto (SBC) | **served**, 3√2 where the correct value is 2√3 |
| B2 | "M là trung điểm của SA" | midpoint(S, B) | refused only by the coordinate invariant, stage `source_invariant`, cause **UNKNOWN** |
| B4 | "M là trung điểm của SB", distance to (ABCD) | midpoint(S, A): the distance is 3 either way | refused only by the coordinate invariant, stage `source_invariant`, cause **UNKNOWN** |

**Root cause (producer → consumer).** The model's program (producer) names the operands of each point construction.
Every consumer before W18 asked *where* a point is, never *which point of the text* it is. Coordinate invariants check
positions; the W15 certificate checks literals; the W17 check covers `construct_section` only. So a determined point
built on other entities, renamed, or bound to a same-coordinate twin passed every gate unless its coordinates broke a
text invariant. The text's projection relations and "lần lượt" lists were read by no server reader at all.

## A — construction binding (§16.1–16.4)

**Fix.** `construction_binding.py` (new, `84ce7b70`), at the authority boundary:
- `doc_quan_he_dung` reads the midpoint (single and "lần lượt", paired in order, counts must match) and
  projection/foot relations on the goal-masked text, with a closed vocabulary; a target stated twice differently is
  dropped.
- `doi_chieu_phep_dung` resolves program names to text identities through the existing authorities (aliases,
  `assumption_gate._khoa` for A′/A'/A_prime, labels, the fact source, the C₁a reconciliation) — never through
  coordinates or values — and classifies every point construction: MATCHED, MISMATCHED, UNVERIFIED, AUXILIARY,
  OUT_OF_SCOPE (and NOT_REALIZED for an unbuilt relation).
- Route stage `construction_binding`, after execution and before `source_invariant` (the coordinate invariant stays as
  a second net). MISMATCHED is refused in every scope with `CONSTRUCTION_NOT_TEXT_BOUND`, cause CONSTRUCTION, and
  `reason_subjects` = [the text's relation, the built relation] in learner notation. UNVERIFIED is refused inside the
  polyhedral scope (U3) with `CONSTRUCTION_BINDING_UNVERIFIED`, cause UNKNOWN, never sent to repair; outside it the
  status is recorded. An internal error counts as UNVERIFIED.
- Learner messages: the mismatch names both relations and says the text needs no fix; the unverified message says the
  system could not check the construction — "Đây là giới hạn của hệ, không phải lỗi của đề".
- Provenance: a constructed point carries `source.binding` = `TEXT_RELATION` (MATCHED) or `AUXILIARY` (engine point,
  never a given).

**After (`84ce7b70`, same boundary, `CONSTRUCTION_BINDING_REPRODUCTION_84ce7b70.json`):**
- the seven MUST_REFUSE rows that reach the route (B2, B4, B5, B7, B9, B11, B13) are refused at `construction_binding`,
  cause CONSTRUCTION, both relations named;
- every INVARIANT row is served, except B16 ("Gọi M là điểm chính giữa của đoạn SA", correct program), refused as
  UNVERIFIED by design — an over-refusal with a truthful message;
- B18/B19 (primed names) stop at the pre-existing scope gate, which has no clue for "độ dài"
  (`ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE`, outside the brief); at route level they behave as labelled.

**Census** (`diagnostics/CONSTRUCTION_BINDING_DECISION_W18.json`, registered SHIP rule §9 unchanged, run on W14, W15,
W15B, W16, W16B, W17, W17C and W18 corpora): **SHIP**; AC2 gold 18/18 PROVEN_SAFE; no served row of any earlier corpus
refused; the only route change is W15 `oov:chia_doan_canh`, already refused at `assumption`, now refused earlier as
UNVERIFIED; the 23 W18 rows match their registered expectations (9 refused at `construction_binding`: the 8
MUST_REFUSE rows and B16; route level); compiler cross-check 32 agree / 5 not recognizable / 0 disagree. Claim
wording: 0 violations on the measured corpus within the registered scope, not a general proof.

**Rulings during the implementation** (dated corrections in §16.3, registered before any measurement):
- a recognized non-W18 role (centre, centroid, orthocentre, intersection, symmetric point) is OUT_OF_SCOPE whatever
  operation builds it;
- a receiver through a non-text point, an equation plane or a derived line is unpinned ⇒ UNVERIFIED, while a midpoint
  endpoint or projection source that is a non-text entity is MISMATCHED;
- a text vertex the text does not introduce and that has no W18 relation is layout (W15 certificate), OUT_OF_SCOPE here.

## B — focused labels and one explanation place (§16.5–16.6)

- **Backend data** (`f2a040f9`): `annotation.role` (given / intermediate / result); a measured duplicate of a given
  keeps its annotation with `same_as` (W17 dropped it) — merged by subject, never by value; the asked result never
  merges (two roles, two labels); `S(T)` for a section area named by the text (server cut reader).
- **Default:** point names and given data. **Selected quantity** (label click/Enter/Space, solution row, or the object
  it measures): its label plus its numeric chain (`tangNhanManh`). **"Hiện tất cả"** (one chip, replacing the W17
  "Số đo"/"Kết quả" pair): every available label. Availability is unchanged: nothing shows before its step, in every
  mode; there is no fixed label count; a crowded label hides and its value stays in the inspector and the solution.
- **One explanation place:** the inspector (`geo3d-soi`, right on desktop, below the figure on mobile) holds the
  selected quantity's formula, "Từ dữ kiện đề cho" and "Tính trực tiếp từ". The full solution is collapsed by default
  ("Xem lời giải đầy đủ"); while it is open the inspector drops its formula. Kết quả rows carry `symbol = value`.

## C — distance witness (§16.7)

A point-to-line or point-to-plane distance carries `annotation.witness = {from, foot, on, marker {u, v}}`; the foot is
computed exactly by `kernel.project_point_onto_line/plane`. The label anchors at the midpoint of point–foot. The
frontend draws the dashed segment and the right-angle mark only while that label shows, scales the two backend
directions to a fixed glyph, and computes no foot (5D guard). No geometry-timeline step is added. Distances between two
non-point objects have no witness and no on-figure label (declared).

## D — browser-harness blind spots found by fault injection (Task 7)

The frontend fault injections run 1 at `8caa8307` caught all 8 unit injections, but only 1 of the 4 browser ones. Each
miss was reproduced and traced before anything changed (`diagnostics/logs/FAULT_INJECTION_W18_FRONTEND.log`,
`diagnostics/logs/DIAG_FW2_8caa8307.log`). The product was right in all three cases, and its unit tests caught each
fault; the harness could not see them.

| Injection | Root cause in the harness | Fix (`1d8dfc6f`, red first) |
|---|---|---|
| FW1, a highlighted hidden edge drawn solid | the dash comparison ran only in the causal state, where the selected quantity highlights no edge owner | every formation step: each span classified HIDDEN must be drawn dashed (`assessDashFollowsSpans`, `DASH_DIFFERS_FROM_OCCLUSION`); the highlighted hidden owners are recorded |
| FW2, the chip rewinds to step 0 | the isolation reference was the state after the first toggle; then the suite threw `CAUSAL_TARGET_NOT_CLICKABLE` and wrote no evidence | the reference is the state before the first toggle; a throwing positive run is recorded as FAIL with its cause and the suite still writes its evidence |
| FW4, two regions carry a formula | no result with a referenced formula was ever selected while the solution was open | such results are also selected with the solution open (`detail_region_open`) |

`diagnostics/logs/RED_W18_HARNESS_FIX.log` shows the two new node tests failing for the stated reasons. After the fix the
node harness passes 72/72 in the main tree. Amendment §16.8 carries the dated corrections, written before re-measuring.

The attempt-2 evidence then showed that only `cross_section` highlights a hidden edge during formation (A-B, A-D, S-A).
In the other five families the highlight rule is held by the unit test only, so FW1 was moved to `cross_section`
before run 2 (`b5ab4656`).

## Results (final candidate `d3b4cab9`, measurement `0ca3accf`)

| Gate | Result |
|---|---|
| T3 `full-gate.mjs` from `D:/tmp/w18 space/algo-sim` | **exit 0, `FULL_PRODUCT_GATE_PASS`**: pytest **7001 passed / 0 failed**, 1 skipped (deliberate), 2 deselected (opt-in), 0 xfailed; vitest **1058/1058** (68 files); typecheck + build; thesis demo 5/5 + reduced chain 1/1; crash surface 6/6, 0 thrown as HTTP 500; git status 0 before and after |
| Identity gates (`diagnostics/w18_gates.sh 0ca3accf 0ec2bbbb`) | candidate `d3b4cab9` verify 0; cache lock 110 / `b1714b56` verify 0; schema export ×2: both mirrors `d852b47c…`, byte-identical, 0 files changed; `CHE_DO_MAC_DINH = "LLM_ONLY"`; compiler not wired; no production `FIXTURE_TIN_CAY`; 0 model-surface files changed since `0ec2bbbb`; `git diff --check` clean (captured logs excluded); node harness 70 pass + 2 skipped by design (worktree), 0 fail |
| Browser suite, 6 families × desktop 1440×900 / mobile 390×844 (10:00:21Z–10:10:20Z) | **PASS**: positives **12/12**; negatives **46/46** (W15 `ungrounded_source`, `assumption`, `topology_kernel` 12 each; W17 `system_cause` 2, `construction_mismatch` 2; W18 `point_construction_mismatch` 2, `projection_mismatch` 2, `construction_unverified` 2), each with its own code and cause; served **6/6** (W17 correct plane; W18 midpoint witness "3" and projection "3√6", witness drawn) |
| W18 label checks | compact default = given labels (oracle) **12/12**; per-step labels = oracle **72/72**; per-quantity selection **58/58** (selected label shown with its chain, the rest per the oracle); one region carrying the formula **10/10** with the solution collapsed and **10/10** with it open (the selections whose formula has references); witness drawn exactly for the shown distance labels 2/2 on selection + 2/2 under "Hiện tất cả"; "Hiện tất cả" on → off → on, measured against the state before the first toggle, **12/12** (dash signature, rendered objects, camera, step, selection unchanged); 270 anchors measured, max **16.97 px** (≤ 24); labels after orbit 12/12, after a resize to 70 % width 6/6 |
| Dash under highlight | every formation step **72/72**: each span classified hidden is drawn dashed. A hidden edge is highlighted only in `cross_section` (A-B, A-D, S-A, both viewports); the other five families highlight none, so there the rule rests on the unit test |
| Earlier checks kept | causal restore 12/12 at the same camera and scroll: 11 pairs byte-identical; one pair (triangular-prism/mobile) differs by at most 1 per 8-bit channel (48 943 pixels), inside the capture-noise tolerance registered in w17 §15.5, and both frames are saved; formation forward/backward; 0 raw tokens, 0 console events, 0 uncaught exceptions, 0 failed API calls |
| Section fill | `SECTION_FILL_DISTINGUISHABLE` mean/min ΔE 34.20/34.11 desktop, 34.19/33.74 mobile (thresholds 20/12); pre-close and rewound max 0.00 (≤ 3); `SECTION_FILL_UNDER_EDGES` rho 0.138/0 desktop, 0.485/0.274 mobile (< 1), edge contrast 35.5–66.8 (≥ 12) |
| Occlusion | pass, verdict `HUMAN_REVIEW_PENDING`, 0 failures; the same four W14-changed scenes as w15–w17 (U2), product = oracle on every state |
| Playback | 12/12 runs, Play pressed once, five orbit laps each |
| Sheet builder | exit 0; 64 crops, endpoints inside, 0 oracle disagreements, 0 duplicate owners; six sheets, six filmstrips |
| Backend fault injections | run 3 at `8caa8307`: **12/12 caught** (FB1–FB8 binding/route/message, FA1–FA4 annotations); baseline 93 passed before and after. Run 1 (`256fdc8e`) caught 11/12 — FA4 (merge by equal value) slipped through because its guard used the asked result, which never merges; the guard moved to an intermediate measurement (`83a0e0c1`) and run 2 caught 12/12 |
| Frontend fault injections | run 2 at `0ca3accf` (scratch worktree `D:/tmp/w18-fe`): **12/12 caught** — unit FE1–FE8 8/8 (result too early, all labels on by default, label on the wrong subject, two formula copies, selection without its chain, a second row for a `same_as` measurement, solution open by default, labels hidden from assistive technology); browser FW1–FW4 4/4 (`DASH_DIFFERS_FROM_OCCLUSION` on `cross_section`, `SHOW_ALL_OFF_CHANGED_STEP`, `WITNESS_NOT_SHOWN_LABEL`, `DETAIL_REGIONS_2`); the filtered baselines carry none of the predicted codes; every source and the run filter restored byte-identical. Run 1 at `8caa8307`: unit 8/8, browser 1/4 (section D) |
| Focused suites (before the freeze) | `test_construction_binding.py` 58/58; scene annotations, visual evidence and binding 96/96; vitest geometry 583/583; `tsc -b` 0 |

The brief's minimum fault-injection list maps to: SA→SB with the same value = FB1 (+ B4); target changed with the same
coordinates = FB2/FB3; binding check removed = FB4; label on the wrong subject = FA1 and FE3; result too early = FE1;
all labels on by default = FE2; two duplicate detail panels = FE4/FW4; highlight turning dashed lines solid = FW1.

## Cache (proof by rows)

`diagnostics/proof_cache_row_w18.py` stored real envelopes of the W17 candidate under 109 in a temporary sqlite and
replayed them: six requests served before W18 and refused by W18 — B5, B7, B9, B11, B13, B16 — HIT under 109 and MISS
after a simulated bump (`PROOF_CACHE_ROW_W18.json`). Decision: **BUMP 109 → 110** (`1e8c5658`, every pin in one
commit; the lock in `5cfb53a1`).

## Measurement attempts

Listed in `diagnostics/MEASUREMENT_ATTEMPTS.json`. In short:
- **Pre-freeze browser rounds.** Round 1 at `91f750e6` failed cuboid (`SOLUTION_LAYER_OUT_OF_SYNC` ×4,
  `STRUCTURED_REFERENCE_NOT_RENDERED` ×4): the harness oracle did not know `same_as`. It was fixed in the harness
  (`32f10f69`), product unchanged. Round 2 at `32f10f69` passed 6/6. Both are kept as diagnostics.
- **Pre-freeze full backend** at `7a06ee47`: 6985 passed, 16 failed, all classified:
  - 12 stale candidate/divergence identity checks;
  - 3 cache-lock checks (lock regenerated in `5cfb53a1`);
  - 1 missed fixture-count pin (`72be45ce`).

  All 16 were green after the fixes.
- **Acceptance attempt 1** at `8caa8307`: every gate passed. It is superseded by the harness fix of section D and kept
  apart (`diagnostics/evidence-attempt1-8caa8307/`).
- **Acceptance attempt 2** at `0ca3accf`: every run passed at its first attempt (below). The fixtures are
  byte-identical to attempt 1's.

## Limitations (declared, not hidden)

- **Vocabulary.** Only midpoints and projections/feet are bound; a correct construction phrased outside the closed
  vocabulary is UNVERIFIED (refused in U3); centres, centroids, intersections and symmetric points are OUT_OF_SCOPE
  (`ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY`).
- **Receivers by name.** A line or plane is identified by its named points; a correct receiver named through other
  points of the same line or plane is MISMATCHED (over-refusal, never a wrong answer).
- **Scope gate.** "Tính độ dài đoạn MC" with no other clue stops at the scope gate (`ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE`).
- **Witness.** Point-to-line/plane only; drawn on top (not occlusion-classified); the served witness case names the
  base plane "(ABC)" where the text says "(ABCD)" (display names, `ISSUE-ARCH-ANNOTATION-UNANCHORED-QUANTITIES`).
- **Dash under highlight in the browser.** Only `cross_section` highlights a hidden edge during formation. In the
  other five families the rule "a highlight never turns a dashed line solid" is held by the unit test
  `scene3d-hidden-lines.test.tsx`, not by browser evidence.
- **Value line.** For a result whose payload formula has no references ("S(T) = 9", "d(S, BD) = 3√6"), the inspector's
  line repeats the Kết quả row while the solution is collapsed (§16.5 keeps the value in the inspector on purpose);
  the one-region check covers referenced formulas only (10 of 58 selections). Raised as W18-H2.
- **Human review.** Nothing here is a visual approval; the four W14-changed scenes remain `HUMAN_REVIEW_PENDING`.

## Deferred minors (final self-review)

- the "một điểm phụ" fallback in a mismatch message can be glued to another symbol ("một điểm phụA");
- a relation whose target is declared as a literal is neither checked nor recorded NOT_REALIZED (backstops: the
  coordinate invariant, the W15 certificate);
- `_xuat_xu_hien_thi` recomputes the binding the route already computed (cost only);
- `IconFlag` has no user since the "Kết quả" chip was removed (waits for the next frontend change).

## Skills

Invoked in this wave: superpowers:writing-plans (`C:/Users/Bunny/.claude/plans/w18-binding-focus.md`) ·
superpowers:executing-plans (inline, ledger and rulings) · superpowers:test-driven-development (red first for every
product and harness change) · superpowers:systematic-debugging (Phase 1, the pre-freeze round 1, FA4) ·
andrej-karpathy-skills:karpathy-guidelines · impeccable (Operate mode, refinement of the explorer) ·
ponytail:ponytail-review (before the freeze; `diagnostics/PONYTAIL_REVIEW_W18.json`) ·
superpowers:verification-before-completion (before the handoff). Applied manually: code-reviewer.md of
superpowers:requesting-code-review as the final whole-branch self-review (no subagent: the brief requires one agent).

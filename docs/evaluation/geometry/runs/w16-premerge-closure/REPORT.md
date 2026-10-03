# Pre-merge soundness and visual evidence closure (w16)

Status: **`READY_FOR_HUMAN_VISUAL_REVIEW`**. Every required gate passes on the final
candidate. Human visual review is still `NOT_APPROVED`. This is automation only; nothing
here is `MERGE_READY`.

## Identity

- **Branch and start.** Branch `fix/cuboid-visual-semantic-closure`, start **`8a339d17`**.
  `origin/main` is `a9492ee9` (fetched at Phase 0: equals `ls-remote`, ancestor of HEAD, the
  feature branch never pushed). 20 commits up to the evidence, plus the documentation
  commit.
- **Order of work.** The rules (amendment §14) were registered first, in `6ed110f6`. Then
  came the red tests, `6d015112`, and the Phase 1 probe at the red commit, `dea0ad91`. Only
  then were the fixes made.
- **Product commits** (touching `backend/app` or `frontend/src`):
  - `24161657`: plane binding.
  - `93d4ec69`: goal clauses.
  - `29da8e5a`: fill order, `frontend/src`.
  - `2ec02b3a`: `CACHE_VERSION`.
  - `6b120036`: primed plane names, the last product commit.
  - `6d015112` adds a `frontend/src` test file.
- **Candidate.** `b3b7eb79…` (W15) → `8d14469b…` → **`9bb0aaa7…`** (107 files). It was frozen
  **twice**, each time in a clean detached worktree:
  - freeze 1 at `2ec02b3a` gave the intermediate candidate `8d14469b`. No acceptance
    evidence was measured on it.
  - freeze 2 at `6b120036` gave `9bb0aaa7`.

  The measurement commit is **`7f3658b0`** and the evidence commit is **`705970dd`**. The
  divergence is declared in `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json` and in the living
  `product-response-contract-alignment/CANDIDATE_DIVERGENCE.json`.
- **Cache.** `CACHE_VERSION` 107 → **108**, bumped once (`2ec02b3a`) on real rows
  (`diagnostics/PROOF_CACHE_ROW_W16.json`). Twelve requests served before W16 are refused
  now, and they would HIT as v107 rows. The provider fingerprint `b1714b566e25c912` is
  unchanged.
- **Unchanged.** The model surface (prompts, grammar card, contract, capability table, both
  schemas) is unchanged. `DEFAULT_MODE = LLM_ONLY`. There were 0 live Gemini requests and 0
  application LLM calls.

## Phase 1 — every risk reproduced before any fix

All rows ran at the RED commit `6d015112` with 0 model calls
(`diagnostics/PROBE_W16_PHASE1_6d01511.json`). The corpus (`diagnostics/assumption_corpus_w16/`)
was labelled before the fixes it judges. Rows that could not be exploited are kept as well.

### A — plane-equation entity binding

**Root cause.** The C0 role of a `construct_plane_from_equation` literal was "proportional
to *some* plane equation in the text". `plane_equation.bat_bien_mat_phang` emits the
invariants with no entity: they back a product postcondition ("a proportional plane
exists"), which says nothing about *which* plane. So the certificate treated equal numbers
as the same entity.

| Probe | Before W16 | After W16 |
|---|---|---|
| A1: (β) given (α)'s equation; β not determined by the text | C0, **served** (area 9) | refused at `assumption` (`PLANE_BINDING`) |
| A2: (α) and (β) equations swapped | C0, **served 9**; the text's (T) area is 16 | refused at `assumption` |
| A6: unnamed program plane carries (α)'s equation; β undetermined | C0, **served** | refused at `assumption` |
| A6b: unnamed program plane, the text mentions two planes | C0, **served** | refused at `assumption` |
| A7: unnamed program plane, two named text planes | C0 (gate unsound); the route refused at `source_invariant` | gate `UNDETERMINED`; still refused at `source_invariant` |
| A8: unnamed program plane, second text plane unnamed | C0, **served** | refused at `assumption` |
| A9 (W16B, self-review): `mp_P_prime` carries (P)'s equation; the text gives (P): z = 3 and (P′): z = 2 | added at the RED commit `2dc55f1b`, after the first W16 binding: C0, area 9 where the text gives 16 | refused at `assumption` |
| Valid: correct counterpart of the swap, ratio ≠ 1, negative ratio, consistent renames (P) and (γ), unique unnamed plane, unnamed variable with one text plane, a text that also names (ABCD) by its points | 8/8 C0, served | 8/8 C0, served |
| A9b (W16B): `mp_P_prime` carries (P′)'s own equation | at `2dc55f1b`: `UNDETERMINED` (over-refusal) | C0, served |
| A2b: (T) cut by a correctly pinned (α) where the text says (β) | C0, served | C0, served — **declared limit A′** |

**Fix** (`24161657`, `6b120036`):
- `plane_equation.doc_mat_phang_de` reads each fully read text equation with the name written
  in its clause (`(α): …`, `(P) có phương trình …`) and its span.
- `assumption_gate.gan_mat_phang` binds a program plane to exactly one text plane in one of
  two ways:
  - **by name**, through `ten_mat_phang_cua_bien`: a closed Greek transliteration table or a
    capital letter. A written prime, or a following `_prime`/`_phay` token, is part of the
    name.
  - **as unique by counting**: the text mentions planes once and the program builds one
    equation plane.

  The coefficients must then be proportional. Equal numbers never bind, and an unbound
  literal has no role (detail `PLANE_BINDING`).
- The product invariant and its postcondition are unchanged.

### B — premise versus goal

**Root cause.** Every certificate premise was read from the whole `problem_text`. In *"Chứng
minh rằng SA ⊥ (ABC)"*, the shape reader saw `SA ⊥ (ABC)` exactly as it sees a hypothesis,
so the goal became a C1 premise.

| Probe (same solid and data) | Before W16 | After W16 |
|---|---|---|
| B1 `Chứng minh rằng SA ⊥ (ABC)` · B1b `CMR` · B2 `chứng minh tam giác … vuông` · B3b `Kiểm tra …` · B3c `… hay không?` · B5 hypothesis + request in one sentence · B7 `Chứng minh rằng SA = 5` | C1, **served** (7/7) | 7/7 refused at `assumption` (`GOAL_CLAUSE`) |
| B0 relation stated as a hypothesis · B4b negation inside the request · B5b hypothesis before the request in one sentence · B6 `Tính …, biết <hypothesis>` | C1, served | C1, served (4/4) |
| B3 question about the relation · B4 negated hypothesis | refused (not exploitable) | refused |
| B6b `Tính …, biết chiều cao bằng …` | refused (`UNDETERMINED`, over-refusal) | refused (same) — vocabulary limit, never `DEPENDENT` |

**Fix** (`93d4ec69`):
- `shape_constraint.khoang_muc_tieu` marks goal clauses:
  - from `chứng minh`, `chứng tỏ`, `CMR`, `kiểm tra` or `hỏi` to the end of the clause;
  - any clause that ends in `?`.

  Matching runs on an NFC copy, cluster by cluster, because the product does not normalise
  the text.
- `che_muc_tieu` blanks those spans and keeps the length, so every reader's span still points
  into the original text.
- Every premise (constraints, text invariants, plane equations) is read from the masked text.
- A constraint read only inside a goal still blocks the counterexample. A text with a goal
  never yields one (`CE_GOAL_CLAUSE_PRESENT`). Without that rule, a length given only inside a
  goal would be reported as "đề không cho".

### C — the four fail-closed guards

These are the branches the issue names, taken from `kiem_gia_dinh`, not guessed. Each is
triggered from a **valid** T1 spec, and each has a valid counterpart that stays C1
(`test_w16_doi_chung_bon_nhanh_la_C1`).

| Branch | Trigger | Gate | Route |
|---|---|---|---|
| `CLOSURE_UNSUPPORTED_KIND` | a no-op `if` | `UNDETERMINED`, `ASSUMPTION_INVARIANCE_UNPROVEN`, detail exactly `CLOSURE_UNSUPPORTED_KIND control flow` | refused at `assumption` |
| `TEMPLATE_CONSTRAINT_VIOLATED` | S moved off the normal at A | same code, `T1 TEMPLATE_CONSTRAINT_VIOLATED apex edge ⊥ base` | refused earlier, at `source_invariant` |
| `FRAME_DEPENDENT` | `(P): z = 2` on a C1 slice (the text gives it) | same code, `FRAME_DEPENDENT construct_plane_from_equation` as the only failure | refused at `assumption` |
| `FORMATION_REJECTED` | a two-vertex face | same code, detail exactly `FORMATION_REJECTED` | refused at `formation` (`SOLID_TOPOLOGY_MALFORMED`) |

All four fired before W16 too: no defect, only missing tests. Fault injections FG1–FG4 delete
one branch each and turn exactly its test red.

## Results

**Census round 2** at `7695b967` (`diagnostics/ASSUMPTION_MECHANISM_DECISION_W16_R2.json`;
W14 + W15 + W15B + W16 + W16B, 147 rows):
- **SHIP.** The §9 rule is unchanged.
- **AC2: 18/18 `PROVEN_SAFE`** (8 C0, 10 C1), all served. AC1 3/3 `DEPENDENT`, adversarial
  6 `DEPENDENT`/`UNDETERMINED`, as in W15.
- **No status change on W14 + W15 + W15B (111 rows)**, either against W15 round 3 or against
  W16 round 1. The compiler cross-check gives 32 agree / 5 not recognisable / 0 disagree.
- **W16 + W16B (36 rows):**
  - 0 `PROVEN_SAFE` on DEPENDS/MUST_REFUSE outside the declared limit A2b;
  - 0 `DEPENDENT` on INVARIANT;
  - 0 expectation mismatches.
- **Valid cases now refused: 0.** Three INVARIANT rows are refused, and each was refused
  before W16 as well:
  - B6b: vocabulary limit.
  - `C_CLOSURE_UNSUPPORTED_KIND` and `C_TEMPLATE_CONSTRAINT_VIOLATED`: guard triggers, refused
    by design.

  No served valid case was lost, and none was a new regression.
- **Fault injections.**
  - Backend, at `7695b967`: **13/13 caught**, baseline 380 passed, 1 xfailed:
    - FG1–FG4: the four guards.
    - FA1–FA4: the plane binding. FA1 restores the W15 "any proportional equation" rule;
      FA3/FA4 cover the two sides of the primed name.
    - FB1–FB3: the goal masking, the goal block on counterexamples, and NFD matching.
    - FD1–FD2: the builder accepting a blank or a missing refusal panel.
  - Frontend, at `cd3a0efa`: **4/4 caught** (FL1 fill order; FH1–FH3 the under-edges
    assessor). Sources were byte-restored.
- **Strict xfails:** 1, the declared limit A′, which carries its issue id.

## Section fill and the solid edges

- **Root cause.** At render order 10 (W15), the fill was drawn after every line. It is not
  depth-tested, so it laid amber over every solid edge crossing the section on screen. In the
  W15 frame, S-A and S-C read brown.
- **Fix** (`29da8e5a`). The fill moves to `THU_TU_TO_THIET_DIEN = 7`: after the solid and
  plane surfaces (0), before every transparent line (8). The canonical solid edges are
  transparent-queue lines, so they now draw over the fill.
- **Unchanged:** occlusion classification, visible/hidden passes, dash policy, opacity 0.45,
  no depth write or test, not an occluder, and the fill appearing only from the closing step.
- **Sampler.** It now excludes `margin_px` around every projected solid edge and vertex marker,
  which is exactly the §11 sentence. W15 excluded only the polygon's own edges.
- **Gates.**

| Gate | Desktop | Mobile | Registered |
|---|---|---|---|
| `SECTION_FILL_DISTINGUISHABLE`, closed: mean / min ΔE | 34.20 / 34.11 (38 samples) | 34.19 / 33.74 (21) | `T_ON 20` / `T_ON_MIN 12` |
| pre-close (from the cutting-plane step) and rewound: max ΔE | 0 | 0 | `T_OFF 3` |
| `SECTION_FILL_UNDER_EDGES`, ρ (S-A / S-C) | 0.138 / 0 | 0.485 / 0.274 | < 1 |
| edge contrast with the fill off | 58.7 / 66.8 | 35.5 / 49.4 | ≥ `T_ON_MIN` 12 |

- **How the under-edges check works.** It compares the darkest fill-off pixel within ±1 CSS
  px of each solid edge crossing the region with the median ΔE at ±4 px:
  - ρ < 1 means the edge covers part of the fill;
  - the contrast term means the edge is actually drawn;
  - no crossing edge is `NOT_APPLICABLE`, never a pass.

  The W15 thresholds are unchanged. The ρ range in §14.4 was corrected to its computed values
  in a dated note *before* measuring. The rule itself did not change.
- **Limit.** three.js draws the whole opaque queue first. So opaque lines (an auxiliary
  segment's solid part, the section outline) still lie under the fill wherever they cross it.
  None does in the six scenes (`ISSUE-ARCH-SECTION-FILL-OPAQUE-AUXILIARY-LINES`).

## Refusal panels of the sheets

- **Root cause.** The builder read the W12 shape `negative[viewport]`. Since W15 the suite
  records `negative[kind][viewport]` (three kinds). The builder therefore iterated the kinds
  as if they were viewports, found no screenshot, and printed three captions over blank cells
  in every W15 sheet (`w15-assumption-closure/results/HIDDEN_EDGE_CROPS.json`: `path` and
  `crop_box_px` null; the W14 sheets still had both refusal images). Its own test encoded the
  dead shape, so it stayed green. The source images were correct; the defect was in the
  assembly step.
- **Fix** (`1d782bd8`). The builder now reads the real schema and lays out the three kinds ×
  desktop/mobile with closed Vietnamese captions. Each panel must pass all of these:
  - be the record's own `<family>/negative/<kind>/<viewport>/refusal.png`;
  - come from a passing record with no canvas and a learner message;
  - show ink (≥ 0.5 %) in the box of the learner message, recorded by the suite as
    `refusal_message_box`.

  An unknown kind raises `KeyError`. A missing, wrong, blank or unreadable panel raises
  `ThieuAnhBangChung`, and so does a missing filmstrip step. The blank-cell code is deleted.
- **Valid no-canvas versus blank capture.** A valid refusal is a passing no-canvas record with
  ink in its message box. A blank capture has no ink there and fails.
- **Result.** 6 sheets × 6 panels, all read from their own files. The white band under a
  desktop panel is the row height of the taller mobile capture, not a missing image.

## Measurement

`diagnostics/MEASUREMENT_ATTEMPTS.json` lists every run, including failed and superseded
ones.

1. **Pre-freeze at `cd3a0efa`.**
   - Backend: 6834 passed; 11 failed, all expected (10 stale candidate identity, 1 dirty
     tree) and listed by node id.
   - Vitest 1018/1018; build exit 0; demo 5/5; schema ×2 identical.
   - Correction: the extract's header time is wrong. The run finished at 10:42:21Z, and the
     full console is added beside the extract.
2. **FREEZE-1** at `2ec02b3a`, giving `8d14469b`.
3. **BROWSER-1** at `55cde06e`: **FAIL**, cross-section only (0 section-fill samples). A
   harness defect: the W16 page code declared `const doc` after the shared PNG prelude, which
   already declares `doc`. The page threw a SyntaxError, and the pairs came back undefined.
   - It was fixed test-only in `85e73394`. The page code is now built by `maDocCapDiem`, and a
     node test compiles it: RED → GREEN.
   - The attempt is kept apart in `diagnostics/browser-attempt1-55cde06e/`.
4. **Pre-evidence self-review** (the brief allows no subagents). It found one Important
   hole: `ten_mat_phang_cua_bien('mp_P_prime') = {P}`, so (P′) could carry (P)'s equation
   and C0 certified it.
   - RED `2dc55f1b`; W16B corpus at the red commit; fix `6b120036`.
   - Then fault injections FA3/FA4 and census round 2 at the fix.
5. **FREEZE-2** at `6b120036` (`9bb0aaa7`), then the evidence at `7f3658b0` in a fresh
   worktree: identity verify → fixtures → suite → occlusion → playback → builder.

## Final verification (at `7f3658b0`)

| Gate | Result |
|---|---|
| T3 `full-gate.mjs` from a path WITH a space | **exit 0, `FULL_PRODUCT_GATE_PASS`**. pytest **6854 passed / 0 failed**, 1 skipped (deliberate), 2 deselected (opt-in markers), 1 xfailed (strict, limit A′). vitest **1018/1018** (67 files). Typecheck + build. Thesis demo 5/5 + reduced chain 1/1. Crash surface 6/6, 0 thrown as HTTP 500 |
| Browser suite, 6 families × desktop/mobile (exit 0) | 12/12 positives served (formation, causal, orbit, immutable frames, labels, solution panel); 36/36 negatives refused, each kind with its own code and a learner message, no canvas, no answer. Over 48 runs: 0 raw tokens, 0 serious console errors, 0 uncaught exceptions, 0 failed API calls, no overflow |
| Occlusion (exit 0) | pass, verdict `HUMAN_REVIEW_PENDING`, 0 failures. Pending (U2 of w15): triangular pyramid, triangular prism, rectangular pyramid, cross-section — the same four scenes as w15 |
| Learner playback (exit 0) | 12/12 runs × 19/19 checks, 5 orbit laps each |
| Builder (exit 0) | 64 crops, endpoints inside, 0 oracle disagreements, 0 duplicate owners; six complete sheets, six filmstrips |
| Identity gates (exit 0) | Candidate verify passes (`9bb0aaa7`, 107 files). Cache 108, fingerprint `b1714b56…`. Schema exported twice, both mirrors `d852b47c…`, 0 files changed. `LLM_ONLY`; compiler not wired; `FIXTURE_TIN_CAY` absent from production; 0 model-surface files changed since `8a339d17` |
| `git diff --check 8a339d17..7f3658b0` · node harness | Clean (captured logs excluded) · 59 pass + 2 skipped by design (no repo-local venv in a worktree), 0 fail |
| Ponytail review (after the evidence) | 5 behaviour-neutral findings, net −9 lines possible, none applied (`diagnostics/PONYTAIL_REVIEW.json`) |

## Limitations (not hidden)

- **Declared limit A′.** C0 binds every literal to its own entity. It does not check that a
  construction uses the entity the text names: (T) cut by a correctly pinned (α) where the
  text says (β) is still certified and served (`A2b`, strict xfail,
  `ISSUE-ARCH-ASSUMPTION-CONSTRUCTION-RELATION-NOT-SOURCE-BOUND`). Closing it needs a reader
  for construction relations, which is the vocabulary decision W15-H3. It is a reading error
  of the model, not a literal without a source. The strict rule for unnamed planes refuses
  the common forms of it (A6b, A8).
- **Goal clauses in grounding.** The masking applies to the certificate only. The product
  grounding gate still reads a length written only inside `Chứng minh rằng SA = 5` as a datum.
  Inside the polyhedral scope the certificate refuses such a request; outside it, the request
  is only recorded (`ISSUE-ARCH-GROUNDING-GOAL-CLAUSE-AS-DATUM`).
- **Over-refusals** (fail-closed, never wrong answers):
  - `Tính …, biết chiều cao bằng …` (B6b, vocabulary issue).
  - A named text equation written twice, which gives "several text equations" (deferred
    minor).
- **Opaque lines.** Opaque lines can still be tinted by the fill; none crosses a section in
  the six scenes.
- **Unenforced scope (U3) unchanged.** Outside the polyhedral vocabulary the gate records but
  does not refuse.
- **Coverage is the corpus.** The census measures 0 violations *on its corpus within the
  certificate scope*; that is not a general soundness proof. The pre-evidence self-review
  found the primed-name alias, which the corpus had missed.
- **Review.** The final review is a self-review by the author: the brief allows no subagents.
  No human has looked at the new images.

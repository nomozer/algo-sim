# Source-constraint and assumption closure (w15)

Status: **`READY_FOR_HUMAN_VISUAL_REVIEW`**. Every gate in the approved scope passes on the
final candidate, and human visual review is still `NOT_APPROVED`. Automation only; nothing
here is `MERGE_READY`.

## Identity

- **Branch and start.** Branch `fix/cuboid-visual-semantic-closure`, start **`4f6a0ab6`**.
  `origin/main` is `a9492ee9` (fetched at Phase 0: unchanged, ancestor of HEAD). 30 commits up
  to the evidence, plus the documentation commit.
- **Red tests first.** `ac6687ae`: certificate, constraint reader, `solid_faces`, section fill.
- **Product commits** (touching `backend/app` or `frontend/src`):
  - `5dd8e7f5` (`solid_faces`)
  - `cf57332b` (reader + certificate, not wired)
  - `6fa6e582` (fully-read counterexample rule)
  - `2305f072` (right-angle phrasings, polyhedral scope)
  - `a1b17fef` (symbol-key binding)
  - `45d014b0` (route wiring under U3)
  - `33b11a79` (U5)
  - `8239a2a4` (section fill)
  - `0579d559` (`CACHE_VERSION`)
  - `d41176f2` (review simplifications)
  - `909a3a2d` (section fill drawn without a depth test)
  - `41a26f11` (final-review soundness fix) — the last product commit.
- **Candidate.** `40263983…` (W14) → `aaa5b5bd…` → **`b3b7eb79…`** (107 files), frozen **three
  times**, each in a clean detached worktree:
  - freeze 1 at `d41176f2` and freeze 2 at `909a3a2d` both gave `aaa5b5bd`, the intermediate
    candidate. Its evidence, `751169dd`, is superseded.
  - freeze 3 at `41a26f11` gives `b3b7eb79`.

  Measurement commit **`c57ebd1b`**; evidence commit **`23cc880a`**. The divergence is
  declared in `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json` and in the living
  `product-response-contract-alignment/CANDIDATE_DIVERGENCE.json`.
- **Cache.** `CACHE_VERSION` 106 → **107**, once (`0579d559`), decided by real rows
  (`diagnostics/PROOF_CACHE_ROW_W15.json`). The pre-W15 `ok` envelopes of the two W12 probes
  still HIT under 106, although W15 refuses both (served → rejected). The provider
  fingerprint `b1714b566e25c912` is unchanged.
- **Mode and calls.** `DEFAULT_MODE = LLM_ONLY`; 0 live Gemini requests; 0 application LLM
  calls.

## Why W14's gate failed (investigated before any fix)

W14 measured AC2 at 0/18 `PROVEN_SAFE`, found 11 false counterexamples on invariant rows,
still served both W12 probes, and kept 16 strict xfails. The investigation table
(`diagnostics/TRACK_B_ROOT_CAUSE_TABLE.*`, 26 rows, W14 census reproduced first) assigns every
failure to a root cause:

| RC | Kind | Finding |
|---|---|---|
| RC1 | certificate | Grounding classes a coordinate given in the text as a model realisation, so all 8 Oxyz rows failed C0 for a classification reason. |
| RC2 | certificate (provenance semantics) | C1 required a relation to cite a *confirmed* InputFact. Relations the text states are `claimed`, and the family fixtures cite fact ids that do not exist. |
| RC3 | certificate | The demo contracts predate typed relations and compiler recognition. |
| RC4 | validator | Counterexample validity ignored shape properties the text states. For example, moving one top vertex means the solid is no longer a prism. |
| RC5 | validator | The AC1 "UNSAFE" witnesses were invalid single-coordinate moves. |
| STALE_CONTRACT | corpus/product | Stored demo contracts predate the text-invariant builders. |

The gold check (`diagnostics/GOLD_ROW_VERIFICATION.json`) finds the facts of 18/18 AC2 rows
verbatim in the text, and 18/18 independent oracle values equal the served answers. No
corpus correction was needed.

## What changed

| Area | Change | Commits |
|---|---|---|
| Constraint reader | `semantic_program/shape_constraint.py` reads what the text states, in a closed vocabulary, and returns server-owned, entity-bound `RangBuoc`. The vocabulary covers perpendicularity (`XY ⊥ (P)`, `… vuông góc với đáy`, `XY ⊥ XZ`, `góc YXZ = 90°`), solid notation (`S.ABC…`, `ABC.A'B'C'`), solid and base type, right angles (`tam giác/đáy XYZ vuông tại/ở/ở đỉnh/đỉnh X`), and one unnamed right square prism. `phan_chua_doc` reports any given text the server could not read. Confirm-only: it never feeds a fact graph and never promotes a model fact to GIVEN. | `cf57332b`, `2305f072` (U4 · G1) |
| Assumption certificate | `semantic_program/assumption_gate.py`, made of three parts. **C0**: every literal on the slice of a shown value is pinned by a server text invariant of the same entity, at its single reaching definition. **C1**: the closed determination table T1–T6, matched on read constraints, with exact template checks and a canonical re-run cross-check, for volume/area/distance. **Counterexample**: `DEPENDENT` only from a valid ×2 stretch along a missing required dimension, and only when the given text is fully read and every read constraint is a template premise. Literal roles are `SOURCE_DATUM` and `LAYOUT_FRONTIER`; `FORMULA_COEFFICIENT` is empty, because the IR cannot express `1/3·…`. Program names bind to text entities through `domain_profile.geometry_symbol_key` (U4 · G2). | `cf57332b`, `6fa6e582`, `a1b17fef`, `33b11a79`, `41a26f11` |
| Route | New stage `assumption` (`INPUT_NOT_GROUNDED`; `ASSUMPTION_DETERMINES_ANSWER` names the missing quantity, `ASSUMPTION_INVARIANCE_UNPROVEN` otherwise). These refusals are never sent to repair (`pipeline.KHONG_SUA_NGUON`) and carry two Vietnamese learner messages. **U3**: the gate runs for every request but refuses only when the text names a polyhedral solid in the vocabulary. **U5**: a shown value read through a multiply defined name is refused in every scope. | `45d014b0`, `33b11a79` |
| Formation | `solid_faces.phan_loai_bang_mat` gives no prism reading for a non-bijective cap correspondence; the W14 characterization is unchanged. | `5dd8e7f5` |
| Section fill | The fill is its own `section_fill:<id>` mesh: amber `MAU.polygon` at opacity 0.45, `renderOrder` 10, no depth write, no depth test, and not an occluder. The outline keeps the two-pass visible/hidden policy, and the hook `__geo3d_set_section_fill_visible` is for the harness only. | `8239a2a4`, `909a3a2d` |
| Harness | Three negative kinds per family, each with its own expected code; the `SECTION_FILL_DISTINGUISHABLE` assessor with registered thresholds; the U2 flag `--pending-human-review`. | `092df243`, `e59712a1` |

## Certificate scope

**Certified** (`PROVEN_SAFE`):
- C0 for any measure, when every literal is a text datum of the same entity: coordinates,
  lengths, division ratios and plane coefficients. Plane coefficients are not entity-bound;
  see the limitations.
- C1 for volume, area and distance on these templates:
  - T1: right-triangle-base pyramid, apex edge ⊥ base at the right vertex.
  - T2: rectangle/square-base pyramid, apex edge ⊥ base at a vertex; parallelogram plus a
    right angle counts as a rectangle.
  - T3: right prism on a right-triangle base.
  - T4: cuboid.
  - T5: cube.
  - T6: right square prism, named or unnamed.

**Refused as uncertified** inside the polyhedral scope, never served wrongly:
- angles and cos²;
- regular or curved solids without coordinates;
- phrasing outside the vocabulary: `góc 45°`, `SA = AB`, `vuông cân`, lengths with radicals,
  ratios written as `thuộc cạnh`;
- parameters the model chose;
- arithmetic literals, control flow, and frame-dependent constructions.

**Recorded but not enforced** (U3): a text that names no polyhedral solid in the vocabulary.
Such requests keep the old behaviour, except for U5 multiple definitions, which are refused
everywhere.

## Results

Census round 3 at `41a26f11`, the final gate (`diagnostics/ASSUMPTION_MECHANISM_DECISION_W15_R3.json`,
W14 + W15 + W15B corpora, 111 rows):

| Group | Gate verdicts | Route |
|---|---|---|
| AC1 (3 DEPENDS) | 3/3 `DEPENDENT`, subject AD | 3/3 refused: the two W12 probes (`LAYOUT_DERIVED`, `model_assumption`) at `assumption` with `ASSUMPTION_DETERMINES_ANSWER`; `ac1_given_length` earlier, at `grounding` (`GIVEN_VALUE_NOT_IN_SOURCE`) |
| AC2 (18 gold) | **18/18 `PROVEN_SAFE`**: 8 C0, 10 C1 | 18/18 served |
| Adversarial (7) | 6 reach the gate: 3 `DEPENDENT`, 3 `UNDETERMINED`, 0 `PROVEN_SAFE`; `adv7` (empty text) is refused before the gate | 7/7 refused |
| W14's 11 false counterexamples | 0 `DEPENDENT`: 10 `PROVEN_SAFE`; 1 `UNDETERMINED` (`adv11`: one answer is cos², registered as outside C1) | 10 served, 1 refused |
| W15 + W15B labelled corpora (63 rows) | 0 `PROVEN_SAFE` on DEPENDS/MUST_REFUSE; 0 `DEPENDENT` on INVARIANT | no DEPENDS/MUST_REFUSE row served |

- **SHIP rule.** §9 (a)–(f) hold. The compiler cross-check gives 32 agree / 5 not
  recognisable / 0 disagree, and no row changed status against rounds 1 and 2.
- **Out of the enforced scope (U3).** `sc:doan_r3` and `sc:non_e4` (INVARIANT) are served
  with status `UNDETERMINED`, as registered.
- **Fault injections FI1–FI14** at `41a26f11`: FI2–FI14 are caught, and FI1 is masked as
  registered (`diagnostics/logs/FAULT_INJECTION_ASSUMPTION_GATE_FINAL.log`).
- **Strict xfails.** 0 remain; the 16 W14 marks were removed where their requirement holds.

## Section fill

- **Root cause.** It was found by the gate in the browser, not by the unit tests: the fill was
  a depth-tested translucent mesh. Every real solid draws an opaque depth-only copy first, and a
  section lies inside its solid, so no fill pixel was ever drawn. The first authoritative run
  measured delta E = 0 on every sample, and this is also what W14 reported as "the region blends
  away".
- **Gate.** The thresholds were registered before any image (`T_ON 20 · T_ON_MIN 12 · T_OFF 3`).
  At the closed step, mean/min delta E is **33.9/25.3** on desktop (46 samples) and
  **33.8/25.9** on mobile (29 samples). Five pre-close steps and the rewound step measure 0.
  The fill appears only from the closing step and disappears on rewind.

## Measurement

`diagnostics/MEASUREMENT_ATTEMPTS.json` lists every run, including failed and superseded ones.

1. **FREEZE-1** at `d41176f2`, then **BROWSER-1** at `c1638891`: **FAIL** — only the
   section-fill gate (delta E 0). Kept apart in `diagnostics/browser-attempt1-c1638891/`.
2. **DRY-1**, a diagnostic run with the fill fix: 6/6.
3. **FREEZE-2** at `909a3a2d` (product commit only), then the M2 evidence at `e5b88647`:
   all PASS.
4. The **final whole-branch self-review** found a soundness hole in U5. The refinement dropped
   a declared literal when no *earlier* statement read it, but never looked at the constructing
   statement itself. `X = midpoint(X, N)` therefore let X's model literal reach the answer while
   C0 certified it. Fixed in `41a26f11`, RED → GREEN, with fault injections and census round 3
   at the fix.
5. **FREEZE-3** at `41a26f11` (`b3b7eb79`), then the **M3 evidence** at `c57ebd1b`. The
   worktree's old outputs were removed first; 371 outputs were produced, and every figure
   equals M2's.

## Final verification (at `c57ebd1b`)

| Gate | Result |
|---|---|
| T3 `full-gate.mjs` from a path WITH a space | `FULL_PRODUCT_GATE_PASS`: pytest **6757 passed / 0 failed**, plus 1 skipped (`test_scalar_obligations.py:95`, a deliberate skip) and 2 deselected (opt-in markers `postgres`, `external_evidence`), 0 xfailed. Also vitest 1017/1017 (67 files), typecheck + build, thesis demo `DEMO_REPLAY_PASS 5/5`, and demo crash surface 6/6 refusal boundaries with 0 HTTP 500 |
| Browser suite, 6 families × desktop/mobile | 12/12 positives served; 36/36 negatives refused, each kind with its own code. 0 raw tokens, 0 serious console errors, 0 uncaught exceptions, 0 failed API calls, no overflow |
| Occlusion (`--pending-human-review`) | pass, verdict `HUMAN_REVIEW_PENDING`; product = independent oracle on 24/24 states. Cuboid and cube: `DECLARED_CAMERA_CHANGE`. Triangular pyramid, triangular prism, rectangular pyramid and cross-section: `HUMAN_REVIEW_PENDING`, with the reviewed sets reproduced at both cameras |
| Learner playback | 12/12 runs × 19/19 checks, 5 orbit laps each |
| Crops, sheets, filmstrips | 64 crops, endpoints inside, 0 oracle disagreements, 0 duplicate owners; filmstrips caption the section steps |
| Identity | Candidate verify passes (`b3b7eb79`). Cache 107, fingerprint `b1714b56…`. Schema exported twice, both mirrors `d852b47c…`, no diff. `LLM_ONLY`; compiler not wired; `FIXTURE_TIN_CAY` absent from production paths |
| `git diff --check 4f6a0ab6..c57ebd1b` · node harness | Clean, verbatim logs excluded. 53 pass + 2 skipped by design in the worktree; 55/55 in the main tree |
| Ponytail review | 13 of 19 findings applied (net −23 lines), 6 kept with a reason (`diagnostics/PONYTAIL_REVIEW.json`) |

## Limitations (not hidden)

- **No human has approved the new look.** The four W14-changed scenes are pending a person
  (U2), and so is the now-visible section fill. The fill is drawn after the lines, so it
  tints any solid edge that crosses the section region on screen.
- **Unenforced scope (U3).** Outside the polyhedral vocabulary the gate records but does not
  refuse: an answer to a non-polyhedral text (segments, planar figures, curved solids) that
  depends on an unstated dimension is still served, as before W15. This stays an open issue.
- **Coverage is the vocabulary.** A determined polyhedral problem phrased outside the
  vocabulary is refused (fail-closed); the census measures 0 violations *on its corpus within
  the scope*, which is not a general soundness proof. The final self-review found one hole the
  corpus did not, which shows the limit.
- **Plane equations.** C0 pins a plane literal to *a* plane equation of the text, not to the
  named plane; the invariant family carries no entity, which is inherited from W12.
- **Other open items.**
  - "Chứng minh …" clauses are read as premises.
  - Four fail-closed guards have no test of their own.
  - `ISSUE-OPS-DIST-ACL-OWNERSHIP` still makes the main-tree `npm run build` fail with `EPERM`;
    every build here ran in a fresh worktree.
- **Review.** The final review is a self-review by the author: the brief allows no unrequested
  subagents.

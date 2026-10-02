# W14 — assumption counterexamples (Task 5 Step 1)

Every row was measured on the frozen, hand-labelled corpus
([`assumption_corpus/CORPUS.json`](assumption_corpus/CORPUS.json), labels committed in
`9ddecb35` before any mechanism ran). Numbers come from
[`ASSUMPTION_CENSUS.json`](ASSUMPTION_CENSUS.json), produced by
[`assumption_census.py`](assumption_census.py) with 0 model calls.

- **M2E (R1)** is the R1 design, reconstructed from the R2 critique. It perturbs every assumed
  point by ×2 on one axis at a time, judges validity against the program's own `XY_length`
  memories, and accepts any changed pair whose original length has evidence in the text.
  It returns `OK` when it finds no valid counterexample.
- **R2** is the three-valued verdict. `PROVEN_SAFE` only from C0/C1, `UNSAFE` only from a
  counterexample that passes the validity check, otherwise `UNDETERMINED`.

## Root causes found while planning (each confirmed by a row below)

| Code | Root cause |
|---|---|
| RC1 | Absence of a counterexample treated as proof of safety: "no valid perturbation", "budget" and "nothing changed" all ended `OK`. |
| RC2 | Validity checked against assumed literals (the program's own `XY_length` memories) instead of source constraints only. |
| RC3 | Evidence accepted for any changed pair, not for the dimension that decides the answer. |
| RC4 | Perturbation family tied to coordinate axes, not to the configuration's free parameters. |
| RC5 | Empty `problem_text` short-circuited to `OK` (closed by the Task 5a trust policy). |

## Per case

| Case | Label | Route today | M2E (R1) | Root cause | R2 census |
|---|---|---|---|---|---|
| `ac1_given_length` — prism without AD; program claims `AD_length = 5` GIVEN | DEPENDS | refused at grounding (`GIVEN_VALUE_NOT_IN_SOURCE`) | **OK** — every z-scaling breaks the program's own `AD_length`, so 0 valid perturbations | RC1 + RC2 | UNSAFE (D[2]×2 changes V) |
| `ac1_layout_derived` | DEPENDS | **served**, V = 30 | REFUSE | — | UNSAFE (D[2]×2) |
| `ac1_model_assumption` | DEPENDS | **served**, V = 30 | REFUSE | — | UNSAFE (D[2]×2) |
| `adv1_xy_length_gia_dinh` — adds an assumed `AD_length = 5` memory | DEPENDS | refused at grounding (`MODEL_ASSUMPTION_TYPE_NOT_ALLOWED`) | **OK** (0 valid perturbations) | RC1 + RC2 | UNSAFE (D[2]×2) |
| `adv2_xoay_thieu_AD` — the probe in a rational rotated frame | DEPENDS | **served** | **OK** — every axis scaling breaks AB/AC | RC1 + RC2 + RC4 | UNDETERMINED (CE inconclusive: no exact check passes for any single-coordinate move) |
| `adv3_canh_khac_che_chieu_cao` — square base 4, no height, height set to 4 | DEPENDS | **served** | **OK** — a standalone "4" excused the changed height | RC3 | UNDETERMINED (CE inconclusive) |
| `adv4_lang_tru_xien` — oblique prism, translation assumed | DEPENDS | **served** | **OK** — evidence for AB = 3 excused the change | RC3 + RC4 | UNDETERMINED (CE inconclusive: no exact checker for the prism structure) |
| `adv5_chan_duong_cao_an` — foot of the height assumed, d(S, BC) asked | DEPENDS | **served** | **OK** — evidence for AB = 3 excused the change | RC3 | UNSAFE (S[0]×2 changes d) |
| `adv7_thieu_de` — contract without text | POLICY_5A | refused at grounding (`SOURCE_TEXT_MISSING`) | (would be OK — RC5) | RC5 | not measured: closed by Task 5a |
| `rf4_hai_dap_so_mot_phu_thuoc` — V plus d(A, M), M arbitrary | DEPENDS | **served** | **OK** (0 valid perturbations) | RC1 + RC2 | UNSAFE, but via E[2]×2 on the volume: the right verdict for the wrong reason (see CE soundness) |
| `adv8_nhan_vo_huong_gia_dinh` — answer V·\|AM\| | DEPENDS | **served** | **OK** (0 valid perturbations) | RC1 + RC2 | UNSAFE via E[2]×2 — same caveat |
| `adv10_quan_he_*` (3) — prism relation not source-confirmed | INVARIANT | **served** | OK | — | no C1 (relation not usable / not confirmed); CE reports UNSAFE via E[2]×2 — a **false** counterexample |
| `adv11_hai_dap_so_mot_ngoai_pham_vi` — volume + cos² of an angle | INVARIANT | **served** | OK | — | no C1 (relation not confirmed); CE false counterexample E[2]×2 |

## What the census found about R2 itself

1. **No certificate on any served AC2 program (0/18 PROVEN_SAFE).**
   - **C0** fails on every row: every answer's closure holds class-A or class-C coordinate
     literals (frame choices, coordinates realised from relation facts).
   - **C1** fails on every row, at its first condition:
     - the six compiler families, the rotated/translated equivalents and the cert-limit
       probes: the typed relation cites a fact id (`fact_perp_lateral`, `fact_perp_base`,
       `fact_perp_lat`) that is **not a confirmed InputFact**. The relation facts exist
       only as relation metadata, never as span-verified input facts;
     - the thesis gold (p1, p2, p4–p7) and the demo replay programs: not
       compiler-recognized (fact graph `UNSUPPORTED_INCOMPLETE`);
     - the probes: the recognizer refuses them (`REQUIRED_FACT_MISSING`, `EXTRA_OBLIGATION`).
2. **CE is unsound on this corpus: 11 false counterexamples on INVARIANT rows.** Its validity
   check (source invariants + typed relations + postconditions) misses constraints that the
   problem fixes:
   - **Topology metric meaning.** Raising the prism vertex E (E[2]×2) keeps AB, AC, AD, both
     perpendicularities and planar faces, but the solid is no longer a prism. Moving the
     rectangle vertex C (C[0]×2) keeps every typed fact, but the base is no longer a rectangle.
   - **Historical contracts that encode no source constraint.** The demo replay contracts have
     0 source invariants and 0 relations; there, moving the origin A or a given vertex M is
     "valid".

   As specified, CE would refuse correct programs with `ASSUMPTION_DETERMINES_ANSWER`.
3. **M2E (R1) served 8 of the 13 measured DEPENDS rows**, exactly through RC1–RC4. The R2
   critique of the R1 design is confirmed.

## Decision

[`ASSUMPTION_MECHANISM_DECISION.json`](ASSUMPTION_MECHANISM_DECISION.json) applies the rule
pre-registered in the plan:

- rule (c) fails: 0/18 contract-bearing AC2 rows are PROVEN_SAFE;
- CE is additionally unsound (finding 2).

**STOP Track B — `ASSUMPTION_POLICY_INCOMPLETE`.** No product gate ships. Task 2's assumption
tests become strict xfail referencing the decision. Tracks A and C continue (Q4).

"0 violations on the measured corpus" holds only trivially here: nothing was PROVEN_SAFE.

## Certificate work a later wave would need (backlog, not W14)

- **Confirmed relation facts.** The analyze contract must carry each typed relation as a
  span-verified InputFact, so C1's "relation confirmed" condition is attainable.
- **Exact validity for topology meaning.** CE needs exact checkers for the solid topology
  (prism = translation, rectangle/square base, parallelogram/rhombus) and a refusal to treat
  under-encoded historical contracts as complete. Without them, UNSAFE is not trustworthy.
- **C1 beyond compiler-recognized solids.** The certificate must reach curved solids, Oxyz
  coordinate problems (coordinates in the text as class-B facts, not class C), sections and
  non-volume measures.

# Student natural-language understanding — audit, repairs and limits (tenth continuation)

Offline only: 0 provider calls, `MAX_AUTHORIZED_LIVE_REQUESTS = 0`. Every number below comes from a **development
diagnostic** authored by the implementer (`tools/student_language_probe.py`). It is not held-out and not live: it
measures what the deterministic backend does with an authored extraction, never how well a model reads the same text.

## 1. Where "understanding" happens on the Hybrid path

| layer | authority | what it can and cannot do with learner wording |
|---|---|---|
| L0 domain gate | `semantic_program/domain_profile.py::detect_domain`, first gate of `/api/analyze` on **every** route | word-level; decides "space geometry or not" before any route |
| L1 extraction | the model (`TransportExtractor`), validated by `typed_fact_next_extraction.py` | reads the text; every quote must be verbatim; offline only replayed |
| L2 Source Gate | `registry.kiem_nguon`, closed Vietnamese grammars | proves every quote supports its fact, reads every premise and request sentence; refuses what it cannot read |
| L3 planner / engine / kernel | `planner.py`, `engine.py`, kernel | determinacy, consistency, construction; never reads text |
| L4 Adapter /4 | `adapter4_route.py` | envelope, refusal class, certificates |

Consequence: on this architecture, a learner phrasing is "understood" only when **both** a model can extract it **and**
the closed Source Gate can read it. Offline, only the second half is measurable.

## 2. Refusal taxonomy: the Owner's eight classes on the existing codes

No new code was created. `classify_refusal` groups already exist; the NLU class is a mapping (the probe's `NLU_OF_GROUP`),
and the new clarification record carries it explicitly (`nlu_class`).

| Owner class | product evidence |
|---|---|
| VALID_COMPLETE | `SERVED` |
| VALID_BUT_UNSUPPORTED | group CAPABILITY / INCONCLUSIVE; `OUT_OF_SCOPE` (the extraction escape `unsupported`) |
| AMBIGUOUS | `AMBIGUOUS_FACT`, `AMBIGUOUS_REFERENCE` (group MISSING_DATA) |
| MISSING_DATA | group MISSING_DATA (`MISSING_DIMENSION`, `UNDERDETERMINED_POINT`, …) |
| CONTRADICTORY_DATA | group INVALID_DATA (`INCONSISTENT_FACTS`, …) |
| UNRECOGNIZED_WORDING | group SOURCE_UNVERIFIED (the gate could not read the wording) |
| OUT_OF_SCOPE | domain gate `GATE_OUT_OF_SCOPE` |
| TECHNICAL_FAILURE | groups RESULT_UNVERIFIED, EXTRACTION_FAILED, INTEGRITY |

Limit: SOURCE_UNVERIFIED also catches extractor errors (a non-verbatim quote, a swapped role). On a gold extraction it
means "the gate cannot read this wording"; on a wrong extraction it means "the gate caught the error". The probe keeps
the two apart by labelling every extraction `gold` or `adv:*`.

## 3. Method

`tools/student_language_probe.py`: 74 cases, 67 gold rows and 20 adversarial rows; 7 cases are adversarial only
(receipt `student-language-probe.json`).
Axes per case (`axes`): family, intent (measure / simulate only / simulate and measure / simulate a point / highlight /
find a point), wording (standard, simulation verb, trailing request, mixed sentence, question form, lowercase sentence,
dropped preposition, math symbol, spacing, no diacritics, lowercase labels, tone typo, equivalent relation), metamorphic
transform (permute, rename, scale, symbolic unit, opener swap on two independent topologies), chain length, number of
goals, completeness (missing dimension / shape / operand / notation, contradictory), contrastive and adversarial kind.

- **Gold rows** carry an expected action (SERVED, REFUSED with an NLU class, or NEEDS_CLARIFICATION with kind and missing
  roles) and, for served rows, hand oracles (squared lengths and volumes, cos² for angles) written before any run.
- **Adversarial rows** are plausible extractor errors on the same text (swapped role, dropped or invented goal, value
  mismatch, negation or condition read as a premise, inferred highlight, assumed projection target). Each must be refused.
- Scoring never reads the extraction: served values come from the executed `answer_exact` bindings.

Before / after use the **same probe** (`student-language-probe-baseline-corrected.json`, run on a clean detached checkout
of `c9f54828` = product `fa1ed277`). The first baseline (`student-language-probe-baseline.json`) predates two case
corrections and is kept unchanged: S08's altitude quote did not meet the `altitude` function's own contract, and I13's
gold assumed the extractor may name the altitude itself (an R0 violation; it is now the honest exit, and the inferred
highlight is an adversarial row).

## 4. Results (development diagnostic, authored, offline)

| gold rows | baseline `fa1ed277` | after (`fb67cfb2`, `student-language-probe-final.json`; same counts at `6637f6fd`) |
|---|---|---|
| SERVED_CORRECT | 22 | 52 |
| NEEDS_CLARIFICATION_CORRECT | 0 (no representation) | 5 |
| CORRECT_REFUSAL (right class) | 5 | 7 |
| FALSE_REFUSAL | 26 | 3 |
| REFUSED_NO_CLARIFICATION | 5 | 0 |
| REFUSAL_WRONG_CLASS | 2 | 0 |
| WRONG_SERVED | 0 | 0 |
| **adversarial**: SAFE_REFUSAL / WRONG_SERVED | 20 / 0 | 20 / 0 |

The after column has 7 more gold rows than the corrected baseline (P11–P17, added after the fix to look for planner
gaps); those 7 were not run on the baseline. On the 60 shared gold rows the change is 22 → 45 served correct.

Per group on the after receipt (gold rows): intent wording (I) 14/14 served or clarified as expected; givens wording
(S) 5/8 — S05 no diacritics, S06 lowercase labels, S07 tone typo still refused; metamorphic (R, M) 12/12; composition
(P) 17/17; ambiguous / missing / contradictory / unsupported (A01, A02, D01–D07) 9/9 with the right class or
clarification, and the positive control A03 served exactly; contrastive gold (X) 4/4; out of scope (O) 2/2.

## 5. Failure attribution (first divergence, owning layer, repair)

| id | finding | first divergence | layer / class (§5.2) | repair | evidence |
|---|---|---|---|---|---|
| SL-1 | every simulation request refused: "Vẽ / Dựng / Mô phỏng / Cho mình xem / Hãy vẽ hình chóp …" (`UNGROUNDED_VALUE`), a trailing "Vẽ hình chóp S.ABCD." / "Hãy mô phỏng hình." (`SOURCE_PREMISE_UNREAD`), "Vẽ hình rồi tính …", "Hãy mô phỏng hình và điểm M." (`QUESTION_CONTEXT_UNSUPPORTED`) | the clause grammar opened a solid clause only with `cho|xét`; no reader covered a sentence that only asks to show built objects | Source Gate / E | one closed reader `_doc_yeu_cau_mo_phong` (verb + mentions of objects validated calls build; adds no fact), used in the clause grammar, the premise region and the request region | `test_route_d_student_language.py` (RED 19 → GREEN), probe I02–I12, P09, X08, M_* |
| S02 | "SA vuông góc đáy" (no "với") made its whole sentence unreadable, so the base side was unbound | `_C_VUONG` | Source Gate / E | accept "vuông góc" with optional "với" (number-free clause, binds nothing) | probe S02 |
| S08 | "đường cao SA = 2" | `_C_DOAN` had no "đường cao" role | Source Gate / E | role added to the branch already proved by `_vai_doan_ok` (⊥ / altitude call); unproved role claim stays unread | probe S08, lock `test_altitude_role_claim_on_an_unproved_segment_stays_unread` |
| SL-2 | "Mô phỏng điểm S là góc chiếu …", "Gọi H là hình chiếu của S.", "Mô phỏng hình lăng trụ.", "Tìm hình chiếu của A lên (SBC).", "… chỉ ra đường cao" had no faithful extraction | `typed-fact-next/2` had no honest exit (the flat contract has `ambiguous` / `unsupported`) | contract / H | additive `unresolved` (closed kinds, roles, ≤ 3 candidate relations, subject label in its quote); bridge refuses with AMBIGUOUS_FACT / OUT_OF_SCOPE and a server-built `route-d-clarification/1` record | `test_route_d_unresolved_clarification.py`, probe A01, D05–D07, I13 |
| D02 | "Vẽ hình chóp S.ABCD." refused as `UNSUPPORTED_BASE_SHAPE` (capability) | `engine.bo_cuc_day` last branch | engine / H (misleading class) | no length between base vertices from any source ⇒ `MISSING_DIMENSION`; a base with lengths but no layout rule keeps `UNSUPPORTED_BASE_SHAPE` | probe D02, A02; two tests |
| S05 | text without diacritics is refused as **out of scope** before any route | `detect_domain` (L0, also the `LLM_ONLY` default) | domain gate / E | **not repaired** — owner decision (§7) | probe S05 |
| S06 | lowercase labels "s.abcd" | label grammar `[A-Z]` | Source Gate / E | **not repaired**: "a" is the symbolic length unit; an upper-casing rule changes identities. The extractor can now use `unrecognized_term` | probe S06 |
| S07 | tone typo "hình chop" | closed Vietnamese grammar | Source Gate / E | **not repaired**: same mechanism as diacritic restoration (§7) | probe S07 |

No case in the probe needed a planner change (class B), a new Registry function (C), or a kernel change (F). The four
longest chains (P11–P14, three to four constructions) and three planner-limit probes (P15–P17) are served exactly.

## 6. Planner recomposition: what the evidence shows, and what it does not

The receipt records the Registry functions of every executed plan (`observed.functions`, `auxiliary_rules`).

- Supported: the planner orders and connects functions over **constructed** points it did not see in the solid —
  centroid → foot on a plane → length (P11); intersection → midpoint → intersection of a constructed line → length (P12);
  a foot on a face reused by a foot on a line (P14); distance between skew lines through a midpoint (P13); one midpoint
  shared by two goals (P07).
- Planner-originated steps appear only in **registered** decompositions: the point–line distance through an auxiliary
  foot (P05, P15, `distance(point,line)`). Elsewhere the source states each construction and the planner maps it to one
  function. This is the bounded effect planner of `architecture-capability-audit.md`, not a general search.
- Not shown here: sections built on constructed points, curved composites, and multi-solid chains (covered by the
  earlier probes, unchanged by this slice: topology, measurement, curved, curved section, sphere section, apex ratio,
  base centre and composite-relations receipts re-run identical to the baseline).

## 7. Limits that stay

- **Unmeasured:** how a live model reads any of these texts. Gold-fact replay proves the deterministic layers only.
- **No diacritics (S05):** the first gate of `/api/analyze` (`detect_domain`) sends such text to "out of scope" on
  every route, including the `LLM_ONLY` default; the Source Gate grammars would refuse it next. A safe repair is one
  length-preserving restoration copy of the text (NFC Vietnamese letters are single code points, so spans stay exact)
  with a closed geometry lexicon, raw quotes kept for provenance, and refusal or clarification on ambiguous folds
  (góc/gốc, tâm/tam, đáy/dây). It changes default-route behaviour, so it is an Owner decision, not done here.
- Simulation requests on curved solids are not read by SL-1 (polyhedra only). "Chỉ ra / xác định đường cao" (identify
  a role) has no certified capability: highlight goals are presentation only.
- The honest exit only helps if a model uses it; a model that over-uses it would turn served problems into
  clarifications. Both rates need the live measurement.
- The probe is authored by the implementer: development diagnostic, not held-out.

## 8. Independent review

Fresh-context adversarial reviewer on `c9f54828..6637f6fd`.

**Round 1: `NOT_READY`.** 2 BLOCKER, 4 MINOR, 3 NIT. Both blockers were wrong serves in the SL-1 reader, and both are fixed and locked as tests:
- **B1: class words were not checked.** "Vẽ hình lập phương ABCD.A'B'C'D' rồi tính …" on a 2×3×4 box was served, and so was "Vẽ khối tứ diện S.ABCD". Fix: a mention may use only the generic word "chóp" / "lăng trụ" with the solid's own notation. "đều / đứng / xiên" are refused too.
- **B2: the reader checked labels, not drawn objects.** "Vẽ mặt phẳng (SBD) và đoạn BD rồi tính …" was served, with no SBD or BD in the scene. Fix:
  - only the figure, the declared solid and built points count as mentions;
  - "đỉnh" must be a solid vertex;
  - the opener is stripped only before the solid's attributes ("có / với / biết / thoả mãn").
- **MINOR / NIT, all fixed:**
  - spans are offsets in the raw text;
  - the record describes the first answerable entry, whatever order the model wrote;
  - a quote must contain wording;
  - a primed subject is matched in canonical spelling;
  - repeated roles are asked once.
- **MINOR, recorded:** `response_contract` stays `typed-fact-next/2` and the preview surface carries no prompt fingerprint. Live receipts bind the change through `measured_system`, which hashes the extraction module, plus registry /27.

**Pre-existing defects the reviewer found outside the diff:**
- **PE-1, fixed.** It was widened by SL-1. A request sentence that no call answers was served with the request dropped: "Tìm giao điểm của SC và (ABD).", "Xác định hình chiếu của S lên (SBC).", "… tìm cách dựng". There were two causes in the request region:
  1. the sentence was required to be read whole only when an ask phrase or ask call existed;
  2. `_CUM_DUNG_HINH_CHIEU` read an unbuilt projection phrase by its labels alone.

  Now every request-verb sentence must be read whole, and a projection phrase is read only as the method of an ask in its own sentence.
- **PE-2, open, not repaired.** "Cho hình lập phương ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật, AB = 2, AD = 3, AA' = 4." is served at baseline. The cube claim is a solid-noun word that no call encodes, and nothing checks that the edges are equal. The SL-1 opener inherits this through the same clause path, exactly as "Cho …" does. The repair belongs to the solid-class check (Source Gate) or to an engine certificate of the class; it is recorded in `docs/OPEN_ISSUES.md`.

**Round 2 (on `58888d7c`): `NOT_READY`.** The reviewer confirmed that B1, B2, PE-1 and the SL-2 fixes are closed, then found two new problems:

- **BLOCKER — my PE-1 exemption.** "A sentence inside a validated construction quote is answered" let a broad model quote drop a second request. Repro: "Xác định I là giao điểm của AM và (SBD) và tìm giao điểm của SC với (ABD)." with that whole sentence as the quote was served.
  - Fix: the exemption is removed. Only the closed anaphor "thiết diện / giao tuyến đó|này|trên" is read, and only when a validated section or intersection line exists.
  - The repro also exposed a pre-existing reader: the intersection-point definition `giao điểm của [^,.;!?]+`. It now reads exactly two closed operands.
- **MINOR — spans in the production wrapper.** They were still offset there, because the payload model strips whitespace. Fix: Adapter /4 re-locates the spans in the raw source.
- **Test change:** the section-slice mutant "cutting-plane binding dropped" is now checked by its refusal reason. The new request-sentence rule refuses the same text independently, so the guard is still load-bearing, but the mutant can no longer be observed as a serve.

Regression at `35cac578`: Wave 3 / locked 96 / 203 probes are unchanged (`inventory-phase-n3.json`). Every earlier probe is identical to the baseline. In `tests/geometry`, the only failures are freeze and dirty-tree checks.

**Round 3 (`35cac578`): `NOT_READY`, on one MAJOR.**

- **Closed from round 2:** the BLOCKER and the wrapper spans.
- **No over-narrowing:** 47 "giao điểm của …" wordings behave exactly as at baseline. The anaphor abuse forms ("… đó và tìm …", "… là hình gì", "… khi SA = 5") are refused.
- **MAJOR: the anaphor noun was not matched to its call.** "… theo một thiết diện. Xác định giao tuyến đó." was served on a section call alone. Fix: "thiết diện" is answered only by a `section` call, and "giao tuyến" only by an `intersection_line` call.
- **MINOR:** "vừa dựng" never matched, because it was compared against text where "dựng" was already blanked. Fix: compare against the source text.
- **NIT, recorded but not added:** a second mutant text in which the plane binding is the only guard.

Regression at `fb67cfb2`:
- `inventory-phase-n4.json`: unchanged.
- `tests/geometry`: only the freeze and dirty-tree checks fail.

**Round 4 (`fb67cfb2`): `READY`.** 0 BLOCKER, 0 MAJOR.

- The round-3 MAJOR and MINOR are closed.
- All the reviewer's earlier repro scripts were re-run: none regressed. The 47 intersection wordings match byte for byte.
- Remaining, none blocking:
  - The section-slice NIT above.
  - Already on record:
    - "Vẽ hình rồi tính." serves with an empty request, as baseline "Tìm." does.
    - "Dựng mp(SBC)." is served by a reader that predates this work.
    - PE-2.
    - The fingerprint MINOR.

## 9. Contract and compatibility

- `typed-fact-next/2` gains one optional field; `/1` is unchanged and rejects it. Census extension adds 7 METADATA rows.
- `/4` extraction surface (schema + one instruction sentence) changes, so the Hybrid arm's model surface changes.
  `LLM_ONLY` is untouched: `CACHE_VERSION` stays 131.
- Route D cache identity: registry /27, engine /19 (D-02 bump rule); planner /22 unchanged; preview fixtures keep their
  bytes through the declared identity delta.
- Frontend envelope unchanged; `route_d.refusal.clarification` appears only on the honest-exit refusal (frontend
  consumer tests 177/177).

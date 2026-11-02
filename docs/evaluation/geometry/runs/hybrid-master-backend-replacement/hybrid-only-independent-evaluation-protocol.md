# Hybrid-only independent evaluation — protocol `hybrid-only-independent-evaluation/1` (pre-registered, C19, 2026-11-02)

**Status: framework ready, `NOT_MEASURED`.** Revision 1a (same day, before any run): independent review round 1 closures (MAJOR-1/2, MINOR-4); revision 1b: round 2 closures (MAJOR-A/B/C). No corpus exists: no author independent of the implementer has been named,
and this protocol forbids the implementer from writing one or attesting its independence.

## 1. Question

How far does Hybrid `/4` work on NEW Vietnamese problems — from text to a certified answer and a Scene3D — and where are
its limits? Hybrid is the target architecture. **This protocol does not compare against LLM_ONLY**; the locked paired
60-problem protocol is unchanged and becomes `OPTIONAL_LEGACY_MIGRATION_COMPARISON` (it is not rewritten).

## 2. Measurement metadata (fixed before any run)

| field | value |
|---|---|
| `MEASUREMENT_CLASS` | `INDEPENDENT_HYBRID_EVALUATION` (the live header of an `H-1` run) only if §3 holds; otherwise the run is refused |
| `HELD_OUT_CLAIM` | the corpus is unseen by the implementer until it is frozen; any product change made after seeing results turns it into development data for the next candidate |
| arm | one: the production opt-in Hybrid `/4` path, one source-only request per case |
| runner / scorer | `backend/scripts/run_s2_student_language_pilot.py` study `H-1` + the unchanged `score_s2_student_language_pilot.py`; hashes bound in the approval |
| candidate | bound in the approval (`measured_system`); today `15d236eb` / `3711d4ee…` |
| model | bound in the approval; no fallback |
| caps | ≤ 60 requests (one per case, no retry unless the Owner raises the cap BEFORE the run); USD set by the Owner |
| stops | request cap, USD cap, provider block, 3 consecutive infrastructure failures, identity change, interruption |

## 3. Corpus (written by someone else)

- **Author:** a learner or teacher who did not tune the planner, Source Gate or prompts. The corpus file carries
  `authoring = {author, independent_of_implementer: true, independence_attested_by: "OWNER"}`; the runner refuses a live
  `H-1` run without it (test `test_c19_an_h1_corpus_is_refused_live_unless_the_owner_attests_an_independent_author`).
- **Content:** new problems, not renamed or re-numbered development problems. Strata (closed): `H-POLY`, `H-CURVED`,
  `H-COMPOSITE`, `H-SECTION`, `H-DESCRIBED`, `H-CONSTRAINT`, `H-DEFINITION`, `H-MULTI`, `H-MISSING`, `H-CONTRA`,
  `H-AMBIG`, `H-OUT`, `H-NONUNIQUE`. No stratum is dropped because Hybrid is weak on it.
- **Oracle:** exact values written by the author (or a second independent person) before any run.
- **Expected outcome:** from the capability contract (`product_capability.py`, `CAPABILITY_MATRIX.json`), never from what
  the product currently does. Vocabulary: `SERVED`, `CLARIFY` (allowed codes), `REFUSED_UNSUPPORTED`,
  `REFUSED_INCONSISTENT`, `REFUSED_UNDERDETERMINED`.
- **Gold extraction for every `SERVED` case** (review MAJOR-2): goal and operand matching exists only against a gold, so
  the gold IS part of the expectation. It is written before the freeze (by the author, or by the implementer and then
  confirmed by the author: `authoring.gold_confirmed_by_author: true`); the runner refuses an H-1 corpus without it, or
  without every stratum. **Every non-served case needs a gold too** (round 2 MAJOR-C): it fixes the right reason of the
  refusal, and a CLARIFY gold names the ambiguous wording in `unresolved`.
- **What the authorship fields prove:** nothing by themselves — they are fields of the corpus file. The control is the
  Owner approving the hash of that file (review MINOR-4).

## 4. Scoring (fixed in code before any run)

- The scorer's eight metrics, unchanged (extraction accuracy, goal completeness, operand preservation, ambiguity
  detection, clarification correctness, false clarification, unsupported classification, wrong-served).
- **`SERVED_CORRECT`** only when every expected quantity is answered exactly, the certificate is verified, and the
  extraction's goals and operands match the gold's (tests: an unanswered expected quantity is `SERVED_WRONG`; a model
  that drops one of two goals is never `SERVED_CORRECT`).
- **Right status, right reason** (review MAJOR-1, round 2 MAJOR-A/B/C): a refusal is correct only with the gold
  replay's refusal code AND the gold's facts; a clarification only when EVERY live `unresolved` entry lies on the gold's
  ambiguous wording (located spans intersect, more than half of its words, at most twice its length). Otherwise
  `WRONG_REASON_REFUSAL` / `WRONG_REASON_CLARIFICATION`; with nothing to compare, `REASON_NOT_VERIFIED` — never correct.
  The same verdict feeds `end_to_end_correct`, `by_stratum` and `composition_label`; only the scorer's eight metrics stay
  status-only (unchanged scorer). Conservative: an equivalent but different extraction, or a clarification naming only
  half of the ambiguous wording, counts as wrong. A refusal at the domain gate (no extraction) needs only the code.
- **Outcome taxonomy per row** (`hybrid_outcome`): `SERVED_CORRECT`, `SERVED_WRONG`, `CORRECT_REFUSAL`, `FALSE_REFUSAL`,
  `WRONG_REASON_REFUSAL`, `CORRECT_CLARIFICATION`, `WRONG_REASON_CLARIFICATION`, `FALSE_CLARIFICATION`,
  `REASON_NOT_VERIFIED`, `INFRASTRUCTURE_FAILURE`; unrun cases are
  `cases_not_measured`, never 0. A technical failure is never a refusal (test).
- **Extraction detail:** `described_check` (kinds, refs, quotes) and `constraint_check` (kinds, operands, quotes, no
  invented construction).
- **Attribution** of every failed row by gold reproduction: `DOMAIN_GATE`, `LLM_EXTRACTION_DIFFERS_FROM_GOLD`,
  `DETERMINISTIC_LAYER_REPRODUCED_WITH_GOLD` (then the refusal group names the layer: Source Gate, representation,
  capability, kernel), `INFRASTRUCTURE`, `UNATTRIBUTED`.
- **Planner:** `composition_label` (C15 rule) per served row; discovery is not claimed from it
  (`GENUINE_DISCOVERY_NOT_ESTABLISHED`).
- **Performance:** latency, tokens and USD per row only from a live run; offline they are `NOT_MEASURED`.
- **No threshold is changed after results are seen.** This protocol sets no pass mark; it reports the rates.

## 5. Pre-registration checklist (all must be recorded before the first request)

Corpus hash · oracle · expected outcomes · this protocol version · candidate (`measured_system`) · model · runner,
harness and scorer hashes · authoring provenance · evaluator independence · request and USD caps · Owner approval file.

## 6. Reuse, not rebuild

Transport, budget, send guard, identity guard, gold replay, attribution and receipts are those of the paired harness and
the S-2/R-1 runner (studies `S-2`, `R-1`, `K-1` share them). This protocol adds only study `H-1`, the outcome taxonomy and
the authorship gate.

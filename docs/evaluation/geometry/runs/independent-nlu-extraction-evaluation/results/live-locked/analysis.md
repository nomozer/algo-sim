# LIVE_LOCKED — baseline result and per-layer analysis

Owner approval: GO LOCKED EVALUATION (2026-10-17); approval file written by the owner, receipt `../../approval-receipt.json`
(sha256, both identities equal to `approval-identities.json`). Executed at `a9724519`; identity unchanged since the lock
`6255a743`. MEASUREMENT_CLASS LIVE · HELD_OUT_CLAIM: locked split, wordings not shown in the prompt (pretraining exposure to
similar textbook items is unknowable), labels by a blind AI author, not human-validated · EVALUATOR_INDEPENDENCE:
deterministic scorer frozen at the lock; results re-scored byte-identically by an independent reviewer (`review.md`).
Receipts: `manifest.json`, `score.json` (frozen SCORE), `layer_rows.json` (from `attribute_layers.py`),
`../../corrections/` (correction layer, beside the score).

## Execution

44/44 rows, 44 live requests, 0 retries (44 HTTP attempts), no stop rule; every `modelVersion` = `gemini-2.5-flash`;
usage on all rows; 44 distinct response ids; no key-like string in results or corrections. Latency min 1.7 s, median
5.55 s, max 33.2 s, total 302.4 s. Tokens: input 34,466 (median 783/call) · output 25,468 (median 484; max 5,688, the
truncated L12) · thinking 35,166 (median 597). **Estimated cost USD 0.162** (list price × counters; billing UNKNOWN, 0 on
the free tier); reservation accounting USD 1.052 of the 1.06 cap. Pilot + locked: 76 requests, est. USD 0.299.

## Preregistered decision (frozen scorer) and the correction beside it

| | frozen (`score.json`) | correction (`corrections/`) |
|---|---|---|
| unsafe rows (P1) | 1 — L01 `WRONG_SERVED` → **P1 FAIL** | 0 → P1 PASS (two-sided exact 95 % upper bound 8.0 %; one-sided 6.6 %) |
| goal+entity on expressible requests (P2) | 24/45 = 0.53, CI95 [0.379, 0.683] → **NO** | 27/45 = 0.60, CI95 [0.443, 0.743] → NO |
| case extraction correct | 7/43, CI95 [0.068, 0.307] | 9/43, CI95 [0.100, 0.360] |
| answer | **UNSAFE** | **NO** |

The preregistered answer stands as **UNSAFE**. The correction is reported beside it because the one unsafe row is a
scorer artifact, verified from the receipts by two agents: on L01 the route served `AC' = 13`, equal to the oracle
(169 = 13²), for the asked object (`length`, points A, C'), and nothing else. Gemini's facts differed from gold only in
slots the planner does not use for those kinds — `measure` on a question (`_cau_hoi` never reads it), `points` on the
solid (read by `_doc_khoi` only into the auxiliary-name set, redundant with the solid name) and `right` on a cuboid
(implied, `_doc_khoi`). The frozen key did not pair the question; its served value was then counted as an unasked answer
without being compared with the oracle — a structural weakness of the scorer (see corrections). The correction changes
2 locked classes/cells (L01 → `CORRECT_COMPLETE`; L02 extraction correct, still a grounding refusal) and one metric row
(L36 goal match); `question.measure` alone accounts for all of it. Under either scorer P2 is NO.

## End to end (44 rows; correction in parentheses where it differs)

| class | rows |
|---|---:|
| CORRECT_COMPLETE (served, oracle value) | 1 (2: L14, L01) |
| WRONG_SERVED | 1 (0) |
| SAFE_REFUSAL (refusal disposition) | 13 |
| FALSE_REFUSAL_CAPABILITY_GAP (gold arm refuses too) | 22 |
| FALSE_REFUSAL_EXTRACTION (gold serves, live extraction wrong) | 6 — L04, L06, L09, L15, L24, L41 |
| NO_PARSE (L12 truncated at 5,688 output tokens) | 1 |

Always-refuse baseline 13/44 — the live safe refusals equal it, so refusal behaviour alone shows no skill. Group E
(context not sent): 6/6 safe refusals. L14 counts as complete because "Tính góc" was not labelled as asking degrees; the
user sees cos²=25/169, not 67.38°.

## Extraction (43 parsed rows; agreement with the implementer encoding; frozen → correction)

| metric | value |
|---|---|
| intent (role/kind/quantity, one-to-one) | 42/57 (74 %) |
| goal + entity, all requests | 24/57 → 27/57 |
| goal + entity, expressible requests | 24/45 → 27/45 |
| premise recall | 139/165 (84 %) → 140/165 |
| premise precision | 142/182 (78 %) → 143/182 (≈ 142/175 if the 7 name-only `triangle` shapes the planner ignores were excluded) |
| multi-goal completeness (gold ≥ 2 requests) | 4/11 (L23, L27, L29, L41) |
| extra requests / unmatched premises | 32 / 40 → 29 / 39 |
| unsupported requests matched as `unsupported` | 0/12 scored; in substance 1/12 — L35 used `unsupported` for the camera request itself but with role `premise` (the engine refuses it either way) |
| unsupported requests approximated by an expressible ask | 6 (L08 draw+explain → angle; L10 `SC²` → length; L21 face centre → distance; L42 maximum over a moving point → area; L31, L33 context references) |
| invented labels | 3 rows: `G` (L19 centroid), `M` (L21), `H` (L22 unnamed foot — stopped by Source Grounding `UNKNOWN_LABEL`) |
| quotes not in the source / `ambiguous` set | 1 row / 2 rows |
| case extraction fully correct | 7/43 → 9/43 |

Error types on parsed rows: request without operands 14 · measure (`base_edge`/`height`/`edge`) without its solid 14 ·
three-point right angles 4 · added `altitude` 2.

## Where each row stopped (`attribute_layers.py` → `layer_rows.json`)

| layer that stopped the live row | rows | extraction correct (correction) |
|---|---:|---:|
| served | 2 | 2 |
| planner input — malformed/incomplete facts (`SCHEMA_INVALID` 12, `UNKNOWN_SOLID` 11, `FACT_INCOMPLETE` 5, `AMBIGUOUS_FACT` 1) and L19, a request without operands that the planner read as plane–plane (`UNSUPPORTED_CAPABILITY`) | 30 | 0 |
| Source Grounding (`NOT_ASKED_IN_SOURCE` 3, `PREDICATE_NOT_IN_QUOTE` 2, `CONDITIONAL_CLAUSE`, `UNKNOWN_LABEL`, `QUESTION_CONTEXT_UNSUPPORTED`, `UNGROUNDED_VALUE`, `PLANE_NOT_IN_QUOTE`) | 10 | 7 |
| extraction flagged unsupported (`OUT_OF_SCOPE`, L35) | 1 | 0 |
| provider / parse (`RESPONSE_TRUNCATED`, L12) | 1 | — |
| Planner / Engine | 0 | — |

Gold arm on the same 44 texts: served 8; Source Grounding 18; unsupported by the schema 12; planner input 1 (L38, the
planner's role gate on a `condition` fact); engine 5, of which 3 are capability gaps (L17 intersection line without
dimensions, L19 centroid, L29 line–line angle) and 2 are correct refusals (L40 underdetermined apex, L44 inconsistent
data). Of the 8 gold-servable cases, 2 were served live and 6 lost to extraction errors at planner input. 9 rows were
stopped by Source Grounding in both arms (8 with the same code; L22 differs).

## Attribution

- **Semantic extraction (LLM) — the dominant cause.** 34 rows have an incorrect extraction (correction scorer): 30
  stopped at planner input, 3 at Source Grounding (L08, L22, L36), 1 flagged unsupported (L35); plus L12 unparsed.
  None was served. The model mostly names the right quantity (74 %) but drops the asked objects (14 rows) or the solid a
  measure belongs to (14), approximates 6 of 12 out-of-schema requests instead of marking them `unsupported`, and invents
  point names (3).
- **Source Grounding.** Correct extractions refused as the gold facts are: L03 "… thì … bằng mấy", L13 "Tính cos²",
  L27 "Tính BD'" (same code and reason as gold), L02 "dài bao nhiêu" (correct only under the correction), and L23
  (`NOT_ASKED_IN_SOURCE`, here on the volume clause "Tính thể tích tứ diện"; the gold arm is refused on "rồi suy ra …"
  although it carries the same volume quote — the order dependence is not diagnosed). These are false refusals of the
  gate for valid wordings, not LLM errors. The gate also stopped one hallucinated label (L22).
- **Planner / Engine.** No live row was stopped by a capability gap; the gold arm's 3 gaps (L17, L19, L29) are masked in
  the live arm by earlier extraction failures.
- **Schema.** 12 requests have no schema form (segment distance, squared length, face centre, construct/explain,
  interaction, optimisation, context); refusing them is correct, not coverage.
- **Scene3D.** Reached only by the 2 served rows; no rendering claim.
- **Safety.** With the correction no row was served wrongly on this corpus; offline counterfactuals by the reviewer show
  Source Grounding would also have caught two of the six approximations (L08, L10) had the planner not refused them
  first. Nothing here bounds safety beyond these 44 items; under the frozen scorer the preregistered answer is UNSAFE.

## Gold Typed Facts vs Gemini live (same 44 texts)

| | gold facts | Gemini live |
|---|---:|---:|
| served correct | 8 (7 + 1 flagged) | 1 frozen / 2 corrected |
| unsafe | 0 | 1 frozen / 0 corrected |
| safe refusals | 13 | 13 |
| refusals for capability / grounding / schema gaps | 23 | 22 |
| refusals caused by extraction | 0 | 6 (+1 no-parse) |

## Limits

44 items with 4 minimal pairs (not independent); one AI corpus author, no human validation; agreement measured against
the implementer's encoding with the preregistered equivalences plus one post-hoc correction; one sample per item;
temperature 0 is not determinism (pilot: 10/15 pairs identical). No prompt, schema, model, label, oracle or product
change before, during or after the run.

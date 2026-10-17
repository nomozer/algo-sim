# Preregistration — independent NLU extraction evaluation (route D, branch B)

2026-10-17 · branch `research/independent-nlu-extraction-evaluation` from `main` `76dca142` · `LLM_ONLY`, `CACHE_VERSION = 125`,
Hybrid NO-GO. The lock is the checkpoint commit that adds this file; no live request precedes it. Live execution needs a
separate human approval (`approval-request.md`). This file is hashed into every run identity: editing it after approval
invalidates the approval.

## 1. Question and decision rule

Can the configured LLM turn Vietnamese 3D-geometry requests — in wordings **never shown to the LLM** (the prompt carries
no examples) — into Typed Facts that (1) carry the right intent, (2) name the right entities/relations, (3) add no facts,
(4) omit no request, (5) pass Source Grounding, (6) let the deterministic Planner compose Geometry Functions, (7) yield
an Engine-verified simulation? Each layer is scored separately; there is no single accuracy.

Decision on LOCKED (`decide()` in the runner, mechanical):
- **P1 safety** PASS iff 0 unsafe rows (`WRONG_SERVED`, `PARTIAL_SERVED`, `OVER_SERVED`); the exact 95 % upper bound of
  the unsafe rate is reported (0/44 ⇒ ≤ 8.0 %).
- **P2 extraction** on goal/entity agreement with the *expressible* gold requests: **YES** if ≥ 0.85 and the exact 95 %
  lower bound ≥ 0.70; **NO** if the upper bound < 0.85; otherwise **INCONCLUSIVE**.
- Answer: `UNSAFE` if P1 fails, else P2's value. Case-level extraction correctness is reported with its interval, without
  a threshold. A YES is a statement about this corpus and this configuration only — not about Vietnamese in general,
  and not a Hybrid enablement decision.

Extraction scores measure **agreement with the implementer's faithful encoding**, with the equivalences listed in §5;
they are not an absolute proof that a fact was added or omitted.

## 2. System under test (locked; Phase A audit in `audit/extraction-architecture.md`)

| item | value |
|---|---|
| provider | Gemini API REST `v1beta/models/{model}:generateContent` via `function_calling.live_transport` (header key, 1 attempt) |
| model | `gemini-2.5-flash` (API model id; not an IDE model label). Accepted `modelVersion`: exactly it or `gemini-2.5-flash-NNN` |
| adapter | `app/ai/fact_extraction.py` unchanged: `build_request` → `parse_response` → `run_fact_route` |
| surface | `surface_fingerprint()` = `485d3834db8b18cf…` (same value the product test locks) |
| config | temperature 0, `maxOutputTokens` 8192 (thinking shares it), JSON + `responseSchema`, no `thinkingConfig` |
| sent | system prompt, schema, the case `source_text` only — never context, labels, gold facts or oracle values |
| product | candidate `57c7f5db…` (`--verify` MATCH on this branch); prompt/schema/Registry/Planner/Engine unchanged |

## 3. Data and independence

| set | author | size | use |
|---|---|---|---|
| corpus `inputs/corpus-authoring/corpus.json` | AI subagent blind to the system (no repository access), from the verbatim brief `inputs/corpus-authoring/AUTHORING_BRIEF.md` | 60 cases: dev 16 (14 structures), locked 44 (40 structures) | semantics, dispositions, expected values |
| oracle `agent1_oracle.py` | same blind author, `fractions` only, own coordinates | 56 values in 43 cases + 12 structural checks | numeric truth |
| gold facts `inputs/gold_facts.json` | implementer, `build_gold_facts.py` | 60 cases, 319 facts | extraction reference + deterministic ceiling |

Independence: **INDEPENDENT_AGENT_AUTHORED_NOT_HUMAN_VALIDATED** (corpus, labels, oracle); gold **IMPLEMENTER_AUTHORED**.
A separate read-only agent recomputed 44 oracle values independently (0 mismatches). No human held-out claim.

Multi-request: 12 locked cases by the corpus annotation; 10 by gold request facts (D11/L25 "dựng hình chiếu … rồi tính"
encode the construction as a projection premise, scored by premise recall). Both counts are reported.

Minimal pairs are not independent items and are reported as pairs: locked L09/L10, L11/L12, L13/L14, L15/L16; the same
line-vs-segment design also appears in dev D04/D05 (harmless only because nothing may change after the pilot).

Overlap with texts already in the repository (5-gram character containment, independent audit): D10 0.988 vs
`backend/tests/geometry/fixtures/text_to_functions_cases.json`; L40 0.943 vs a regular-pyramid LABELS fixture (theirs
answerable); D01 0.889 vs the previous unseen set; L44 0.82 vs `hybrid_holdout_cases.json`; others ≤ 0.77. The LLM prompt
shares one 5-gram with the corpus. Hence: wordings are unseen **by the LLM**; the deterministic route was developed on
some similar fixtures, which matters for route outcomes, not for extraction.

Dev cases may be inspected and drive harness fixes; locked cases may not drive any prompt/product change.
Earlier corpora (`hybrid-semantic-grounding-reliability` A13/A14/B05/U*) are diagnostics only and not part of this test.

Gold rule: encode faithfully by the product prompt rules; what the schema cannot express is `unsupported`. Authoring
errors and audit findings may be fixed before the lock (`inputs/gold_authoring_log.md`); an encoding is never changed
because the route refuses it. Gold-arm refusals are capability or grounding gaps, not gold errors.

## 4. Arms

- **GOLD** — gold facts → deterministic route (0 calls): the extraction-perfect ceiling.
- **REPLAY** — a fake provider returns the gold facts through the full live code path (0 calls; `execution_class FAKE`).
- **LIVE_PILOT** — dev, 16 cases × 2 samples = 32 calls (stability/schema check). **LIVE_LOCKED** — locked, 44 × 1 = 44
  calls, only after `pilot_gate()` returns `CONTINUE_TO_LOCKED`.

## 5. Scoring (`backend/scripts/run_nlu_extraction_evaluation.py`, frozen by `runner_sha256` + `helpers_sha256`)

Fact match: equal content — kind, role, negated, quantity, operand labels (vertex order ignored), point/at/point_kind,
exact value, measure, solid (ignored on triangle-area asks), solid type, shape, regular/right, plane relation, the content
of a `line_ref` target. Ids, quotes, `reason` ignored. Equivalences: a plane operand of ≥ 3 labels matches a containing
or contained label set; distance/angle and symmetric relations match in either operand order; named-segment lengths
compare as a set closed under `equal_lengths` (`AB = AC = 2` as two lengths or as equal_lengths + one length); listed
gold alternatives (OH as distance, centroid distance, AA' as height/lateral edge). `unsupported` facts match only by role
and an overlapping quoted source region. Quotes are grounded with the product's own normaliser (`registry.chuan_hoa`).

Extraction (per parsed row): intent (one-to-one on role/kind/quantity); goal/entity (all requests, and expressible
requests only); premise recall and precision; multi-goal completeness; unsupported-request flagging and approximation
(an expressible fact quoting an unsupported request); extra requests; unmatched premises; ungrounded quotes;
`ambiguous` flags; non-object facts. **Extraction correct** = all requests matched, none extra, all required premises,
no unmatched premise, no ungrounded quote, no ambiguous flag, no malformed fact.

End to end (per row), against the corpus disposition (group E with a context: `clarification_required`,
`CONTEXT_NOT_SENT`, reported separately): `CORRECT_COMPLETE` · `CORRECT_VALUE_COS2_FORM` (value right, shown as cos²
while degrees were asked) · `CORRECT_PART_FLAGGED` (supported part right, proof flagged not proven) ·
`CONSTRUCTION_SERVED` (no numeric request; visual completion NOT scored) · `PARTIAL_SERVED` (a request unanswered) ·
`OVER_SERVED` (an unasked answer added) · `WRONG_SERVED` (a wrong value, another object answered, or served where the
disposition is a refusal) · `SAFE_REFUSAL` · `NO_PARSE` · `FALSE_REFUSAL_CAPABILITY_GAP` (gold arm refuses too) ·
`FALSE_REFUSAL_EXTRACTION` · `FALSE_REFUSAL_GROUNDING` (gold arm serves, live extraction correct) ·
`PROVIDER_OR_HARNESS_ERROR`. Values: squared magnitude, or cos² for angles, at a = 1. A safe refusal is never a
completed simulation; answering SC when SC² is asked is `WRONG_SERVED`.

Cells: LLM correct ∧ served correct · LLM correct ∧ safe refusal · LLM correct ∧ pipeline unsupported · LLM correct ∧
unsafe served · LLM wrong ∧ unsafe accepted · LLM wrong ∧ refused · LLM wrong ∧ benign served. Also reported: refusal
codes, the always-refuse baseline (locked: 13 of 44 rows have a refusal disposition), group E apart, GOLD vs LIVE side
by side. Pilot rows are never pooled into the locked score. Latency, input/output/thinking tokens and estimated USD
(list price × counters; provider-confirmed cost unavailable) are reported separately.

## 6. Budget, stops, receipts

Caps (`inputs/build_protocol.py`, the runner's own reservation): PILOT 32 calls / 629k accounted tokens / USD 0.77;
LOCKED 44 / 864k / USD 1.06; 0 retries; 90 s timeout. Stop rules, pilot criteria and decision rule: `inputs/protocol.json`.
Receipts: `manifest.json` per run (redacted raw responses, usage, model version, response id, latency, reservation,
per-row route) and a SCORE receipt (`--out`); never overwritten; output directory byte-scanned for the key after every
write; SCORE refuses a manifest whose rows hash or input identity does not match.

## 7. Known limits accepted in advance

- Deterministic ceiling is low: the gold arm serves 8/44 locked cases (7 complete + 1 flagged). Live end-to-end success is
  bounded by it; extraction-level and safety metrics carry most of the information.
- One AI corpus author; Vietnamese naturalness and labels are not human-validated.
- Corpus judgment calls (L16, L38–L43, D08/L19/L22) are kept as labelled; disagreements go to a correction receipt
  beside, never instead of, the locked score.
- Temperature 0 is not determinism; the pilot samples twice; the locked set samples once.
- Prompt rule 7 asks for three labels per plane while the source gate refuses a three-label reading of `(ABCD)` (L39):
  recorded as a finding, not changed.

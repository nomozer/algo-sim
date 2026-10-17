# LIVE_PILOT — per-layer analysis (dev split, diagnostic; not the locked score)

Owner approval: GO PILOT ONLY (2026-10-17, `C:\Users\Bunny\nlu-approval.json`, written by the owner). Executed at
`6255a743`, identity equal to `approval-identities.json`. Receipts: `manifest.json` (32 rows, redacted raw responses),
`score.json` (SCORE receipt, gate). MEASUREMENT_CLASS LIVE · split dev (16 cases × 2 samples) · EVALUATOR: deterministic
scorer frozen at the lock; labels by the blind author, gold by the implementer.

## Execution

32/32 rows, 32 live requests, 0 retries, no stop rule fired, every `modelVersion` = `gemini-2.5-flash`, usage on all
32 rows, no key-like string in the artifact. Latency min 1.6 s, median 7.1 s, max 34.4 s, total 253.5 s.
Tokens: input 25,106 · output 22,074 · thinking 29,762. **Estimated cost USD 0.137** (list price × counters;
provider-confirmed billing UNKNOWN — 0 on the free tier). Budget accounting reserved USD 0.765 of the 0.77 cap
(conservative: real input ≈ 785 tokens/call against a reservation of ≈ 11.7k).
Pilot gate (`score.json`): parsed 31/32, truncated 1 (D05 sample 2: 5,989 output tokens, runaway), verdict
**CONTINUE_TO_LOCKED**. The gate certifies harness/model health only, not extraction quality.

## End to end (32 rows)

| class | rows |
|---|---:|
| SAFE_REFUSAL (correct disposition: D13 context, D14, D15, D16) | 8 |
| FALSE_REFUSAL_CAPABILITY_GAP (gold arm refuses too) | 19 |
| FALSE_REFUSAL_EXTRACTION (gold serves, live extraction wrong: D01 ×2, D10 ×2) | 4 |
| NO_PARSE (truncated) | 1 |
| served (any class) | **0** |
| unsafe (WRONG/PARTIAL/OVER_SERVED) | **0** |

Safety: 0/32 unsafe (exact 95 % upper bound 10.9 %). Every wrong extraction was refused; none was accepted.
Completion: 0/4 of the rows the gold arm can serve — the deterministic route never reached Scene3D in this pilot.

## Extraction (31 parsed rows; agreement with the implementer encoding)

| metric | value |
|---|---|
| intent (role/kind/quantity) | 32/37 (86 %) |
| goal + entity, all requests | 16/37 (43 %) |
| goal + entity, expressible requests | 16/34 (47 %) |
| premise recall | 100/132 (76 %) |
| premise precision | 101/164 (62 %) |
| multi-goal completeness (≥ 2 requests) | 4/4 (D10, D12 both samples) |
| extra requests / unmatched premises | 19 / 63 |
| facts with a quote not in the source | 3 rows |
| unsupported requests flagged as `unsupported` | 0/3 (D14 → empty fact list; D05 segment → approximated as a line once) |
| case extraction fully correct | 1/31 (D13, a context-free question correctly refused) |
| identical fact content across the two samples | 10/15 parsed pairs (D02, D10, D11, D13, D16 differ) |

## Where the failures come from

Extraction (model), counted on 31 parsed rows:
- **Request operands omitted** — a `question` with only `quantity` (e.g. distance with no point/plane): 14 rows.
  This is the main cause of the low goal/entity score; intent is mostly right, its objects are dropped.
- **Measure without its solid** — `length` with `measure = base_edge/height/edge` and no `solid`: 20 rows
  (`UNKNOWN_SOLID` in 13). The model prefers `base_edge 2` over the shape value; the slot it then needs is missing.
- **Added facts** — redundant `altitude` without solid (7 rows, `FACT_INCOMPLETE`); `polygon_shape` without a shape
  for a trapezoid (D04/D05); extra `triangle` shapes.
- **Invented labels** — `M` for an unnamed midpoint (D07), `G_A'BD` for a centroid (D09, `SCHEMA_INVALID`): 4 rows.
  This is the hallucination the source gate is built to stop; here the schema stopped it first.
- **Schema misuse** — `right_angle` with three points (8 rows), `value: "A'H"` on a question (D11).
- **No `unsupported`** — the model never used the schema's unsupported kind.

Grounding/Planner/Engine: not reached on most rows because the planner rejected incomplete facts first
(`UNKNOWN_SOLID` 13, `FACT_INCOMPLETE` 9, `SCHEMA_INVALID` 7, `NOT_ASKED_IN_SOURCE` 2, `RESPONSE_TRUNCATED` 1).
Capability gaps (19 rows) coincide with the gold-arm refusals already recorded. Scene3D: not reached.

## Reading

On this dev sample the baseline extractor understands *what kind* of quantity is asked (86 %) but too often does not
fill *which objects* (47 % goal/entity on expressible requests) and adds or under-specifies premises; the deterministic
gates refuse every such output, so the failure is safe but complete-coverage is 0. Small sample (16 cases, 2 samples);
dev was not held out from the gold author. No prompt, schema, model or product was changed.

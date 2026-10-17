# LIVE PILOT — paired baseline vs v2 (dev split)

Owner decision: **GO PAIRED PILOT ONLY** (2026-10-17); approval files written by the owner, one per arm, PILOT identity
only (no LOCKED identity present). Executed on the research tree `7ee8cc14` (identities produced at `c640cd14`, verified
equal before sending). MEASUREMENT_CLASS LIVE · HELD_OUT_CLAIM none (dev split, the tuning split) ·
EVALUATOR_INDEPENDENCE scorer /2 locked at `6ceb2508`, unchanged. Receipts: `live-pilot-baseline/score.json`,
`live-pilot-v2/score.json` (derived; raw manifests only under ignored `.superpowers/sev2-live/`, row hashes recorded).

## Execution

24/24 requests (12 per arm), 0 retries, no stop rule, every `modelVersion` = `gemini-2.5-flash`, usage on all 24 rows.
Prompt, schema, scorer and corpus were not changed during the measurement.

| | baseline (`485d3834…`) | v2 (`c4e4392c…`) |
|---|---:|---:|
| input / output / thinking tokens | 9,372 / 11,152 / 17,323 | 14,832 / 5,603 / 12,262 |
| est. USD (list price × counters) | 0.0740 | 0.0491 |
| reservation accounted (cap 0.50) | 0.287 | 0.294 |
| latency median / max / total (s) | 7.75 / 31.87 / 133.6 | 7.25 / 12.66 / 92.4 |
| truncated (`MAX_TOKENS`) | 1 (dev06) | 0 |

Pilot total est. USD 0.123. v2 sends a longer prompt (+58 % input) but the model writes and thinks less (−50 % output,
−29 % thinking), so it is cheaper and faster on these 12 items.

## End to end

| class | baseline | v2 |
|---|---:|---:|
| served correct | 0 | 0 |
| unsafe (wrong / partial / over / form) · unscorable | 0 · 0 | 0 · 0 |
| safe refusal | 5 | 5 |
| false refusal — extraction (GOLD serves) | 2 (dev01, dev03) | 2 (dev01, dev03) |
| false refusal — capability/grounding gap (GOLD refuses too) | 4 | 5 |
| no parse | 1 (dev06 truncated) | 0 |

The GOLD ceiling on dev is 2/12; neither arm reached it. "0 unsafe" is mostly refusal at planner input: it shows the
gates hold, not that the model understood the problems (always-refuse would also score 5 safe refusals).

## Extraction (denominators from source requests; parse failure stays in them)

| metric | baseline | v2 | GOLD |
|---|---:|---:|---:|
| intent proxy (kind/role/quantity) | 10/16 | **13/16** | 16/16 |
| goal + entity, all requests | 6/16 | 7/16 | 16/16 |
| goal + entity, expressible | 5/11 | 5/11 | 11/11 |
| operand correctness | 2/8 | 2/8 | 8/8 |
| solid association | 3/6 | 3/6 | 6/6 |
| multi-goal complete | 0/4 | 1/4 | 4/4 |
| unsupported flagged as unsupported | 0/1 | 0/1 | 1/1 |
| rows with invented entities | 1/12 (`G`, dev05) | **0/12** | 0/12 |
| parsed rows | 11/12 | 12/12 | 12/12 |
| premise recall · precision (parsed rows) | 33/46 · 33/51 | 37/53 · 37/58 | — |

Paired by case: v2 better on dev07 (goal, operand), dev12 (two goals), dev05 (no invented `G`), dev06 (parses);
worse on dev03 (the length/area operands dropped). Goal, operand and solid cells are otherwise equal; premise recall
moves both ways (higher on dev03, dev07, dev09; lower on dev02, dev10, dev11).

## Why rows stopped (both arms)

The dominant failure is unchanged by v2: **question operands are not placed in the operand slots.** dev01 puts the
asked objects into `value` (`"AG"`, `"ABCD"`) in both arms → `SCHEMA_INVALID`; dev02/dev03/dev06 (v2) send questions with
only `quantity` and `solid`. dev04 still emits a **three-point right angle** in both arms despite rule 5. Altitudes lose
their `solid`/`points` (dev03, dev09). The response schema does carry the field descriptions; but it is one flat object
whose only required fields are `id`, `kind`, `role`, `quotes`, so nothing structural ties a question's quantity to its
operand slots. A system-prompt rule alone did not change that behaviour.

## Reading (descriptive, 12 items, no population claim)

- **Measured gains of v2:** fewer invented labels, no truncation, more parsed rows, better intent proxy, one multi-goal
  item complete, lower tokens/cost/latency. All small counts.
- **Not improved:** operand completeness 2/8 → 2/8, solid association 3/6 → 3/6, expressible goal/entity 5/11 → 5/11,
  unsupported detection 0/1 → 0/1, served 0 → 0. Against the preregistered P2 thresholds (≥ 0.85) both arms are far
  below on this split.
- Pilot gate (approval-request.md): both arms complete, no stop, usage on every row, no unsafe/unscorable → **PASS**
  technically.

## Recommendation on held-out (owner decision)

**Do not run the 48 held-out requests for this prompt.** The dev pilot already shows the dominant extraction failure is
not fixed; a held-out run would very likely confirm P2 NO for both arms and spend the fresh held-out on a candidate that
needs repair (the prereg retires the held-out once repair follows its results). Recommended next step, a separate
approved wave: make the provider contract carry the operand obligation — e.g. per-kind/per-quantity response shapes
with required operand slots and a two-ray right angle — designed and tuned on dev (and on these pilot receipts), then a
single paired held-out run. That is a schema/surface decision, outside this wave's scope.

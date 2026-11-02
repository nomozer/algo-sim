# Constraint extraction pilot — protocol (pre-registered, eighteenth continuation, 2026-11-02)

**Status: `NOT_MEASURED`.** No provider call was made. A run needs its own Owner-written approval; none exists.

**Question.** C17 opened `plane_kind = "constrained"` and C18 opened `orthocenter` / `circumcenter` in
`typed-fact-next/2`. Both are model-surface changes that only gold extractions have exercised. Does Gemini, from the
Vietnamese text alone, emit them correctly — and never invent a construction or a GIVEN?

## 1. Measurement metadata

| field | value |
|---|---|
| `MEASUREMENT_CLASS` | `LIVE_DEVELOPMENT_PILOT` |
| `HELD_OUT_CLAIM` | none: implementer-authored texts, gold in the repo |
| `AUTHORING_INDEPENDENCE` | `NOT_ESTABLISHED` (texts from the C17 / C18 generators) |
| `EVALUATOR_INDEPENDENCE` | deterministic scoring below, fixed before any request |
| arm | one: the production opt-in Hybrid `/4` path, one source-only request per case |
| model | bound in the approval; no fallback model |
| caps (proposed, not granted) | 16 HTTP requests including retries (one per case, no retry); USD 1.0 |
| stops | request cap, USD cap, provider block, 3 consecutive infrastructure failures, identity change, interruption |

## 2. Corpus

`constraint-extraction-pilot-corpus.json`, built once by `tools/build_constraint_extraction_pilot.py` (selection rule
fixed in the builder: the first rows of each stratum in generator order). Gold replay offline:
`constraint-extraction-pilot-gold-replay.jsonl`, 14/14 gold rows end as expected.

| stratum | n | content | expected |
|---|---|---|---|
| K-A | 4 | a plane through stated points, ⊥ a face or ∥ an edge, oracle UNIQUE | SERVED |
| K-B | 2 | constraints fixing no plane (NOT_UNIQUE) or contradicting (NO_PLANE) | REFUSED |
| K-C | 6 | a centre named by its property, composition NECESSARY by the oracle, two topologies, both kinds | SERVED |
| K-D | 2 | a centre of a collinear triple | REFUSED |
| K-E | 2 | an ambiguous reference ("một mặt bên", "một tam giác có ba đỉnh thuộc hình chóp") | CLARIFY |

## 3. Scoring (per case, from the model's raw `/2` extraction and the `/4` outcome)

1. **Kind**: `plane_kind = "constrained"` with the gold multiset of constraint kinds; or the described kind
   (`orthocenter` / `circumcenter`).
2. **Operands**: the gold operand label sets (constraint operands; the triangle's three labels).
3. **Quotes**: every quote non-blank and verbatim in the text (the Source Gate re-checks this anyway).
4. **Ownership**: operands scoped to the right solid (`solid_id`), no label outside the text.
5. **Uniqueness**: K-E must not be resolved to one reference (CLARIFY or `unresolved`), never SERVED.
6. **No construction**: no `described_points` or premise the text does not state (a foot, a midpoint, a translate);
   no constraint the text does not state.
7. **No fake GIVEN**: no premise whose quote states no given.
8. **End to end**: outcome equals `expected`; a SERVED answer equals the oracle (squared, exact).

Attribution as in the S-2 protocol: a gold reproduction that misses its expectation is a deterministic-layer fault, not
the model's.

## 4. What it can and cannot show

It can show whether the extraction surface opened in C17/C18 is usable by the live model on these 16 texts. It cannot
show held-out generality, student wording, or anything about the planner (the planner is measured offline:
`composition-c18.md`).

## Revision A (C19, 2026-11-02, before any live run)

The pilot is now runnable as study **`K-1`** of the S-2/R-1 runner (same transport, budget, identity guard, scorer and
gold-replay attribution). Corpus: `k1-live-pilot-corpus.json` (built by `tools/build_k1_live_corpus.py` from the 16 cases
above; nothing re-selected). Changes, all found by the offline gold replay, never by a model output:
- K-B01 (constraints fix no plane) expects **`REFUSED_UNDERDETERMINED`** (refusal group `MISSING_DATA`), as §2 above
  registered ("REFUSED"); the first conversion had mapped it to CLARIFY, which only a model could produce and only the
  engine can see.
- K-E gold is the honest exit (the source gold without the ambiguous object and its goal, plus one `unresolved`).
- Metrics §3: 1 and 2 are the runner's `constraint_check` / `described_check`; 8 is the scorer plus `hybrid_outcome`.
  6 is `no_invented_construction` ONLY for extra described points and sections (review MINOR-3); an extra premise,
  relation, goal or GIVEN is seen by the facts signature (`extraction_accuracy`) and refused by the Source Gate, not by
  this field. 4 (ownership) and 7 (no fake GIVEN) are not scored separately: the facts signature and the Source Gate
  cover them.
- Review MAJOR-1: K-B and K-E count as correct only for the gold's reason (`reason_verified`: same code and same facts;
  an `unresolved` on the gold's ambiguous wording).

Gold replay (`k1-live-pilot-gold-replay.jsonl`): **16/16**, 0 wrong-served. Approval template
`k1-owner-approval.template.json`: 16 requests (one per case, no retry headroom), USD 1.0; worst-case estimate USD 0.39.

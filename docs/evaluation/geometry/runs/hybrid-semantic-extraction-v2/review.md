# Independent reviews — Semantic Extraction v2

All reviewers are AI agents with repository access (Codex sub-agents, then a Claude sub-agent); none is human
validation. No reviewer made a network or model call or edited repository files.

## Before the takeover (Codex, 2026-10-17)

- **Extraction audit** (A1–A7): the TypedFact schema already represents the measured operand/solid/multi-goal omissions;
  the prompt never taught them. Smallest candidate: prompt clarification, no schema/planner change.
- **Grounding audit**: valid wordings refused by Source Grounding (`dài bao nhiêu`, `… thì … bằng mấy`, `Tính cos²`,
  repeated `tính`, `rồi suy ra`, projection wording); unnamed centroid is a capability gap; ordinary plane operands may
  keep all labels, `line_ref` producers need exactly three.
- **Methodology audit**: L01 `WRONG_SERVED` is a scorer artifact of fact pairing; corpus/oracle 34/34 recomputed, 0
  mismatches; 33 gold encoding corrections required, then PASS for the corpus/gold lock.
- **Scorer review 1** (Codex): four defects + two execution concerns; Codex patched them, then stopped on its usage limit
  before any re-review.

## Scorer review 2 (Claude sub-agent, after the takeover) — NOT_READY → LOCK_READY

Round 1 verdict **NOT_READY**. Findings and disposition (each fixed one is a RED→GREEN test in
`backend/tests/geometry/test_semantic_extraction_evaluation.py`):

| # | severity | finding | disposition |
|---|---|---|---|
| 1 | BLOCKER | correct tetrahedron volume (`OPQR` served as the planner's `R.OPQ`) scored WRONG_SERVED | fixed: solid = vertex structure (`_solid_key`) |
| 2 | BLOCKER | operand ratio > 1 (numerator counted `unsupported` gold goals) | fixed: one population `_operand_goals` |
| 3 | IMPORTANT | model-chosen answer ids reached `score.json` via `extra` | fixed: `extra_count` only |
| 4 | IMPORTANT | receipt could not tell REPLAY from LIVE; no usage/latency | fixed: execution class, identity, stop, calls, budget, usage |
| 5 | IMPORTANT | invented labels in the `solid` slot undetected | fixed |
| 6 | IMPORTANT | midpoint-to-named-line distance unscorable even if correct | fixed: only via an executed foot on that line |
| 7 | MINOR | parse status checked before a SERVED route | fixed; infra rows are `PROVIDER_OR_HARNESS_ERROR` |
| 8 | MINOR | non-dict auxiliary crashed | fixed (also non-dict operand/target, round 2) |
| 9 | MINOR | point-to-point "distance" via `ask_length`, rotated pyramid base | pyramid fixed with #1; distance-by-length left: no corpus item, errs to WRONG_SERVED |
| 10 | MINOR | baseline prompt leaked to a later v2 harness in one process | fixed |
| 11 | MINOR | gold `equal_lengths` never matched itself (inherited V1) | fixed in the v2 wrapper; V1 untouched |

Round 2 verdict **LOCK_READY**: every original reproduction killed; 24 adversarial solid pairs, equal-lengths and
named-line effect-chain attacks found no wrong acceptance. Remaining MINOR, accepted: contradictory live lengths can still
satisfy an `equal_lengths` premise (premise recall is diagnostic only); infra checked before route status (no producing
path). Gold route on all 36 cases: dev 1 correct / 5 safe / 6 capability gap, heldout 2 / 4 / 18, **0 unsafe, 0
unscorable**, agreement metrics complete on gold.

Also found by Claude before the review: polygon order (`ACBD` accepted as `ABCD`), section planes by containment,
`capability_gap` constructions that executed counted as missing (GOLD route, held19 structure), false-refusal split,
rightness of regular prisms. The frozen `run_nlu_extraction_evaluation.py` is byte-identical.

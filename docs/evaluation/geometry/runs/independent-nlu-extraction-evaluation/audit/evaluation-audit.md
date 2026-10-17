# Independent evaluation audit (Agent 3) and disposition

Auditor: separate read-only Claude subagent, fresh context, 2026-10-17, on the uncommitted pre-lock tree. 0 network
calls, no repository writes; offline probes in its own scratch directory (`leak.py`, `oracle3.py`, `adv.py`,
`faults.py`, `persist.py`, `ws.py`, `sym.py`, `replay.py`). Verdict at audit time: **NOT_READY**.

## Findings (condensed from the auditor's report) → disposition

| # | sev | finding | disposition |
|---|---|---|---|
| 1a | MINOR | dev/locked max difflib 0.80; same line-vs-segment design in both splits; locked minimal pairs (L15/L16, L11/L12, L09/L10, L13/L14) are not independent items | prereg §3 reports pairs as pairs and states the design overlap |
| 1b | IMPORTANT | overlap with repo texts: D10 0.988, L40 0.943, D01 0.889, L44 0.82; prompt shares one 5-gram | prereg §1/§3: claim narrowed to "never shown to the LLM"; overlap table published |
| 1b | IMPORTANT | authoring brief not in the repo ⇒ blindness unauditable | `inputs/corpus-authoring/AUTHORING_BRIEF.md` committed verbatim |
| 1c | OK | only `source_text` reaches the provider (payload captured and inspected) | — |
| 2 | BLOCKER | L10 `SC²` encoded as `length SC` | fixed: `unsupported` |
| 2 | BLOCKER | L39 four labels per plane against prompt rule 7 | fixed: three labels; scorer also accepts containment |
| 2 | BLOCKER | `solid` on L23/L28 triangle-area asks | fixed in gold; scorer ignores `solid` on triangle-area asks |
| 2 | IMPORTANT | D04/D05 right trapezoid: right angles expressible | fixed: two `right_angle` facts |
| 2 | IMPORTANT | equal-length chains not equivalent to `equal_lengths` | fixed: segment-length closure in the scorer |
| 2 | IMPORTANT | D11/L25 construct request as premise; L08 one fact for two requests; 12 vs 10 multi-request | L08 split; D11/L25 kept (schema has no construct-request kind), both counts reported |
| 2 | MINOR | vuông cân → right angle only; cuboid AA' without height/lateral alternatives | AA' alternatives added; vuông cân kept (redundant with AB = AC) |
| 3 | OK | 44 values recomputed independently, 0 mismatches; a = 1 convention verified on the engine | — |
| 4.1 | IMPORTANT | empty `pairs` fell back to identity mapping | fixed: no fallback |
| 4.2 | IMPORTANT | extra served answers ignored | fixed: `OVER_SERVED` (unsafe) |
| 4.3 | IMPORTANT | wrong-object answer scored `PARTIAL_SERVED` | fixed: `WRONG_SERVED` |
| 4.4 | IMPORTANT | `schema_gap_flagged` logic | fixed: per gap request, by overlapping quoted region; `schema_gap_approximated` added |
| 4.5 | IMPORTANT | `unsupported` matched on role alone | fixed: role + overlapping quote region |
| 4.6 | IMPORTANT | plane label sets compared exactly | fixed: containment for ≥ 3-label plane operands |
| 4.7 | IMPORTANT | quote grounding stricter than the product | fixed: product normaliser `registry.chuan_hoa` |
| 4.8 | IMPORTANT | unparsed output counted as safe refusal | fixed: `NO_PARSE` |
| 4.9 | IMPORTANT | crash on non-string labels / solid | fixed: coercion; non-object facts counted and make extraction incorrect |
| 4.10 | IMPORTANT | degree requests answered as cos² counted complete | fixed: `CORRECT_VALUE_COS2_FORM` |
| 4.11 | IMPORTANT | correct-cell mixed served and refusals | fixed: split cells; refusal codes and always-refuse baseline reported |
| 4.12 | MINOR | polygon vertex order ignored; intent not one-to-one; `ambiguous` mislabelled; SCORE without gold rows | intent one-to-one; ambiguous makes extraction incorrect; SCORE requires gold rows; vertex order kept with a `ponytail:` note |
| 5 | IMPORTANT | pre-send persistence failure swallowed | fixed: stop `PERSISTENCE_FAILED`, nothing sent (test) |
| 5 | IMPORTANT | continuation gate not implemented | fixed: `pilot_gate()` over the 32 planned rows, written by SCORE `--out` |
| 5 | IMPORTANT | identity omitted imported helpers | fixed: `helpers_sha256`, `preregistration_sha256` |
| 5 | MINOR | invalid key returns 400; SCORE did not check identity/rows hash; stale replay receipts; approval-file authorship | 400 stops at once; SCORE checks rows hash and input identity; receipts regenerated; "human owner only" documented |
| 6 | IMPORTANT | no falsifiable decision rule | fixed: `decide()` P1/P2 with exact intervals, prereg §1 |
| 6 | IMPORTANT | stated counts/claims vs scorer | prereg rewritten (counts, equivalences, classes) |
| 6 | MINOR | pilot criteria wording (cap change; vacuous spend criterion) | cap change = new protocol + restarted pilot; spend criterion removed |

Not fixed by design: failed row write after a paid response would lose the body (persistence failure stops the run;
the provider response id, if any, is not recoverable) — accepted, recorded.

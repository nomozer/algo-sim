# E2E extraction readiness update

Authorization: Session 5 offline consumer research. Provider requests: **0**.

The interface is `Extractor.extract(problem_text: str) -> ExtractionResult | dict | None`. Its only argument is verbatim source text. `ExtractionResult` may contain decoded typed facts and optional numeric usage counters; no model SDK, transport, prompt or endpoint is added. The existing Session 4A `ReplayExtractor` is reused unchanged. `extraction_scoring.py` loads private scoring rubrics only after every extraction invocation has completed. No oracle, gold fact, answer or expected disposition enters the extractor.

`observe` validates canonical `/2` schema and exact `problem_text` identity. Its `SCHEMA_AND_SOURCE_VALID` label means these two checks only: it does **not** certify quote grounding, correct extraction, independent premise coverage or source semantics. Downstream grounding remains the Registry Source Gate's responsibility. `public_receipt` excludes decoded payload and exception text; only validated data stays in memory for scoring.

## Scoring and measurement interface

- Curator supplies source SHA-256, structural paths and accepted values grouped as premise/goal/negation/conditional, plus the complete allowed premise list for invented-premise counting. These are literal structural checks, not an automatic mathematical/NL judge. Curator must cover all requested obligations, source quotations, operand roles and refusal controls; an omitted axis stays UNKNOWN.
- Scoring is bound to the source hash and rejects malformed/empty checks. The implementer has supplied **no independent rubric or new blind dataset**. Tool unit tests use authored fixtures and are labelled accordingly.
- Extraction, source-identity and schema stage times are measured with `perf_counter`. Unexecuted checks are `NOT_EXECUTED`, not zero. Planner/kernel timing fields are `UNKNOWN_NOT_INSTRUMENTED`; scene/browser stages are `NOT_EXECUTED` in the extraction-only track. Session 4A's downstream replay retains its combined offline route latency. This does not measure provider latency or separate planner/kernel cost.
- Optional input/output/thinking token counts, provider latency and USD cost come only from an extractor receipt. Missing counters remain UNKNOWN/absent; negative, nonnumeric, fractional token counts and nonfinite values fail. Actual pricing/model/version and billed-versus-estimated status must be locked externally before any pilot. Unit-test usage values are synthetic test inputs, not measurements.
- Failure codes retain `NO_RECORDED_EXTRACTION`, `SCHEMA_VERSION_MISMATCH`, typed schema failures, source-identity mismatch, extractor technical failure and invalid usage metadata. Session 4A's code-based downstream taxonomy is reused, including technical/unclassified refusals.

## Replayed evidence

Fresh `results/extraction-replay.json`: archived provider outputs 44/44 extraction failures (43 historical flat schema mismatches and one absent output); canonical authored seam 47 rows: 22 verified scenes, 17 source mismatches, one missing premise, one extraction failure, four kernel refusals and two planner limitations. Network attempts 0. These reproduce the earlier seam; they do not create V2 provider samples. No TypedFacts were hand-authored and labelled AI extraction.

Tests: `results/scoring-and-receipts-final/execution.json`, **15 passed, exit 0**, including source-only invocation, omitted data/roles, invented premises, UNKNOWN usage, skipped timing stages, malformed rubric and actual timeout receipt preservation. Targeted backend regression separately runs the original 4A tests.

## Independent handoff

The supplied Session 4A protocol remains authoritative: [`../hybrid-session4a-readiness/INDEPENDENT_HOLDOUT_PROTOCOL.md`](../hybrid-session4a-readiness/INDEPENDENT_HOLDOUT_PROTOCOL.md). No appointed curator or new locked package is recorded in this authorization or the examined public readiness records. Status **PENDING_CURATOR / NOT_EXECUTED**. Private files have not been opened or created by this run.

Curator should appoint an independent adjudicator, seal disjoint pilot/locked sources, gold facts, oracles, rubric, schedule and provenance; commit/witness hashes before outputs are seen. Freeze model/schema/prompt/candidate/harness/camera/thresholds, check contamination against disclosed development sets, and independently score all attempts. Source-only records and rubric packets stay separate.

Offline scorer invocation (from repository root, no model call):

```powershell
& D:/Documents/projects/algo-sim/backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/hybrid-offline-consumer/extraction_scoring.py --records <sanitized-recorded-outputs.json> --rubrics <curator-rubrics.json> --output <new-results.json>
```

The record list uses `case_id`, `source_text`, sanitized `decoded`, and optional `usage`. Rubrics are keyed by case ID and contain `source_sha256`, `checks` (`axis`, nonempty `path`, `accepted`), and optional `allowed_premises`. CLI preserves the scheduled denominator and emits one row per record; missing extraction remains a failure. Duplicate IDs/source scheduling and independent semantic adjudication belong to the curator's locked packet, not an implicit blind claim by this tool.

Keep separate: (1) TypedFacts V2→Scene3D: development offline evidence; (2) NL→TypedFacts V2: **quality UNKNOWN, no eligible new provider samples**; (3) Full NL→Scene3D: **NOT_MEASURED**. Browser results for track 1 do not establish tracks 2 or 3. Live pilot remains **NOT_AUTHORIZED / NOT_READY** pending separate owner GO, curator, actual provider interface, model/prompt lock and enforceable budget/stop rules. Session 4A's proposed 24-request/USD3 limits are a proposal, not permission here.

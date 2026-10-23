# AI-to-TypedFacts V2 E2E readiness

Status: **PARTIAL for offline infrastructure; BLOCKED for an empirical NL→V2 E2E quality claim**.

## Intended boundary

```text
Verbatim natural-language problem
  → Extraction interface: extract(problem_text) → decoded object + optional usage metadata
  → strict typed-fact-next/2 validation and exact source identity
  → bridge_v2 semantic translation
  → Registry Source Gate / bounded goal-directed and section-specific planning
  → Exact Geometry Engine / certificate checks
  → structurally verified Scene3D
  → renderer consumption and visual acceptance (separate checkpoint)
```

The source gate is invoked inside the deterministic route after plan construction, before accepted geometry is served; the diagram describes trust boundaries, not a claim that current execution validates every premise before any planning. Planner-produced auxiliary facts need engine verification and cannot be silently promoted into source premises.

`offline_replay.py` implements the provider-independent seam as `ReplayExtractor.extract(problem_text)`. It receives only the source text. Its recorded output is validated as `/2`; it never sees the oracle, answer, gold disposition or expected refusal. No provider/model SDK or live transport is implemented. All live evaluation remains disabled. Production `flat`, `LLM_ONLY`, route policy and cache identity are untouched.

## Reused data and observed results

Inputs are already tracked project evidence, read in place. The replay reads only `case_id`, sanitized parsed `facts` and parse status from `independent-nlu-extraction-evaluation/results/live-locked/manifest.json`, and matches the exact `source_text` from its locked corpus. It does not persist `raw_response`, text output, traceback or credentials. Input SHA-256 values are in `results/offline-replay.json`.

| Arm | Inputs | Observation | Meaning |
|---|---:|---|---|
| Archived provider extraction | 44 | 43 `SCHEMA_VERSION_MISMATCH`; one `NO_RECORDED_EXTRACTION`; no route execution | Historical outputs are flat facts (one row has no parsed facts), not canonical `/2`. Their conversion is not guessed or hand-authored. This is compatibility evidence, not 44 new extraction attempts. |
| Authored canonical seam | 47 | 22 `VERIFIED_SCENE`, 17 source mismatch, one missing-premise class, one schema extraction failure, four kernel/geometry refusals, two planner limitations | Validates the existing typed route and harness boundary, not provider extraction accuracy. All 25 expected negative cases are refused. |

Fresh twelve-test harness suite passed, including exact source binding, flat rejection, no recorded output, technical/unknown refusal attribution, canonical scene verification and not copying raw output. The new harness was first observed failing when absent; an archive field mismatch was found during execution and corrected to use the corpus's actual `source_text` key. Early pytest temp-directory failures were environmental; final tests use an explicit writable workspace temp directory.

The replay installs a process audit hook rejecting socket connect and DNS events; recorded network attempts are zero. New provider requests are zero. Historical token/cost receipts remain historical; no synthetic replay token counts are treated as provider measurements.

## Failure attribution

Every row retains its exact code. After schema/source identity checks, route-layer attribution reuses `hybrid_preview.classify_refusal`; it is **code-based diagnostic grouping**, not new instrumentation proving the precise origin of every failure.

| Outcome | Definition / boundary |
|---|---|
| EXTRACTION_FAILURE | No recorded decoded output, wrong schema version or `/2` schema validation failure. Missing extraction is not a missing mathematical premise. |
| SOURCE_MISMATCH | Recorded source text differs byte-for-character, gate authority is absent, or the existing source taxonomy rejects source/quote/object binding. Never rewrite source to proceed. |
| MISSING_PREMISE | Existing missing-data/ambiguity taxonomy; retain the exact code. An independent evaluator must distinguish omitted extraction from truly absent source premises. |
| PLANNER_LIMITATION | Bridge/planner/capability/budget refusal, including canonical curved-solid refusal; kernel having a primitive is insufficient. |
| KERNEL_REFUSAL | Existing geometric inconsistency/degeneracy/closure refusal class. Schema failures are caught earlier. |
| TECHNICAL_FAILURE | Internal route/adapter errors or failed engine execution/self-check. Never counted as a correct mathematical refusal merely because status is REFUSED. |
| SCENE_VALIDATION_FAILURE | Scene build/structural validation failure after route execution, separate from browser failure. |
| UNCLASSIFIED_REFUSAL | Unknown codes and non-attributed refusals stay visible; no fallback into a favorable bucket. |
| RENDERER_FAILURE | Reserved evaluation outcome when a valid scene/envelope cannot be consumed/rendered or violates a locked visual obligation. No browser was run in 4A: **UNKNOWN_NOT_EXECUTED**, not PASS or zero failures. |

`VERIFIED_SCENE` means exact route acceptance + `registry.kiem_nguon` authority + existing scene validation; it does not mean independently correct extraction, all requested source obligations satisfied, browser acceptance or pedagogical usefulness.

## Proposed measurement record

Freeze source text/hash, candidate measured hash and complete product commit, prompt/schema/provider versions, route/arm, seed/schedule and expected scope before calls. Use monotonic timing around extraction, validation, planning/kernel and scene rendering, plus total wall latency. Record every attempted call and budget reservation, including refused/failed calls; no silent retries or deleted failures.

- **Extraction:** schema acceptance denominator = all scheduled/attempted inputs, separately report infra/no-output; source-faithful premise/request coverage from independent locked annotations; negation/conditional-role errors and invented facts counted explicitly.
- **Correctness:** acceptance = served / attempted; false serve = served when invalid/underconstrained/out-of-scope or with wrong answer, source claim or required obligation; report numerator and relevant denominator, plus wrong among all served. False refusal = refused on independently preregistered valid supported positives; infra/technical failures reported separately and retained in total failure rate. Correct refusal class agreement is separate from binary refusal.
- **Usage/cost:** input, output and thinking tokens from provider receipts, actual billed/estimated currency distinguished, model/version and effective dated price table locked by owner. Missing counters or pricing remain UNKNOWN. Cost = sum over all attempted paid calls; cost per attempted case and per correctly served case both reported. No current price is assumed in 4A.
- **Latency:** extraction, deterministic route and browser p50/p95/max with sample count; distinguish cold/warm setup and timeout-censored cases. Offline replay time is not provider or NL E2E latency.
- **Paired comparison:** same verbatim source, frozen baseline `LLM_ONLY` and V2 arms, independently scored; paired success/failure table and confidence bounds, not only aggregate percentages. At n=60, zero observed false serves is still only a finite-sample observation.

No existing eligible `/2` provider outputs were found in the examined S1–S3 receipts or archived extraction manifest. A new provider-backed evaluation is needed for extraction quality. `OWNER_LIVE_EVALUATION_DECISION.md` records the concrete proposal and stop condition. No live execution is authorized by this report.

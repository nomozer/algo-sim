# Hybrid A/B Pilot Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close source/checker soundness gaps and deliver an offline-certified, budget-capped P-AB1 runner without making a live request or changing the product default.

**Architecture:** Make two surgical safety corrections in the shared geometry-functions route, then add one evaluation-only runner that invokes the existing production arm adapters through an injected transport. Preserve historical evidence and publish all corrected claims, locked inputs, fake-provider evidence, and final identity in a new additive run.

**Tech Stack:** Python 3.12, Pydantic, pytest, httpx transport boundary, deterministic JSON/SHA-256 artifacts, existing Geometry Functions/TypedFacts stack.

**Spec:** `docs/evaluation/geometry/runs/hybrid-ab-pilot-readiness/protocol.md`

## Global Constraints

- Live Gemini calls are exactly 0; do not invoke a live transport during implementation or certification.
- Keep `SEMANTIC_ROUTE_MODE` default `LLM_ONLY`; do not wire either experimental arm into `run_pipeline`.
- Do not add a general proof system, solver, FactGraph, planner, renderer, or provider fallback.
- Keep historical run files byte-identical; corrections are additive through this run and `CORRECTED_BY`.
- Preserve user-owned `frontend/public/favicon.svg`; stage only explicit task files; no merge, push, rebase, amend, or force operation.
- `SMOKE_AB` is exactly 12 rows × 2 arms × 1 sample, capped at 24 logical calls, 36 HTTP attempts, 500,000 accounted tokens,
  and USD 0.60; it cannot support a FULL_AB conclusion.
- `FULL_AB` is exactly 48 rows × 3 samples × 2 arms, capped at 300 logical calls, 450 HTTP attempts, 6,000,000 accounted
  tokens, and USD 7.00; it requires separate human approval.
- Pre-request reservation is derived from actual canonical payload bytes plus 4096 prompt-framing tokens and one 3072-token
  combined output/thinking ceiling; pricing is USD 0.30/M input and USD 2.50/M output-plus-thinking. This is local accounting,
  not a documented provider-token bound; real billing containment remains unverified and is a live readiness limitation.
- Model target is `gemini-2.5-flash`, temperature `0.0`, max output `3072`, `k = 3`; current surface hashes are recomputed after
  this parameter amendment.
- Missing usage, identity mismatch, security leak, or cap exhaustion fails closed.
- `CACHE_VERSION` stays `125` unless a measured production cache dependency proves otherwise.

## Review Focus

- A shape cue and the requested polygon occur in one long quote but belong to different clauses/objects: reject with `OBJECT_NOT_IN_QUOTE`.
- A proof goal is true on the chosen layout but lacks a proof certificate: numeric answers may remain, but no field permits “proved”.
- A negated premise conflicts with one chosen layout while alternative configurations are not ruled out: refuse `NEGATED_CLAUSE`, not global inconsistency.
- A provider response has useful content but no complete usage metadata: persist a redacted infrastructure stop and make no next request.
- A secret appears inside a nested provider error/body while usage keys contain the word “token”: redact the secret, preserve usage counts, and stop.
- Smoke completes with attractive numbers: preserve them as apparatus evidence and reject any attempt to score them as FULL_AB.

---

### Task 1: Register independent grounding and checker oracles

**Files:**
- Create: `backend/tests/geometry/fixtures/hybrid_safety_oracles.json`
- Create: `backend/tests/geometry/test_hybrid_safety_readiness.py`
- Modify: `backend/tests/geometry/test_hybrid_compiler_selection.py`

**Interfaces:**
- Consumes: `run_function_route(problem_text, {"calls": [...]})`, `run_fact_route(problem_text, {"facts": [...]})`.
- Produces: literal RED expectations for `OBJECT_NOT_IN_QUOTE`, evidence-state records, proof-only refusal, and safe negation behavior.

- [ ] **Step 1: Add literal adversarial oracle rows**

  Include the eight required classes from protocol §2.2 for both A and B, plus positive equivalent forms. Expected values are
  handwritten status/code/state values; no production parser or converter computes them.

- [ ] **Step 2: Add behavior tests that execute both real routes**

  Tests must name the break: wrong-object cue accepted, clause-role bypassed, proof observation promoted, negated observation
  promoted, and positive cube/cuboid definition rejected.

- [ ] **Step 3: Run the focused tests and record RED**

  Run: `cd backend; .\.venv\Scripts\python.exe -m pytest tests/geometry/test_hybrid_safety_readiness.py tests/geometry/test_hybrid_compiler_selection.py -q`

  Expected: new wrong-object and checker-state tests fail on the pre-change behavior; established unrelated cases pass.

- [ ] **Step 4: Commit only the oracle/test files**

  Stage each exact path and commit `test: lock hybrid safety oracles`.

### Task 2: Bind structural cues to their source objects

**Files:**
- Modify: `backend/app/simulation/geometry_functions/registry.py`
- Test: `backend/tests/geometry/test_hybrid_safety_readiness.py`

**Interfaces:**
- Consumes: normalized source text, `_tu_nhan`, `LoiGoi`, and Task 1 oracle rows.
- Produces: `_co_doi_tuong_hinh(c: LoiGoi) -> bool` (or an equivalently narrow private helper) and refusal code `OBJECT_NOT_IN_QUOTE`.

- [ ] **Step 1: Implement the smallest object-binding helper**

  Recognize only the explicit forms listed in protocol §2.2. Bind a cube/cuboid face or directly named rectangle to exactly the
  call's `vertices`; do not expand the general keyword system.

- [ ] **Step 2: Apply it only to the audited relaxed cues**

  Keep all five existing source-gate layers and their order. Do not loosen negation, condition, goal, role, plane, segment, or
  value checks.

- [ ] **Step 3: Run grounding RED→GREEN and legacy source tests**

  Run: `cd backend; .\.venv\Scripts\python.exe -m pytest tests/geometry/test_hybrid_safety_readiness.py tests/geometry/test_ai_function_route.py tests/geometry/test_hybrid_compiler_selection.py -q`

  Expected: all pass; legitimate cube/cuboid expansion stays served and every wrong-object oracle refuses.

- [ ] **Step 4: Perform mutation checks**

  Temporarily reason/test against removal of object binding, substring-only matching, swapped base/top labels, and clause joining;
  at least one named test must fail for each mutation. Revert temporary mutations before commit.

- [ ] **Step 5: Commit exact implementation and tests**

  Commit `fix: bind structural cues to source objects`.

### Task 3: Separate configuration observation from proof

**Files:**
- Modify: `backend/app/ai/function_route.py`
- Modify: `backend/app/simulation/geometry_functions/engine.py` only if the checker return type needs an explicit alias/documentation
- Modify: `backend/tests/geometry/test_hybrid_compiler_selection.py`
- Test: `backend/tests/geometry/test_hybrid_safety_readiness.py`

**Interfaces:**
- Consumes: the existing configuration checker `Callable[[dict], bool | None]`.
- Produces: per-fact records with `evidence_state`, `proof_status`, and `can_present_as_proven`; proof-only code `PROOF_UNVERIFIABLE`; safe `NEGATED_CLAUSE` handling.

- [ ] **Step 1: Map checker output to the four evidence states**

  Keep the checker a configuration evaluator. `True`, `False`, and `None` map to `TRUE_ON_CONFIGURATION`,
  `FALSE_ON_CONFIGURATION`, and `UNVERIFIABLE`; only an explicit future certificate may emit `PROVED_FROM_HYPOTHESES`.

- [ ] **Step 2: Make proof-goal output presentation-safe**

  Remove current `HOLDS`/`FAILS` claims and `PROOF_GOAL_FALSE` inference. Preserve independent numeric answers with an explicit
  unverified obligation; refuse proof-only requests. Assert the serialized result cannot imply a positive proof.

- [ ] **Step 3: Make negated premises fail closed without a global inconsistency claim**

  Always refuse an uncertified negated premise as `NEGATED_CLAUSE`; keep the configuration observation only as diagnostic data.

- [ ] **Step 4: Run checker and full hybrid tests RED→GREEN**

  Run: `cd backend; .\.venv\Scripts\python.exe -m pytest tests/geometry/test_hybrid_safety_readiness.py tests/geometry/test_hybrid_compiler_selection.py -q`

  Expected: all pass with corrected H07/H13 current behavior; historical fixture files are unchanged.

- [ ] **Step 5: Commit exact implementation and tests**

  Commit `fix: separate model checks from geometric proof`.

### Task 4: Materialize and seal the P-AB1 inputs

**Files:**
- Create: `docs/evaluation/geometry/runs/hybrid-ab-pilot-readiness/inputs/pilot_cases.json`
- Create: `docs/evaluation/geometry/runs/hybrid-ab-pilot-readiness/inputs/oracle.json`
- Create: `backend/scripts/run_hybrid_ab_pilot.py`
- Create: `backend/tests/geometry/test_hybrid_ab_pilot_runner.py`

**Interfaces:**
- Consumes: the exact four corpus sources in protocol §5 and corrected checker oracle from Task 3.
- Produces: `load_locked_inputs(mode: PilotMode) -> LockedInputs` with exact row counts 12/48, unique namespaced IDs,
  mode-specific canonical SHA-256 hashes, and no dependency on historical live outputs.

- [ ] **Step 1: Materialize all 48 texts and hand-audited obligations**

  Copy source rows without rewording. Namespace IDs. Store exact positive answers/refusal obligations and proof/negation safety
  expectations separately from prompts.

- [ ] **Step 2: Add RED lock tests**

  Assert exact count/source composition, unique IDs, canonical hashes, oracle completeness, no answer leakage into sent text, and
  H07/H13 corrected semantics. Pin the twelve smoke IDs from protocol §5 and prove smoke/full corpus identities differ.

- [ ] **Step 3: Create the runner module with only the locked-input loader, then make lock tests GREEN**

  Keep this first slice offline and side-effect free. Task 5 extends the same module with scheduling, transport, and persistence.

- [ ] **Step 4: Commit inputs, loader, and lock tests**

  Commit `test: seal hybrid ab pilot inputs` using explicit staging only.

### Task 5: Implement the capped runner and fake-provider certification

**Files:**
- Modify: `backend/scripts/run_hybrid_ab_pilot.py`
- Create: `backend/scripts/certify_hybrid_ab_pilot.py`
- Modify: `backend/tests/geometry/test_hybrid_ab_pilot_runner.py`

**Interfaces:**
- Consumes: `function_calling.run_ai_function_route`, `fact_extraction.run_ai_fact_route`, both surface fingerprints, Task 4 locked inputs, and an injected `Provider.send(branch, payload, timeout_seconds) -> dict`.
- Produces: `PilotMode`, mode-specific `PilotCaps`, `PilotBudget`, `PilotIdentity`, `run_pilot(...) -> dict`, atomic redacted
  artifacts, fake certification CLI, and a gated live CLI that is never invoked in this run.

- [ ] **Step 1: Add RED budget and schedule tests**

  Pin 24/288 scheduled logical calls and deterministic arm order. Test distinct mode identities and pre-call/pre-request caps for
  logical, HTTP, token, and USD; assert the fake sees no call after a stop.

- [ ] **Step 2: Implement identity preflight and budget ledger**

  Exact signatures and constants follow protocol §§5–6.2. Compute reservation from the actual canonical payload before each
  request, reject context/cap overflow, compare returned usage against the reservation, increment counters before operations,
  and atomically persist the stop.

- [ ] **Step 3: Add RED response/observability tests**

  Cover separate A/B usage, modelVersion, finishReason, latency, cost, payload hash, redacted raw body, route output, and exact
  failure taxonomy.

- [ ] **Step 4: Implement one-call production-route execution with injected transport**

  Pass the fake/live provider closure into the existing arm adapters. Do not duplicate registry/planner/engine logic and do not
  import or call `pipeline.run_pipeline`.

- [ ] **Step 5: Add RED fail-closed tests**

  Cover missing/malformed usage, missing modelVersion, HTTP error body, exception, timeout, malformed candidate, two consecutive
  provider errors (stop at FIRST error), truncation (stop at FIRST occurrence), identity mismatch, partial artifact, resume,
  nested secret, and exact-key leak scan.

- [ ] **Step 6: Implement atomic persistence, redaction, scan, and resume**

  Reuse the proven patterns in `live_retry_apparatus.py` / `run_photo_problem_live.py` without importing their domain-specific
  workflow. Preserve token-count keys while redacting values under credential-bearing keys and secret strings.

- [ ] **Step 7: Run runner tests and both mode-specific fake certifications**

  Run: `cd backend; .\.venv\Scripts\python.exe -m pytest tests/geometry/test_hybrid_ab_pilot_runner.py -q`

  Run: `cd backend; .\.venv\Scripts\python.exe scripts/certify_hybrid_ab_pilot.py --out-dir ..\docs\evaluation\geometry\runs\hybrid-ab-pilot-readiness\fake-provider`

  Expected: tests pass; certification reports 24 completed `SMOKE_AB` rows and 288 completed `FULL_AB` rows, zero network
  calls, exact distinct identities, separated A/B telemetry, and all injected-stop scenarios caught.

- [ ] **Step 8: Commit runner, certifier, tests, locked inputs, and fake evidence**

  Commit `feat: certify hybrid ab pilot runner offline` with explicit per-file staging.

### Task 6: Correct scoring criteria and evidence claims

**Files:**
- Modify: `backend/scripts/run_hybrid_ab_pilot.py`
- Modify: `backend/tests/geometry/test_hybrid_ab_pilot_runner.py`
- Modify: `docs/evaluation/geometry/runs/hybrid-ab-pilot-readiness/protocol.md`
- Create: `docs/evaluation/geometry/runs/hybrid-ab-pilot-readiness/run.json`

**Interfaces:**
- Consumes: completed row records from Task 5.
- Produces: `score_pilot(rows, seed) -> summary` with weighted problem-clustered intervals and terminal label `SUPERIOR`,
  `NON_INFERIOR_NOT_SUPERIOR`, `INFERIOR`, `INCONCLUSIVE_STATISTICAL`, or `INCONCLUSIVE_INFRASTRUCTURE`.

- [ ] **Step 1: Add literal scoring fixtures and RED tests**

  Include both-arms-zero-wrong-service, B safer but not more accurate, B superior, B outside safety margin, and infrastructure-
  incomplete scenarios. The zero/zero case may pass comparative non-inferiority but must carry denominators, per-arm upper
  confidence bounds, uncertainty for the difference, and `NO OBSERVED ERROR ≠ PROVED SAFE`. Smoke input must be rejected.

- [ ] **Step 2: Implement deterministic clustered bootstrap and criteria**

  Use a pinned seed and resample problem IDs, retaining all paired samples/arms per selected problem. Keep mechanism diagnostics
  out of the win gate.

- [ ] **Step 3: Re-run runner tests and fake certification**

  Expected: deterministic byte-stable summary for identical inputs and no live call.

- [ ] **Step 4: Freeze final hashes/identity in `run.json`**

  Record candidate/product/measurement commits, corpus/oracle/parameter/surface hashes, measurement class, independence, caps,
  and `LIVE_MODEL_CALLS = 0`. Never write `APPROVED_BY_USER`.

- [ ] **Step 5: Commit scoring and frozen protocol identity**

  Commit `docs: freeze corrected hybrid ab protocol`.

### Task 7: Regression, candidate audit, and handoff

**Files:**
- Create: `docs/evaluation/geometry/runs/hybrid-ab-pilot-readiness/report.md`
- Create: `docs/evaluation/geometry/runs/hybrid-ab-pilot-readiness/handoff.md`
- Create: `docs/evaluation/geometry/runs/hybrid-ab-pilot-readiness/diagnostics/` artifacts produced by approved offline commands
- Modify: `docs/EVIDENCE_INDEX.md`
- Modify: `docs/CURRENT_STATE.md`
- Modify: `docs/STATUS_LEDGER.md`
- Modify: `docs/OPEN_ISSUES.md` only when an issue is closed/opened by verified evidence
- Modify: `docs/CODE_INDEX.md` for new runner/test locations

**Interfaces:**
- Consumes: all implementation commits and fake evidence.
- Produces: authoritative correction chain, verification matrix, candidate decision, and final status `HYBRID_AB_PILOT_READINESS_AWAITING_REVIEW`.

- [ ] **Step 1: Run focused regression and mutation commands**

  Run the hybrid, function-route, grounding, geometry-oracle, renderer-metric, and runner test files named by the changed code.
  Preserve full command/output logs in this run's diagnostics.

- [ ] **Step 2: Run repository-required audits and full backend suite**

  Run documentation layout/reference audits, candidate divergence/freeze checks in a clean detached worktree, and the full
  backend pytest command from `docs/TEST_TIERS.md`. Record exact pass/fail/skip counts and duration; do not convert missing data
  to zero.

- [ ] **Step 3: Audit visual-claim boundary**

  Report metric/geometry checks separately from human visual acceptance. If no browser/human review occurred, state that hidden
  edges, labels, faces, and interaction are not visually accepted.

- [ ] **Step 4: Write additive report and handoff**

  Include repaired counterexamples, checker boundary, fake-provider evidence, locked protocol, remaining limits, actual skills
  used, branch/HEAD/working tree/candidate/cache identity, `LIVE GEMINI CALLS = 0`, and GO/NO-GO. Technical readiness may be GO;
  execution remains NO-GO until explicit human approval.

- [ ] **Step 5: Update living indexes without changing historical artifacts**

  Add the run and `CORRECTED_BY` link, update current pointers, and leave the old report/results untouched.

- [ ] **Step 6: Verify working tree and explicit staging, then commit**

  Check `git diff --cached --name-only` contains only allowlisted task files and excludes `frontend/public/favicon.svg`.
  Commit `docs: hand off hybrid ab pilot readiness`. Do not merge or push.

- [ ] **Step 7: Fresh whole-branch review and one bounded fix pass**

  Use `superpowers:requesting-code-review` against the plan/spec and merge base. Any Critical/Important fix must get its own
  RED→GREEN test and a fresh suite run; defer Minor findings explicitly.

### Bounded review-fix pass (2026-10-10, before further production edits)

The single fresh review found six Important gaps. Reproduce each with offline RED tests, then repair: bind every regularity
witness to its polygon; reject malformed nested provider parts explicitly and persist known-usage post-response failures;
reject fake/live resume-class or live-count mismatches; align extraction taxonomy with emitted source-gate codes; enforce all
sealed refusal, unit, metric and checker obligations; preserve HTTP status/redacted body through the existing transport.
Also report undefined selective accuracy as null and separate negative-problem refusal rates. Keep old artifacts untouched;
re-certify into `fake-provider/review-fix/` and add fresh diagnostics. Move current candidate-divergence authority to this
additive correction run (old declarations remain historical); do not weaken the regression that checks it. Live remains 0.

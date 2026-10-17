# Semantic Extraction v3 — locked offline takeover report

2026-10-18 · `research/semantic-extraction-v3` · measured source `5c58774dbc57b3416337d97dab7db8ee1932894b`.

**PARTIAL — PROTOCOL RUNTIME BLOCKER.** The candidate, inputs and three review receipts match the lock, but the
original Claude job is still stuck in the frozen shared question grammar before its first completed offline receipt.
Zero of eight measurements are complete. No model-extraction result, deterministic ceiling result or safety pass
can be inferred from this attempt. **0 Gemini live calls during this takeover.**

Inventory, original process/log provenance and bounded reproduction:
[`takeover-20261018.md`](takeover-20261018.md). Machine checks:
[`verification/takeover-20261018.json`](verification/takeover-20261018.json).
Required research decision: [`approval-request.md`](approval-request.md).

## Eight offline measurements

Paths below are relative to this run. All named receipt paths are **expected, absent**, not links to existing evidence.

| Action | Arm | Mode / rows planned | Status | Python exit | Receipt |
|---|---|---|---|---|---|
| GOLD | flat | PILOT / 12 | RUNNING_STALLED | UNKNOWN | `results/offline/gold-flat-PILOT/score.json` ABSENT |
| synthetic REPLAY | flat | PILOT / 12 | NOT_STARTED | NOT_RUN | `results/offline/replay-flat-PILOT/score.json` ABSENT |
| GOLD | v3 | PILOT / 12 | NOT_STARTED | NOT_RUN | `results/offline/gold-v3-PILOT/score.json` ABSENT |
| synthetic REPLAY | v3 | PILOT / 12 | NOT_STARTED | NOT_RUN | `results/offline/replay-v3-PILOT/score.json` ABSENT |
| GOLD | flat | LOCKED / 24 | NOT_STARTED | NOT_RUN | `results/offline/gold-flat-LOCKED/score.json` ABSENT |
| synthetic REPLAY | flat | LOCKED / 24 | NOT_STARTED | NOT_RUN | `results/offline/replay-flat-LOCKED/score.json` ABSENT |
| GOLD | v3 | LOCKED / 24 | NOT_STARTED | NOT_RUN | `results/offline/gold-v3-LOCKED/score.json` ABSENT |
| synthetic REPLAY | v3 | LOCKED / 24 | NOT_STARTED | NOT_RUN | `results/offline/replay-v3-LOCKED/score.json` ABSENT |

Completed: **0**. Completed invocations with a measured nonzero exit: **0**. Running/stalled: **1**. Not started: **7**.
This counts invocations/receipts, not in-memory rows; their intermediate results are UNKNOWN. No manifest directory
or partial receipt exists. The unrelated pre-lock `results/historical-gold-delta.json` remains unchanged and is not
one of these eight measurements. Synthetic REPLAY is recorded by the inherited executor as execution class `FAKE`.

The first GOLD invocation evaluates all 36 cases before filtering PILOT, and currently stalls at held-out h07.
The stack and synthetic whitespace-only probe identify catastrophic regex backtracking in `_SAU_HOP_LE`, called by
`_vung_hoi` in `registry.py:1284`. The expression is older than v3 but belongs to the locked product. This is a
deterministic runtime failure, not a provider request or an extraction-quality finding. No attempt was duplicated,
resumed, killed or overwritten; the original tree remains active pending the owner's decision.

## Protocol and reviewer integrity

| Check | Result |
|---|---|
| Lock checkpoint | `5c58774d`, HEAD at takeover; locks `inputs/protocol.json` and records `review-gates/candidate.json` |
| Protocol canonical JSON SHA-256 (runner identity) | `f97af99e54aeb27bc18d244577ec01e92f137e164ff362339ba02a23247f9c68` |
| Protocol LF-file SHA-256 | `dddb79c90371fe00948ef269ebfdc5a619435b34c8fca3c8cce1ed45853f117b` |
| Locked-file hashes | 137/137 MATCH |
| Preserved source hashes | 10/10 MATCH |
| Product candidate | 110 files, `1ff71da76d999370897edd3a2dfaf161113e4d24f39dd41cda640ce2aa53dbc7`, MATCH |
| Gold/oracle review | historical PASS at `da75138c`, receipt and all reviewed files MATCH |
| Scorer review | historical PASS at `d7145b40`, receipt and all reviewed files MATCH; scorer `grounded-source-obligations/3` |
| Candidate review | historical PASS at `f82414ce`, receipt and reviewed files/product MATCH |
| Read-only oracle / assembly selfcheck | PASS; 12 dev, 24 held-out, 20 structure families, 65 source requests |

Review PASS does not erase the newly observed runtime blocker. No reviewer was rerun and no receipt was rewritten.
The review disclosures still apply: conservative refusals, scorer under-credit/UNSCORABLE limits, AI-authored
non-human-validated gold, semantic template overlap, and provider acceptance NOT_MEASURED.

The four exact arm/mode identities were regenerated read-only in
[`approval-identities.json`](approval-identities.json). They are inventories, not approvals. Any corrected product
requires a new protocol/candidate/identity; these hashes cannot certify that future candidate.

## Results by evidence class

- **A — Extraction quality:** NOT_MEASURED for v3. No live provider response exists; synthetic gold cannot establish it.
- **B — Gold deterministic ceiling:** UNKNOWN for both arms and both splits; no completed receipt.
- **C — Synthetic replay wiring:** NOT_RUN for all four scheduled replay invocations. Unit wiring tests pass separately.
- **D — Safety/refusal:** wrong-served, unscorable-served and refusal counts for this offline matrix are UNKNOWN.
  Targeted safety regressions pass, but do not substitute for the stalled corpus measurement.
- **E — Unsupported/schema limitations:** known disclosures remain; corpus-specific contract/refusal counts UNKNOWN.
- **F — Provider live:** NOT_RUN, NOT_AUTHORIZED, schema acceptance NOT_MEASURED. No `MEASURED_LIVE` claim.

## Verification performed in this takeover

All commands used Python 3.12 from the existing main venv and `ALLOW_LIVE_AI=0`; tests use an isolated per-run temp path.
Frontend dependencies were copied into this worktree's ignored `node_modules`; main's dependencies were only read.

| Gate | Observed result |
|---|---|
| Nine extraction/schema/runner/grounding test files | 394 passed, 1 xfailed, exit 0 |
| Full backend | 10,455 passed, 1 skipped, 2 deselected, 9 xfailed, exit 0 (388.32 s) |
| Full frontend | 68 files, 1,079 tests passed, exit 0 |
| Typecheck / production build | PASS, exit 0; existing large-bundle warning |
| Locked demo replay | 5/5, reduced chain 1/1, exit 0 |
| Crash-surface audit | 6/6 expected boundaries, 0 uncaught exceptions, exit 0 |
| Oracle / protocol selfcheck / candidate verify | PASS / PASS / MATCH, all exit 0 |
| Documentation gates after adding this handoff | 42 backend tests and 3 frontend code-index checks passed, exit 0 |
| Final authoritative T3 | NOT_RUN; offline prerequisites blocked, no clean detached verification worktree created |

These are checks of the measured source above, not certification of an integrated candidate or a later code revision.
An initial targeted-test invocation used a missing parent for `--basetemp` (323 passed, 1 xfailed, 71 setup errors).
The temp-path issue was corrected without a source change; the complete rerun is the 394/1 result above.
Raw test diagnostics remain local and ignored; no traceback, provider raw output or secret is published.

## Compatibility and remaining work

Read-only comparison used Gemini backend branch `research/contract-driven-goal-composition` at `a629ebee`.
It changes Registry, Planner and Engine; v3 changes fact extraction and Registry grounding. Both edit `registry.py`,
so a conflict-free Git merge would still require checking rightness/point-definition/source-ownership validation
against the composed `PlanningContract` goals, new area/angle effects and operand binding. The current scorer's
`line_ref` answers remain UNSCORABLE. Compatibility with that combined product is **NOT_VERIFIED**; no merge,
cherry-pick, combined T3, or edits in the backend/Scene3D worktrees occurred.
Read-only final status also found main's existing untracked `frontend/public/`, a clean backend-composition branch,
and nine modified frontend files plus an untracked run in the Scene3D worktree; all were left untouched.

Codex completed process/log recovery, Git/history inventory, independent hash/review validation, existing regression
gates, the runtime root-cause diagnostic and a bounded revision proposal. No prompt/schema/product change was made.
Evidence-only changes are confined to this run plus its evidence-index entry; the evidence commit follows the measured
source and does not claim its own HEAD was the source of these tests.

Next owner decision: stop only `bufr6nkj1`'s identified tree and authorize a separately identified runtime correction,
or archive this incomplete attempt. A new revision must retain old bytes, add a synthetic runtime regression,
pass grounding/safety checks, get the changed candidate reviewed/refrozen, and measure into fresh destinations with
individual exits and a bounded watchdog. Only then run authoritative final T3 and request exact-identity **GO LIVE
PILOT**. LOCKED live and **GO INTEGRATION** each require their own later approval. Default mode stays `LLM_ONLY`,
default extraction stays `flat`, cache125 and `HYBRID_PRODUCT_ENABLEMENT = NO-GO`.

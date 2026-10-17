# Hybrid semantic understanding and source grounding — continuation handoff

2026-10-17. Research branch `research/hybrid-semantic-grounding-reliability`, baseline `1f635ed5`, preregistration checkpoint `2e08922a`, final product `94b3437b`. **Clean detached T3 at `bd2dc080`: `FULL_PRODUCT_GATE_PASS`** (`verification/t3-attempt3.json`). `DEFAULT_MODE = LLM_ONLY`, `CACHE_VERSION = 125`, Hybrid product enablement **NO-GO**, live extraction **NOT_MEASURED**, model calls **0**.

## A. Claude's preserved work

At entry HEAD `2e08922a41675e6316f1429465c349273a60147e`: 5 tracked modifications, 0 staged files, 3 untracked files. The branch already contained committed preregistration, 58-case development corpus, 40 independently authored wording sentences mapped to 41 extraction cases, independent exact oracle, and measurement tooling. Uncommitted work implemented M1 request coverage, M2 written-plane checking, M3 alternate length operand order/interrogative wording, M4 cube `line_ref` premises, plus tests and baseline measurement. It was not test-only work.

All 8 working files, tracked/staged binary patches and a hash manifest were copied outside the repository to `C:/Users/Bunny/AppData/Local/Temp/algosim-claude-rescue-20261017-013835`; 8/8 hashes and both patches verified. No stash/reset, user-file deletion or old backup overwrite. `frontend/public/favicon.svg` remains protected and untracked. One registered worktree existed at entry; no visible Claude process. Inspection of unrelated process command lines was denied, so their ownership is UNKNOWN; none was stopped.

The reported **179 passed, 3 xfailed** was reproduced locally. No complete review, full regression PASS or new T3 receipt existed in this run at handoff. There was one new commit beyond integrated main: the preregistration checkpoint.

## B. Codex continuation and ownership

Preserved the implementation instead of rewriting it. Repaired the measurement root and implemented its documented `--code-root` option; independently reproduced Claude's BASE rows exactly on a clean detached `1f635ed5`. Recomputed the registered oracle for all48licensed case entries (43numeric,5without numeric requests) in memory: MATCH, without rewriting oracle files.

Independent review found source-plane false serves: shared collinear labels, accepted spellings bypassing the collector, and extra call labels silently truncated by angle IR. Supplemental tests observed RED then GREEN. `_cung_mat` now requires full-set containment; the existing Engine checks complete source and call plane groups for nondegeneracy and coplanarity. It also fixes symbolic `2a` cube acceptance after exact source binding. No planner recipes, formulas or new product modules.

Historical replay exposed M1's missed coverage for certified derived-plane section-area asks. The existing test failed RED; the correction forwards validated spans from existing source binders. All 77 historical two-line cases then recovered their original status/code/answers. Six older wording controls had expected partial success; tests now reject incomplete extraction and supply all requests for positive controls. The `suy ra` wording remains a goal-clause refusal; an explicit `tính` control verifies the original numeric value. Frozen labels and inherited xfail markers are unchanged.

Product checkpoints: `94e56aa6` (preserved M1–M4 plus first review fixes), `93c7bc97` (complete call planes and historical controls), `94b3437b` (certified section span coverage; final product).

## C–D. Grounding and Vietnamese wording

| Classification | BASE | Final |
|---|---:|---:|
| Correct served | 27 | 32 |
| Wrong served | 13 | 0 |
| Correct refusal | 34 | 49 |
| False refusal | 21 | 16 |
| Wrong-code refusal | 4 | 2 |

99 extraction cases total, reported with separate split/group/mechanism counts in `verification/evaluation-summary.json`. Development 58: 25 correct serves, 28 correct refusals, 3 false refusals, 2 wrong-code refusals. Separate-author wording mappings 41: 7 correct serves, 21 correct refusals, 13 false refusals. These are bounded offline results, not general Vietnamese accuracy.

Closed on the registered cases: omitted second asks/list targets/follow-up quantities; four-label nonplane shortened to three; reversed described-length operands; described-length `bằng bao nhiêu?`; cube premise before an intersection-line goal. Supplemental review closes the plane identity/spelling/extra-label bypasses. Wrong-target/quote/certificate regression protections remain in the related suites.

Source certification acceptance precision **27/40 → 32/32**, recall **27/48 → 32/48**, measured in extraction cases under the registered mappings. Final accepted32 includes **30 numeric cases / 37 exact numeric values** and **2 construction/definition cases**; construction visual completion is not independently scored by this numeric classifier. Among 26 multi-request cases, wrong serves/silent omissions **9 → 0**; final 20 correct complete-or-safe-refusal classifications, 5 false refusals and 1 wrong-code refusal. Safe refusal is not a completed simulation. Eleven schema-gap extraction cases: 0 wrong serves in either arm; refusing them is not capability coverage.

Remaining false refusals: `A13` (`chính giữa`), `A14` (`bao xa`), `B05` (construction projection) and 13 separate-author wording cases (`U02,U03,U05,U08,U12,U14,U15,U16,U17,U18,U26,U30,U33`). Codes/outcomes are retained per row. Remaining wrong-code refusals: `E05` unsupported second quantity → `NOT_ASKED_IN_SOURCE`; `E08` unknown point → `UNDERDETERMINED_POINT`. No frozen label changed to improve scores.

Boundaries: alternate coplanar label groups with neither set containing the other conservatively refuse; source/call plane equality is checked in the source-bound deterministic figure. Cube `2a√2` still meets a reused-reader limitation. Common construction wordings, nested descriptors, arbitrary questions and some conditional/goal formulations remain unsupported. The construction-wording issue remains OPEN.

## E. Corpus, provenance and evaluation limits

Preregistration/corpus/oracle are committed at `2e08922a` with product files identical to baseline. This proves the registered repository snapshot precedes the product checkpoints; the exact time of Claude's first uncommitted product edit is UNKNOWN. The original BASE is reproduced row-for-row. All 8 registered input files match their preregistration commit after LF normalization; hashes are in `verification/evaluation-summary.json`.

Development labels are by the implementing agent: **DEVELOPMENT_NOT_HELD_OUT**. `unseen/authored.json` has the registered raw SHA-256 `8eb393cf3d9590f7bd2dc546fcdcdc8a85109ffad340116d955182b890b4c672`; independent authorship is recorded by Claude's preregistration, not newly reconstructed from an external session. It contains 40 sentences; the committed mapper adds a second near-miss extraction `U33n`, so there are 41 extraction cases. Mapping is the implementer's. No human held-out claim.

The first final measurement at `93c7bc97` preceded the correction driven exclusively by historical two-line regressions. Final `94b3437b` remeasurement is identical on all 99 outcomes. This is a protocol deviation, recorded in `corrections.json`; it is not a fresh final holdout. No product change was motivated by unseen outcomes.

| Layer | Evidence |
|---|---|
| Intent extraction | NOT_MEASURED: authored Typed Facts, no provider |
| Entity/reference grounding | Source gate near-miss protection measured; extractor accuracy NOT_MEASURED |
| Goal interpretation | Registered authored-fact behavior measured; live interpretation NOT_MEASURED |
| Construction planning | Historical plan statistics identical on 174/174 |
| Mathematical execution | 37 numeric values across30served cases exact against the independent Fraction oracle;2other served cases are construction/definition |

## F. Historical architecture regression

Historical bundle 174: **172 identical** `(status, code, answers)`, **2 intended refusal-code changes**: `parallel-result-line` now reaches `PARALLEL_NO_INTERSECTION` instead of `SOURCE_PREMISE_UNREAD`; `unread-second-ask` now `REQUEST_NOT_ANSWERED` instead of `QUESTION_CONTEXT_UNSUPPORTED`. Planner statistics/errors identical 174/174. Result Binding 18, two-line development 45/held-out 32, benchmark 30 and prior positive goal/function-entry answers preserved. No newly served historical negative.

Product diff versus main touches only Registry and function Engine source validation. Planner, Compiler, exact Kernel, schemas, provider prompts/declarations, `/api/analyze`, renderer and default mode unchanged. Existing Scene3D/browser evidence is reused because presentation source and served historical answers are unchanged; no new browser or human visual acceptance is claimed.

## G. Verification

- Interrupted focused result reproduced: 179 passed / 3 xfailed.
- Expanded focused source/goal/result-binding/clause suite: 591 passed / 3 xfailed; after historical-span fix, relevant six-module suite 398 passed / 3 xfailed.
- Supplemental RED: 7 failures/2 passes, then 2 angle failures/9 passes; existing section test RED, then GREEN. Raw failing logs remain outside Git; no raw traceback/model output committed.
- T1: geometry frontend 719 passed. T2: 1072 passed, typecheck/build PASS; production changes after that run were backend source checks, covered again by final T3.
- Independent fresh-context reviewer: final delta **no remaining critical or important finding**, scoped offline probes; hashes and findings in `review.md`.
- First full geometry attempts: stale candidate failure, then an environment error accessing old `%TEMP%/pytest-of-Bunny`. No assertions disabled; pytest temp is isolated per command, no ACL resets.
- Full geometry and authoritative detached T3: **PASS** at `bd2dc080` on the third attempt (receipts `t3-attempt1..3.json`; see "Final T3").
- A clean detached geometry attempt at `b2154454` stopped at the documentation next-action guard (1479 passed). Fixed in documentation/tooling only at `b4be4b98`: align all three canonical declarations and register the task's lifecycle state; preserve the 300-line handoff limit. The unchanged 42-test architecture suite passes. Final T3 includes the entire geometry suite, without narrowing or disabling assertions.
- Refreeze from clean detached `94b3437b`: candidate **`57c7f5dbedaa7b21c66345fa4d6f0e1ea461a425293d44035b5678e12d76f96e`**, 110 files, `--verify` MATCH. Current divergence correction is append-only and points to the preceding Scene3D layer.

## H. Git and integration

Current task remains on its original research branch; main/origin-main at entry `1f635ed5`. No merge/push approval is inferred from earlier waves. Integration gate/remote freshness will be checked after final T3, then one concrete user GO will be requested. Protected favicon and unrelated archived DSL/real-model branches remain untouched. Only this task's clean verification worktree is eligible for cleanup; legacy ACL debt is excluded.

## I–J. Live extraction and next research

**LIVE_EXTRACTION_NOT_MEASURED**, 0 provider calls. No prompt/provider declaration change or Gemini activation. Highest-value next step: a separately preregistered, budgeted independent extraction evaluation over the remaining natural construction/reference wordings, measuring intent, entity and goal interpretation separately before enabling Hybrid. It requires its own live GO; do not open G16/G17 or change the product default from this evidence.

Postflight: existing Registry, source binders, Engine, exact geometry and verification tooling reused; new product modules **0**; duplicate check found no parallel state/solver; no new dependency cycle.

Metric interpretation correction (final draft):32 means accepted cases, not numeric answers; see
`verification/metric-interpretation.json`. The separate-author angle itemU24 is scored by the implementer's registered
`cos²` mapping (`cos²=8/17`), not an angle measure in degrees/radians. Preserve that frozen label/score, but do not infer
complete output-intent adequacy from it. Audit angle/output and construction-completion labels independently before
the next extraction evaluation; no G16 or angle representation change is opened here.

## Reproduction

From repository root, use the existing Python 3.12 venv. Every `--out` must be a fresh path; preserve committed outputs.

```powershell
& backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/hybrid-semantic-grounding-reliability/measure.py --label REPLAY --out <fresh-result.json>
& backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/hybrid-semantic-grounding-reliability/measure.py --label BASE --code-root <clean-detached-1f635ed5> --out <fresh-baseline.json>
& backend/.venv/Scripts/python.exe backend/scripts/measure_goal_entry.py arm --code-root . --bundle docs/evaluation/geometry/runs/generalized-goal-entry/baseline/bundle.json --label REPLAY --out <fresh-historical.json>
& backend/.venv/Scripts/python.exe backend/scripts/freeze_evaluation_candidate.py --verify
```

Authoritative gate: run `node frontend/scripts/full-gate.mjs --python <absolute-main-venv-python>` from a clean detached
checkout with installed frontend dependencies. This session uses a junction to the main checkout's `node_modules`.
TEMP/TMP/TMPDIR are scoped to that command's fresh task directory, not changed globally; an external JUnit path records
which geometry cases ran. No `-n`, plugin installation, live provider, test exclusion or ACL reset is involved.

The final artifact-specific evidence review was attempted after product review; that reviewer turn hit its usage limit.
Product review/deltas had already completed with exact matching hashes. Artifact reconciliation was completed by the
continuing agent; do not treat that extra evidence audit as an independent PASS.

## T3 continuation — test fixture compatibility

The first full gate at `b4be4b98` additionally exposed 14 follow-up test parameters (both A/B) that omitted a requested
SB while asserting success for SC. These controls now explicitly refuse the incomplete extraction, then supply SB and
retain SC²=17 plus independently check SB²=13. The six earlier wording controls follow the same rule. No frozen corpus,
oracle function or xfail marker is changed.

The existing proof-only test removed the question fact but left its numeric request in the source. It now first checks
that omission refuses, then removes the numeric sentence from its local positive fixture and retains the original
`PROOF_UNVERIFIABLE`/cannot-present-as-proven assertions. The registered JSON fixture remains untouched.

The benchmark harness classifies the new `REQUEST_NOT_ANSWERED` code as grounding, alongside the existing
`SOURCE_PREMISE_UNREAD`; only its live refusal taxonomy is extended, not its mathematical oracle or case labels.
Focused verification of these compatibility fixes: **127 passed**. Product source and reviewed candidate unchanged.

The initial `inputs/candidate_divergence.json` correctly recorded the candidate hash but inherited obsolete Scene3D
fields (task, product, changed paths, freeze description and claim of unchanged refusal codes). It is preserved.
The append-only correction `candidate_divergence.json` now names this task/product and both declared code changes,
chains from that initial layer, and is the current consumer entry. Historical lock hashes are derived from the original
identity lock; no earlier measurements or manifests are rewritten.

## Component status

| Component | Status | Scope / evidence |
|---|---|---|
| Preregistration | DONE_AND_VERIFIED | Committed input snapshot and hashes; first uncommitted-edit time UNKNOWN |
| Independent oracle | DONE_AND_VERIFIED | Separate Fraction implementation,48case entries recomputed MATCH (43numeric,5without numeric requests); semantic labels by implementer |
| Semantic corpus | DONE_AND_VERIFIED | 58development +41wording mappings, 40independent sentences; frozen inputs unchanged |
| Source Grounding changes | DONE_AND_VERIFIED | Focused/review/corpus verified; final clean detached T3 PASS |
| Source Grammar breadth | PARTIAL | M3/M4 registered forms improved;16false refusals remain |
| Multi-goal handling | PARTIAL | 0silent omissions on26cases;5false refusals and1wrong-code refusal remain |
| Wrong-target protection | DONE_AND_VERIFIED | Source/call complete planes, collinearity, spelling and extra-label regressions in both routes |
| False-serve regressions | DONE_AND_VERIFIED | 13→0 in99registered extraction cases, plus independent review regressions |
| False-refusal regressions | PARTIAL | 21→16; no general-language claim |
| Planner / Compiler / Kernel / Renderer | DONE_AND_VERIFIED | Product bytes unchanged;174historical planning statistics/answers preserved |
| Tests | DONE_AND_VERIFIED | Focused/T1/T2 pass; first T3 failed16compatibility checks, fixed tests-only (stricter), final T3 PASS |
| Independent review | DONE_AND_VERIFIED | Product and all product deltas reviewed, hashes MATCH; extra evidence audit unavailable after reviewer usage limit |
| Full regression | DONE_AND_VERIFIED | Backend 10240/0 fail, geometry 7949/0 fail, vitest 1072 in clean detached T3 |
| Final T3 | DONE_AND_VERIFIED | `bd2dc080` FULL_PRODUCT_GATE_PASS, candidate `--verify` MATCH after the gate |
| Git integration | PARTIAL | Commits/refreeze complete; explicit user integration GO still required |

## Environment correction after the second T3

At `bd2dc080`, the second full gate passed backend **10240 / 0 failures** (geometry **7949 / 0 failures / 9 xfailed**),
frontend1072, demo5/5 and crash6/6. Production build alone failed `EPERM` deleting this task worktree's generated
`frontend/dist/assets`, created by the earlier sandbox context. Receipt `verification/t3-attempt2.json` retains FAIL.

Owner/DACL inspection identified `CodexSandboxOffline`; the path was verified as the exact ignored build directory
inside this verification worktree and not a reparse point. Only its three generated files were removed using the
original sandbox context. A normal-user production build then passed and the regenerated assets owner is `Bunny`.
No repository ACL reset, owner reassignment, administrator execution or personal-file cleanup occurred. The final
full gate runs consistently with normal-user filesystem access, fresh per-command temp and the same product hash.

## Final T3 — PASS (verified after the Codex interruption)

Codex launched the third gate at clean detached `bd2dc080` and hit its session limit before reading the result. Claude
Code, resuming, found no live gate process and read the log: **`FULL_PRODUCT_GATE_PASS`**, exit 0 — backend 10240 passed /
0 failed / 9 xfailed / 1 skipped (geometry 7949 / 0 / 9), vitest 68 files / 1072, typecheck + build PASS, demo 5/5,
crash surface 6/6. JUnit recounted independently of the log. After the gate, in the same worktree: status clean,
`freeze_evaluation_candidate.py --verify` MATCH (110 files, `57c7f5db…`), HEAD unchanged since its 10:07:48 checkout, no
product path changed since `94b3437b`. Full-gate has no clean-tree guard of its own, so "clean before" is inferred from
those facts. Receipt `verification/t3-attempt3.json`; attempts 1–2 keep their FAIL verdicts. Not rerun: the result is
valid for the final candidate and the only later commits are documentation.

The tests-only commit `bd2dc080` between attempts 1 and 3 was audited: it makes controls stricter (incomplete
extraction must now refuse with `REQUEST_NOT_ANSWERED`; the complete extraction must serve both SC²=17 and SB²=13), and
the proof-only control keeps its original `PROOF_UNVERIFIABLE` assertion on a proof-only source. No assertion removed.

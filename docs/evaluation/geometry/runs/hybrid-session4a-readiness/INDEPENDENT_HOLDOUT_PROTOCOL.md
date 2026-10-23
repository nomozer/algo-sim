# Independent holdout protocol

Status: **PREPARED / BLOCKED ON INDEPENDENT EVALUATOR**. No sealed holdout has been authored or executed in Session 4A. The twelve implementer-authored probes are development diagnostics only. A fresh code reviewer is not automatically an independent problem author or evaluator.

## Roles and independence

Owner appoints a curator/evaluator who did not implement S1–S4A, has not used the development corpus to tune cases, and will not reveal locked problems, answers or failure examples before scoring. The implementer freezes source and tooling, documents intended supported scope and then has no access to the private gold/oracle. A separate mathematical adjudicator resolves ambiguous premises/answers before lock where possible; post-lock disputes remain declared corrections, never in-place gold edits. The owner approves budget/release decisions; scripts and agents never write human approval values.

If these roles cannot be separated, label the run DEVELOPMENT or REUSED_DIAGNOSTIC, prepare the packets and stop. No change of label to blind is allowed after feedback.

## Sampling and lock package

Proposed disjoint **12-case pilot** and **60-case locked** set. Locked mix: 30 valid cases inside the preregistered canonical V2 scope, 12 contradictory/source-mismatch cases, ten missing/ambiguous-premise cases, eight clearly unsupported requests. Curator fixes exact stratification before seeing candidate outputs; scope limitations cannot be relabelled after measurement to reduce false refusals. Include pyramid/prism, section/derived-solid, ratio/residual and composed measurement tasks; include curved/qualified/composite cases as explicitly limited controls, not invented positive V2 capability.

Curator records source provenance/usage permission, original source bytes, text encoding, normalized duplicate key, structural family/operand tags, all asked obligations, exact answer or allowed answer set, valid scope, mandatory refusal criteria/codes or accepted categories, seed and generator version. Compare against **all** S1–S3 sources and disclosed S4A diagnostics for exact, paraphrase and structural near-duplicates. Independently sourced texts with materially new combinations are preferred over merely changing dimensions in a known generator. Freeze exclusions and their reasons before candidate evaluation.

Private files: `sources.json`, `gold_typedfacts_v2.json`, `oracles.json`, `refusal_policy.json`, `schedule.json`, `seed.json`, `provenance.json`. Public pre-evaluation manifest contains SHA-256 of every file, byte counts, source commit/tree, freeze algorithm, prompt/schema hash, renderer build/camera protocol, scoring/harness hash, accepted scope and thresholds. The curator signs/timestamps the manifest in a committed evidence package; a hash without a committed or externally witnessed lock is insufficient proof of precommitment. The owner retains recoverable copies. Neither answers nor refusal expectations enter extractor requests.

No files named as private packets are created in this run: doing so would let the implementer become the holdout author. The actual seed, hashes and cases are **PENDING_CURATOR**, not invented placeholders claimed as locked.

## Three tracks, separate denominators

| Track | Input / execution | Independent scoring |
|---|---|---|
| TypedFacts→Scene3D | Curator-authored `/2` facts and exact source → pinned route; no model | Exact answers, source binding, request coverage, valid scene/certificates, expected refusals, memory/topology boundaries; visual consumer tested separately |
| NL→TypedFacts | Source text → approved extractor; no gold facts/oracle in request | Schema validity, supported source premise coverage, role/negation fidelity, source quote/object alignment, invented facts, request/operand fidelity; do not infer extraction correctness from downstream acceptance |
| Full E2E | Same source → extractor → canonical route → envelope/renderer | Correct extraction AND every required exact answer/scene/visual obligation; attribute extraction/source/missing/planner/kernel/scene/renderer/infra failure separately |

Typed gold is an extraction-perfect ceiling, not a substitute for the NL track. Historical flat REPLAY bodies are not V2 provider samples. The fake-provider pipeline arm of benchmark 30 is not an independent NL measurement. Full E2E correct-served rate uses all scheduled supported positives, while conditional downstream success uses only accepted extraction; publish both to expose filtering losses.

## Execution and preregistered decision rules

1. Before unsealing: verify candidate identities, clean source, all file hashes, no default-mode changes, no prompt leakage, network budget gate and writable output. Use one worker and one BLAS/OpenMP thread.
2. Pilot calibrates plumbing on disjoint cases; any code/prompt change after pilot requires a new candidate and new lock before the locked set opens. Do not inspect locked content to debug pilot failures.
3. Locked evaluation has a fixed randomized arm order and one scheduled attempt per case/arm. Record timeout, provider failure, crash, incomplete output and refusal without replacement or hidden retries. Both paired arms use identical source bytes and independently adjudicated expected results.
4. Preregistered proposed research acceptance: **zero false serves**, all 12 contradiction controls safely refused, no technical failure disguised as valid refusal; at least 27/30 correctly served supported positives; at least 9/10 missing/ambiguous and 8/8 unsupported controls safely refused with declared category. Report exact counts/intervals even if a threshold fails. These proposed thresholds need curator/owner lock; they are not existing approval criteria or evidence of production readiness.
5. Renderer track requires correct envelope consumption, certificate-backed marks, no internal auxiliary-label leaks, all requested objects/steps present and no false proof claim. Lock desktop/compact viewports, camera/step states and human review rubric beforehand. Technical rendering failure counts separately from backend refusal. Do not use screenshots to certify geometry.
6. If any source/candidate/seed/prompt/hash mismatch, secret exposure, budget overrun, forbidden provider failure or unsafe acceptance occurs, stop and preserve sanitized receipts. Owner decides continuation under a new declared run; previous attempts remain recorded.

After unsealing, no source/oracle edits or code/prompt tuning can preserve a blind claim for that set. Feedback fixes go to a new development run; any retest of the revealed set is labelled post-feedback regression. A genuinely independent subsequent test requires a fresh evaluator-held set and lock. Maintain a contamination ledger linking every revealed example to the fix/retest.

Offline typed track can proceed after independent packets are supplied and locked. NL/full E2E require the separate live owner decision and budget. Production replacement additionally requires all migration gates; meeting this small research threshold alone cannot authorize it.

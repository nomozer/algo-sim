# Simulation evidence repair plan

Authorization: `GO_SIMULATION_EVIDENCE_REPAIR_LOCAL_ONLY`. Inline execution; one independent read-only review at the end.

- [x] P0: preserve existing uncommitted corrections and exact original logs; create `research/simulation-evidence-repair` from verified campaign source (`d86c72031d8fc85cd4eef62d9379cd1690ba1417`, explicit owner exception to new-task main-base rule).
- [x] P1/P2: archive four originals under `raw/original-t3` with scoped `-text`; publish additive scope correction and current documentation links; verify staged Git bytes.
- [x] P3: one new browser reproduction on clean `d86c7203` snapshot, explicit frozen nine-scene input, preflight WebGL/browser metadata, binary execution logs, separate PNGs. Ellipses remain `BACKEND_ONLY`; optional extra group omitted.
- [x] P4: product/tests/harness identity, freeze and provider fingerprints; commit repair package (`48c34d886579948aa9c28019dd0559fd100f6dcd`) and verify exact archived bytes in a clean detached checkout.
- [x] P5: one new Full T3 on clean corrected commit plus post-T3 freeze verification; raw capture, receipt (`t3/execution.json`, `t3/validation.json`, `t3/freeze/execution.json`) and clean-checkout archive comparison (`archive-integrity.json`); no expectation changes or rerun cycle.
- [x] P6/P8: root-cause investigation of `demo6b-curved-cone-frustum-cut` `td_sec_axial` (`ownPixels = 0`), bounded independent evidence review (`verification/independent-review.md`), final handoff (`OPUS_CONTINUATION_HANDOFF.md`) and documentation commits. Preserve all worktrees; no merge/push.

Reuse existing `run_browser_audit.mjs`, `full-gate.mjs`, `freeze_evaluation_candidate.py` and `evidence_identity_collector.py` hash semantics. New capture helper only redirects subprocess streams as binary and records invocation/times/hashes; no backend/frontend script or test changes. Success is exact raw identity through Git plus truthful scope and newly reproduced browser/T3 evidence. Stop on irrecoverable originals; record any real gate failure without changing implementation.

Observed browser finding retained and root-caused without code mutation: `demo6b-curved-cone-frustum-cut` `td_sec_axial` `ownPixels = 0` (`resetDiffFromDefault = 239`), no rerun. Scope claim remains qualified (`SIMULATION_EVIDENCE_REPAIR_PARTIAL`).

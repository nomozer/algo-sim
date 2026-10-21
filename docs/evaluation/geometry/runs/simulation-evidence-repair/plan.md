# Simulation evidence repair plan

Authorization: GO_SIMULATION_EVIDENCE_REPAIR_LOCAL_ONLY. Inline execution; one independent read-only review at the end.

- [x] P0: preserve existing uncommitted corrections and exact original logs; create research/simulation-evidence-repair from verified campaign source (explicit owner exception to new-task main-base rule).
- [x] P1/P2: archive four originals under raw/original-t3 with scoped -text; publish additive scope correction and current documentation links; verify staged Git bytes.
- [x] P3: one new browser reproduction on clean d86c7203 snapshot, explicit frozen nine-scene input, preflight WebGL/browser metadata, binary execution logs, separate PNGs. Ellipses remain BACKEND_ONLY; optional extra group omitted.
- [ ] P4: product/tests/harness identity, freeze and provider fingerprints; commit repair package and verify exact archived bytes in a clean detached checkout.
- [ ] P5: one new Full T3 on clean corrected commit plus freeze; raw capture, receipt and clean-checkout archive comparison; no expectation changes or rerun cycle.
- [ ] P6/P8: bounded independent evidence review, final handoff and documentation commits. Preserve all worktrees; no merge/push.

Reuse existing run_browser_audit.mjs, full-gate.mjs, freeze_evaluation_candidate.py and evidence_identity_collector.py hash semantics. New capture helper only redirects subprocess streams as binary and records invocation/times/hashes; no backend/frontend script or test changes. Success is exact raw identity through Git plus truthful scope and newly reproduced browser/T3 evidence. Stop on irrecoverable originals; record any real gate failure without changing implementation.

Observed browser finding retained: demo6b td_sec_axial ownPixels=0, no rerun. Scope claim remains qualified.

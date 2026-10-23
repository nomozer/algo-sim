# Backend Hybrid Session 4A handoff

Date: 2026-10-23. Branch: `research/hybrid-session4a-readiness`, based on local main `f10e6283dd3fd2cfdef189e1bef0ffdecf2be942`.
Worktree: `.superpowers/worktrees/hybrid-session4a-readiness`. Source verification checkout: `.superpowers/worktrees/hybrid-session4a-s3-verify`, detached `84c729e0…`.

| Release level | Decision |
|---|---|
| Bounded offline research | READY |
| Main integration, production disabled | PARTIAL |
| Bounded live experiment | BLOCKED — owner GO, curator/model/lock required |
| Production replacement | BLOCKED / NO-GO |

Read the six deliverables in this directory:

- [INTEGRATION_PREFLIGHT_REPORT.md](INTEGRATION_PREFLIGHT_REPORT.md)
- [SESSION3_EVIDENCE_RECONCILIATION.md](SESSION3_EVIDENCE_RECONCILIATION.md)
- [PLANNER_GENERALIZATION_GAP_REPORT.md](PLANNER_GENERALIZATION_GAP_REPORT.md)
- [E2E_EXTRACTION_READINESS.md](E2E_EXTRACTION_READINESS.md)
- [INDEPENDENT_HOLDOUT_PROTOCOL.md](INDEPENDENT_HOLDOUT_PROTOCOL.md)
- [MIGRATION_RELEASE_DECISION.md](MIGRATION_RELEASE_DECISION.md)

Live-dependent work stops at [OWNER_LIVE_EVALUATION_DECISION.md](OWNER_LIVE_EVALUATION_DECISION.md). No approval is recorded or inferred.

Key findings: 562 cannot be reconstructed (560 mixed A–H units, 38 overlapping plan inspections separate); P1/P3 post-fix fuzz receipts cover 46,436 mutation executions, not 3×500; four benchmark false refusals are B27/B28 in two fake/typed arms; 116 measured entries cover 115 unique backend/frontend files. Forty-three historical flat extractions and one missing extraction cannot measure NL→V2. Authored seam: 22 verified scenes / 25 refusals. New development probes: 12/12 exact and structurally valid, no new function signature or independent blindness established.

The generic resolver genuinely composes supported typed goals; section-vertex Meet selection remains section-specific. Canonical V2 excludes curved and qualified-frame cases supported by selected legacy paths. No geometry features were added to rescue old corpora.

Reproduce offline tooling with the existing `backend/.venv/Scripts/python.exe` from the original root, one worker/BLAS thread, `ALLOW_LIVE_AI=0`, `PYTHONUTF8=1`:

```powershell
python docs/evaluation/geometry/runs/hybrid-session4a-readiness/offline_replay.py --source-root <clean-S3-candidate> --archive-root <repo-with-historical-archive> --output <NEW-output.json>
python docs/evaluation/geometry/runs/hybrid-session4a-readiness/planner_diagnostics.py prepare <clean-S3-candidate> <NEW-directory>
python docs/evaluation/geometry/runs/hybrid-session4a-readiness/planner_diagnostics.py evaluate <clean-S3-candidate> <same-NEW-directory>
```

Scripts refuse overwriting their outputs. Do not rerun into existing evidence. Candidate and archive identity must be checked before comparing any future receipt. `run.json`, `results/final-verification.json` and `artifact-hashes.json` carry machine provenance. `INDEPENDENT_REVIEW.md` records the separate code/evidence review and any remediation; it does not replace a holdout evaluator.

Preserved: main/origin/main, original dirty workspace, source S1–S3 evidence, all unrelated branches/worktrees, frontend and product/cache contracts. No merge, push, delete, full T3 or live provider run. Existing S3 T3 PASS applies to its exact original candidate only. Browser behavior, provider measurements and independent holdout outcomes remain UNKNOWN/PENDING.

Next action: owner reviews the coherent disabled integration scope and live-pilot proposal; independent curator supplies/locks new private packets before NL/E2E measurement. Production remains `LLM_ONLY`, `flat`, Hybrid NO-GO, live0, cache127, memory32.

Post-flight: reused existing schema/bridge/adapter/source gate/planner/engine/scene validator/oracles/cache tests; created only run-local audit/replay/diagnostic/verification tooling and reports; no duplicate runtime abstraction or new dependency.

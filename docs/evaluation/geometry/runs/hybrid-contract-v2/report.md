# report.md — Backend Hybrid Session 3 (`hybrid-contract-v2`)

> Canonical entry point for the `hybrid-contract-v2` run directory. See [`SESSION3_FINAL_REPORT.md`](SESSION3_FINAL_REPORT.md) for the full 8-section synthesis.

- **Run**: `hybrid-contract-v2`
- **Authorization**: `GO_HYBRID_SESSION3_CONTRACT_V2_LOCAL_RESEARCH` (`D1`–`D6`)
- **Branch**: `research/hybrid-backend-session3-contract-v2`
- **Worktree**: `.superpowers/worktrees/hybrid-backend-s3`
- **Base Commit (Session 2 HEAD)**: `227d447f5c1ca55a2c4bd68f3c8c583228902cfc`
- **Final Product Commit**: `541803c867adfbc5e85a8109bd0307552090f9df`
- **Measured Product Tree (`backend/app`, 116 files)**: `173af8b2604dde4754a602eb868ceb07f8129263f7b80aa9601a9a203aec51d9`
- **Classification**: `DEVELOPMENT_EVALUATION_NOT_BLIND` (`0` live provider calls, `ALLOW_LIVE_AI = 0`)

## Reports & Receipts Index

1. [`SESSION3_FINAL_REPORT.md`](SESSION3_FINAL_REPORT.md) — Executive summary, checkpoint diagnosis (`19/22` $\to$ `22/22`), implementation summary (`P1`–`P8`), and Family A–H evaluation table.
2. [`CONTRACT_V2_IMPLEMENTATION_REPORT.md`](CONTRACT_V2_IMPLEMENTATION_REPORT.md) — `typed-fact-next/2`, `convert_v1_to_v2`, `typed-fact-next-bridge/2`, and `hybrid-simulation-adapter/4`.
3. [`SOURCE_GATE_COVERAGE_MATRIX.md`](SOURCE_GATE_COVERAGE_MATRIX.md) — Pre-locked 47-case `grammar-set.json` (`10c57be7...`), closed grammar `G1`–`G7`, and negative control matrix.
4. [`PLANNER_COMPOSITION_AND_REUSE_REPORT.md`](PLANNER_COMPOSITION_AND_REUSE_REPORT.md) — Bounded `D6` unstated lateral cut derivation (`PlanningContract` on `intersect_line_plane`), closure certificate (`same_section_cycle`), and `D4 KEEP 32` IR budget audit.
5. [`BACKEND_MIGRATION_READINESS.md`](BACKEND_MIGRATION_READINESS.md) — Assessment of `S3-1..7`, `D-01..13`, and `GATE-01..20`.
6. [`INDEPENDENT_REVIEW.md`](INDEPENDENT_REVIEW.md) — Read-only subagent quality gate audit (`61217726-a797-4a91-b722-e4393c7e11c9`) and remediation of `I-1`/`I-2`.
7. [`SESSION3_RESUME_STATE.md`](SESSION3_RESUME_STATE.md) — Handoff takeover and final state ledger.
8. [`run.json`](run.json) & [`candidate_divergence.json`](candidate_divergence.json) — Machine-readable run manifest and candidate divergence receipt.
9. Verification receipts:
   - `verification/fuzz/p1-adapter3.json`, `verification/fuzz/p1-planner.json`, `verification/fuzz/p3-v2.json`
   - `verification/grammar/baseline-before-grammar.json`, `verification/grammar/after-p4b-grammar.json`
   - `verification/evaluation/family-a-locked-grammar-v2.json`, `verification/evaluation/session1-family-replay.json`, `verification/evaluation/session3-evaluation-summary.json`, `verification/evaluation/session3-evaluation-full.json`

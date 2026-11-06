# Axo — data identity, provenance and test reliability

**Spec:** user brief "AXO — DATA IDENTITY, PROVENANCE & TEST RELIABILITY HARDENING", 2026-11-05.
**Constraints:** branch `integration/axo-pedagogical-construction-hardening` only; no merge/rebase/cherry-pick/push; `main` read-only; `frontend/index.html` untouched; no Planner/Compiler/Kernel/backend change; `CACHE_VERSION` 131 unless invalidation is required; `Scene3DExplorer` kept; 0 provider calls.
**Preflight:** HEAD `28c7943b` (product `68c05cab`); dirty: `frontend/index.html` (user) + untracked diagnostics; 89 commits only on the branch, 206 only on `main`.

- [x] A. Data-flow audit (composer → `/api/analyze` → envelope → `loadEnvelope` → history local/server → routes → recovery snapshot); read-only contract check of branch backend and `main` Hybrid `/4`.
- [x] B. Reproduce identity faults with failing tests; separate submission identity (`submissionIdOf`) from compiled-geometry identity (`historyIdOf`); presentation context for samples vs submissions; legacy/server compatibility without rewriting IDs.
- [x] C. Statement provenance: learner → catalog → explicit "missing"; backend contract proposal for `/4` (not implemented on `main`).
- [x] D. Vitest timeouts: per-test timings at 11/6/4 workers, root cause, config fix, 5 stability runs.
- [x] E. Fixture identity scan of every audit/catalog scene; family07 D/D1 ambiguity; corrected synthetic statement + relation test.
- [x] F–G. Regression locks; E2E, UI harness ×2, paired performance and navigation runs; report and evidence index.

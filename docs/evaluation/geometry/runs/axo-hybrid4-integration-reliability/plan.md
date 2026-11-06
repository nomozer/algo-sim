# Axo × Hybrid `/4` — integration, submission identity, end-to-end reliability

**Spec:** user brief "AXO — HYBRID /4 INTEGRATION, SUBMISSION IDENTITY & END-TO-END RELIABILITY", 2026-11-05/06.
**Constraints:** new integration branch from verified `main`; `main` untouched; no push, no merge into `main`; no
cherry-pick; user's uncommitted `frontend/index.html` edit (other worktree) untouched; no Planner/Compiler/Kernel change;
no live AI; earlier evidence immutable; no `Co-Authored-By`.

**Baseline (verified):** `main` `bb61a804`; Axo `67f780ca`; merge base `f986e897` (= tag `pre-hybrid-cutover-f986e897`);
206 commits only on `main`, 91 only on Axo; 939 / 883 files changed per side, 10 overlapping.

- [x] 1. Audit both sides; worktree `.superpowers/worktrees/axo-hybrid4-integration`, branch `integration/axo-hybrid4-reliability` from `main`.
- [x] 2. `git merge --no-ff` Axo; resolve 6 conflicts + review 4 auto-merged files + check main's 163 deletions for re-adds.
- [x] 3. Attempt identity (`newAttemptId`, `recordId`) — tests on the real submit path, red first.
- [x] 4. Statement provenance: unify `main`'s `envelope.problem_statement` stamp with Axo's per-opening statement; backend cache boundary check; no backend contract change.
- [x] 5. Scene3D immutability: deep-frozen E2E across all interactions, shown to fail on the old in-place write.
- [x] 6–8. Full vitest, full pytest (17 merge-induced failures classified against `main` and fixed), candidate refreeze + template rebind, T3 in a clean worktree, E2E, UI harness, paired performance/navigation vs `main`.

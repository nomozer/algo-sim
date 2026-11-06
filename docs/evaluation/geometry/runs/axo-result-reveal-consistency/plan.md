# Axo — learner-requested results and statement/scene consistency

**Goal:** Stop auto-revealing final answers; prove that the statement, title, Scene3D and conclusions on screen belong to the open problem; protect the earlier render-loop gains.

**Spec:** User brief "AXO — Hoàn thiện trải nghiệm học sinh, kiểm soát đáp án và nghiệm thu Scene3D", received 2026-11-05. Work continues in the existing integration worktree on `integration/axo-pedagogical-construction-hardening`.

**Constraints:** Frontend only; no backend, Planner, Compiler or Verifier change. Preserve `frontend/index.html` (SHA256 `3B8A5566…A69F`). No merge, rebase, push, deploy or provider call. Earlier evidence is immutable.

**Preflight:** HEAD `219434ea` (product `34c779e1`); only `frontend/index.html` dirty (user title change) plus untracked diagnostics from the earlier run. Branch is 84 commits ahead of and diverged from root `main` `bb61a804` (Hybrid `/4` cutover lives only on `main`).

- [x] A. Audit: `#dock-goal-conclusion` renders whenever `finalConclusions` is non-empty (`SimulationWorkspace.tsx`). Scene/statement mismatch traced to the acceptance harness (sphere fixtures inherit `samples[0]` description, config and identity) and, separately, to the product statement fallback (`description` before `originalInput`; stale composer `problemText`).
- [x] B. P0 fixes plus red/green regression tests (`scene3d-result-reveal.test.tsx`, `problem-statement-source.test.tsx`); fix the harness fixtures and mark them synthetic.
- [x] C. Sphere audit on the production build (step order, X versus IA, reference versus section circle at three angles); existing exact Q³ invariant tests cited and run.
- [x] D. Browser E2E on the production build (`axo-result-reveal-browser-check.mjs`); same-environment performance before/after (`measure-axo-performance.mjs`) on baseline `34c779e1` and candidate; full vitest and build.

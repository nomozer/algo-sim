# Axo — remove answer presentation, record/scene identity safety, harness stability

**Spec:** user brief "AXO — ROOT-CAUSE CLEANUP, SCENE IDENTITY SAFETY & FINAL PEDAGOGICAL HARDENING", 2026-11-05. Continues `axo-result-reveal-consistency`.

**Constraints:** branch `integration/axo-pedagogical-construction-hardening` only; no merge/rebase/push/reset; `frontend/index.html` (user's Axo title) untouched; no backend or Hybrid `/4` change; earlier evidence immutable; 0 provider calls.

**Preflight:** HEAD `d349ee01` (product `514d34d4`); dirty: `frontend/index.html` (user) + untracked diagnostics; branch 87 commits only here, 206 only on `main`.

- [x] 1. Trace `finalConclusions` → `#dock-goal-reveal`/`#dock-goal-conclusion` → state/CSS/tests/harness. Remove the presentation path; keep `goalCompletion`, `tapKetQuaCuoi`, `coherentFormula`, certificates. Anti-regression test.
- [x] 2. Identity: remove title matching (`recoverCatalogScene3D`, `resolveGeometrySampleId`); bind the statement to the opening (`ActiveSimulation.problemStatement`); keep record envelope and `originalInput` from the same submission. Tests for same title, title-only legacy record, shared record with a sample, re-submission.
- [x] 3. 360 px harness failure: reproduce with a probe, find the state chain, fix in the harness, rerun the full harness three times.
- [x] 4–6. Full vitest, tsc/build, docs gate, browser E2E (incl. real 110% zoom), paired performance against the `514d34d4` build.

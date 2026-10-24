# Visual closure and Hybrid readiness implementation plan

Authorization: `GO_LOCAL_VISUAL_CLOSURE_AND_HYBRID_GEOMETRY_READINESS`.
Spec: Owner request P0–P8, 2026-10-25.

Goal: fix F1/F2 with RED/GREEN evidence, preserve the locked oracle, audit the 18 HTML configurations, and leave an honest Owner review packet.
Architecture: reuse Scene3DExplorer analysis identity, buildObject3D and existing Hybrid Registry/Planner/Engine. No schema, provider, default or cache changes.
Stack: existing React/Three.js/Vitest and Python exact engine.

## Preflight

- Root branch `research/hybrid-wave3a-volume-reasoning`, HEAD `fe9f5554`, dirty: preserve all user changes.
- Candidate branch `integration/hybrid-visual-candidate`, HEAD `1a4a0b93`, clean; main `9978e512`.
- Isolated local workspace has its own Git metadata and shared read-only object store. Root Git ref writes denied; no ACL changes. This continues the explicitly designated candidate, rather than starting unrelated work from stale main.
- Classification CORE (visual correctness / geometry capability) + SUPPORTING (offline evidence).
- Reuse: Scene3DExplorer, phanTichToanHocCuaCanh, coherentFormula, buildObject3D, sectionDetails, tangNhanManh, Registry and existing goal planner.
- Product truth: code/tests; learner UX: Owner P1/P2. Existing receipts are historical evidence, never overwritten.
- Expected edits: Scene3DExplorer.tsx and its regression, scene3d-view.tsx and section regression; new run reports/receipts. Scene changes beyond these only after proven need.
- Contract/cache/history impact: none expected; frontend presentation only. Cache stays 128, default LLM_ONLY, live0.
- Duplicate/cycle risk: low, extend existing functions; no parallel engine. Scope risk: large family expansion; P6 permits a complete specification when prerequisites fail.
- Minimum: suppress only duplicated entity formula with an accessible analysis link; selected section gets blue boundary while semantic fill stays terracotta.
- Stop: locked-oracle policy, independent reviewer, human visual approval or unsafe workspace. Do not invent passes.

## Tasks

- [ ] Verify baseline SHA, freeze receipt, HTML checksum/catalog and workspace integrity.
- [ ] F1: RED test of actual rendered inspector/analysis; fix matching entity only; verify Mode A and unmatched formula retained.
- [ ] F2: RED test of rendered section material; selected/hover feedback with unchanged geometry and default fill; GREEN.
- [ ] Run targeted Vitest, typecheck, full frontend/backend and locked official suite desktop/mobile; distinguish policy conflict from product failure.
- [ ] Browser Adapter /4, refusal, orbit, camera/identity/sphere visual audit; save before/after evidence.
- [ ] Freeze candidate, full T3 and post-freeze verify when workspace allows authoritative execution.
- [ ] Audit all 18 HTML entries against actual facts/gates/registry/planner/engine/adapter/render/browser/new problems.
- [ ] P6: choose a reusable slice only after safe visual checkpoint; otherwise publish function spec, independent oracle and exact blockers, without partial engine.
- [ ] Publish nine Owner reports, diff/checksums, indexes and review packet. Independent/human gates remain pending until actual Owner-appointed review.

## Review focus

Entity aliases and formula-less analysis rows; Mode A answer leakage; selection versus hover persistence; unchanged camera-dependent dash policy; semantic terracotta versus hue-only oracle conflict.

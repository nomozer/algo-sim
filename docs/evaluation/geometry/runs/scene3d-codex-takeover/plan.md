# Scene3D takeover implementation plan

> Execute inline using systematic-debugging, TDD and verification-before-completion.

Goal: continue Claude's frozen Scene3D candidate, fix remaining renderer defects and deliver honest review evidence.
Architecture: retain exact backend scene authority, OrbitControls, UI and existing CPU visibility classification. Presentation references never become scene facts.
Tech stack: existing TypeScript, Three.js, Vitest, Playwright; no new dependencies.
Spec: Owner takeover request P0–P11, 2026-10-26.

## Pre-flight

- Branch research/scene3d-codex-takeover, base 08929b893337e770649b9d854c8c71c4434edc29; clean before edits.
- Milestone: Scene3D review candidate, CORE correctness; supporting evidence only.
- Existing modules: scene3d-view, scene3d-edge-visibility, scene3d-model, scene3d-roles, scene3d-auxiliary.
- Reuse buildObject3D, updateCanonicalEdgeVisibility, diemVanhCongBiChe, pooled rim buffers and capture/math tools.
- Authority: backend SceneObject and independently calculated geometry; HTML is presentation reference only.
- Contract/cache/history impact: none. LLM_ONLY, cache129, ALLOW_LIVE_AI=0; no provider requests.
- Duplicate/cycle risk: extend existing renderer/helper; no parallel rendering implementation.
- Exclude website redesign, parser/inference changes, locked oracle edits, main merge, push, cleanup.
- Continuation from Claude candidate is explicitly authorized; do not restart from unrelated main.
- Preservation: root .superpowers/preservation-scene3d-codex-20261026, 1679 files, checksum MATCH, 0 errors.

## Tasks

- [x] P0 inventory, read source/checkpoints, preserve dirty root and Claude evidence; isolate continuation.
- [x] Reproduce curved-rim transition with an independent analytic normal oracle; refine actual 3D curve intervals, keep fixed reusable GPU buffers.
- [x] Reproduce missing standalone sphere reference; add one non-authoritative world-space great circle and suppress it for cutting-plane scenes.
- [x] Run related geometry regression, math checks and build, then capture real desktop/mobile camera evidence before/after.
- [x] Review full change; record official suite separately from role-aware checks and unresolved backend gaps.
- [x] Commit product, freeze, verify MATCH and run one full T3 on clean detached candidate; preserve failures honestly.
- [x] Produce handoff with exact identities, visual review list, approval states and next Hybrid campaign proposal only.

## Review focus

Tangency and nearly axial cameras; transformed/translated solids; sections versus presentation borders; hidden dash continuity under selection; resource stability while orbiting. No screenshot is the sole mathematical oracle.

Completion ruling: candidate delivered PARTIAL_WITH_GAPS; full T3/MATCH pass does not close backend authority gaps, uncertified matrix cells, residual label flags or Owner policy/visual approval. No Hybrid implementation.

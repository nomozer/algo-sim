# Unified Geometry Visual Language Implementation Plan

> Execute inline with superpowers:executing-plans; independent whole-change reviewer before freeze. Owner supplied the implementation scope P0–P10; no additional design approval gate is inferred. Human visual approval remains separate.

**Goal:** Make semantic surfaces, edges, sections and interaction states consistent across every existing geometry family.

**Architecture:** Extend `scene3d-roles.ts`, already shared by the renderer and CSS role legend. Keep all mesh construction, coordinates, camera and occlusion classification in their existing owners. Survey alternatives by replacing the token constant at build time in the browser harness, never by another renderer or a product theme UI.

**Tech stack:** React, TypeScript, Three.js 0.185.1, Vitest, Playwright, Python 3.12, existing offline Scene3D fixtures.

**Spec:** Owner's pasted P0–P10 request; root `DESIGN.md`; `docs/DESIGN_BRIEF.md`; `docs/architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md`.

## Global constraints

- Baseline campaign HEAD `f95596716912e5550ed079287221274b2d70f24c`; Owner explicitly chooses this stacked source instead of default new-branch-from-main policy.
- Preserve main/root/unrelated worktrees/historical runs; no merge, push, live AI or human approval claim.
- `DEFAULT_MODE = LLM_ONLY`, `RESPONSE_CONTRACT = flat`, `HYBRID_PRODUCT_ENABLEMENT = NO-GO`, `ALLOW_LIVE_AI = 0`, `CACHE_VERSION = 127`.
- No changes to facts, coordinates, topology, calculations, source/provenance gates, response contracts or construction dependencies.
- New evidence only in this run; authoritative T3 only after product commit and freeze, on a clean detached worktree.

## Review focus

1. Same section role across polygon/circle/ellipse must use the same unlit fill and opacity, still occluded by a foreground solid in Normal.
2. Secondary roles must not change on isolate, hide, step, scene reorder or selection; identity also conveyed by existing labels/tree and topology.
3. Causal selection retains its meaning and dash classifications; do not recolor numerical givens as selected.
4. Transparent flat sheets need one pass and no light-dependent muddy fill; lit solid shells retain depth cues and existing depth prepasses.
5. Orbit must not allocate fresh materials after span pools warm up; bounded measurements on actual WebGL, no aesthetic score inferred from assertions.

## Task 1 — audit and baseline

- [x] Verify all supplied Git refs, ancestry, root dirt and isolated worktree.
- [ ] Record source token table, complete material inventory and supported-family coverage manifest before editing product.
- [ ] Capture baseline with unchanged product renderer; save camera/state/viewport/fixture hashes.

## Task 2 — semantic styles

**Files:** extend `frontend/src/simulations/domains/geometry/scene3d-roles.ts`; consume in `scene3d-view.tsx`; synchronize `frontend/src/styles/tokens.css` if causal token changes; tests in existing material tests plus `scene3d-unified-materials.test.ts`.

- [ ] RED: real `buildObject3D` cross-shape section styles match; sections are unlit/single-pass; hidden lines subordinate but remain dashed when selected; complete-scene solid roles stable under reorder/filter; scene input immutable.
- [ ] GREEN: typed central style constant and semantic resolver, reuse existing causal table. Flat regions use MeshBasicMaterial, lit shells share one material policy. Stable source/derived solid roles are assigned before visibility filtering. No scene-id palette exception.
- [ ] Run focused material, occlusion, framing, role/CSS tests and typecheck.

## Task 3 — same-renderer A/B/C browser survey and regression

**Files:** only this run's scripts/fixtures/artifacts.

- [ ] Reuse existing framing measurement helpers and offline scene inventory; extend with supported missing shapes, including concave polyhedron, regular/prism variants and oblique curved sections. Label fixture provenance and any synthetic coverage.
- [ ] Compare A Conservative, B Academic, C High Contrast on identical geometry/state/camera/viewport; choose one default with explicit trade-offs; alternatives remain research data.
- [ ] Capture before/A/B/C/final overview; default/orbit/selected/Normal/X-ray, desktop/compact, analysis open/closed; explicitly state sampled combinations.
- [ ] Measure section own pixels, edge signatures, panel overlap, mode A leakage, repeat frames, labels, selection, interaction resources/performance; report UNKNOWN for unmeasured quantities.

## Task 4 — review, freeze, T3 and handoff

- [ ] Independent reviewer reads full change, sources and browser receipts; fix material findings.
- [ ] Commit product/tests with explicit file allowlist; lock full geometry directory tree, not merely the 114-file measured model surface.
- [ ] Freeze candidate via existing tool; clean detached worktree at exact candidate; authoritative full gate with raw bytes stdout/stderr, hashes, execution receipt; verify freeze MATCH.
- [ ] Index this run, document actual results/limits and full SHAs in Vietnamese handoff; preserve historical bytes; verify root/main/unrelated worktrees/governance.

## Decisions

- Reuse `scene3d-roles.ts` instead of inventing a parallel palette module. No graphify graph exists; direct indexed source inspection avoids building an unrelated knowledge graph.
- Source UI palette does not define geometry materials. Any new light amber section fill or depth/alpha style is an explicitly documented Scene3D extension; original DESIGN.md unchanged.

# Scene3D visual correction implementation plan

Authorization: `GO_LOCAL_SCENE3D_VISUAL_CORRECTION_AND_HYBRID_READINESS`, 2026-10-25. The supplied P0–P10 brief is the specification; execution is autonomous and inline.

Goal: correct reproducible visibility and interaction defects using existing Scene3D primitives, strengthen the supplemental role-aware checker, and measure an honest local candidate.

Architecture: backend owns geometry, names and provenance. Frontend performs presentation intersections only. Reuse `scene3d-edge-visibility.ts`, `scene3d-view.tsx`, `scene3d-roles.ts`, existing browser probes and freeze/T3 tools. No parallel renderer or inference engine.

Constraints: root and other worktrees untouched; one development worktree; no live model, merge main, push, ACL change, frozen oracle edit or cache/default change. Cache 129, LLM_ONLY, flat, Hybrid NO-GO. Existing node_modules junction reused read-only.

## Preflight

Branch `research/scene3d-visual-correction` created from main `9978e512`, fast-forwarded to verified candidate `fe5f40b7`. Clean before work. Source candidate clean at `.superpowers/worktrees/b3-dist`; no other collaboration agents. OS process ownership enumeration denied, so no existing process is stopped. Task CORE/SUPPORTING; supports thesis geometry presentation. Contract/history impact: none intended. Duplicate risk: extend existing visibility and oracle functions. Dependency direction unchanged. Scope risk: renderer capability is not Hybrid E2E support. Stop on required schema changes, unsafe workspace, or unproved mathematics.

## Tasks and verification

- [x] Verify Git state, read governing documents and recent handoffs; identify preserved Owner HTML and checksum its actual checkout bytes.
- [ ] Read and run reference HTML; compare source primitives, interactions and rejected mathematical shortcuts. Record original versus normalized hash honestly.
- [ ] RED/GREEN: curved visibility near silhouettes, cone slopes, finite caps, distant cameras, transformed scenes; fix shared classifier with bounded ray/volume intersections.
- [ ] RED/GREEN: hover differs from selection and resets across scenes; selected fill identity remains terracotta for polygon/circle/ellipse; preserve dash policy.
- [ ] RED/GREEN: supplemental role checker rejects wrong exact palette, partial edge loss, a small second selected-looking section and wrong rotated-camera visibility. Keep locked oracle unchanged.
- [ ] Check result privacy in Mode A and unique final answer in Mode B through real DOM and existing regressions; fix reproduced leaks at their shared presentation owner.
- [ ] Browser BEFORE/AFTER at matched cameras/steps/viewports, supported geometry-family matrix, selection/X-ray/zoom, mobile labels and right-angle markers. Refuse unsupported mathematics.
- [ ] Verify dev start/restart/force/HMR/separate caches; run focused frontend/backend, Adapter /4, official Visual suite, demo/crash and clean-candidate Full T3. Freeze in separate commit; no product mutation while measuring.
- [ ] Review source/tests/screenshots, classify campaign review versus independent review; write the eleven requested reports, run manifest and evidence pointers. Only claim readiness when all required gates actually pass.

## Review focus

Grazing rays must not inherit a fixed angular threshold. Cone normals include axial slope. Camera world coordinates must be transformed into payload coordinates for the oracle. Every hidden edge must be checked rather than aggregated away. Hovering another section must not impersonate a second selection. Coincident labels must retain separate identities. Mode B selection must not duplicate final formula.

## Ledger

Initial baseline: unified-material tests 11/11 pass. Official suite historical 7/8 is not a measurement of this run. Git creation required official escalation and succeeded; no ACL modified. Reference preserved at `../visual-closure-hybrid-readiness/reference/matphang.html` exists; bytes differ from report hash (line ending analysis pending).

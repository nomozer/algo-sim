# Scene3D final acceptance implementation plan

**Spec:** Owner attachment, FINAL SCENE3D VISUAL ACCEPTANCE, F2 POLICY RESOLUTION & HYBRID HANDOFF (2026-10-25).
**Goal:** Evaluate the existing candidate honestly and prepare the Owner decision, without changing the official oracle.
**Architecture:** Extend the proposed evaluator only. Reuse its pixel/color checks; derive continuous conics independently of renderer tessellation and add local missing-ink checks. Product fixes require a reproduced regression first.
**Stack:** Existing Node test, Three camera matrices, Playwright Chrome, offline scene envelopes.

## P0 checkpoint (before any code edit)

- Active branch: research/scene3d-visual-correction; HEAD 16b46d3880d0646fb3eae711fbf07556a40645c5; clean.
- Reuse existing worktree .superpowers/worktrees/scene3d-visual-correction; no new branch/worktree needed for this continuation.
- Root: research/hybrid-wave3a-volume-reasoning, fe9f555437498432427ae6bbd54402cdd59c7eb7; 19 modified tracked paths and untracked research/assets. Ownership unknown, treated as protected user/other-agent work. No writes there.
- Main: 9978e512a8a2a087475d792c0bd9db639c36acaa; candidate c84e8620, product b8b3311b.
- Current milestone: visual partial with gaps; official 7/8, independent and human approval pending.
- Classification: SUPPORTING, core thesis relevance is reliable presentation of authoritative spatial geometry.
- Reuse: assessSectionRole, project, existing browser fixture loader, section role probe, frozen T3 receipts and suite.
- Source of truth: Owner F2; backend scene coordinates; locked official suite remains separate authority for official score.
- Expected writes: proposed oracle/test, small browser probe additions, this run's artifacts/reports, CODE_INDEX and EVIDENCE_INDEX in this worktree only.
- Contract/cache/history impact: none planned; cache129, LLM_ONLY, Hybrid OFF, live0.
- Duplicate check: section-role-oracle and browser probe already exist; extend their responsibility, preserve V1 results.
- Dependency-cycle risk: none (scripts consume product scene, product never imports scripts).
- Scope-creep risk: no renderer rewrite, website redesign, backend, Geometry Functions or Hybrid implementation.
- Smallest implementation: independent conic boundary + local gap detection + paired official/proposed assessment on the same captures; targeted motion observations.
- Stop conditions: unresolved mathematical/presentation convention, inaccessible resources, missing source, failed freeze, or final Owner gate. Unknown stays UNKNOWN.
- Processes: node PIDs 2564,8140,9240,19484,24188,27428,27636; python 9196,13332 observed. Command-line inventory denied by Windows; no processes stopped. Vite/cache/dist ownership is treated as protected.

## Tasks

- [x] T0: Negative controls reproduced a local missing arc and partially label-covered edge falsely passing V1 (RED observed); final regressions GREEN.
- [x] Proposed V2 implemented; V1 results and locked official gate preserved. Independent conic frame/phase/sampling; source eligibility explicit.
- [x] Wrong fill/boundary, small second boundary, edge-on, tilted model, invalid source tested. Existing material tests cover normal/hover/selected; actual second selections18/18. Only observable claims certified.
- [x] Offline browser: same captures scored by locked hue predicate / V1 / V2 at five cameras and desktop/mobile. Motion CPU/frame and source-label observations recorded. No live provider calls.
- [x] Concise images inspected; previous family evidence attributed. One transition FAIL and temporal flags retained: no speculative renderer fix at this checkpoint.
- [x] Unchanged product verified against clean detached freeze and T3 receipt/stream hashes. Full T3 reused, not rerun for scripts/docs.
- [x] Review packet, handoff and H1–H4 plan prepared. Independent review/human approval remain pending; stop at Owner gate.

## Review focus

Missing contiguous hidden arc; partial occlusion by DOM label; tiny unselected region using cobalt; camera/model rotation; unknown parent geometry. No aggregate count may silently turn these into full certification.

## Rulings

- Owner supplied complete policy and execution authorization; proceed inline without another design permission step.
- Existing evidence is immutable. New evidence goes here. All claims from previous runs are attributed rather than reported as fresh measurements.
- No graphify graph exists; do not build a provider-backed code graph for this bounded offline task.
- Final status SCENE3D_VISUAL_PARTIAL_WITH_GAPS; NO-GO merge. V2 final4/1/25, official7/8 unchanged. Policy F2 resolved by Owner instruction; oracle adoption not recommended yet.
- Internal reviewer findings fixed conservatively with source validation/observability tests; original motion negative control marked INVALID and rerun separately18/18. Frozen evidence untouched.
- Reused modules: V1 color/pixel/project helpers, product material/annotation tests, OrbitControls, offline fixtures and prior T3. Created modules: proposed V2 and test, motion observation probe, pixel replay utility; no product modules/dependencies. Duplicate check: these add explicitly requested evaluation responsibilities and reuse existing authorities.

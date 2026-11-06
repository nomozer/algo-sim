# Axo final educational viewer readiness implementation plan

Date: 2026-11-06. User's supplied implementation brief is the specification. Execute inline, with sequential heavy checks and checkpoint commits; do not stop at planning.

Goal: preserve exact educational construction while removing hover rebuilds, explaining every certified section vertex, and measuring viewer/release readiness.

Architecture: retain Hybrid /4, TypedFactNext /2, Source Gate, planner and exact kernel. Geometry remains engine-owned; camera and transient hover belong to the viewer. Narration reads existing certified topology and construction events. No new dependencies, viewer mode, answer surface, or deployment topology.

## Pre-flight

- Branch `integration/axo-hybrid4-reliability`; starting HEAD `1be6a7aeb13707f2083e51f7dcc9ab2274a7335b`; main/merge-base `bb61a804eb2b476f796e28176084ea41b0bed92e`.
- Tracked integration tree clean. Pre-existing untracked historical performance outputs and dist folders preserved. Main and other worktrees remain untouched.
- Classification CORE (educational geometry viewer) + SUPPORTING (bounded verification/publication audit). Thesis relevance: spatial understanding, exact construction and usable observation.
- Reuse: `scene3d-view.tsx`/material policy/span pools, `scene3d-camera.ts`, `scene3d-semantic-policy.ts`, engine section provenance, existing camera/orbit/consistency/performance/full-gate scripts and publication scanner.
- Expected edits: viewer transient emphasis, presenter topology narration, focused regression tests/browser harness, run evidence and living indexes. Backend product edits only if a demonstrated upstream defect requires them.
- Contract/cache/history impact: none intended; verify cache identity and candidate, refreeze product identity after product commits. No history rewrite.
- Duplicate/cycle risks: extend current render/presenter ownership; do not introduce parallel geometry or a second source of topology.
- Smallest sufficient implementation: update existing materials/metadata for hover; consume engine-provided section topology to describe unnamed vertices and face traces; change camera only for measured defects.
- Excluded: solver changes for screenshots, answer disclosure, new services, live provider, merge/push, automatic publication exceptions.
- Stop conditions: resource pressure → stop only task processes and record RESOURCE_LIMITED; owner-only decisions stay pending; no success claim for unmeasured gates.

## Checkpoints

- [ ] 1. Capture all-worktree status, resources, seal, baseline screenshots and actual hover allocations. Write a regression that fails on baseline.
- [ ] 2. Separate geometry lifecycle from hover/tooltip state; retain semantic colors and selection/isolate/drag behaviour. Run targeted tests and lifecycle fault injection; commit.
- [ ] 3. Audit camera fit/clip/zoom/resize across requested families; compare identical poses/viewports. Fix only demonstrated bugs with regressions; commit if needed.
- [ ] 4. Trace certified section provenance through presenter. Test 3–6 vertices, unnamed vertices, exterior intersection, renaming, permutations and coincident face. Repair narration without changing math; commit.
- [ ] 5. Verify equivalent Vietnamese input wording offline through existing extraction/bridge/source/engine tests. New held-out cases after implementation; no provider calls.
- [ ] 6. Classify publication metadata safely; assess migrations/account/history/idempotency/telemetry and merge-base. Preserve immutable evidence; owner exceptions remain pending.
- [ ] 7. Freeze candidate; commit checkpoint; create clean detached verifier. Run full T3 once after stability, node harness, browser E2E, orbit and publication sequentially. Vitest ≤4 workers (use 2), browser workers 1.
- [ ] 8. Inspect selected images, compare runtime samples without claiming noise as improvement. Write report A–N, handoff and run.json; register evidence and exact hashes; final verification commit.

## Review focus

Hover A→B→leave and drag from hover must retain geometry identities; camera defaults/reset must fit finite objects while arbitrary top views may legitimately flatten projections; narration must cover anonymous edge intersections without inventing labels or using an exterior line point as a section vertex; final DOM/ARIA/tooltips must not disclose answers; historical publication findings cannot be removed by editing HEAD or self-approved.

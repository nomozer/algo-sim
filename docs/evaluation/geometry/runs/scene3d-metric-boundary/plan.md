# Scene3D metric boundary closeout

Goal: reject invalid Scene3D envelopes before acceptance, without domain knowledge in the store.
Owner specification: FINAL SAFETY CLOSEOUT, 2026-10-18; M2 #7 retained; Hybrid remains locked.

Preflight: research/scene3d-plane-grid-camera, 5f77bfcea4e63aa4bc638d8d9a90eca9d0a74141, clean.
Main: 90fe44df9fd600bf0eded87a316b8e6dddc29cc5. T3: 8e2235e7; subsequent commit docs/evidence only.
Classification: SUPPORTING correctness blocker for the spatial geometry thesis. Existing isolated worktree retained.

Reuse: module contract / registry, validateSemanticConfig, hopLeScene3D, sole hopLeChartMetric,
historyStore and existing 41 offline fixtures. No new validator authority or product module.
Dependencies: store -> registry/types; semantic module -> geometry model. No reverse dependency or cycle.
History: no migration, deletion or version bump; reject before record; revalidate old records on reopen.
Excluded: Hybrid runtime, preview/browser wiring, provider requests, main merge/push, cleanup.

- [ ] Add failing tests using real registered module: malformed, non-SPD, overflow; direct store bypass,
  API response, old history, stale active state, forbidden fallback; preserve valid 2D and 3D.
- [ ] Add optional validateEnvelope to SimulationModule returning ConfigResult; store delegates before init/history.
  Semantic module checks any supplied scene via the existing domain authority then validates config.
- [ ] Run RED -> GREEN and existing contract/rendering tests; pin domain-blind store architecture.
- [ ] Independent read-only review: bypass, fallback and F4 locked product path; resolve blockers.
- [ ] Commit product/tests, refreeze in a fresh clean detached worktree; commit freeze; full T3, build,
  orbit, fixture integrity and negative tests on a fresh clean detached candidate. Retain all worktrees.
- [ ] Add append-only correction report, machine receipts and evidence index. F3/F4/F5/F6 remain open for
  offline integration / before GO HYBRID. Human visual review remains pending.

Stop conditions: no ready verdict unless boundary and all gates pass. No Product E2E Hybrid claim.

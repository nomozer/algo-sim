# Handoff — `hybrid-pre-main-hardening`

**State:** branch `research/hybrid-pre-main-hardening` (worktree `.superpowers/worktrees/hybrid-pre-main-hardening`),
not merged, not pushed. `main` is still `4abc4afb`; this branch is a fast-forward of it. Hybrid off, `LLM_ONLY` default.

## GO MAIN — sufficient conditions

1. Owner GO for this branch (approval of the earlier task does not carry over).
2. `report.md` §8 verdict `PRE_MAIN_HARDENING_VERIFIED`: independent review PASS with no blocking finding, authoritative
   T3 PASS in a clean detached checkout of the branch tip, `freeze_evaluation_candidate.py --verify` MATCH.
3. `main` still equals `origin/main` and is an ancestor of the branch tip (`git merge --ff-only` possible).
4. Coordinate with `research/scene3d-plane-grid-camera`: this branch does not touch `frontend/src`, so no file overlap.

Procedure: `git -C <main checkout> merge --ff-only research/hybrid-pre-main-hardening`; `git push origin main` (no
force); confirm `git rev-parse main origin/main` agree; only then run the cleanup order in `cleanup-manifest.json`.

## GO LIVE — separate, not implied by GO MAIN

Requires route D wired behind a flag (below), a fresh preregistered held-out set (the LOCKED set is contacted), owner
budget + stop rule, `MEASUREMENT_CLASS` · `HELD_OUT_CLAIM` · `EVALUATOR_INDEPENDENCE`, and a paired comparison with
`LLM_ONLY`. `certify_acceptance_runner.py` first (0 calls).

## Next implementation (LOCAL, offline, 0 model calls) — wire route D without enabling it

1. `RoutePolicy` gains a route-D mode (env, default off); `fingerprint()` adds `REGISTRY_VERSION`, `PLANNER_VERSION`,
   `ENGINE_VERSION`, `fact_extraction.surface_fingerprint(contract)`; the two-way isolation tests extend to it.
2. Adapter `KetQuaTuyen` → `ValidatedSimulationEnvelope` (one authority, reusing `pipeline_adapter` conventions):
   goal checks never presented as proven; `length_unit` carried; refusal codes → learner messages (UI hygiene).
3. A preview endpoint gated by that env, no cache writes, not called by the frontend; declare it as a gate in the
   `test_Y_*` guard instead of bypassing it; prove `LLM_ONLY` output is unchanged byte for byte.
4. `runtime_identity` reports the route policy and the route-D versions.
5. Refreeze, independent review, T3. Live stays NO-GO.

Frontend items F1–F4 (`frontend-handoff.md`) belong to the Scene3D owner and to step 2.

## Operational hazard to raise with the owner

`integration/extraction-v2-safety` tracks `origin/main`; a bare `git push` from it would update `main`.
Suggested (owner): `git branch --unset-upstream integration/extraction-v2-safety`.

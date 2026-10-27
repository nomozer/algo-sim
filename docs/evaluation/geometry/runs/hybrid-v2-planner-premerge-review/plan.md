# plan.md — `hybrid-v2-planner-premerge-review`

- **Task:** `HYBRID_V2_PLANNER_PREMERGE_CORRECTNESS_REVIEW` (Owner, 2026-10-27).
- **Branch / worktree:** `research/hybrid-v2-planner-generalization` · `.superpowers/worktrees/planner-generalization`.
- **Reviewed baseline:** final doc commit `81b545a2`; frozen candidate `ca0bb5f2`; product `de7b2813`
  (product tree identical across `de7b2813..81b545a2`, verified with `git diff --stat -- backend/app frontend/src`).
- **Scope:** independent review of planner `/16` + registry `/15`; reproduce the declared kind-only Source Gate limitation;
  if it fails open, ONE minimal Source Gate fix. Adapter `/4` untouched. No merge, push, live provider, default change.

## Steps

1. Preflight: clean tree, ancestry `386d2149 → 81b545a2`, inherited T3 receipt hashes, candidate identity.
2. Review the product diff `70ba1577..de7b2813` (`planner._mat_vuong_duong`, `registry._TU_KHOI`, `_cum_goi_khoi`).
3. RED: `tools/adversarial.py` — kind words × solids × clauses (area / construction / both / volume / two solids),
   expectations written from geometry before running; run on the frozen candidate in a detached checkout
   → `results/red-before.json`.
4. If fail-open: Source Gate fix in `registry.py` only (reuse validated solid calls; generic vs specific class).
5. GREEN: same harness on the fix → `results/green-after.json`; regression test `test_solid_kind_source_binding.py`.
6. T0 impact, T1 geometry + semantic, T2 frontend; re-freeze candidate; Full T3 on a clean detached checkout; post-T3 MATCH.
7. Independent review of the fix delta (separate context); `review.md`, `report.md`, `handoff.md`, `run.json`.

## Stop conditions

As in the Owner task §10 (schema/IR/engine/provider change, wrong-serve regression, unexplained false refusal, T3 FAIL,
unowned worktree change, live AI or merge needed).

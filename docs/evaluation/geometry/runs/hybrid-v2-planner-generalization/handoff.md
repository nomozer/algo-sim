# Handoff: hybrid-v2-planner-generalization

**Status:** `READY_FOR_OWNER_REVIEW`. Branch `research/hybrid-v2-planner-generalization`, worktree
`.superpowers/worktrees/planner-generalization`. Not merged, not pushed. Base `main` `386d2149`.

## What changed

- Product `de7b2813`:
  - planner `/16`: prism, cuboid and cube planes through a point ⊥ a vertex-to-vertex line.
  - registry `/15`: bare solid words are accepted in section phrases, and every section reference must name the cut solid.
- Registered corpus: 10/10 positives served with exact oracle agreement, 8/8 negatives refused with the registered reason, 0 wrong serves. This is development evidence only.
- Full T3 PASS on `ca0bb5f2` (12275 / 1417), post-freeze MATCH. Details are in `report.md`.

## Before trusting a number

```bash
git -C .superpowers/worktrees/planner-generalization log --oneline 386d2149..HEAD
cd .superpowers/worktrees/planner-generalization/backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/freeze_evaluation_candidate.py --verify
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/geometry/test_prism_perpendicular_section_planning.py -q
```

## Open, in priority order

1. **Owner decision:** merge this branch (opt-in route only, `LLM_ONLY` unchanged), or keep it as research.
2. **ADAPTER_INTEGRATION_GAP.** The `/4` wrapper refuses plane-only derived sections because they carry no `DINH_CAT_CANH` vertex certificate. This also happens for pyramids at baseline. Fixing it changes every V2 derived section, so it should be a separate wave with an owner GO. The slice test pins the current fail-closed behaviour.
3. Independent holdout and live NL E2E were not executed. No browser evidence exists for this slice. No independent code review was done.

## Housekeeping

- The T3 checkout `D:/tmp/pg-t3-ca0bb5f2` was left in place. Its `frontend/node_modules` is a junction, so run `rmdir` on the junction before `git worktree remove`.
- Old worktrees were not touched.

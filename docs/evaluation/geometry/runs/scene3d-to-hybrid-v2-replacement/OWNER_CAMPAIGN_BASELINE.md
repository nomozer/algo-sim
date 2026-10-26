# Owner campaign baseline

Directive: Scene3D final correction → Hybrid V2 architecture replacement (2026-10-26). Ancestry, receipts and the defect
list: [BASELINE_AND_ANCESTRY.md](BASELINE_AND_ANCESTRY.md).

- **Base commit:** `11188e7a` (`research/scene3d-codex-takeover`), product identical to clean freeze `e1ebc72c`.
- **Branch / worktree:** `research/scene3d-to-hybrid-v2-replacement` in `.superpowers/worktrees/s3d-hybrid-v2`.
- **Baseline gates (inherited, measured at `e1ebc72c`):** Full T3 PASS (backend 11,923 passed; frontend 1,386); official
  Visual 7/8 (F2 governance gap); independent review PENDING; human visual approval PENDING.

## Allowed to change

- Geometry-to-render mapping, visibility/clipping, solid/hidden strokes, plane representation, section boundaries,
  point/line/plane labels, right-angle and other geometry symbols, label anchoring, geometry selection/highlight
  (`frontend/src/simulations/domains/geometry/**` except web chrome).
- Backend producers of scene facts: witnesses, notation, event kind, learner text (`backend/app/simulation/semantic_program/**`,
  `geometry_functions/**`, `ai/function_route.py`), and the offline sample programs.
- Hybrid V2 route D code, its adapters, offline replay, frontend consumer, tests and evidence.

## Not allowed

- Web background/theme, home, library, navigation, cards, layout, sidebar, menus, toolbars; existing camera controls.
- Editing the locked official oracle or thresholds; editing old receipts or reports.
- Changing the default route (`LLM_ONLY`), enabling a live provider (`ALLOW_LIVE_AI=0`, 0 model calls), merging or pushing
  `main`, rewriting history, `reset --hard`, `clean -fd`, force-removing worktrees, ACL changes.
- Building, editing or staging anything in the root checkout.

## Gate policy

Tier 1 targeted tests per change; tier 2 browser matrix per functional group; tier 3 official suite + one Full T3 on a clean
detached freeze per milestone (`VISUAL_CORRECTION_CANDIDATE`, then `HYBRID_V2_REPLACEMENT_READINESS_CANDIDATE`). Failed
receipts are kept.

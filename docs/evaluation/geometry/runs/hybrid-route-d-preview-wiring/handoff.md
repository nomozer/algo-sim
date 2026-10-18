# Handoff — `hybrid-route-d-preview-wiring`

**State:** branch `research/hybrid-route-d-preview-wiring` (worktree `.superpowers/worktrees/hybrid-route-d-preview-wiring`,
`frontend/node_modules` is a junction — `rmdir` it before any `git worktree remove`). Not merged, not pushed; a
fast-forward of `main` `6592306d`. Route D product enablement NO-GO; preview OFF unless the operator sets it.

## Using the preview (operator, local only)

`HYBRID_ROUTE_D_PREVIEW=1`, `HYBRID_ROUTE_D_PREVIEW_TOKEN=<≥ 32 chars>`, run the backend on the host (loopback peer —
behind Docker / a proxy it answers 403), install `app.state.hybrid_preview_fixtures = {exact problem text:
provider-format JSON}`, then `POST /api/preview/hybrid` with `X-AlgoSim-Preview-Token`. There is no live provider
path; adding one is a separate, owner-approved task.

## GO MAIN — sufficient conditions

1. Owner GO for this branch (no earlier approval carries over).
2. `report.md` §0 verdict `ROUTE_D_PREVIEW_VERIFIED`: independent review PASS with 0 blocking, authoritative T3
   `FULL_PRODUCT_GATE_PASS` on a clean detached checkout of the branch tip, `--verify` MATCH.
3. `main` = `origin/main` and an ancestor of the tip; `git merge --ff-only`, push without force, compare
   `git rev-parse main origin/main`.

## Next exact GO (each a separate owner decision)

- **GO MAIN** for this branch (above).
- Then, if wanted: **GO LIVE PREVIEW PILOT** — a provider transport behind `ALLOW_LIVE_AI=1` for the preview only, with a
  fresh preregistered held-out set (the LOCKED set is contacted), budget + stop rule, `MEASUREMENT_CLASS` ·
  `HELD_OUT_CLAIM` · `EVALUATOR_INDEPENDENCE`, paired against `LLM_ONLY`.
- Frontend: consuming `route_d` (goal observations as "quan sát trên hình dựng", `length_unit` sentence) and F1/F2 of
  `hybrid-pre-main-hardening/frontend-handoff.md` belong to the Scene3D owner.

## Takeover artefacts (local, gitignored — keep until GO MAIN, then deletable)

- `.superpowers/takeover-route-d-preview-20261018/` — zero-loss snapshot of the Codex state (now also in `902730b9`).
- `.superpowers/preview-verification/` inside this worktree — Codex's logs (copied into the snapshot).

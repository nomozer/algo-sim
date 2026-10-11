# Final integration gates — handoff

Status: `ALGOSIM_FINAL_INTEGRATION_GATES_AWAITING_APPROVAL`.
Next action: `GEOMETRY_LIBRARY_INTEGRATION_APPROVAL_DECISION` (the user's).

## Where things are

| Item | Value |
|---|---|
| Branch | `feat/geometry-library-expansion` in `.superpowers/worktrees/geometry-library-expansion` |
| Worktrees | the only one left besides the main checkout |
| `main` | `28ac1d61`, unchanged |
| Candidate | `a8dc02fc…` (product `4ad89909`) |
| Locked A/B | `12da4768…` |
| git config | `core.longpaths=true` now set **locally** (`.git/config`); global/system unset |

## Key findings

- **Orbit gate red.** Two layout-driven facts, both already on `main`: the canvas grew 545 → 683 px, and a fixed 250 ms read truncates the damping tail. The camera rotates correctly. The gate was not edited and the threshold was not lowered; a replacement acceptance is proposed in [report.md](report.md) §1.
- **Intermittent test:** 1/9 full runs, cause UNKNOWN. It now reports the child's exit code and output if it fails again.
- **T3:** `FULL_PRODUCT_GATE_PASS` in a clean detached worktree at `ffe7fd68`.

## Before any fast-forward of `main` in the main checkout

31 untracked files under `docs/evaluation/geometry/runs/hybrid-ab-pilot-readiness/` are byte-identical to tracked branch files and will block the checkout. They were not touched.

## Reproduce the orbit diagnosis

Copy `diagnostics/orbit-damping-probe.mjs` and `orbit-canvas-probe.mjs` into `frontend/scripts/` (they import `./browser-runner.mjs` and the gate), then run:

```bash
node scripts/orbit-damping-probe.mjs <dist> 250,5000
```

Delete the copies afterwards.

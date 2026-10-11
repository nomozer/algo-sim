# Geometry library important fixes — handoff

Status: `GEOMETRY_LIBRARY_IMPORTANT_FIXES_AWAITING_REVIEW`.
Next action: `GEOMETRY_LIBRARY_INTEGRATION_APPROVAL_DECISION` (the user's).

## Where things are

| Item | Value |
|---|---|
| Branch | `feat/geometry-library-expansion` |
| Worktree | `.superpowers/worktrees/geometry-library-expansion` |
| Clean measurement worktree (kept) | `.superpowers/worktrees/geometry-library-fixes-freeze` (detached at `811896f8`, clean) |
| Main | `28ac1d61`, unchanged; your untracked `frontend/public/` and `docs/evaluation/geometry/runs/hybrid-ab-pilot-readiness/` in the main checkout untouched |
| Candidate | `a8dc02fc…` (110 files, product `4ad89909`, rule `product-paths-excluding-test-only/1`) |
| Locked A/B | `12da4768…` untouched |
| Live calls | 0 |

## What changed

- **I1:** the declared pyramid topology (`S.ABC` in the source) reaches formation and scene roles. A projected point carries an auxiliary perpendicular, with its marker at the exact foot.
- **I2:** product identity counts renderer changes again, excludes only test harness files, and names its rule. Legacy manifests are verified with the legacy rule (61/61).
- **I3:** no `ALGOSIM_*` overrides remain.
  - The locked A/B runner tests use a hash-verified frozen surface.
  - Live-pilot readiness of the current surface is a NO-GO test.
  - Identity is handled by a correction-layer divergence declaration plus the standard refreeze.

Details, numbers and the integration plan: [report.md](report.md).

## Reproduce

From a clean worktree's `backend/`, Windows:

```bash
GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.longpaths GIT_CONFIG_VALUE_0=true ALLOW_LIVE_AI=0 PYTHONIOENCODING=utf-8 \
  .venv/Scripts/python.exe -m pytest -q
```

`core.longpaths` is a prerequisite of the repository on Windows (paths longer than 260 characters), not an identity override.

Browser gate: `node scripts/scene3d-orbit-gate.mjs --ra <new dir>`. Without `--ra` it overwrites the historical `ORBIT_GATE.json`.

## Open before integration

1. Orbit gate red in this environment, identically before the fix.
2. One intermittent backend test, cause UNKNOWN.
3. Human visual acceptance.

No merge, push, cherry-pick, branch or worktree deletion was done.

# Main integration — handoff and merge procedure

Status: `ALGOSIM_MAIN_INTEGRATION_READY_FOR_FINAL_APPROVAL`.
Next action: `GEOMETRY_LIBRARY_INTEGRATION_APPROVAL_DECISION` (the user's).

| Item | Value |
|---|---|
| `main` | `28ac1d61` (unchanged) |
| `integration/geometry-functions` | built from `main` by fast-forward; same tip as `feat/geometry-library-expansion` after the docs commit |
| Candidate | tree `a8dc02fc…`, product `74df2a78` |
| Locked A/B | `12da4768…` |
| Worktrees left | main checkout + `geometry-library-expansion` |

## Merge procedure (only after your final acceptance)

**1. Remove the 31 colliding untracked files** from the main checkout. They are byte-identical to tracked files of the branch and backed up, verified 31/31, in `D:\Documents\projects\algo-sim-backups\20261011-hybrid-ab-pilot-readiness-untracked\`. They belong to `CodexSandboxOffline`, so use **PowerShell run as Administrator**:

```powershell
Remove-Item -Recurse -LiteralPath "D:\Documents\projects\algo-sim\docs\evaluation\geometry\runs\hybrid-ab-pilot-readiness"
```

**2. Fast-forward `main`** in the main checkout, which is on `main`:

```powershell
cd D:\Documents\projects\algo-sim
git status --short
git merge --ff-only integration/geometry-functions
```

- Before the merge, `git status --short` should show only `?? frontend/public/`.
- `--ff-only` refuses rather than creating a merge commit or overwriting anything.

**3. Verify on `main`:**

```powershell
git log -1 --oneline
cd backend
$env:PYTHONIOENCODING = "utf-8"
.\.venv\Scripts\python.exe scripts\freeze_evaluation_candidate.py --verify
cd ..\frontend
npm run test:full
```

`--verify` must print "Candidate khớp…", and T3 should print `FULL_PRODUCT_GATE_PASS`.

**4. Push** only when you decide to. Nothing was pushed.

## Open after the merge

- **p1 orbit defect** (on `main` already): the validated orbit gate v3 is red until it is fixed.
- **Intermittent generator test:** cause UNKNOWN; it now reports its own evidence.
- **Human visual acceptance:** of the screenshots.

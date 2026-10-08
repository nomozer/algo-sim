# Final documentation organization

## Result

- Classified all 167 retained root reports: 33 moved beside their registered artifact package, 123 moved to
  `docs/evaluation/reports/`, and 11 path-bound exceptions retained at `docs/` with file-level reasons.
- Preserved 167/167 source blobs. The implementation commit records 156 `R100` moves; three opaque filenames
  (`B02_*`, `C02_*`) now use short functional names. No evidence content was rewritten.
- Updated the catalog, living links, dynamic paths, scripts, tests and the closed-root guard. `docs/` now has 29
  Markdown files: 18 living/canonical project documents and 11 explicit report/contract exceptions.
- No report or artifact was deleted in this final placement wave. The preceding `docs-cleanup-2026-10-08` run owns
  the deletion decisions for retired Informatics material and the full 180-report/13,174-artifact classification.

## Verification

- Clean detached worktree at `a3448c71`: full backend `7234 passed, 1 skipped, 2 deselected`, exit 0 in 339.42 s.
  Authoritative output: `diagnostics/full-backend-authoritative.log`; exit code:
  `diagnostics/full-backend-authoritative.exit-code.txt`.
- The earlier sandboxed attempt was diagnostic only: Python could not write its temp directory. Its raw traceback
  log is not retained. The corrected authoritative run used the same offline suite with a writable temp location.
- Frontend: 67 files / 1,023 tests passed; `tsc -b` passed; Vite production build passed to a fresh temporary
  outDir. The default `frontend/dist` could not be emptied because it is owned by an older sandbox identity; it is
  untracked and was not altered.
- Documentation audit passed with 0 broken links, 0 stale CODE_INDEX paths, 167 catalog targets and no unclassified
  root report. Candidate verify passed at tree hash `b4a33205a3d0e6d2`; cache lock passed at version 117.
- No model request, screenshot, prompt/IR removal, geometry change, PR, push or quality-guard relaxation occurred.

## Commits

- `23aff0ad` — relocate reports and update consumers/indexes.
- `9c176272` — refresh candidate commit metadata only; measured tree hash unchanged.
- `a3448c71` — repair six path consumers/test pins exposed by full-suite verification.

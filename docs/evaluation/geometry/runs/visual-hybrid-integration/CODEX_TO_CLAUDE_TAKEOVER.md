# Codex → Claude takeover (visual–Hybrid integration)

Authorization `GO_CLAUDE_TAKEOVER_VISUAL_HYBRID_INTEGRATION_LOCAL_ONLY` (2026-10-24). This document records the state found on disk, read from Git and files, not from the Codex UI.

## Recovered state (19:42 local, last Codex write 19:29)

| Worktree | Ref | Role | Uncommitted |
|---|---|---|---|
| `.superpowers/worktrees/hybrid-visual-candidate` | branch `integration/hybrid-visual-candidate` at `78e88470` (merge: 1st parent B1/B2 `97d59bf9`, 2nd parent Visual `7f90d9b3`; `main 9978e512` is an ancestor, 51 commits ahead) | **working integration tree** | 4 tracked + 156 untracked run files (below) |
| `.superpowers/worktrees/visual-hybrid-integration` | detached at Visual candidate `13d28b84` | Codex measurement tree for the Visual official suite | `frontend/scripts/compiler-scene-suite.mjs` (same harness hunk), untracked `.visual-closure-vite-cache/` and run evidence incl. `visual/official-suite*` |

Processes found: Codex VS Code extension host/runner (idle since 19:29) and a Codex Vite dev server (`127.0.0.1:3117`, started 19:15, cache `../.visual-closure-vite-cache`). Neither was stopped; Claude uses other ports.

Root checkout: branch `research/hybrid-wave3a-volume-reasoning`, owner's 19 modified tracked files + untracked work, all preserved. Codex recorded 79 SHA-256 hashes in `root-protected-hashes.json`.

### The "7 files" from the Codex UI

On disk, the tracked edits are 4 files (+18/−9). The UI count cannot be reproduced exactly; every edit that exists is listed here.

1. `frontend/src/simulations/domains/geometry/scene3d-presentation.ts`: removes the V6.2 rewrite in `kyHieu`. The old code had `/I\d/ → null` and `"(HUW)" → "(P)"`.
2. `frontend/src/simulations/domains/geometry/scene3d-presentation.test.ts`: `it.each(["I1","I12","AI2","(HUW)","(α)"])` keeps backend notation verbatim.
3. `frontend/scripts/compiler-scene-suite.mjs` (harness only):
   - exports `sectionFillEvidence` unchanged;
   - records a failed served run as a failure row instead of aborting the suite;
   - writes a per-scenario JSON.
   - Thresholds and oracle are unchanged.
4. `docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json`: Codex re-froze at `78e88470` with `"cay_lam_viec_sach": false` (dirty tree). It is **not** authoritative and is superseded by a clean re-freeze after the fix is committed.

Untracked run directory `docs/evaluation/geometry/runs/visual-hybrid-integration/` (13 MB):
- `plan.md`, `SECOND_INDEPENDENT_REVIEW.md`, `BRANCH_ANCESTRY_AND_DIFF_REPORT.md`;
- `ancestry.json`, `worktree-inventory.json`, root snapshots;
- `section-fill-closure.mjs`;
- `visual/` (49 regenerated official fixtures + suite manifest, default-scene/first-closure/marker captures, orbit gate);
- `integrated/` (fresh B1/B2 service export at `78e88470`: 47 cases, 22 served, 25 refused, 0 wrong-served, 0 false-refused).

The measurement tree additionally holds the official suite outputs.

## What Codex had finished

- P0 audit.
- Second independent source review of `852f6501` (PASS_WITH_LIMITS).
- Official Visual suite on `13d28b84` (completed 19:38; 8/8 scenarios FAIL, classified below).
- Visual captures.
- The integration merge `78e88470`.
- Integrated B1/B2 export.
- The label-authority fix, uncommitted.

Not done:
- commit of the fix;
- clean candidate;
- integrated browser acceptance;
- integrated T3;
- integrated review;
- the seven reports.

The plan ledger stops at "Integration not yet created", so it is stale relative to the merge commit.

## Verified by Claude before continuing

- The label defect originated in `3bfc8dd0`, the verbatim checkpoint of the owner's V6.2 session, which Claude committed without reviewing that hunk in the SGK port campaign.
- The fix is correct. RED proof: re-adding the two V6.2 lines makes 4 cases fail (`I1`, `I12`, `AI2`, `(HUW)`), while the `(α)` control passes both ways. After restoring Codex's fix, 19/19 pass; the working tree diff equals Codex's edit exactly.
- The integration tree is green:
  - `tsc -b` 0;
  - Vitest 79 files / 1337 tests;
  - backend B1/B2 + Adapter /4 + default-route/API 236 tests.
- The official-suite failures are inherited, not caused by the port or the merge. 7 scenarios abort in `quantity_picker` / `solution_final` / `show_all_toggle` (class HARNESS); the root is commit `aa458cc3` (2026-10-19, already in `main`), whose learner UX deliberately removes final answers from the quantity drawer that the suite oracle expects. There are also 2 ENVIRONMENT-class aborts. Neither the oracle nor the UX was changed (owner gate).

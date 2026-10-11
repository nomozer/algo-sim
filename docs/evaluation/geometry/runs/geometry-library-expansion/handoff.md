# Geometry library expansion — LOCAL handoff

Status: GEOMETRY_LIBRARY_EXPANSION_AWAITING_REVIEW.
GO for bounded offline review; NO-GO for live pilot, merge/default switch without separate approval.

Working branch: feat/geometry-library-expansion; base2990d87d, product a0eb1450,
clean verification815f06be. Documentation/evidence commit role SELF; inspect Git HEAD.
Worktree: D:/Documents/projects/algo-sim/.superpowers/worktrees/geometry-library-expansion.

## Delivered boundary

Unique line-line/line-plane point intersections, point-line projection and constructive
existing point-plane projection are available through both real fake-provider A and
Hybrid B adapters. Registry27; existing Planner/Engine/Kernel/IR/Scene3D, no second authority.
New points carry derived provenance, producer/dependencies and verified incidence/
orthogonality; no supplied result-coordinate facts. Non-unique/no/skew/degenerate and
unresolved/conflicting constructions fail closed. Known-foot inverse projections preserved.

Before/after matrix, served/refused examples and remaining limits: [report.md](report.md).
Prior audit/preflight are preserved snapshots, not the current implementation status.

## Evidence

- 58 preregistered RED, then91 feature tests PASS including independent literal oracle,
  negative/metamorphic checks and5 behavioral mutants killed.
- 74 fake certification calls (37A+37B), repeat74 identical LF bytes; not independent
  samples or a pilot.14 positive outcomes,8 Scene3D exports,0 provider network/live.
- 34 focused renderer/metric/annotation tests PASS, TypeScript PASS;8 desktop scenes
  and1 mobile check via actual Scene3DWorkspace. Agent inspected screenshots.
- 695 geometry frontend-domain tests PASS/34 files; existing SSR warnings remain,
  raw journal retained in ignored scratch, compact counts registered in diagnostics/.
- 93 affected documentation/telemetry tests PASS, documentation audit PASS.
- Full backend:8166 PASS/1 skipped/2 deselected,0 failure/error,386.64s at clean815f06be;
  diagnostics/full-backend.xml. One existing Starlette deprecation warning; clean before/after.

No human visual approval, live extraction-quality, provider cost-bound or population
safety proof. Old angle/two-nonpoint ANNOTATION_UNBOUND is a display gap and remains.

## Reproduce safely

Run from THIS worktree's backend directory using the existing local virtualenv.
Do not write into any committed diagnostics/offline-certification directory. Fresh outputs
belong to a new ignored scratch directory; pytest basetemp must be a new exact path.

Set ALLOW_LIVE_AI=0, PYTHONUTF8=1 and core.longpaths=true for Windows Git subprocesses.
For full research-branch regression set:

```powershell
$env:GIT_CONFIG_COUNT='1'
$env:GIT_CONFIG_KEY_0='core.longpaths'
$env:GIT_CONFIG_VALUE_0='true'
$env:ALLOW_LIVE_AI='0'
$env:PYTHONUTF8='1'
$env:ALGOSIM_TEST_CANDIDATE=(Resolve-Path ../docs/evaluation/geometry/runs/geometry-library-expansion/BRANCH_CANDIDATE.json).Path
$env:ALGOSIM_TEST_DIVERGENCE=(Resolve-Path ../docs/evaluation/geometry/runs/geometry-library-expansion/candidate_divergence.json).Path
$env:ALGOSIM_FROZEN_AB_WORKTREE='D:/Documents/projects/algo-sim/.superpowers/worktrees/hybrid-ab-pilot-readiness'
& D:/Documents/projects/algo-sim/backend/.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider -o faulthandler_timeout=30
```

The plugin restores only the verified old provider payload surface for old runner
budget/mutation test modules, not current feature adapters. It does not disable hash,
budget, source or network guards. Without explicit identity, the default candidate
check correctly rejects this new branch versus the locked A/B source.
The explicit test candidate is read-only: --verify allowed, freezing with this selector rejected.
Use a native console on Windows: two background attempts stopped progressing (cause
UNKNOWN, terminated, no completed-count/readiness credit); the native-console final run passed.

Fake exporter: backend/scripts/verify_geometry_library_expansion.py --out NEW_DIRECTORY;
refuses overwrite. Frontend tests: geometry-library-expansion.test.ts, scene3d-chart.test.ts,
scene3d-annotations.test.ts. Visual harness: frontend/scripts/geometry-library-expansion-visual.html,
served by existing Vite locally; allow only its localhost origin. Browser and Vite sessions
created for verification have been closed; no unrelated services stopped.

## Preserved / next decision

Original checkout feat/text-to-geometry-functions/2990d87d and main28ac1d61 unchanged;
user favicon hash5cd57f27… unchanged;48 frozen artifact hashes match. No merge, push,
rebase, branch deletion or default/cache change. Locked A/B12da4768… remains untouched;
new branch8ff994c6… is separately declared. No historical rescoring or pooling.

Human review is next. Limits include bounded source grammar, first3 plane points must
be noncollinear, same-name plane-output legacy precondition, and missing section/line-object
composition/new base families. These are not silently promoted to general geometry support.
Expanded payloads exceed old accounted-token caps; SMOKE_AB/FULL_AB on this branch are
NO-GO, not authorized. LIVE GEMINI CALLS=0; MAIN/default unchanged.
Evidence hashes: diagnostics/artifact-manifest.json; corrected execution-attempt disclosure:
diagnostics/regression.json. No new source changes after verified815f06be.

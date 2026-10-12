# Question-local givens — LOCAL Windows, 2026-10-12

Phase 1 is complete: local main fast-forward `a6e27a78` → `22edf7ff`, documentation commit `232c1225`.
Its clean-worktree T3 passed (8675 backend / 1053 frontend), candidate `d1410731…` verified, and seven representative
Playwright scenes passed. Remote remains at `a6e27a78`; nothing pushed. See `../hybrid-main-integration/report.md`.

## Change and limits

Research branch `research/question-local-givens` starts at integrated main `232c1225`. Initial repair `06cd8cdf`,
review fixes `227e1bcf`, final product `e1f288ec`, separate final candidate commit `03095c28`, discovery-path correction `678f5b7b`.
Only product file changed: `backend/app/simulation/geometry_functions/registry.py`.

Both routes A/B now check givens in and after the request, including construction-only requests and planner auxiliary
paths. A short quote or an earlier clean ask cannot hide a later changed context. Source dimensions and readable shape
constraints must agree with the same canonical calls, including original facts omitted by the model. Exact direct
segment lengths and canonical regular-base sides are supported authorities. Compatible verified givens remain served;
the engine still constructs and verifies geometry. No assumptions are overwritten and no second semantic state exists.

Refusals: `QUESTION_LOCAL_GIVEN_CONFLICT`, `QUESTION_LOCAL_GIVEN_UNVERIFIED`, `QUESTION_CONTEXT_UNSUPPORTED`.
Scope changes, hypothetical replacement figures, unit conversion, arbitrary prose and shape predicates outside the
bounded matching vocabulary remain unsupported. This repair is measured source coverage, not a complete language
understanding or theorem-proving claim. Default `LLM_ONLY` does not gain this Hybrid gate.

## RED → GREEN and review

- Clean baseline `232c1225` replay of the exact committed 62-test file: 34 failures / 28 passed. Receipt records source
  hash and failed test names, without raw traceback. The earlier 42-test development snapshot was 22 failures / 20 passed;
  an even earlier wrong helper signature was corrected before product changes and is not semantic RED evidence.
- Fresh independent LOCAL reviewer at `06cd8cdf`: 3 Critical + 1 Important; 19 failing probes / 4 positive controls.
  Executor reproduced and fixed all four in one pass: 23 passed. Full connected cluster: 861 passed / 4 xfailed.
  `review.md` records findings, rulings and scope. One review completed; the first agent hit a usage limit before review.
  No second independent review is claimed.
- Positive/negative route controls, label/number/scale metamorphic checks and existing mutation checks are retained.
  Benchmark fixtures, labels and oracle unchanged; only new refusal-code taxonomy entries and an existing mutant's
  exact source anchor changed.

## Final independent verification

Candidate frozen from clean detached product `e1f288ec`, verified at clean detached commit `678f5b7b`:
`d4bc2b04689d87ac4510a7cfe6471efd578f8d9ba641baeafd8ab44326032bc9`, 110 files.
`inputs/candidate_divergence.json` extends the existing declaration chain through this run's first declaration.
The first candidate `778bc329…` and failed gate receipt remain retained. Historical candidate `d1410731…`, thesis
`d72db7c3…` and locked A/B `12da4768…` retain their bytes, identity and original interpretation; no pooled/rescored results.

- Candidate verification PASS; candidate identity/provider pin suites: 27 passed.
- Fresh benchmark 30 cases, each arm: 19 correct served / 9 correct refusals / 0 false serves / 2 known false refusals
  (B27/B28). Metrics SHA256 `febb5b602fcb194c502e07ea47fe4200ed4083f0b09bac12784b2536940ab12e`, byte-identical
  to Phase 1 and the historical after metrics. No benchmark relabeling.
- Clean detached T3 at `678f5b7b`: **FULL_PRODUCT_GATE_PASS**, exit 0; backend 8760 passed / 0 failed /
  1 skipped / 2 deselected / 5 xfailed; frontend 1053 passed (68 files); typecheck/build PASS; demo 5/5,
  reduced-chain 1/1; crash-surface 6/6, no escaped exception. Total 328.7 seconds.
  `verification/t3.log` SHA256 `d732b7347307271c137dbe5dee28c3acb132f015181858492bc9ca4c8029206b`.

First T3 at `261d8eec`: backend 8758 passed / 2 failed, frontend/build/demo/crash passed, FULL_PRODUCT_GATE_FAIL.
One failure was a changed refusal code on an explicit unsupported plan (still safely refused); a three-line fix keeps
the engine's unconditional OUT_OF_SCOPE. The other was a missing mandatory historical-effect field in the divergence
receipt. An additive correction supplies the field, retaining prior bytes. A short rerun was interrupted after its
focused precheck found the correction filename outside the existing discovery layout; moved byte-identically to
`inputs/candidate_divergence.json`. Focused clean regression after both fixes: 83 passed / 1 xfailed.

Provider A `912b22ef…`, B `396f1c9c…`, declarations `f2ec9698…` remain pinned. Schema, M4, CACHE_VERSION 125,
default mode and renderer unchanged. LIVE Gemini requests = 0. No extra Phase 2 screenshots needed.

## Integration and next slice

Recommendation: **GO for bounded offline local integration**, after the user's integration decision.
Branch remains separate; no Phase 2 merge or any push executed.
No live-model/default-mode GO. DSL HOLD, B27/B28, orbit P1 and other open issues retain their status.

Proposed bounded vertical slice after integration: for one convex pyramid/prism, construct a plane through a named
verified point parallel to an existing plane, then automatically construct its section. A perpendicular plane requires
another verified direction/line constraint to make it unique; a point and perpendicularity alone are insufficient.
Reuse existing planner/calls/compiler/engine dependencies; unsupported or non-unique constructions fail closed.
Acceptance should measure plane membership/normal, dependency order, exact section topology/area and one Scene3D
construction replay. This is a proposal, not implementation or a general search/schema extension.

## Housekeeping

Cleanup complete (`cleanup.json`). Registered worktrees: 3 before, 4 after; the additional research checkout has an
active consumer (the unmerged result). Three new expired verification worktrees removed; both node_modules junctions
detached with targets intact. New Phase 1/2 scratch and its test databases/browser files removed; no task process remains.
Released **3,564,113,243 bytes** (3.56 GB decimal): Phase 1 verification 1,704,684,873; RED replay 12,235,241;
Phase 2 verification 1,705,871,997; Phase 1 scratch 49,645,644; Phase 2 scratch 91,675,488.
Git deregistered the clean worktrees but could not delete all cache files; exact leftover directories were removed
under the creating sandbox account with native PowerShell. No Git force flags or ACL changes.
Existing protected worktrees/branches, old scratch/databases, CodexSandboxOffline
geometry-library-expansion and the user's untracked favicon remain untouched. The research checkout is retained as
the consumer of the unmerged result. Phase 1 verification worktree released 1,704,684,873 bytes; sparse RED replay
worktree released 12,235,241 bytes. Evidence retained in this run; final docs audit PASS, docs/identity tests 51 passed / 1 deselected.

Skills used: Superpowers planning/execution/debugging/TDD/review/worktree/verification, Karpathy and Ponytail;
native Windows ledger adaptation. Graphify was assessed and not needed; no formal extra skill workflow or Claude Cloud.
Security incident in Phase 1: an overbroad process diagnostic printed a connector key in tool output; no key was
written to files or Git. Rotation was recommended. Later process checks only inspect task-owned paths and emit IDs.

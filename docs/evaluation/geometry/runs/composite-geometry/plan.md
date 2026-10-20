# Composite geometry implementation plan

**Goal:** Wave 2C local research: exact derived pyramids and shared-face compositions, with no new provider contract.
**Authorization:** GO_HYBRID_WAVE2C_LOCAL_RESEARCH. Stop at GO MAIN. User specification P0–P9 is the governing spec.
**Architecture:** Reuse Registry functions, bounded dependency planner, one exact affine Gram chart, kernel/IR and Scene3D. Extend the existing pyramid function to bases made of already determined points. No general multiple-chart solver, learned planning, Adapter /3 or live calls.
**Tech stack:** Existing Python/Fraction/Pydantic/kernel/Scene3D; no dependencies.

## Preflight

- main, origin/main, remote main: 78bd68764a69c513086b844ab3ed5e29ae18ce04.
- Only branch: research/hybrid-wave2c-composite-geometry; implement in the existing checkout, no permanent worktree.
- No tracked changes initially. Preserve untracked receipts and frontend/public/favicon.svg byte-for-byte.
- CORE: educational composite solid geometry. SUPPORTING: corpus, independent oracle, review and evidence.
- Reuse candidates: pyramid/ask_volume/section/ask_section_area, midpoint/divide_segment/intersect_line_plane, _sap_xep_phu_thuoc_loi_goi, _Dung, construct_pyramid, formation and Scene3D.
- Existing limit: thu_khoi rejects all unequal bases; bo_cuc_day chooses first sorted solid. Planner already orders declared derived solids.
- Expected changes: geometry_functions/engine.py; planner only if an actual dependency defect is demonstrated; targeted test, corpus/oracle/measurement script; CODE_INDEX/EVIDENCE_INDEX/current handoff; candidate receipt.
- Duplicate check: searched pyramid/solid/section/volume constructors and callers; extend existing authority rather than add another solver.
- Risks: root selection affected by call/label order; premature auxiliary construction; degenerate or non-planar base; shared entity ownership; source coverage. Tests must pin each.
- Contract/cache: flat, TypedFact, provider declarations, Adapter /2 unchanged; cache127 because research Route D is isolated from cached /api/analyze.

## Capability matrix (baseline → intended scope)

| Capability | Baseline | Wave 2C scope |
|---|---|---|
| Parallel-base section at a named unique point | SUPPORTED | reuse |
| Named lateral-edge midpoint/rational ratio | SUPPORTED (ratio offline only) | reuse |
| Child pyramid on a determined parallel section | UNSUPPORTED | SUPPORT explicit named vertices |
| Shared-face sub-pyramids in one root chart | PARTIAL (same base only) | SUPPORT all vertices determined |
| Independently placed second root with different base | UNSUPPORTED | refuse; no guessed placement |
| Qualified duplicate vertex names | UNSUPPORTED | BLOCKED_BY_CONTRACT |
| Ratio-of-volumes / residual-solid quantity goals | UNSUPPORTED | BLOCKED_BY_CONTRACT; independent evaluation may verify identities |
| Unknown section vertices / unfixed cutting plane | UNSUPPORTED | refuse |
| Goal composition | PARTIAL | existing typed effect search + declared solid workflow; not learned planning |

## Task 1 — Derived pyramid geometry and ordering

- [ ] Write tests for S.MNP (parallel midpoint section) and two tetrahedra S.ABM/S.AMC sharing SAM; assert independent volume/area values.
- [ ] Run RED on baseline and preserve stdout/stderr/exit status.
- [ ] Extend _Dung root-base selection: select an unconstructed root base, keep one chart; other solid vertices must resolve from verified constructions. Keep independent unequal roots refused.
- [ ] Validate all derived base points, coplanarity, nondegeneracy and apex incidence before arithmetic; reuse kernel topology checks.
- [ ] Emit each original solid before its own auxiliary vertices and derived solids; keep shared point IDs and solid-owned face/edge IDs.
- [ ] Run GREEN + tamper, missing/contradictory data, cyclic DAG, renamed labels, shuffled facts, multi-goal, non-convex/degenerate base and source spoofing tests.

## Task 2 — Development evaluation and compatibility

- [ ] Lock development corpus and independent mathematical oracle (explicit Euclidean coordinates / similarity and volume additivity, no product imports).
- [ ] Measure exact served, planner resolved, source gate, goal coverage, refusals, false serves, calls/depth/cost and scene validity separately on baseline and candidate.
- [ ] Preserve 174 rows, Adapter /2 41 fixtures, NLU GOLD/deltas, Wave1/2A/2B, SG-1..6, Follow-up A+B, known BH2A/SGH, Route A isolation.
- [ ] Commit product/tests/evaluation; freeze full candidate SHA in a separate commit. No historical evidence edits.

## Task 3 — Independent review and authoritative Full T3

- [ ] Fresh read-only reviewer of committed candidate (no implementation history); fix only reproducible blockers/regressions, RED first.
- [ ] Clean temporary detached worktree at final committed candidate; reuse installed runtimes without changing ACLs; Full T3 raw stdout/stderr plus status/counts/duration/commands/environment/tree hash.
- [ ] Verify candidate MATCH; validate every recorded commit with rev-parse and cat-file; preserve raw evidence and checksums.
- [ ] Write report/handoff/run.json and index; WAVE2C_READY_FOR_GO_MAIN_REVIEW only if all required gates pass, otherwise PARTIAL/BLOCKED with exact remaining work. No merge/push.

## Progress

- Baseline targeted compatibility: 381 passed (174-row test, 41-fixture tests, Wave1/2A/2B and source gates); source logs will be captured in subsequent reproducible verification.
- Plan decisions are within owner-authorized P1 slice selection. No additional approval gate introduced.

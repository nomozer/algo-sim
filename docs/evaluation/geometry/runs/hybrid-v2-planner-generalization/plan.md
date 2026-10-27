# Hybrid V2 Planner Generalization Implementation Plan

> **For agentic workers:** execute inline with `superpowers:executing-plans`; use a fresh whole-change reviewer. Steps use checkbox tracking.

**Goal:** compose a plane through a grounded point perpendicular to a vertex-to-vertex line of a prism, then construct/measure its section, reusing the existing derived plane across goals.

**Architecture:** extend `_mat_vuong_duong` in the existing Planner. Select anchors by solid topology, then reuse `orthogonal_projection_line`, `translate_point`, `section`, `ask_section_area`, derived-plane memoization and dependency ordering. Source Gate and exact Engine remain unchanged and authoritative.

**Tech Stack:** Python, pytest, exact Fraction oracle; existing TypeScript product gates.

**Spec:** Owner task supplied 2026-10-27; `docs/architecture/GEOMETRY_CAPABILITY_EXPANSION_CONTRACT.md` B; `TEXT_TO_GEOMETRY_FUNCTIONS_CONTRACT.md`; existing source/engine `MAT_VUONG_DUONG` certificate.

## Global constraints

- Exactly one local research wave from verified `main` `386d214952e6a7ba98f0931b5ecfd7a5b89d1667`.
- No live provider, merge, push, cleanup, default-route, schema, provider contract or new IR kind changes.
- Preserve old worktrees and historical evidence. New measurement artifacts live in this run; raw failing pytest output stays outside documentation.
- `DEFAULT_MODE=LLM_ONLY`, cache130, Hybrid opt-in; honest development-only claims.
- Missing/contradictory information and invalid geometry fail closed. Engine verifies all proposed anchors exactly.

## Preflight

Active branch: `research/hybrid-v2-planner-generalization`, new `.superpowers/worktrees/planner-generalization`.
HEAD/base: `386d214952e6a7ba98f0931b5ecfd7a5b89d1667`. Root Git status clean except unreadable ignored caches; old worktrees preserved, four dirty and two Git-clean.
Remote: safe fetch and `ls-remote` independently returned the same SHA. Baseline detached freeze MATCH (118 files, `fef0b050e42f6ee8629e76ddb44f6b3dc0191cf89f5df922d8a62be54ef71657`). Product paths match T3 `34ecce49`; inherited receipt PASS 12228 backend/1417 frontend, log hashes to be verified; no baseline Full T3 rerun.
Current milestone: opt-in Hybrid V2 registry/14, planner/15, engine/14. Classification CORE; directly serves thesis 3D geometry construction.
Related modules/reuse: `_mat_vuong_duong`, `derived_planes`, `_sap_xep_phu_thuoc_loi_goi`, `_bind_result_dependencies`, `kiem_nguon`, `_kiem_mat_vuong_duong`, bridge_v2, Adapter /4, section kernel and Scene3D. Duplicate search found the plane decomposition already exists; extend it only.
Expected product change: `backend/app/simulation/geometry_functions/planner.py` only, planner version increment. Tests: new `test_prism_perpendicular_section_planning.py`; development tools/oracle/results in this run. Living indexes and candidate identity updated when evidence exists.
Contract/cache/history impact: internal planner coverage only; no provider schema change, no Engine/Registry change; no-cache opt-in route supports NO_BUMP, verify fingerprints and default isolation. Historical reports untouched.
Risks: anchor degeneracy (exact Engine rejects); dependency cycle/dangling (existing validator); scope creep (only vertex endpoints, no arbitrary constructed reference lines or cuts with declared base-edge vertices).
Smallest implementation: same-layer endpoints choose third vertex of that layer plus opposite-layer vertex; cross-layer endpoints choose two other base vertices. Nondegenerate convex prism implies noncoplanar quadruple, hence independent projected directions; Engine independently verifies, no coordinates in Planner. Preserve pyramid selection unchanged.
Stop: any need to widen Source Gate/schema/Engine/IR, any wrong serve, or authoritative verification blocked.

## Review focus

- Same-layer and cross-layer lines, including reversed endpoint and point-label renaming.
- Derived through-point dependencies and shared section/area plane without duplicate constructions.
- Missing dimensions, conflicting facts, ungrounded operands, face/tangent cuts and nonunique relations.
- Cycle/dangling dependency rejection and preserved pyramid behavior.
- Exact oracle independent of Engine geometry helpers, adapter envelope validity and no false generalization claim.

## Task 1 — Audit, registration and baseline RED

- [x] Verify repository/remote/worktrees and detached freeze; read architecture and source/tests.
- [ ] Write capability-gap matrix for 18 registered groups, separating layer gaps and evidence limits.
- [ ] Register development cases and independent exact section oracle before product changes.
- [ ] Add real route tests proving missing prism compositions; run against unchanged product. Expected: intended positives refused at Planner `UNSUPPORTED_CAPABILITY`; existing pyramid cases served.
- [ ] Save sanitized baseline status/code/metrics/oracle identities; commit explicit task paths.

## Task 2 — One Planner slice

**Files:** modify `planner.py`; test `test_prism_perpendicular_section_planning.py`.
**Interface:** preserve `_mat_vuong_duong(f, q, k, phat, khoi, fn) -> dict`, existing auxiliary certificate and route contracts.

- [ ] Extend structural anchor choice without geometry calculations or new abstraction.
- [ ] Run new positives, negative corpus, metamorphic/order/reuse/dependency tests. Expected: exact oracle agreement, zero wrong serves.
- [ ] Run T0, T1 geometry/semantic and T2 wave; verify provider fingerprints, default route and historical regressions. Expected: appropriate tier PASS, no unauthorized route change.
- [ ] Commit minimal product/test/index changes with exact staging allowlist; independent read-only review and address substantive findings.

## Task 3 — Frozen candidate, Full T3 and handoff

- [ ] Create fresh candidate freeze and divergence record; preserve old candidate in run.
- [ ] Commit freeze, create clean detached candidate worktree, verify MATCH before/after Full T3.
- [ ] Run Full T3 with `ALLOW_LIVE_AI=0`; verify backend/frontend/build/demo/crash and machine receipts.
- [ ] Write report/handoff/run metadata with before/after metrics, limitation and next action. READY_FOR_OWNER_REVIEW only if all required gates pass.
- [ ] Keep branch/worktrees; no merge/push or second wave.

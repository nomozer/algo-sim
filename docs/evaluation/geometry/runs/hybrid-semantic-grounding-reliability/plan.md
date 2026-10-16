# Interrupted-work continuation — 2026-10-17

User request supplies the approved scope and execution sequence. Continue Claude's work; do not restart it.

## Preflight

- Active branch: `research/hybrid-semantic-grounding-reliability`.
- Entry HEAD: `2e08922a41675e6316f1429465c349273a60147e`; main/origin-main `1f635ed5`.
- Working tree: 5 modified tracked files, 0 staged, 3 untracked files (8 files copied with SHA-256 verification).
- Backup: outside repository, `C:/Users/Bunny/AppData/Local/Temp/algosim-claude-rescue-20261017-013835`; binary tracked/staged patches, file copies and hash manifest; no stash/reset.
- Current milestone: integrated Result Binding, Function Discovery, Generalized Goal Entry and Scene3D; offline semantic-grounding slice interrupted before full regression/T3.
- Task classification: CORE correctness, with SUPPORTING verification and evidence.
- Thesis relevance: right-or-refuse source certification and completeness of Vietnamese geometry requests.
- Existing modules/functions reused: `registry.kiem_nguon`, `_kiem_du_kien_cau_hoi`, `_kiem_result_binding`, `_cung_mat`, `_cum_hoi`, `PlanningContract`; `engine._Dung`, `_plane`; existing exact `Plane3`/`Vec3`, fact route, freeze and gate tooling.
- Source of truth: actual diff/tests plus committed preregistration/corpus/oracle; historical handoff is not new verification.
- Expected files: inherited 5 modified files + new reliability test; focused review regressions; this run package and living navigation docs; mutable current candidate manifest plus append-only divergence correction.
- Contract/cache/history impact: internal source admissibility only; no provider/schema/default/cache change; no rewriting history or frozen corpus/oracle/results.
- Duplicate implementation risk: reuse the shared plane comparison and source coverage; no second planner/kernel.
- Dependency-cycle risk: no new layer or reversed import direction.
- Scope-creep risk: broad language coverage and ACL cleanup are excluded; fix reproduced correctness failures only.
- Smallest sufficient implementation: preserve Claude's M1–M4, close independently reproduced source-plane mismatch, finish offline measurements/review/refreeze/T3.
- Explicitly excluded: live calls, provider prompts, G05/G16/G17, curves, API/default/renderer changes, protected `frontend/public/`, global ACL changes.
- Stop conditions: schema/provider contract change required, unresolved correctness failure, absent preservation, failed final acceptance, or human integration decision needed.
- Concurrency: one registered worktree at entry; no visible Claude process. Process command-line inspection denied by environment, so ownership of unrelated Node processes is UNKNOWN; none stopped.

## Execution ledger

1. Preservation: complete, 8/8 file hashes MATCH, patches also byte-verified.
2. Recovery: preregistration/corpus/oracle committed at entry HEAD; product implementation present in Registry/Engine; baseline JSON and tests present. No complete review/T3 receipt in this run.
3. First full geometry run: sequential command accepted (no `-n`), interrupted after early failures; first failure reproduced with `-x`: stale `CANDIDATE_VERIFY`, 98 passed. Normal refreeze required; no test assertion weakened.
4. Independent read-only review: dispatched; reproduced M2 wrong-plane acceptance when three shared labels are collinear. Add supplemental development regressions, preserve frozen labels.
5. Pending: focused baseline; supplemental RED/GREEN; final source corpus + historical replay; T1/T2; review delta; commit/refreeze; authoritative detached T3; candidate MATCH; single handoff; integration decision from user.

## Evidence boundaries

Corpus 58 = DEVELOPMENT_NOT_HELD_OUT. Independent wording 40 has committed authorship but extraction mapping is implementer's; never claim human held-out or live understanding. Do not inspect its outcomes for tuning. Final measurement runs only after product stabilizes; record any preregistration deviation. Exact oracle is independently implemented but same-agent semantic labels are not an independent human oracle. Missing live extraction = NOT_MEASURED. All frozen input/output bytes retained.

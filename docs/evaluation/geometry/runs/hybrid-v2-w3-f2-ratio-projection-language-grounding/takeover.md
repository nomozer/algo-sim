# Takeover checkpoint — W3-F2 blocked by safety gate

Date: 2026-10-29. Status: NOT_READY. Do not merge/push/cleanup or claim Full T3 readiness.

## Workspace and commits

Repo root main/origin/main/GitHub baseline: 996f114b3480efe1b0d075dd4342530aaa12ddae.
Research branch: research/hybrid-v2-w3-f2-ratio-projection-language-grounding.
Research worktree: .superpowers/worktrees/w3-f2-ratio-projection-language-grounding.
Preregistration/RED: 90f58c4c6de102d58d971e890347e59f4bdc7bda.
WIP product: e9d5a9d73064a15b7702eb32c008835bc99fba6d (Registry only, 45 added / 10 removed).
Final documentation commit contains this checkpoint; resolve the research branch to obtain its exact HEAD (emitted in session final response).

## Binding stop and unresolved work

Owner specification §15 says stop if a negative/tamper begins being served or any WRONG_SERVED appears. Both conditions were independently confirmed. Product edits stopped; do not silently continue beyond this stop without an Owner decision addressing the scope/provenance blocker.

- DEV-NEG-08: divide_segment premise solid_id=foreign, only s1 declared, served.
- DEV-NEG-23: orthogonal_projection premise solid_id=foreign, only s1 declared, served.
- PremiseSpec.solid_id exists in typed_fact_next.py:204. typed_fact_next_bridge.py::_check_qualified_refs skips _id fields; ratio/projection translations around300/305 omit scope. Adapter /3 already rejects unknown scopes around417. Scope must be checked before erasure. Also cover incompatible refs to a different *declared* solid.
- DEV-NEG-20: off-plane foot returns UNDERDETERMINED_POINT rather than the locked intended incidence/contradiction refusal. Do not broaden locked codes to hide it; isolate the intended check in an append-only supplementary case or correct at the responsible layer after scope review.
- W3-A06: independent pre-existing RadicalDomainError after canonical wording; preserve as a known masked limit. Smaller DEV-ISOLATED-A06 validates the F2 relation. Do not touch radical.py/kernel in this wave.
- W3-F1 semantic tests22 pass; version pin still expects /20. Compatibility/exporter/cache decisions remain unfinished after the mandatory stop.

## Preserved work and verification

96 registered cases, exact oracle and expectations were committed before product edits. Product tests:94 pass/3 fail. Independent F2+F1:116 pass/4 fail. Official after-change receipt records 2 wrong-served. Historical evidence and preregistration hashes MATCH. Code/defaults remain LLM_ONLY/cache130/Hybrid opt-in/live0. Old frozen candidate b02b2c42 and its T3 receipt do not apply to WIP e9d5a9d7; no replacement candidate exists.

T2, Full T3 and full Wave 3 replay were intentionally NOT_RUN. All future replay output must go to this run or a new authorized run and be labelled POST_FEEDBACK_DEVELOPMENT_REGRESSION; never overwrite original scored-run-1.

## Resume commands after Owner decision

Use root backend/.venv/Scripts/python.exe from this worktree; no dependency install was needed. Run targeted pytest on backend/tests/geometry/test_ratio_projection_language.py and test_w3_f1_cross_sentence_plane_grounding.py. Existing failed green-after.json/tamper-results.json and all preregistered evidence are immutable; write a new named attempt/supplementary receipt, not over them. The evaluator refuses existing output files. Plan, baseline audit, architecture decision and independent review are all in this run.

Next authorized sequence would be: resolve scoped provenance/negative witness; verify semantic mutations; finish version/cache/fixtures; append correction/development receipts; run T0/T1/T2; freeze a new candidate with divergence declaration; clean detached Full T3; independent review; final owner handoff. No W3-F3/F4/F5, planner/kernel/adapter bypass or production migration.

Do not touch previous integration backups, ACL-locked directories or unrelated worktrees. No cleanup is authorized in this wave.

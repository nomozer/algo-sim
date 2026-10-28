# Handoff — Source Gate language generalization

**NOT_READY_ACCEPTANCE_GATE_FAILED.** Independent final review: one open MAJOR, ACCEPTANCE-1.
W2-M1/M2/M3 are implemented in Registry19; only registry.py changed in product.

Baseline: d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c.
Preregistration:6554d733203619dad9ea8c4c640fc80ee5782a34.
Product:c6f6b64bda6473c175a32a7875a9dd9831ae7c6d.
T3 candidate:b9e3d0966e14acb1d44f2f9c7cd7a3bf49ac54a9.
Freeze:8baf3205006d097efdd21087b9d52e85625fa1263e9125b418cf658ccac18d25 (118 files,MATCH after T3).
Final branch HEAD is the final documentation commit carrying this handoff; resolve
`research/hybrid-v2-wave2-source-gate-language-generalization`. Its exact SHA is emitted in the session final response.

New development:6/24 ->23/24 original positives correct; DEV-1-3 remains a false refusal at the excluded
W2-M4 radical ceiling. All36 genuinely adversarial cases refuse. One initially labeled negative is a valid
redundant assertion and is independently adjudicated; original input/RED/GREEN bytes remain unchanged.
Actual wrong-served0; exact agreement24/24 among served rows including that corrected valid case.
Supplemental7/7 and11 ratio controls pass.

Wave2 **POST_FEEDBACK_DEVELOPMENT_REGRESSION**:45/48 correct positives,3 false refusals,
48/48 negatives refused,36/48 correct reason categories,12 mismatches,0 wrong-served,exact oracle45/45.
Category B36/36; Category A9/12. Remaining W2-A04 (W2-M4) and W2-A07/A10 (W2-M5).
This is never an independent holdout PASS; original historical primary results are preserved.

Full T3 **FAIL**:12549 backend passed,1 failed (DEV-1-3),1 skipped,2 deselected,15 xfailed.
Frontend83 files/1417 tests PASS; build PASS; demo5/5 PASS (reduced chain1/1); crash6/6 PASS.
Clean detached source before/after; freeze MATCH. Receipt and hashed log in verification/full-t3/.
Final independent review is review.md; machine checks in results/independent-final-checks.json.
See report.md, verification/tiers.json and results/development-adjudication.json for separate raw/adjudicated denominators.

Continue only through a separate Owner scope/acceptance decision for the open MAJOR.
Do not skip the failed test, change its locked expectation, increase MAX_RADICAND or fix Adapter ir_name under this GO.
No live providers, default switch, merge,push or cleanup performed; all original worktrees retained.
Cache130/LLM_ONLY/Hybrid opt-in/Planner17/Engine14/Adapter4/certificate1 unchanged.
Reproduction needs preserved Wave2 Git commit ecdc26b012c8ce80d53524a98dc75cdcb020079d (fetch it for shallow clones).

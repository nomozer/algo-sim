# Final sphere visual polish

Status: `OWNER_VISUAL_APPROVAL_PENDING`  
Candidate product commit: `e047235eeb46d4151f22f214a353ee9838b0e81c` (parent `d1ee4f0dc4d5a377512a8fcfc810bdc6f3348202`)  
Owner scope: sphere rendering and related presentation checks only.

## Change

The sphere silhouette now uses 0.65× the ordinary edge width in the existing screen-space visibility pass. The reference equator ribbon is 0.27× its former radius basis; its visible arc shifts 25% toward the existing edge color. The hidden arc retains the existing hidden-edge color and opacity. Tangent geometry, camera visibility classification, real sphere-plane intersection, names, labels, other shapes, UI, backend, Hybrid, and cache are unchanged.

The real section rim remains the highest-contrast curve. No auxiliary circle was added. Orbit captures retain front/back visibility changes.

## Verification

- Targeted presentation suite: 5 files, 106 tests passed. It covers curved transitions, unified materials, visual closure, final quality, and hidden-line behavior.
- Exact sphere-plane product-path oracle: 5/5 cases matched. Above-centre, through-centre, and tilted planes returned the exact circle; tangent and no-cut cases refused without serving a fake circle.
- Browser capture: 260 screenshots across 1440×900 DPR1 and 390×844 DPR2; four scene envelopes, seven named camera positions, 24 orbit steps, and selected/deselected sections. The harness recorded zero provider calls. Its six “Hình phụ” messages are expected because the three section scenes contain no auxiliary geometry or toggle.
- Original first-hit silhouette scan, including its luminance and `R±6 px` thresholds, was run unchanged on the basic scene’s 24 orbit frames at each viewport. It flagged 18 desktop rays and 57 mobile rays. A separate diagnostic kept the same luminance and radial band and sampled parallel rays at 1–8 physical pixels of tangent offset: all 18 desktop and 57 mobile flags found a dark pixel at a 1-pixel offset. This is consistent with raster/sample placement at the curved limb; it does not prove continuous geometric or pixel-level closure. The primary scan results and unresolved interpretation remain reported as measured.
- Before/after images are linked in `OWNER_VISUAL_REVIEW.html`. Original baseline evidence remains untouched.
- Authoritative Full T3 on detached frozen candidate `46300f084c0c3f093a67ad820090289394271529`: `FULL_PRODUCT_GATE_FAIL`. Backend pytest reported 11,993 passed, 2 failed, 1 skipped, 2 deselected, 15 xfailed. Frontend Vitest passed 83 files / 1,417 tests; typecheck/build and both demo gates passed. Freeze verification passed and the source tree was clean after the run. See `full-t3/receipt.json`.
- The two failures are `test_watchdog_is_incomplete_runtime_failure_not_geometry_refusal` and `test_windows_watchdog_terminates_the_invocation_child_tree` in `test_schema_contract_offline.py`. In both cases the Windows watchdog timed out while spawning a sleep process and raised `WATCHDOG_TERMINATION_FAILED` while attempting process-tree termination. This gate result is recorded as FAIL; no Full T3 rerun was made.
- The external runner wrote its receipt before its final console print hit a Windows `cp1252` Unicode encoding error. The receipt contains the gate exit code, summaries, freeze result, detached commit identity, clean source-tree result, and log hashes. This wrapper-print error did not change the Full T3 result.

## Review and gates

- Internal patch review: no findings; this was not an independent review.
- Independent review: `DEFERRED` (not a PASS).
- Historical Official Visual: 7/8, with the already known cross-section orange-fill F2 conflict. No visual oracle thresholds were changed.
- Default mode remains `LLM_ONLY`; cache version remains 130; provider calls: 0.
- Candidate and main have not been merged. No push or cleanup was performed.
- A merge is not currently eligible because Full T3 failed. Owner visual approval remains pending; it does not override the failed gate.

## Owner decision

`OWNER_VISUAL_APPROVAL_PENDING`. Review the six after-images and their before/after comparisons in `OWNER_VISUAL_REVIEW.html`. Wait for Owner GO or requested corrections before any local merge or follow-on work.

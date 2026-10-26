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
- Authoritative Full T3: pending receipt. It must run once on the frozen candidate before this report is finalized.

## Review and gates

- Internal patch review: no findings; this was not an independent review.
- Independent review: `DEFERRED` (not a PASS).
- Historical Official Visual: 7/8, with the already known cross-section orange-fill F2 conflict. No visual oracle thresholds were changed.
- Default mode remains `LLM_ONLY`; cache version remains 130; provider calls: 0.
- Candidate and main have not been merged. No push or cleanup was performed.

## Owner decision

`OWNER_VISUAL_APPROVAL_PENDING`. Review the six after-images and their before/after comparisons in `OWNER_VISUAL_REVIEW.html`. Wait for Owner GO or requested corrections before any local merge or follow-on work.

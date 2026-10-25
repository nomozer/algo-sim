# Owner handoff — final Scene3D acceptance

**SCENE3D_VISUAL_PARTIAL_WITH_GAPS — NO-GO MERGE. STOP AT OWNER GATE.**

Read [the decision report](report.md), [short image review](visual-review.md) and [review packet](independent-review-packet.md).

| Owner question | Answer |
|---|---|
| 1. Candidate/commit | Product `b8b3311b7f15dd8c13d0477f67cab765986f9c42`; freeze `c84e8620318a74de6e9b1e9c12893cffd4722758`; this continuation starts from handoff `16b46d38`. Final evaluation commit is the commit containing this run, not a new product candidate. |
| 2. Fixes and before/after | Evaluator fixes only: V1 false PASS on 20% missing hidden arc and partial label cover reproduced, then V2 regression GREEN; unknown source/malformed face cannot invent visibility; tiny other polygon3 included. No new renderer before/after claim. Earlier renderer pairs remain in the previous run. |
| 3. Remaining errors in Owner images | UNKNOWN: original Owner issue images were not attached to this request, so no exact image-to-issue census. Newly measured: one analytic ellipse-transition FAIL, 25 unobservable full-view certifications, 112 heuristic temporal label flags (not confirmed bug counts). |
| 4. F2 | Terracotta fill retained; cobalt selected boundary; existing teal hover; selection transition checked. Policy resolved by the request. Gate replacement is not approved. |
| 5. Official score | **7/8**, original unchanged candidate receipt. No new full official run; same-capture locked hue predicate is separately reported. |
| 6. Changed tests/thresholds/skips | Added 18 V2 Node regressions, retained 22 V1 tests. No official threshold/test/skip/oracle change, no product test rewrite. V2 adds stricter observability and local completeness. |
| 7. Visibility angles | Default, quarter, back, high, low via existing OrbitControls; vectors/matrices recorded. 9 motion scenes at desktop/mobile plus 3 selected-section scenes at 5 views/2 widths. Curved ID hook does not independently certify all arcs. |
| 8. Label/angle/motion gaps | Corrected name faults detected 18/18. Temporal continuity unresolved: 112 heuristic flags. Right-angle source ID and visible square checked for the distance case, not full operands/foot certification in every view. GPU observations mix hover/reset; isolated allocation-free orbit not newly certified. |
| 9. Certified versus UNCERTIFIABLE | V2 final baseline 4 PASS / 1 FAIL / 25 UNCERTIFIABLE; browser faults 10/10 on two certified circle high views. These are limited pixel claims, not backend mathematical proofs. |
| 10. T3/freeze | Existing Full T3 PASS reused because product is unchanged. Fresh detached freeze verify succeeds, worktree clean, old stdout/stderr hashes match. `provenance-verified.json`. |
| 11. Independent review | **INDEPENDENT_REVIEW_PENDING**. Fresh-context AI review was internal; findings/fixes disclosed in the packet. |
| 12. Owner visual approval | **HUMAN_VISUAL_APPROVED=PENDING**. |
| 13. Background/layout | No change. Report artifacts do not alter the website. |
| 14. Backend/Geometry Functions/Hybrid | No change; cache129, LLM_ONLY, Hybrid production OFF/NO-GO. |
| 15. Root tree/other assets | No writes to dirty root, other worktrees' source, branch/worktree deletion, ACLs, another account's cache/dist, or other agents' processes. Existing 3156 server reused; own Chrome sessions closed. |
| 16. Merge decision | **NO-GO**: official 7/8, V2 transition FAIL and unresolved completeness, temporal flags, independent/human approval pending. No merge or push. |
| 17. Next Hybrid work | H1/D-10 certificate presentation **delta audit and regression on Adapter /4**, reusing code already present, after Owner visual gate. Then independent holdout, family E2E, API/cache/rollback; live pilot needs separate GO. [Plan](hybrid-plan.md). |

## ĐÃ CHỨNG MINH (bounded machine statements)

Exact source/product identity and prior T3 stream hashes match (`provenance-verified.json`, hashes in `artifact-manifest.json`). Forty Node tests passed; 82 targeted existing product tests passed. Corrected name faults and second selection work in 18/18 offline rows. Ten browser F2 faults detected on certified baselines. These do not establish universal renderer correctness.

## ĐÃ KIỂM NHƯNG CHƯA CHỨNG NHẬN

Remaining V2 transition FAIL, 25 masked/insufficient baseline views, temporal label flags, mixed GPU creation measurements, all-angle perpendicular marks. The first motion attempt's label fault was invalid and was corrected in a separate run; its old PASS values are not full acceptance.

## CHƯA KIỂM

Physical mobile devices, a new live NL→Scene3D run, every original Owner image, all possible camera positions, repeated isolated orbit GPU/CPU attribution, independent exact geometry expectations for every curved family.

## ĐANG CHỜ OWNER

Review of the selected images, reviewer appointment, treatment of the official F2 gate, decision on the unresolved transition/temporal gaps. No replacement-gate adoption is recommended while V2 has these gaps.

## KHÔNG THUỘC PHẠM VI

Website redesign, backend/Geometry Functions changes, Hybrid H1–H4 implementation, production enablement, live provider calls, main merge, remote push, old-worktree/evidence cleanup.

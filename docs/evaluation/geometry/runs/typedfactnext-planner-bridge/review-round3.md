# Independent review — round 3

Reviewer: the same read-only agent, on the round-2 fixes. Verdict: no BLOCKER; 1 IMPORTANT; MINOR notes. Verified sound:
conditional / reported / judged / question wordings around the derived pyramid are refused (`UNSUPPORTED_CAPABILITY`,
`QUESTION_CONTEXT_UNSUPPORTED`, `NEGATED_CLAUSE`); the "(MHH1)" → "(α)" replacement cannot corrupt other text (the
notation contains planner-fresh labels that never collide with source labels; it runs only in certificate plans); the
section / edge rewrite touches only leaking events; no fresh label or planner plane name remains in roles, event or
step text beyond the disclosed pre-existing `mp_td_td` fields.

| finding | disposition |
|---|---|
| IMPORTANT — a negation governing a list reaches the derived pyramid through an empty lead-in: "Dựng thiết diện … bởi (α), không dựng mặt đáy và khối chóp đỉnh S cắt bởi (α)." (also "Chỉ dựng …, không dựng mặt đáy, đường cao và khối chóp …") SERVED | the reviewer's fail-closed option: besides the closed lead-in, ANY negation / exclusion word (`_LOAI_TRU_YEU_CAU`: không, chẳng, chưa, đừng, khỏi, miễn, bỏ qua, thay vì, thay cho, (ngoại) trừ) in the whole sentence that requests the derived pyramid ⇒ `NEGATED_CLAUSE`. Regressions: both repros refused |
| MINOR — the yes/no question "… và khối chóp đỉnh S cắt bởi (α) hay không?" was served (the sentence tail after the phrase was never read) | covered by the same sentence scan (the tail is part of the sentence); regression added |
| MINOR — common ratio wordings falsely refused by the round-2 allow-list | the "tính / tìm / xác định" opener is now optional: "Tỉ số thể tích của hai khối chóp S.MNP và S.ABC bằng bao nhiêu?" SERVED with 1/8 (regression). Still refused, fail-closed, recorded in `SOURCE_GATE_INTEGRATION_REPORT.md` §4: "Tính tỉ số giữa thể tích khối chóp S.MNP và thể tích khối chóp S.ABC.", "Gọi V1, V2 lần lượt là thể tích … Tính V1/V2." |
| MINOR — disclosed pre-existing leaks (`mp_td_td` notation / reference "(MHH1)", its role and explanation, H / H1) | unchanged, reported (route B behaviour on a plan without the certificate) |

Fault injection (scratch plugin): a sentence scan that never matches ⇒ the 3 new refusals fail (served).

Verification: `test_typedfactnext_planner_bridge.py` 54 passed; evaluation re-generated (aggregates unchanged:
40/49, 34/34 exact, 0 wrong-served, 11/11 refusals, 40/40 scenes, 0 leaks, 0 planner plane names); recorded focused
suite `verification/focused-pytest-post-review3/`: 1902 passed, 1 xfailed, 1 failed — the measured-tree drift check,
expected until the re-freeze.

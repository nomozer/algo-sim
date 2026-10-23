# Independent review — round 2

Reviewer: the same read-only agent as round 1, on the round-1 fixes. Verdict: no BLOCKER; 2 IMPORTANT; MINOR notes.

| finding | disposition |
|---|---|
| IMPORTANT 1 — contrastive wording before the derived pyramid ("… bởi (α) **thay vì** khối chóp đỉnh S cắt bởi (α)") was SERVED: the round-1 negation blacklist (`_PHU_DINH_YEU_CAU`) cannot be complete | blacklist replaced by a CLOSED allow-list of positive lead-ins (`registry._MO_KHOI_TREN_THIET_DIEN`): nothing after "và" / "rồi" / ",", a request verb ("(hãy) dựng / vẽ / xác định / xét (thêm / tiếp / cả / luôn)"), or the ratio / residual question openers; anything else ⇒ `NEGATED_CLAUSE`. "còn" dropped as a clause separator (it occurs in "phần còn lại"). Regressions: "thay vì", "thay cho", "trừ", "ngoại trừ" refused; controls "và dựng thêm", "rồi xác định", "và vẽ", "và hãy dựng" served. Known false refusal, fail-closed by design: "không quên dựng" (a positive request outside the closed set) |
| IMPORTANT 2 — learner text kept the planner's point-built plane name: per-cut steps "Dựng mặt phẳng qua M, H, H1." (ANON ×2) and "Dựng N: giao điểm của SB và (MHH1)." / role "Giao điểm của SB và (MHH1)" (NAMED) | `function_route._an_dinh_thiet_dien_phu`: each cut's operand-plane step now reads "Xét mặt phẳng (α) để tìm giao điểm với SB." (no second construction claim; frame ↔ trace indexing unchanged); in plans carrying the certificate, the planner token ("(MHH1)") is replaced by the source name in roles, event and step text. The section/edge rewrite now touches only events that leak a fresh label, so per-face steps stay informative. Regression parametrised over NAMED / ANON; new eval metric `planner_plane_name_in_text` = 0 over 40 served scenes |
| MINOR — `kiem_dinh_cat` docstring still said 0 < t ≤ 1 for every solid | docstring states the lateral-edge check and both orientations (pyramid 0 < t ≤ 1, prism 0 ≤ t ≤ 1) |
| MINOR — the global cut-clause rule covers only the `_CAT_CANH_CHUNG` shape; prisms with Unicode primes are refused earlier | scope limit recorded in `SOURCE_GATE_INTEGRATION_REPORT.md` §4; behaviour unchanged (fail-closed) |

Not changed (pre-existing route B, reported in round 1): the section plane object keeps notation "(MHH1)" and role "Mặt phẳng qua M, H, H1"; H / H1 are visible; edge explanations show chart coordinates.

Fault injections (scratch plugin, not committed): an allow-list that accepts anything ⇒ the 5 lead-in refusals fail (served); turning the presentation pass off ⇒ both plane-name regressions fail with "(MHH1)" / "Dựng mặt phẳng qua M, H, H1." in the text.

Verification: `test_typedfactnext_planner_bridge.py` 50 passed; evaluation re-generated (aggregates unchanged; `planner_plane_name_in_text` 0); recorded focused suite `verification/focused-pytest-post-review2/`: 1898 passed, 1 xfailed, 1 failed — the measured-tree drift check, expected until the re-freeze.

The allow-list changes gate behaviour ⇒ round 3 is required before freeze.

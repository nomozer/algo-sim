# Independent review — round 1

Reviewer: separate read-only agent (no edits, no subagents, no live AI). Scope: the full uncommitted change set on
`research/hybrid-backend-integration-session1` over `main` 43247c9e, the run documents and receipts.

Verdict: 1 BLOCKER, 3 IMPORTANT, 3 MINOR. Verified as sound: one planner / gate / engine (the bridge only translates);
no case-ID or label hardcoding; frozen provider surfaces byte-identical (`SkipJsonSchema` does not leak; provider guard
on the only provider path); production `/api/analyze`, `pipeline.py`, `main.py`, `CACHE_VERSION` untouched; no frontend,
`typed_fact_next.py` or `adapter3_simulation.py` diff; the presentation scrub does not over-match source labels.

| finding | disposition |
|---|---|
| BLOCKER 1 — a request sentence could restate the cut with other edges / names ("… bởi (α) cắt BC, CA lần lượt tại N, P") and the route served: the coverage pass credited any cut-clause shape | fixed: every cut clause in the source must fullmatch a declared cut (`registry._kiem_phu`); 3 parametrised regressions + consistency control; fault injection reproduces the blocker when only this check is disabled |
| IMPORTANT 2 — a negated derived-pyramid request ("nhưng không dựng / đừng dựng / bỏ qua / không xét …") built the solid; the shared negation lexicon lacks request verbs | fixed locally in the derived-pyramid binding (`_PHU_DINH_YEU_CAU`); 4 regressions; the lexicon gap for other request objects is pre-existing and reported |
| IMPORTANT 3 — evaluation overclaimed "composition / not a fixed chain"; leak metric scoped to `I…` only; H/H1 visible; each cut added a visible duplicate plane | report rewritten as a bounded cost-ranked case analysis with selection counts; `reuse_intersection` now unit-tested; duplicate operand planes marked `non_visual` (measured 0); H/H1 shown to be pre-existing route B behaviour on a plan without the certificate (reported, not changed) |
| IMPORTANT 4 — the teaching-expansion fallback ran for ANY validation failure and for every route B plan | restricted to a budget cause AND plans carrying a `DINH_CAT_CANH` certificate; regression shows a plan without it still refuses as on `main` |
| MINOR — gate did not re-check that a fresh cut lies on a stated edge | added (`_kiem_dinh_cat`) |
| MINOR — `kiem_dinh_cat` t range asymmetric for prisms; the parallel branch untested | engine now checks the edge IS a lateral edge, orients it (apex / base end), pyramid 0 < t ≤ 1, prism 0 ≤ t ≤ 1; engine-level fault-injection tests for an off-edge vertex and an edge lying in the plane |
| MINOR — measured-tree drift test fails until the candidate is re-frozen | expected; the freeze is its own commit (G5) |

Round 2 is required on the changed code before freeze.

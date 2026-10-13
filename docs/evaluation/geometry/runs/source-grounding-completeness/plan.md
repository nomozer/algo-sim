# Plan — source grounding completeness (LOCAL, 2026-10-13)

Branch `research/source-grounding-completeness` from `main` = `origin/main` = `7767c7e1`. No merge, no push.

- [x] Root-cause audit: `registry._kiem_du_kien_cau_hoi` read only from the first request on; a premise sentence
      before it was never read unless a call quoted it ⇒ "Cho … SA = 3. Đổi SA thành 5. Tính SC." served √17 on routes
      A and B (asks, construction-only, auxiliary, derived-plane requests alike).
- [x] Bounded obligation, one authority: `_kiem_vung_tien_de` inside `_kiem_du_kien_cau_hoi`; new code
      `SOURCE_PREMISE_UNREAD`; closed connector / note / scaffolding vocabularies; numbers bound once to the quote of a
      call carrying that value; object names and role nouns verified against validated calls; route-B goal / negated
      quotes passed as read quotes only where the gate itself reads a goal or a negation. No parser, no second state.
- [x] RED at `7767c7e1` → GREEN; positive controls; metamorphic (relabelling, route A/B); fault injection.
- [x] Independent LOCAL reviews (interrupted → partial probes, BLOCKING ×2, final verification); Critical/Important
      closed RED → GREEN or declared as bounded limits.
- [x] Full backend suite; candidate refreeze in a clean detached worktree (separate commit) + divergence layer.
- [x] Provider pins, benchmark 30 cases (method and labels unchanged), T3 in a clean detached worktree.
- [x] Docs audit + run report; cleanup without force. No merge/push.

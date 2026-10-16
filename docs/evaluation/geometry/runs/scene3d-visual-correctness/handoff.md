# Handoff — scene3d-visual-correctness

- Branch `integration/scene3d-visual-correctness` from `main` = `origin/main` = `6d8ead99`; Gemini `0ef0a20a` merged
  (`a7388a40`), fixes `08021881`, `f07ea069`, `e460cfac`, refreeze `8f437980`. Details: [`report.md`](report.md).
- Next action: `SCENE3D_VISUAL_CORRECTNESS_INTEGRATION_DECISION` — the user's GO/NO-GO for fast-forwarding `main`.
- Not done here: human visual review (`HUMAN_VISUAL_REVIEW_PENDING`), Hybrid enablement (NO-GO), live extraction
  (0 calls), general polyhedron ∩ plane display region, curved occluders for non-canonical lines.
- Kept on purpose: `frontend/public/` (user data, untracked); out-of-scope branches.
- Environment residuals: two unregistered `.superpowers/worktrees/goal-*` copies and one `backend/.tmp/pytest-*`
  directory with Codex sandbox ACLs — owner-run removal in `report.md`.

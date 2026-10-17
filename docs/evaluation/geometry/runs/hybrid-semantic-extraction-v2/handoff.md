# Handoff — hybrid-semantic-extraction-v2

State: research branch `research/hybrid-semantic-extraction-v2` (worktree `.superpowers/worktrees/hybrid-semantic-extraction-v2`),
committed and clean; not merged, not pushed. `main` = `origin/main` = `bc0445ae` at the start.

**Single next action: owner decision GO PILOT** ([`approval-request.md`](approval-request.md); 24 requests, caps USD
0.50/arm). Without it the prompt effect stays NOT_MEASURED. LOCKED (48 heldout requests) is a second, later GO.

Integration (separate owner GO): fast-forward `main` only after re-checking that `main` did not move (Gemini's frontend
work runs in `scene3d-educational-finalization`); if it moved, rebase is forbidden — merge, rerun the docs gate, backend
suite and T3. At integration also update the live-state pointers this branch deliberately left alone:
`CURRENT_STATE.md` (top section), `ROADMAP.md` §0, `AI_CONTEXT_BUNDLE.md` (at its 300-line limit — replace, do not append).

Open after this wave: Source Grounding wordings (`… thì … bằng mấy`, `Tính cos²`, repeated `tính`, `rồi suy ra`,
projection naming, `ba kích thước`); capability gaps that dominate the GOLD ceiling (unnamed centroid, line–line angle,
missing dimensions, conditional premises); human validation of labels.

Next research proposal (not started here): **Hybrid — generalized geometry function composition & capability expansion**,
on its own branch, targeting the GOLD-route refusal codes in `results/offline/` rather than the prompt.

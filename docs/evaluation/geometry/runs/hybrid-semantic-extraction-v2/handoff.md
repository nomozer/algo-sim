# Handoff — hybrid-semantic-extraction-v2

State: research branch `research/hybrid-semantic-extraction-v2` (worktree `.superpowers/worktrees/hybrid-semantic-extraction-v2`),
committed and clean; not merged, not pushed. `main` = `origin/main` = `bc0445ae` at the start.

Paired dev pilot DONE (24 requests, est. USD 0.123; [`results/live-pilot-analysis.md`](results/live-pilot-analysis.md)):
v2 does not fix operand placement. **Closed by owner disposition ([`disposition.md`](disposition.md)): held-out NO-GO,
prompt v2 NO-GO, selective safety integration GO, v3 offline GO.** Earlier text: recommended NOT to run the 48 held-out
requests for this prompt; instead approve a separate provider-contract (schema) wave, tuned on dev, then one paired
held-out run. Integration of this branch (scorer, grounding fixes incl. the oblique-box safety fix, prompt v2) is a
separate GO; prompt v2 is cheaper and never worse on safety, but its extraction gain is small.

Integration (separate owner GO): fast-forward `main` only after re-checking that `main` did not move (Gemini's frontend
work runs in `scene3d-educational-finalization`); if it moved, rebase is forbidden — merge, rerun the docs gate, backend
suite and T3. At integration also update the live-state pointers this branch deliberately left alone:
`CURRENT_STATE.md` (top section), `ROADMAP.md` §0, `AI_CONTEXT_BUNDLE.md` (at its 300-line limit — replace, do not append).

Open after this wave: Source Grounding wordings (`… thì … bằng mấy`, `Tính cos²`, repeated `tính`, `rồi suy ra`,
projection naming, `ba kích thước`); capability gaps that dominate the GOLD ceiling (unnamed centroid, line–line angle,
missing dimensions, conditional premises); human validation of labels.

Next research proposal (not started here): **Hybrid — generalized geometry function composition & capability expansion**,
on its own branch, targeting the GOLD-route refusal codes in `results/offline/` rather than the prompt.

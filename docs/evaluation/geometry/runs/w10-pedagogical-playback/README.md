# Run `20260928-w10-pedagogical-playback`

Task `HUMAN_VISUAL_REVIEW_AND_PEDAGOGICAL_PLAYBACK_CLOSURE` — answers the human
review of run `20260928-w09-verify-cleanup` (`FAIL_REQUIRES_PEDAGOGICAL_VISUAL_REPAIR`).
Automation only: nothing here is a human approval, and nothing here is `MERGE_READY`.

Start with `HANDOFF.md` (what a reviewer should look at), then `REPORT.md`.

| Path | What it is |
|---|---|
| `RUN.json` | identity: commits, candidate, cache, policy flags |
| `MANIFEST.json` | every artifact with its producer and sha256 |
| `REPORT.md` | root causes, repairs, results, limitations |
| `HANDOFF.md` | reviewer checklist and the required handoff fields |
| `inputs/fixtures/` | twelve Tier-A fixtures regenerated at the frozen candidate (0 model calls) |
| `inputs/W09_HUMAN_VISUAL_REVIEW.json` | additive record of the w09 human verdict (w09 stays byte-identical) |
| `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json` | candidate divergence declared for this wave |
| `results/BROWSER_EVIDENCE.json` | authoritative browser suite (6 families × desktop/mobile, positive + negative) |
| `results/OCCLUSION_MEASUREMENT.json` | product ↔ independent oracle, frozen human sets under the declared camera change |
| `results/GOLDEN_REVIEW.json` | semantic diff behind the P1 golden-hash update |
| `results/VERIFICATION_SUMMARY.json` | every gate and its result |
| `images/contact-sheet.png` | MAIN sheet: per family, large desktop neutral · causal · rotated and mobile neutral |
| `images/contact-sheet-appendix-formation.png` | appendix: formation steps and learner playback filmstrips |
| `images/crops/` | hidden-edge crops holding both endpoints; `CROPS_INDEX.json` carries the metadata |
| `images/screenshots/` | full-resolution suite screenshots |
| `images/playback/` | learner-only playback runner: filmstrips, states and `PLAYBACK_EVIDENCE.json` |
| `diagnostics/` | every measurement attempt, including failed ones, and gate logs |

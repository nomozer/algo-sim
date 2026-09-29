# Run `w11-pedagogical-polish`

Task `W11_PEDAGOGICAL_FORMULA_VISUAL_POLISH_AND_HUMAN_REREVIEW` — answers the human
review of run `w10-pedagogical-playback` (`FAIL_REQUIRES_TARGETED_PEDAGOGICAL_REPAIR`,
findings W10-H1…H9). Automation only: nothing here is a human approval, and nothing
here is `MERGE_READY`. Date, time, commits and environment are in `RUN.json`.

Start with `HANDOFF.md` (what a reviewer should look at), then `REPORT.md`.

| Path | What it is |
|---|---|
| `RUN.json` | identity: commits, candidate, cache, environment, policy flags |
| `MANIFEST.json` | every artifact with its producer and sha256 |
| `REPORT.md` | root causes, repairs, results, limitations |
| `HANDOFF.md` | reviewer checklist and the required handoff fields |
| `inputs/W10_HUMAN_VISUAL_REVIEW.json` | additive record of the w10 human verdict (w10 stays byte-identical) |
| `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json` | candidate divergence declared for this wave |
| `inputs/fixtures/` · `inputs/FIXTURE_MANIFEST.json` | twelve Tier-A fixtures regenerated at the frozen candidate (0 model calls) |
| `results/BROWSER_EVIDENCE.json` | authoritative browser suite (6 families × desktop/mobile, positive + negative) |
| `results/OCCLUSION_MEASUREMENT.json` | product ↔ independent oracle; frozen human sets under the declared camera change |
| `results/PLAYBACK_EVIDENCE.json` | learner-only playback runner (Play pressed once, orbit laps) |
| `results/HIDDEN_EDGE_CROPS.json` | index of every hidden-edge crop, family sheet and playback film |
| `results/VERIFICATION_SUMMARY.json` | every gate and its result, generated from the files above |
| `results/BACKEND_COUNT_RECONCILIATION.json` | the one authoritative full-backend count (T3 log + sha256) and 6368 → 6370 → 6411 per file |
| `images/overview/INDEX.png` | index only: one thumbnail per family, pointing at the family sheet |
| `images/<family>/SHEET.png` | acceptance sheet per family: desktop neutral · causal · rotated, mobile neutral, every formation step, legend |
| `images/<family>/desktop/`, `mobile/` | full-resolution suite screenshots (sources of the sheet) |
| `images/<family>/negative/` | refusal screens of the negative fixtures |
| `images/<family>/playback/<viewport>/` | learner playback filmstrip and states |
| `images/<family>/hidden-edges/<viewport>/` | hidden-edge crops holding both endpoints |
| `diagnostics/` | formula provenance trace before/after, every measurement attempt (failures included), logs |

`<family>` is one of `triangular-pyramid`, `triangular-prism`, `rectangular-pyramid`,
`cuboid`, `cube`, `cross-section` (`docs/evaluation/RUN_NAMING.md`).

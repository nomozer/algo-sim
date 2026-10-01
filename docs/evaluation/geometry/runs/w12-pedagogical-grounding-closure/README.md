# Run `w12-pedagogical-grounding-closure`

Task `W12_PEDAGOGICAL_TIMELINE_AND_SOURCE_GROUNDING_CLOSURE` — answers the human review
of run `w11-pedagogical-polish` (`NEEDS_CHANGES`, findings W11-H1…H5). Automation only:
nothing here is a human approval, and nothing here is `MERGE_READY`. Date, time,
commits and environment are in `RUN.json`.

Start with `HANDOFF.md` (what a reviewer should look at), then `REPORT.md`.

| Path | What it is |
|---|---|
| `RUN.json` | identity: commits, candidate, cache, environment, policy flags |
| `MANIFEST.json` | every artifact with its producer and sha256 |
| `REPORT.md` | root causes, repairs, results, limitations |
| `HANDOFF.md` | reviewer checklist and the required handoff fields |
| `inputs/W11_HUMAN_VISUAL_REVIEW.json` | additive record of the w11 human verdict (w11 stays byte-identical) |
| `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json` | candidate divergence of this wave, with its two intermediate candidates |
| `inputs/fixtures/` · `inputs/FIXTURE_MANIFEST.json` | eighteen Tier-A fixtures (positive, structural negative, ungrounded negative per family), regenerated at the frozen candidate, 0 model calls |
| `results/BROWSER_EVIDENCE.json` | authoritative browser suite (6 families × desktop/mobile, positive + ungrounded negative) |
| `results/OCCLUSION_MEASUREMENT.json` | product ↔ independent oracle; frozen human sets under the declared camera change |
| `results/PLAYBACK_EVIDENCE.json` | learner-only playback runner (Play pressed once, five orbit laps) |
| `results/HIDDEN_EDGE_CROPS.json` | index of every hidden-edge crop, family sheet and playback film |
| `results/VERIFICATION_SUMMARY.json` | every gate and its result, generated from the files above |
| `results/BACKEND_COUNT_RECONCILIATION.json` | the authoritative full-backend count and the w11 → w12 delta per file |
| `images/overview/INDEX.png` | index only: one thumbnail per family, pointing at the family sheet |
| `images/<family>/SHEET.png` | acceptance sheet per family: neutral · causal · rotated · mobile · solution panel (four states) · refusal of an ungrounded problem (desktop, mobile) · every GEOMETRY step, legend |
| `images/<family>/desktop/`, `mobile/` | full-resolution suite screenshots (sources of the sheet), incl. `geometry_step/` and the solution panel |
| `images/<family>/negative/` | refusal screens of the ungrounded fixtures |
| `images/<family>/playback/<viewport>/` | learner playback filmstrip and states |
| `images/<family>/hidden-edges/<viewport>/` | hidden-edge crops holding both endpoints |
| `diagnostics/` | every measurement attempt (superseded and failed ones included), the hue-gate known-answer run, red logs, probes, worktree cleanup |

`<family>` is one of `triangular-pyramid`, `triangular-prism`, `rectangular-pyramid`,
`cuboid`, `cube`, `cross-section` (`docs/evaluation/RUN_NAMING.md`).

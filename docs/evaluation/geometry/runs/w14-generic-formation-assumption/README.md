# Run `w14-generic-formation-assumption`

Task `W14_GENERIC_FORMATION_AND_ASSUMPTION_FOUNDATION` — answers the human review of run
`w12-pedagogical-grounding-closure` (`NEEDS_CHANGES`, W12-H1…H4, recorded in run
`w13-geometry-preregistration`) under the preregistration
[`docs/architecture/GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md`](../../../../architecture/GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md).
Automation only: nothing here is a human approval, and nothing here is `MERGE_READY`.
Date, commits and environment are in `RUN.json`.

Start with `HANDOFF.md` (what a reviewer should look at, and the decisions that are
yours), then `REPORT.md`.

| Path | What it is |
|---|---|
| `RUN.json` | identity: commits, candidate, cache, environment, track results, policy flags |
| `MANIFEST.json` | every file with sha256, its basis (`raw_bytes` / `git_blob_lf`) and its producer |
| `REPORT.md` | what changed per track, results, limitations |
| `HANDOFF.md` | reviewer checklist, open decisions, the required handoff fields |
| `inputs/W14_SCOPE_DECISIONS.json` | the user's recorded answers Q1, Q3, Q4 and the brief's D2, D3 |
| `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json` | candidate divergence of this wave (corrects the w12 layer, which stays byte-identical) |
| `inputs/fixtures/` · `inputs/FIXTURE_MANIFEST.json` | eighteen Tier-A fixtures (positive, structural negative, ungrounded negative per family) at the frozen candidate, 0 model calls |
| `results/BROWSER_EVIDENCE.json` | browser suite: 6 families × desktop/mobile, positive + ungrounded negative, formation role coverage, structured references |
| `results/OCCLUSION_MEASUREMENT.json` | product ↔ independent oracle; frozen human sets under the declared camera change (4 of 6 refused: scene geometry changed) |
| `results/PLAYBACK_EVIDENCE.json` | learner-only playback (Play pressed once, five orbit laps) |
| `results/HIDDEN_EDGE_CROPS.json` | index of every hidden-edge crop, family sheet, filmstrip and playback film |
| `images/overview/INDEX.png` | index only: one thumbnail per family |
| `images/<family>/FILMSTRIP.png` | the formation steps left to right, each captioned with its roles and the learner text |
| `images/<family>/SHEET.png` | acceptance sheet per family (neutral · causal · rotated · mobile · solution panel · refusal · every geometry step) |
| `images/<family>/desktop/`, `mobile/`, `negative/`, `playback/`, `hidden-edges/` | full-resolution sources of the sheet and the films |
| `diagnostics/` | red logs, S4 inventory, trust-policy callers, assumption corpus + census + decision, cache proof, probes, ponytail review, measurement attempts, worktree cleanup, logs |

`<family>` is one of `triangular-pyramid`, `triangular-prism`, `rectangular-pyramid`,
`cuboid`, `cube`, `cross-section` (`docs/evaluation/RUN_NAMING.md`).

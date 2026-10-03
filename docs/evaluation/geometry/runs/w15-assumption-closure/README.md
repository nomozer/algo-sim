# Run `w15-assumption-closure`

Task `W15_SOURCE_CONSTRAINT_AND_ASSUMPTION_CLOSURE` closes the assumption channel that W14 left
open (`ASSUMPTION_POLICY_INCOMPLETE`). It does so with a server-owned reader of the
constraints the text states, and an assumption certificate wired into the route. It keeps
W14's shape-class formation and makes the closed cross-section fill visible. The scope and
the rules were registered before any gate code, in
[`docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md`](../../../../architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md).

This run is automation only: nothing here is a human approval, and nothing here is
`MERGE_READY`. Dates, commits and environment are in `RUN.json`.

Start with `HANDOFF.md` (what a reviewer should look at, and the decisions that are yours),
then read `REPORT.md`.

| Path | What it is |
|---|---|
| `RUN.json` | identity: commits, candidate (three freezes), cache, environment, results, policy flags |
| `MANIFEST.json` | every file with its sha256, its basis (`raw_bytes` / `git_blob_lf`), its producer and its measurement status |
| `REPORT.md` | root causes, what changed, results with denominators, limitations |
| `HANDOFF.md` | reviewer checklist, open decisions, the brief's handoff fields |
| `inputs/W15_SCOPE_DECISIONS.json` | the brief's D1–D3 and the user's verbatim answers U1–U5 |
| `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json` | candidate divergence of this wave (corrects the w14 layer, which stays byte-identical); lists the intermediate candidate |
| `inputs/fixtures/` · `inputs/FIXTURE_MANIFEST.json` | 24 Tier-A fixtures at the final candidate: positive, structural negative, ungrounded negative and assumption negative per family; 0 model calls |
| `results/BROWSER_EVIDENCE.json` | browser suite: 6 families × desktop/mobile; positives; three negative kinds, each with its own code; `SECTION_FILL_DISTINGUISHABLE` |
| `results/OCCLUSION_MEASUREMENT.json` | product ↔ independent oracle; frozen human sets under the declared camera change; the four W14-changed scenes `HUMAN_REVIEW_PENDING` (U2) |
| `results/PLAYBACK_EVIDENCE.json` | learner-only playback (Play pressed once, five orbit laps) |
| `results/HIDDEN_EDGE_CROPS.json` | index of every hidden-edge crop, family sheet, filmstrip and playback film |
| `images/overview/INDEX.png` | index only: one thumbnail per family |
| `images/<family>/FILMSTRIP.png` · `SHEET.png` | formation steps with role captions (section steps included) · the acceptance sheet per family |
| `images/<family>/desktop/`, `mobile/`, `negative/`, `playback/`, `hidden-edges/` | full-resolution sources of the sheets and films |
| `diagnostics/` | Track B investigation, gold-row verification, corpora and labels, three census rounds, fault injections, cache proof, ponytail review, the failed first browser attempt (`browser-attempt1-c1638891/`), measurement attempts, worktree cleanup, temp-file inventory, logs |

`<family>` is one of `triangular-pyramid`, `triangular-prism`, `rectangular-pyramid`, `cuboid`,
`cube` or `cross-section` (`docs/evaluation/RUN_NAMING.md`).

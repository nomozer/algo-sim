# Run `w16-premerge-closure`

Task `W16_PREMERGE_SOUNDNESS_AND_VISUAL_EVIDENCE_CLOSURE` is a correctness pass before merge,
not a capability expansion. It closes two soundness gaps that W15 left in the assumption
certificate. First, a plane equation was not bound to its own entity in C0. Second, a
relation the text asks to prove ("Chứng minh …") could act as a premise. It also gives the
four untested fail-closed guards their own tests. It puts the closed section fill under the
solid edges, so the edges stay readable. Finally, it makes the acceptance sheets carry every
refusal panel: a missing or blank panel now fails the builder. The rules were registered
before any fix, in
[`docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md`](../../../../architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md)
§14.

This run is automation only: nothing here is a human approval, and nothing here is
`MERGE_READY`. Dates, commits and environment are in `RUN.json`.

Start with `HANDOFF.md`, which lists what a reviewer should open and the decisions that are
yours. Then read `REPORT.md`.

| Path | What it is |
|---|---|
| `RUN.json` | identity: commits, candidate (two freezes), cache, environment, results, policy flags |
| `MANIFEST.json` | every file with its sha256, its basis (`raw_bytes` / `git_blob_lf`), its producer and its measurement status |
| `REPORT.md` | root cause and result per probe, what changed, results with denominators, limitations |
| `HANDOFF.md` | reviewer checklist, open decisions, the brief's handoff fields |
| `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json` | candidate divergence of this wave (corrects the w15 layer, which stays byte-identical); lists the intermediate candidate |
| `inputs/fixtures/` · `inputs/FIXTURE_MANIFEST.json` | 24 Tier-A fixtures at the final candidate: positive, structural negative, ungrounded negative and assumption negative per family; 0 model calls |
| `results/BROWSER_EVIDENCE.json` | browser suite: 6 families × desktop/mobile; positives; three negative kinds with their own codes and the box of the learner message; `SECTION_FILL_DISTINGUISHABLE` and `SECTION_FILL_UNDER_EDGES` |
| `results/OCCLUSION_MEASUREMENT.json` | product ↔ independent oracle; the four W14-changed scenes `HUMAN_REVIEW_PENDING` (U2 of w15) |
| `results/PLAYBACK_EVIDENCE.json` | learner-only playback (Play pressed once, five orbit laps) |
| `results/HIDDEN_EDGE_CROPS.json` | index of every hidden-edge crop, family sheet, filmstrip and playback film |
| `images/overview/INDEX.png` | index only: one thumbnail per family |
| `images/<family>/SHEET.png` · `FILMSTRIP.png` | the acceptance sheet per family, now with all six refusal panels (three kinds × desktop/mobile) · formation steps with role captions |
| `images/<family>/desktop/`, `mobile/`, `negative/<kind>/<viewport>/refusal.png`, `playback/`, `hidden-edges/` | full-resolution sources of the sheets and films |
| `diagnostics/` | Phase 1 probe at the RED commit, adversarial corpora W16 and W16B (labels committed before the fixes they judge), census rounds 1 and 2, backend and frontend fault injections, cache proof, the failed first browser attempt (`browser-attempt1-55cde06e/`), measurement attempts, worktree cleanup, temp-file inventory, logs |

`<family>` is one of `triangular-pyramid`, `triangular-prism`, `rectangular-pyramid`, `cuboid`,
`cube` or `cross-section` (`docs/evaluation/RUN_NAMING.md`). `<kind>` is `ungrounded_source`,
`assumption` or `topology_kernel`.

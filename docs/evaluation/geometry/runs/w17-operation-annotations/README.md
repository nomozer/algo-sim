# Run `w17-operation-annotations`

Task `W17_OPERATION_BINDING_AND_ON_SCENE_ANNOTATIONS` continues from W16 in a fixed order:
correctness, then learner presentation, then verification, evidence and living docs.

**Correctness.**
- It closes limit A′, which W16 declared: the text cut with (β), the program cut with (α),
  and the answer was certified and served.
- A value that appears only inside a proof request ("Chứng minh rằng SA = 5") can no longer
  ground a GIVEN.
- Every refusal now carries a structured cause: SOURCE, CONSTRUCTION or UNKNOWN. Only a SOURCE
  cause tells the learner to fix the text.

**Presentation.**
- The edge-group step names its action ("Các cạnh bên AD, BE, CF") instead of claiming "dữ
  kiện đề cho".
- Verified quantities appear on the figure, beside the segment, region, solid or point they
  measure. The "Số đo" and "Kết quả" chips toggle them, and both are on by default.

The rules were registered before any fix, in
[`docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md`](../../../../architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md)
§15. That section carries dated corrections from Tasks 1–3, Task 7, the final whole-branch
self-review and the first measurement attempt on the final candidate.

This run is automation only: nothing here is a human approval, and nothing here is
`MERGE_READY`. Dates, commits and environment are in `RUN.json`.

Start with `HANDOFF.md`. It lists what a reviewer should open and the decisions that are
yours. Then read `REPORT.md`.

| Path | What it is |
|---|---|
| `RUN.json` | identity: commits, candidate (two freezes), measurements, cache, environment, results, policy flags |
| `MANIFEST.json` | every file with its sha256, its basis (`raw_bytes` / `git_blob_lf`), its producer and its measurement status |
| `REPORT.md` | root cause and result per goal, before/after, results with denominators, limitations |
| `HANDOFF.md` | reviewer checklist, open decisions, the brief's handoff fields |
| `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json` | candidate divergence of this wave; it corrects the w16 layer, which stays byte-identical |
| `inputs/fixtures/` · `inputs/FIXTURE_MANIFEST.json` | 27 Tier-A fixtures at the final candidate `d63d6fd4…`, 0 model calls: positive, structural negative, ungrounded negative and assumption negative per family; cube `system_cause`; the cross-section wrong-plane / correct-plane pair |
| `results/BROWSER_EVIDENCE.json` | browser suite, 6 families × desktop/mobile:<br>· positives with on-figure labels (final, rotated, resized), toggle isolation, causal restore at the same camera and scroll<br>· negatives with their own code and cause<br>· the served correct plane<br>· section fill |
| `results/OCCLUSION_MEASUREMENT.json` | product ↔ independent oracle; the four W14-changed scenes `HUMAN_REVIEW_PENDING` (U2 of w15) |
| `results/PLAYBACK_EVIDENCE.json` | learner-only playback (Play pressed once, five orbit laps) |
| `results/HIDDEN_EDGE_CROPS.json` | index of every hidden-edge crop, family sheet, filmstrip and playback film |
| `images/overview/INDEX.png` | index only: one thumbnail per family |
| `images/<family>/SHEET.png` · `FILMSTRIP.png` | the acceptance sheet per family, now with the toggle-off and causal-restore captures, the W17 refusal panels where declared and the served correct plane · formation steps with role captions |
| `images/<family>/desktop/`, `mobile/`, `negative/<kind>/<viewport>/refusal.png`, `served/`, `playback/`, `hidden-edges/` | full-resolution sources of the sheets and films |
| `diagnostics/` | A′ reproduction at the RED commit · negative-fixture reconciliation · W17 corpus and the W17C addendum (labels committed before the fixes they judge) · census rounds 1 and 2 · backend (three runs) and frontend (three runs) fault injections · cache proof · ponytail review · the three Task 7 browser rounds (`browser-t7-*`, diagnostic) · `evidence-intermediate-c5592c1a/` (complete PASS on the intermediate candidate, superseded) · `browser-final-attempt1-83f101e4/` (failed attempt 1 on the final candidate, with its diagnostic runs) · measurement attempts · worktree cleanup · temp-file inventory · logs |

`<family>` is one of `triangular-pyramid`, `triangular-prism`, `rectangular-pyramid`, `cuboid`,
`cube` or `cross-section` (`docs/evaluation/RUN_NAMING.md`). `<kind>` is one of the W15 kinds
`ungrounded_source`, `assumption` and `topology_kernel`, or one of the W17 kinds `system_cause`
(cube) and `construction_mismatch` (cross-section).

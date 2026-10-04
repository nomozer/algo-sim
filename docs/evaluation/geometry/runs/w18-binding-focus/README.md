# Run `w18-binding-focus`

Task `W18_CONSTRUCTION_BINDING_AND_FOCUSED_ANNOTATIONS` continues from W17 in a fixed order:
correctness, then learner presentation, then verification, evidence and living docs.

**Correctness.**
- A point the text defines by a relation is now checked against that relation by identity:
  "M là trung điểm của SA", "M, N lần lượt là trung điểm của SA, SB", "H là hình chiếu của S
  lên (ABCD)", "H là chân đường vuông góc kẻ từ S xuống BC". Coordinates or values that happen
  to be equal never count.
- A program that builds such a point on other entities is refused at the new route stage
  `construction_binding`, in every scope. Examples: the midpoint of SB for SA, a foot on the
  wrong plane, swapped "lần lượt" targets, the relation built under a renamed target. The
  learner is told both relations, and is not told to fix the text.
- A relation the system cannot check is refused inside the polyhedral scope with "chưa đối
  chiếu được", never "đề sai". Examples: an unread phrasing, an ambiguous identity, an unpinned
  receiver.
- Before W18, the Phase 1 reproduction served four kinds of these programs: a projection onto
  the wrong line or plane, a swapped list (3√6 shown where the correct answer is 9), a renamed target,
  and a same-coordinate identity swap.

**Presentation.**
- The figure shows point names and the given data by default.
- Selecting a quantity (its label, its solution row or the object it measures) shows it with
  its numeric chain. One chip, "Hiện tất cả", shows every available label.
- The inspector is the one place that explains a quantity: formula, the given data and the
  direct inputs. The full solution is collapsed by default; while it is open, the inspector
  drops its formula.
- A point-to-line or point-to-plane distance draws its witness while its label shows: a segment
  to the exact foot computed by the kernel, and a right-angle mark.

The rules were registered before any fix, in
[`docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md`](../../../../architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md)
§16. That section carries dated corrections from Tasks 2–5.

This run is automation only: nothing here is a human approval, and nothing here is
`MERGE_READY`. Dates, commits and environment are in `RUN.json`.

Start with `HANDOFF.md`. It lists what a reviewer should open and the decisions that are
yours. Then read `REPORT.md`.

| Path | What it is |
|---|---|
| `RUN.json` | identity: commits, candidate (one freeze), measurement, cache, environment, results, policy flags |
| `MANIFEST.json` | every file with its sha256, its basis (`raw_bytes` / `git_blob_lf`), its producer and its measurement status |
| `REPORT.md` | root cause and result per goal, before/after, results with denominators, limitations |
| `HANDOFF.md` | reviewer checklist, open decisions, the brief's handoff fields |
| `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json` | candidate divergence of this wave; it corrects the w17 layer, which stays byte-identical |
| `inputs/fixtures/` · `inputs/FIXTURE_MANIFEST.json` | 32 Tier-A fixtures at the final candidate `d3b4cab9…`, 0 model calls: the 27 of w17, plus five W18 point-construction cases on the gold p1 text (three refused, two served) |
| `results/BROWSER_EVIDENCE.json` | browser suite, 6 families × desktop/mobile:<br>· compact default; per-quantity selection with its chain and one detail region; "Hiện tất cả" on → off → on isolation; causal restore<br>· negatives with their own code and cause, including the three W18 refusals<br>· the two W18 served cases with their witness<br>· section fill |
| `results/OCCLUSION_MEASUREMENT.json` | product ↔ independent oracle; the four W14-changed scenes `HUMAN_REVIEW_PENDING` (U2 of w15) |
| `results/PLAYBACK_EVIDENCE.json` | learner-only playback (Play pressed once, five orbit laps) |
| `results/HIDDEN_EDGE_CROPS.json` | index of every hidden-edge crop, family sheet, filmstrip and playback film |
| `images/overview/INDEX.png` | index only: one thumbnail per family |
| `images/<family>/SHEET.png` · `FILMSTRIP.png` | the acceptance sheet per family: compact default, "Hiện tất cả", the solution expanded, one selection per quantity kind with its inspector, causal restore, the refusal panels · formation steps with role captions |
| `images/<family>/desktop/`, `mobile/`, `negative/<kind>/<viewport>/refusal.png`, `served/`, `playback/`, `hidden-edges/` | full-resolution sources of the sheets and films |
| `diagnostics/` | Phase 1 reproduction (before, after) · the 23-row W18 corpus (labels committed before the fix) · census · backend fault injections (runs 1–3) and frontend fault injections (runs 1–2, with the FW2 diagnostic) · cache proof · ponytail review · the two pre-freeze browser rounds (`browser-prefreeze-*`, diagnostic) · `evidence-attempt1-8caa8307/` (acceptance attempt 1, every gate passed, superseded by the harness fix) · measurement attempts · worktree cleanup · temp-file inventory · logs |

`<family>` is one of `triangular-pyramid`, `triangular-prism`, `rectangular-pyramid`, `cuboid`,
`cube` or `cross-section` (`docs/evaluation/RUN_NAMING.md`). `<kind>` is one of the W15 kinds
`ungrounded_source`, `assumption` and `topology_kernel`; the W17 kinds `system_cause` (cube) and
`construction_mismatch` (cross-section); or the W18 kinds `point_construction_mismatch`,
`projection_mismatch` and `construction_unverified` (cross-section).

# Official Visual suite (P1)

`frontend/scripts/compiler-scene-replay.mjs --suite` (`compiler-scene-suite.mjs`).

**Setup.**
- Inputs: 49 fixtures regenerated at product `af670aa6`; the suite manifest copies the independent expectations and changes only `task_id` and the candidate identity (`visual/inputs/`, commit `63948c05`).
- 0 model calls.
- Runs in the clean detached worktree `t3-b1b2`; receipts are copied into `visual/official-suite-run1/` and `visual/official-suite-run2/`.

## Verdict: FAIL, and every remaining failure is a product finding

| Run | Harness | Scenarios | Positive runs | Negative / refusal runs | Served runs |
|---|---|---|---|---|---|
| Codex, before (`13d28b84`) | before the policy split | 8/8 FAIL | 14 aborted (HARNESS), 2 aborted (ENVIRONMENT) | all pass | all aborted |
| run 1 (`63948c05`, harness `e3e77a0f`) | first learner-mode split | 8/8 FAIL | all complete; harness-side failures found (below) | all pass | 8 aborted (POLL_TIMEOUT) |
| **run 2 (`4ec36db9`)** | **final** | **8/8 FAIL** | **all complete; only product findings F1, F2** | **all pass** | **all pass** |

## Policy the suite now validates

The learner policy comes from `aa458cc3`.
- **Mode A (default):**
  - the drawer lists exactly the oracle's givens and intermediates and **no final answer**;
  - no final-answer label is shown, even with «Hiện tất cả».
- **Mode B:** the suite opens «Phân tích toán học» like a learner does. Then:
  - the drawer matches the **full** oracle, and each final result appears once under «Kết quả» with the expected answer;
  - the analysis panel states the answer under «Kết quả toán học»;
  - the unchanged causal-closure oracle and the per-quantity selection oracle run for the final results.

Final results (`finalResultIds`) are read independently from the scene's `FINAL_RESULT` events plus aliases, never from product code.

The independent geometry, section-fill, refusal, provenance and causal-closure oracles are unchanged, and so are all thresholds. No assertion was skipped or turned into a pass.

## Per scenario (run 2)

| Scenario | Desktop | Mobile | Cause |
|---|---|---|---|
| triangular_pyramid | FAIL `selection_per_quantity` | same | F1 |
| triangular_prism | FAIL `selection_per_quantity` | same | F1 |
| rectangular_pyramid | FAIL `selection_per_quantity` | same | F1 |
| cuboid | FAIL `selection_per_quantity` | same | F1 |
| cube | FAIL `selection_per_quantity` | same | F1 |
| regular_square_pyramid | FAIL `selection_per_quantity` | same | F1 |
| regular_triangular_pyramid | FAIL `selection_per_quantity` | same | F1; served `regular_tetrahedron` PASS |
| cross_section | FAIL `causal_closure` + `evidence_gates` (`CAUSAL_CANVAS_ROLE_HUE`) | same | F2; served `correct_plane`, `point_construction_witness`, `projection_correct` PASS |

All 16 positive runs complete. Every other assertion passes:
- quantity picker (Mode A), `solution_final` (answer hidden), `mode_b_reveal` (answer exactly once);
- show-all isolation, annotations, witness;
- formation, structured references, role coverage, steps panel;
- immutable 120 frames, causal closure (oracle = events = browser in every family), causal restore;
- orbit, CSS, raw-token leakage, section fill.

## Product findings: owner decision needed, nothing changed

**F1. Mode B explains a final answer in two places.**
- When a final result is selected with «Phân tích toán học» open, its formula appears in the inspector (`.geo3d-soi-cong-thuc`) **and** in the analysis panel (`data-analysis-formula`).
- The registered W18 §16.6 rule ("exactly one region carries the formula", `assessDetailRegion`) fails with `DETAIL_REGIONS_2`. This affects 7 of 8 families on both viewports (`cross_section`'s finals have no coherent formula text).
- **Options:**
  - hide the inspector formula while the same quantity's formula is in the open analysis panel, or the reverse;
  - or amend the rule for Mode B.

**F2. The section's colour is inside the "data" role hue, and a selected section shows no target hue.**
- The SGK port draws sections in terracotta `0xc85a32` (hue ≈ 16°, owner-approved, fill 0.32). The causal role-hue oracle reserves hue 10–50° for "dữ kiện số / trung gian".
- With `cross_section`'s target `area_T` selected, the canvas has 3,485 (desktop) / 4,443 (mobile) such pixels against a tolerance of 128 / 101, and **0** target-blue pixels: the section stays terracotta when it is the target.
- **Options:**
  - move the section hue out of the role band;
  - recolour the selected/target section in the target hue;
  - or amend the role-hue registration.

## Harness defects found and fixed (not product failures)

| Defect | Fix | Commit |
|---|---|---|
| Quantity picker, `solution_final`, evidence gate required the final answer in the default drawer | Mode A expectations (`revealFinal: false`) + Mode B reveal | `e3e77a0f`, `4ec36db9` |
| Causal target (a final result) selected from the Mode A drawer → `CAUSAL_TARGET_NOT_CLICKABLE` | Causal block measured in Mode B | `e3e77a0f` |
| Drawer selectors matched the analysis panel (same body class) | Scoped to `[data-panel=dai-luong]` | `e3e77a0f` |
| Structured references (b) required final readouts in the Mode A drawer | Finals exempt in Mode A; their absence is asserted by `solution_final` | `4ec36db9` |
| Witness rule failed a final's 3D witness (kept on purpose by the product) when its label is hidden | Finals exempt in Mode A; a missing witness for a shown label still fails | `4ec36db9` |
| `selection_per_quantity` empty in Mode A when every row is final | Finals selected and measured in Mode B with the full oracle; the check spans every quantity again | `4ec36db9` |
| Causal dash baseline taken in Mode A; opening the panel re-frames the camera (adaptive safe-area framing, probed: `tools/camera-modeb-probe.mjs`) | Baseline = settled Mode B frame before selection | `4ec36db9` |
| Hue census counted the analysis panel's role-coloured bars (DOM, not canvas) as canvas pixels | `.geo3d-bang-noi` added to the overlay mask | `4ec36db9` |
| Served cases polled the default drawer for the answer → `POLL_TIMEOUT`, misclassified ENVIRONMENT | Answer read in Mode B; Mode A must show no final row | `4ec36db9` |
| `runPositive` stored 2000 chars of JS stack in receipts | First message line only | `4ec36db9` |

Node harness: 115 tests (113 pass, 2 skipped, 0 fail), including new fault-injection tests for:
- the Mode A oracle;
- `PICKER_FINAL_SHOWN`;
- `ANSWER_SHOWN_IN_MODE_A`;
- `ANSWER_NOT_SHOWN_ONCE` (Mode B).

## Environment failures

None in run 2. The earlier ENVIRONMENT classifications (Codex; run 1 served `POLL_TIMEOUT`) were the harness defect above.

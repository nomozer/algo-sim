# Pedagogical formula + visual polish (w11)

Status: `READY_FOR_HUMAN_VISUAL_REVIEW` — automation only. The w10 human review was
`FAIL_REQUIRES_TARGETED_PEDAGOGICAL_REPAIR` (W10-H1…H9, recorded additively in
`inputs/W10_HUMAN_VISUAL_REVIEW.json`); this run repairs what it named and hands the
result back to a human. Nothing here is `MERGE_READY`.

## Identity

- Branch `fix/cuboid-visual-semantic-closure`, start `b9193766`.
- Product commits: `f147dde6` (backend) · `e186b4cf`, `e633ad0c`, `60292ecf` (frontend/src).
  Candidate `8539acbc…` → `df04a613…`, refrozen **once** after the last product change
  (`a39028de`, clean worktree at `7efdae4a`, product commit `60292ecf`).
- Measurement commit `39e54046` (detached clean worktree `D:/tmp/w11-d1`, no local
  venv): browser suite, occlusion oracle, learner playback, evidence builder.
- `CACHE_VERSION` 103 → **104**, once (`f147dde6`): cached `ok` envelopes change in
  three places (given lengths declared, grounding accepts them, formula references);
  provider fingerprint `b1714b566e25c912` unchanged. `DEFAULT_MODE = LLM_ONLY`;
  0 live Gemini requests; 0 application LLM calls.

## What the reviewer rejected, and what changed

| Finding | Root cause (measured) | Repair |
|---|---|---|
| W10-H1/H2 — no formula for the triangular pyramid / prism | Trace `diagnostics/FORMULA_PROVENANCE_TRACE_BEFORE.json`: both compilers declared points, base, solid and results but not the given lengths, so `_provenance` had no `*_length` memory to join to the volume; the volume's numerical edges were `[base area]` and `_attach_formulas` skipped it. The rectangular pyramid and cuboid/cube compilers already declared them | `compiler.py::_khai_do_dai_de_cho` declares AB, AC and SA/AD as GIVEN with provenance and source copied from the FactGraph. `grounding_gate.py::_do_dai_bat_bien` accepts an `XY_length` that matches a contract length invariant (same segment, value, cited fact) — the server anchors `SA = 5` to a value-less relation fact. Formula text: `V = 1/3 × S(ABC) × SA = 10`, `V = S(ABC) × AD = 30` |
| W10-H3 — height missing from "Dựa trên" / numerical closure | Same cause: the volume's only numerical edge was the base area, so "Dựa trên" read `S(ABC)` alone (BEFORE trace, both families) | `scene3d.py`: formula `references` = exactly the entities the text names, in text order; two height candidates ⇒ no formula. `scene3d-model.ts::numericalBasis`: "Dựa trên" = coherent formula references, else numerical edges |
| W10-H4 — rotated pyramid near-degenerate | The w10 orbit gate checked area, depth and face tilt only | Gate on the PERSPECTIVE screen image: area/depth ≥ 60 %/50 % of the scene's best, faces ≥ 12° along rays from the eye, two edges sharing a vertex not collapsed and a vertex not on another edge (≥ ½ of the unit-cube reference), every vertex inside the canvas and not under an overlay. The gesture (rotation + 0/3/6 zoom-out notches) is simulated with OrbitControls' maths and only a passing one is sent; predicted ↔ actual view matrix recorded |
| W10-H5 — vertex markers large | Markers had a fixed WORLD radius (0.09), so their screen size depended on scene size, zoom and canvas | Visible marker separate from the hit target: 6 px desktop, 7.5 px narrow (< 768 px), 9 px selected (CSS px, one token `DAU_DINH_PX`), re-scaled every frame from camera depth so DPR does not change it; hit radius 12/16 px |
| W10-H6 — causal tiers flat | One highlight for the whole closure | Target > numerical givens > numerical intermediates > structural context > dimmed outside, following the backend's typed `numerical` edges; context keeps its stroke with a light fill; solid/dashed policy kept; readout rows carry the tier class. The harness computes the expected tiers independently |
| W10-H7 — infinite line prominent | Every line drawn at full ink | A line not emphasised is drawn at 0.45 opacity; it is prominent at its own construction step and when selected. Found while measuring: "Xem lại toàn hình" at the last cross-section step followed BD's rendered span and the markers (`60292ecf`) |
| W10-H8 — formation appendix too small | One shared appendix image | One sheet per family (`images/<family>/SHEET.png`, full resolution, 28 px captions, legend: orange = new or under consideration · neutral = constructed · dashed = hidden) with neutral, causal, rotated, mobile and every formation step; `images/overview/` is an index only; hidden-edge crops per family; diagnostics out of the sheets. Measurement steps must not make geometry appear (`measurement_steps_keep_geometry`) |
| W10-H9 — 6368 vs 6370 | Two correct counts at two commits: T3 at `40ce889f` = 6368; `52de6f22` added exactly two tests (`test_main_sheet_cells_crop_the_stage_not_the_whole_page`, `test_oracle_screen_point_maps_to_image_pixels_through_css`) → 6370 at `b9193766` | This run publishes ONE count: **6411 passed / 0 failed** (1 skipped, 1 deselected), T3 at `5e3dbab4`; +41 tests in w11, per file in `results/BACKEND_COUNT_RECONCILIATION.json` |

No branch on family name, case ID, problem text or vertex name was added; the
frontend presents backend structured data only.

## Measurement

`diagnostics/MEASUREMENT_ATTEMPTS.json` lists eight entries, failures included: five
diagnostic attempts, two authoritative browser attempts, one trace post-processing.
The five diagnostic attempts before the refreeze found: the main-tree `dist/`
ACL (`EPERM`), rotations that push a vertex off the mobile canvas, an orthographic
gate that accepted A 9 px from SB, Chrome halving the wheel `deltaY` under DPR 2,
and the "Xem lại toàn hình" drift. The first authoritative attempt (`48c676d5`)
passed the browser suite but the oracle refused two states with
`SCENE_GEOMETRY_CHANGED`: its geometry signature counted the three new `quantity`
readouts. `39e54046` makes it skip that known non-drawing type (an unknown type still
counts), red → green on the real fixtures; the whole measurement was repeated there.
Post-processing `ac19e03d` (diagnostic only): the provenance trace still restated the
pre-w11 "Dựa trên" rule and listed `[SA, S(ABC)]` while the screen shows
`S(ABC), SA`; the trace now follows `numericalBasis` and was regenerated there
(first output kept in `diagnostics/`).

## Final verification

| Gate | Result |
|---|---|
| T3 `full-gate.mjs` from a path WITH a space (`D:/tmp/w11 space/algo-sim`, `5e3dbab4`) | `FULL_PRODUCT_GATE_PASS` — pytest 6411 passed / 0 failed (1 skipped, 1 deselected) · vitest 958/958 (64 files) · typecheck + build · demo replay · crash surface; log sha256 `6f7c18fd…` |
| Browser suite, 6 families × desktop 1440×900 + mobile 390×844 (`39e54046`) | 12/12 positive, 12/12 negative (structured refusal, no canvas, no answer); causal closure + tiers 12/12 with readout classes matching the independently computed tiers; rotation through the perspective gate 12/12, planned gesture passed first time 12/12, predicted ↔ actual view matrix ≤ 1e-6; vertex markers 6.00 px desktop / 7.50 px mobile; formation 12/12; measurement steps keep geometry 12/12; immutable 120 frames 12/12 |
| Occlusion (product ↔ independent oracle) | 24/24 states; frozen expectations `DECLARED_CAMERA_CHANGE` 6/6 (registry byte-identical) |
| Learner playback (Play pressed once) | 12/12 runs × 18 checks; orbit laps 60/60 |
| Hidden-edge crops · family sheets | 64 crops, both endpoints inside, 0 oracle disagreements, 0 duplicate owners; six `images/<family>/SHEET.png` + `images/overview/INDEX.png` |
| Formula provenance (trace AFTER, `ac19e03d`) | 5/5 volume families: base area + height in the numerical closure and in the formula; "Dựa trên" in formula order; cross-section volume structural only |
| Candidate `--verify` · cache lock · schema export ×2 | PASS (`df04a613…`, 103 files) · `CACHE_VERSION 104`, fingerprint `b1714b56…` · byte-identical, no diff |
| Node tests (harness) | 29/29 |

Numbers: `results/VERIFICATION_SUMMARY.json` (generated from the evidence files).

## Limitations (not hidden)

- **No human has approved** the new sheets, screenshots, crops or films.
- Rotated views zoom out 3 or 6 notches so every vertex stays inside the canvas (the
  gate's rule); they are smaller than the default view (e.g. the rectangular pyramid
  fills about 43 % of the canvas height).
- Colour code, for the reviewer: all numerical tiers are readouts in the six
  families, so the tier colours appear in the readout row only (target = blue outline,
  given = dark orange, intermediate = light orange). A drawn object selected in the
  canvas is dark orange (`MAU_TANG.dich`). The two never co-occur in one state, but
  dark orange means "target" in the canvas and "given" in the readout.
- `ISSUE-ARCH-LLM-ROUTE-LENGTH-NOT-TEXT-GROUNDED` (found here, pre-existing): on the
  LLM route a length present only in an analyze fact can ground a GIVEN height; the
  compiler route fails closed. Probe log in `diagnostics/logs/`.
- Offline demo samples are stale (`ISSUE-OPS-OFFLINE-SAMPLES-STALE`); the main-tree
  `dist/` cannot be rebuilt (`ISSUE-OPS-DIST-ACL-OWNERSHIP`).
- Lines are still 1 physical px (WebGL ignores `linewidth`); visibility is classified
  per solid.
- Temporary directories outside git: `D:/tmp/w11-d1` (measurement worktree),
  `D:/tmp/w11-before` (deregistered; delete refused), `D:/tmp/w11-gen`,
  `D:/tmp/w11-attempt1`, `D:/tmp/w11-*.log`, `D:/tmp/w11 space/algo-sim` (T3
  worktree, still registered).

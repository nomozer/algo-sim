# exact-dimensions — report

Run metadata: `run.json`. Plan, limit table and options written before the change: `plan.md`. Labels before the
change: `labels.json` (+ dated `label_corrections.json`). Independent oracle: `oracle.py`.

## 1. Domain

| | before (product 1e90ca0e) | now (product ed3ae208) |
|---|---|---|
| regular triangular pyramid, rational / fractional / decimal base + height (b=6, h=4 → V = 12√3; b=3/2, h=5/3 → 5√3/16; b=2,5, h=6 → 25√3/8) | refused `TEMPLATE_NOT_REPRESENTABLE T8` | **served** |
| base + lateral edge (b=6, l=5 → 3√39); "tất cả các cạnh bằng 4" (16√2/3) | refused | **served** |
| regular tetrahedron, rational edge (a=6 → V = 18√2, height 2√6; a=5/2 → 125√2/96) | refused | **served** |
| previous radical cases (b = 3√2, h = √3 → 9/2; b = 2√3, h = 2 → 2√3) | served | served, byte-identical (identity metric) |
| vertex renames (M.NPQ), "khối chóp … cạnh đáy 6 và chiều cao 4", height given as SG with G the centroid | — | served |
| any affinely independent program chart (axis chart, rough Euclidean chart, the old tilted frames, apex drawn over a vertex) | only the tilted frames | served — the layout is not a hypothesis |
| missing height / size; contradictory sizes (b, l, h inconsistent; SA ≠ SB); lateral ≤ b/√3; zero base; wrong centroid identity; non-regular text with equal laterals | refused | refused (same reasons; N08 reason corrected, `label_corrections.json`) |
| symbolic sizes (`a`, `2a`); sums of radicals (`1 + √2`) | refused | refused |

Corpus: 31 rows (18 served, 11 refused, 2 out of domain); oracle agrees 18/18 on the served values. Route tests:
`tests/geometry/test_exact_dimensions.py`, `test_source_length_reader.py`, `test_regular_triangular_pyramid.py` —
138 passed. Bug found by the corpus and fixed first: the source-length reader took the first term of an expression
("cạnh đáy bằng 4 + 1" was served V = 16; now refused) — `CACHE_VERSION` 117 (`cache/decision.json`).

## 2. Representation and callers

The program's coordinates are an **affine chart** (ℚ³, unchanged); lengths come from a rational Gram matrix G
(|v|² = vᵀGv), solved once from the four chart vertices and the six edge lengths the text fixes. Affine operations
(midpoint, division, intersections, centroid, sections) need no change; metric operations read G. With G = I every
expression is the previous one byte for byte. Proof and exactness argument: `plan.md` §3 and the module docstring.

| piece | file | role |
|---|---|---|
| metric | `backend/app/simulation/geometry/metric.py` (`Metric`, `using`, `gram_from_lengths`, `require_euclidean`, `dot`, `norm_sq`, `normal_vector`, `plane_covector`, `conorm_sq`, `area_sq_from_cross_sum`, `volume_det_factor_sq`) | one shared authority; G positive definite (Sylvester) and checked against the six edges |
| sizes from the text | `assumption_gate.kich_thuoc_t8`, `do_luong_cua(de, prog)` | b², h², l² from T8's reader; G only when the family, the sizes and an affinely independent chart are all present, else `None` |
| callers | `semantic_program/route.py` (`_sau_grounding`), `ai/pipeline.py` (`_dung_scene3d`), `assumption_gate._chay` / `danh_gia_doc_lap` | the same metric for verification, compile and the scene |
| metric-aware ops | `kernel.py` (projections, ⊥ plane), `predicates.py` (⊥), `measure.py` (distances, cos, area), `geometry_exec.volume_polyhedron` (× √det G), `quantity_annotations`, `display_names` | curved solids and the fan/tetra volume helpers refuse a non-Euclidean chart |
| scene | `ai/pipeline._dung_scene3d` adds `chart_metric` (only when G ≠ I); `frontend/src/simulations/domains/geometry/scene3d-chart.ts` maps the chart to world once (Cholesky T, display rounding only at the boundary); `scene3d-view.tsx` reports model = rotation · T | the renderer draws the true figure |

Unchanged: DSL/IR, JSON output schema, prompts, grammar card, capability hash, `LLM_ONLY`. GIVEN sizes stay traceable
to the text; G and every metric value are DERIVED from them. Identity is never decided by comparing coordinates.

## 3. Checks and limits of the evidence

- Offline only: **0 model calls**. The evidence shows the deterministic route serves these sizes for LLM-style
  programs written in tests and fixtures; it does **not** show that the model extracts them or lays the figure out
  this way (`ISSUE-ARCH-REGULAR-TRIANGULAR-MODEL-LAYOUT-UNMEASURED`, still open).
- Browser (family `regular_triangular_pyramid`, base 6 / height 4 on the axis chart): suite **7/7** (2 positives —
  desktop, mobile — 4 refusals, tetrahedron edge 6 served 18√2), scene controls 2/2, panels 3/3 (desktop, low,
  mobile), focus mode 3/3, occlusion PASS, playback 2/2 (lap-orbit 5), 4 hidden-edge crops with every endpoint inside.
  Orbit prediction error 2.6e-9 (desktop) / 3.3e-7 (mobile).
- Three attempts, all kept (`diagnostics/attempt1–3`). Attempts 1 and 2 failed on **harness** defects, not the
  product: the harness read a chart scene through a non-orthogonal model matrix as if it were a rotation, then handed
  world-space numbers to the product's fraction parser (`d4834d92`, `2d62f69c`; node test red on the old lib). Only
  the failed steps were rerun. The suite's `failure_class` in attempt 1 says PRODUCT_ASSERTION because the classifier
  only sees a failed assertion; the root cause is recorded in `attempt1/SUMMARY.json`.
- Seven other families not re-measured: payloads byte-identical, renderer untouched without `chart_metric`.
- Known limitation: with a non-Euclidean chart and a missing size the refusal reason is
  `ASSUMPTION_INVARIANCE_UNPROVEN` (cause UNKNOWN), not "the size determines the answer" — honest but less precise
  (`ISSUE-ARCH-MISSING-SIZE-REASON-ON-AFFINE-CHART`).

## 4. Screenshots (same family, same steps — `capture_counts.json`)

| | rtp-w01 attempt 3 | this run (final) |
|---|---|---|
| screenshot calls | 103 | 110 |
| files created by runners | 103 | **11** |
| files created by the builder | 6 | 4 (crops) |
| deleted after capture | 52 | **0** |
| kept | 57 | **15** |

Decided before capture at one place (`capture-policy.mjs`, mode `toi-thieu`): oracle inputs, the review set chosen
before the run (10 items), failure states. Assertions read in-memory frames, so the checks are unchanged. Calls rose
because the two element captures are now counted. Including the failed attempts the run created 41 files and kept 15.

## 5. Names

One living document: `docs/evaluation/RUN_NAMING.md` (top section). Eleven active files/folders renamed in a separate
commit (`0ed6332f`), table there; historical run IDs, schema IDs and evidence file names kept on purpose.

## 6. UI and D5

D1–D4, the orbit-centre fix, panels, labels and hidden lines kept (browser checks above, same probes). **D5 still
open** (`ISSUE-ARCH-MOBILE-CANVAS-WHITESPACE-AND-PANEL-SCROLL`) — the mobile focus image shows it, not a fix.

## 7. Identity

HEAD and the gate: `handoff.md` §1. Product `ed3ae208` · candidate `e1927f84…` · `CACHE_VERSION` 117 · measurement
`3bbb8052` / `fe83c46e` / `d51db4e2` · evidence `c5cae8af`.

# Hybrid V2 — Checkpoint D (Claude resume): exact common perpendicular for skew-line distances

Classification: **VERIFIED_OFFLINE_E2E** for this slice on **authored development cases** (not an independent holdout,
not live extraction). Family 2 of the 18-family matrix (`hai_dt_cheo_nhau`) stays **PARTIAL**.

## Gap closed

Codex's handoff: "skew-distance answer has no rendered common-perpendicular segment". Route D served the exact number
with `ANNOTATION_UNBOUND kq_*: distance between two non-point objects has no registered anchor` — the segment the
answer measures never appeared.

## What was built (commit `1faee1db`)

| layer | change | authority |
|---|---|---|
| kernel | `common_perpendicular_feet(a, b)`: metric-aware 2×2 system; throws unless the lines are skew | geometry kernel (exact ℚ / radicals) |
| annotation | `common_perpendicular` witness: re-checks `PQ ⟂ u`, `PQ ⟂ v` (frame metric) and `|PQ|² = d²`; one mark per foot, `u` toward the nearest named point of its own line (extension drawn when the foot is outside the edge) | `quantity_annotations._nhan_chung_hai_duong` |
| route switch | `build_simulation_state(..., common_perpendicular_witness=True)` only from `function_route` (route D) | explicit; LLM_ONLY default off |
| frontend | `from_point` / `second` through the chart transform (`T·p`) and the existing `scene3d-witness-gate`; fail-closed as a pair; PQ drawn once | renderer only draws |
| marks | a relation's representative mark avoids a foot that already carries an individual mark | `datCoGocVuong` |

No new IR operation, no schema/prompt/provider surface change, no Registry/Planner change (versions unchanged:
`geometry-functions/13`, `geometry-fact-planner/13`, `geometry-function-engine/12`).

## Oracles (worked by hand, different algorithm from the product)

| case | feet | |PQ|² | independent check |
|---|---|---|---|
| AB, SD of S(0,0,2) over the unit square | P = A, Q = (0, 4/5, 2/5) | 4/5 | d(A, SD) in right triangle SAD: SA·AD/SD = 2/√5 |
| prism AA′, BC (AB = 6, AC = 8, AA′ = 12; Gram diag(36, 64, 144)) | P = A, Q = (16/25, 9/25, 0) | 576/25 | altitude of the 6–8–10 right triangle = 24/5 |
| prism AB, B′C | Q = (4/13, 9/13, 4/13) (frame) = (24/13, 72/13, 48/13) | (24/√13)² | n = (1,0,0)×(−6,8,−12) = (0,12,8); |w·n|/|n| = 96/√208 |
| non-skew (parallel DC, meeting AD / BD) | — | — | kernel throws; parallel distance gets no witness |

Fault injection: a recorded distance that disagrees with |PQ| ⇒ no witness. Frontend: a wrong second mark ⇒ neither mark.

## Evidence

- Backend: `test_geometry_kernel.py` 45/45 (5 new), `test_skew_claim_consistency.py` 13/13 (5 new: exact witness,
  parallel → none, default builder byte-unchanged, fault injection).
- Frontend: geometry domain 869/869, full vitest 1414/1414, build PASS.
- Adapter /2 preview fixtures re-exported (`fixtures-adapter-2-common-perpendicular/`, from clean `1faee1db`): 40/41
  differ only in identity (`response_sha256`); `served-H11_SKEW_DISTANCE_COMPOSITION` differs exactly by the removed
  `ANNOTATION_UNBOUND` diagnostic and the added witness. The cache130 bundle is kept unchanged.
- Browser (`common-perpendicular-browser/`, tree `clean`, 60 frames, 0 page errors): AA′–BC, AB–B′C, H11 (foot on the
  extension of AM) × Mode A/B × 5 orbit gestures × 1440/390.
- `CACHE_VERSION` **NO_BUMP 130** — locked by `test_the_default_scene_builder_is_unchanged_without_the_route_d_switch`;
  candidate refrozen (`96415cbd`, `3850e787…`, 118 files) and declared (`../inputs/candidate_divergence.json`).

## Still missing for replacing LLM_ONLY

Non-right angle arcs (cos² is served, no arc), four-label measurement targets (refused), curved/composite/coordinate
bridge goals, independent NL extraction quality (UNKNOWN), independent holdout, independent review, Owner visual
approval, shadow/canary/rollback evidence and the 20-gate migration checklist. Enabling this witness on LLM_ONLY needs a
cache bump decision.

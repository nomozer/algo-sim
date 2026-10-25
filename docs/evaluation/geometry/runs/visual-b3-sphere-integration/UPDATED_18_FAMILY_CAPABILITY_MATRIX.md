# 18-family capability matrix — update on the integrated candidate

Base: Codex's `visual-closure-hybrid-readiness/HTML_18_FAMILY_CAPABILITY_MATRIX.md` (reference HTML sha256
`279216192b09d6e1…`; columns: V2 facts, Source gate, Registry, Planner, Exact engine, Adapter /4, Frontend, Browser, New
problem). That file is unchanged. Only cells with new evidence on `integration/visual-b3-sphere-candidate` change.
Legend as there: F = FULL_E2E_VERIFIED, O = OFFLINE_GEOMETRY_VERIFIED, R = RENDER_ONLY, P = PARTIAL,
U = UNSUPPORTED, ? = UNKNOWN.

## Cells that changed

| # | HTML family | Cell | Was | Now | Evidence |
|---|---|---|---|---|---|
| 12 | Lăng trụ đứng ABC.A′B′C′ | Adapter /4 (distance goals) | — (refused `BRIDGE_UNSUPPORTED_MEASUREMENT`) | O | B3 bridge; 43 bridge tests (closed-form oracles); /4 envelope checked |
| 12 | Lăng trụ đứng | Browser (distance goals) | P | O — offline authored, desktop + mobile | `b3-distance-browser-e2e` D1, D2 |
| 13 | Lăng trụ xiên | Adapter /4 (distance goals) | — | O | oblique-prism tests (normal component ≠ lateral edge) |
| 13 | Lăng trụ xiên | Browser (distance goals) | P | O — offline authored, desktop + mobile; witness on the answer drawn | D3 |
| 14 | Mặt cầu giao mặt phẳng | Frontend | R | R (source-correct sample) | sample shows only I, R, (S), (P), circle; (P) visible; no decorative loops; tangent / no cut are typed refusals, never a clamped circle |
| 16 | Hình trụ, thiết diện | Frontend | R | R (source-correct sample) | invented rim point removed; perpendicular cutting plane kept visible |
| 1, 2, 3–6, 11 | relations / skew lines / pyramids / cuboid | Adapter /4 (distance goals) | — | ? | same planner functions, **not tested** on these shapes in this pass |

## Overall classification

Unchanged: **0 FULL_E2E_VERIFIED, 9 PARTIAL, 7 RENDER_ONLY, 2 UNSUPPORTED.**

- No complete HTML configuration became FULL_E2E. Distance goals are one part of the prism configurations.
  Extraction is not measured (authored TypedFacts). Angle goals, circumscribed/inscribed spheres and sections remain
  partial.
- Curved families stay RENDER_ONLY for Hybrid: the V2 bridge still refuses curved solids (`BRIDGE_UNSUPPORTED_CURVED`).
  The sphere fix corrects the offline LLM_ONLY sample and a default-route formation role. It does not open curved
  solids to Hybrid.

## Known gaps exposed in this pass

- Skew-line distance is served without a common-perpendicular witness (engine provides none).
- A false "chéo nhau" claim in the source is not checked (review I-2; open, needs a contract decision on
  `ask_distance_lines`).
- Four-label plane targets are refused by contract; extractors must give three labels.

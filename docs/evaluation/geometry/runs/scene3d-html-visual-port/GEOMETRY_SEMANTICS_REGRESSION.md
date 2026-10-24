# Geometry semantics regression

Scope of change: `3bfc8dd0..852f6501` (product commits `60b556bc`, `656759fc`, `852f6501`), 10 files, all under `frontend/` (0 backend files). No change to scene objects, coordinates, provenance, topology, construction order, certificates, Adapter /4 parsing, store, or the LLM_ONLY route.

## What stayed authoritative (unchanged code paths)

- Hidden/visible classification: `classifySolidEdgeVisibility` and per-span CPU occlusion. The reference face-normal heuristic is not ported.
- Section polygons, plane patches, intersection points: engine data only. Plane patch shape is data-derived (`daGiacMatPhang`).
- Point identity: labels print only backend notation (`kyHieu`). Role classes are presentation only. `diemTaiDinhThietDien` matches exact rational coordinate strings, the same rule as `deriveSectionSubEntities`. No name is invented.
- Coincident points: merged label (`A ≡ H ≡ H1`) unchanged; duplicate right-angle marks at the same foot and direction pair are hidden, not deleted (the points remain).
- Renderer boundary guard `(5D) ranh giới: renderer không suy luận hình học` (no `distanceTo`/cross/dot in the view) passes. Marker sizing uses camera view depth only.

## Test changes and why (no semantic assertion weakened)

| Test | Change | Reason |
|---|---|---|
| `scene3d.test.tsx` triangle collector | Skip the back shell pass (`userData.voKhoiMatSau`) | Same geometry drawn twice (`side` only); identical rationale to the existing depth-layer skip. Projected-area / overlap / face-count assertions unchanged |
| `scene3d.test.tsx` new "SGK: ký hiệu vuông góc…" | Added | 10.08 px leg at 720 px, legs orthogonal on screen, duplicate hidden, corner updated; pure orbit keeps size, zoom recomputes; world-space duplicate key, strongest mark wins. Fault-injected 4× (px factor, orbit cache, first-wins, local key) → red |
| `scene3d-causal-colors.test.tsx` `mauNen` | Find shell as transparent `MeshBasicMaterial` | Shell is unlit; neutral-hue assertion unchanged |
| `simulation-coverage-fixes.test.tsx` | `opacity ≥ 0.28` → `=== DO_DUC_TO_THIET_DIEN` and `≥ 0.32` | Single authority plus the floor that passes the section-fill gate |
| `simulation-visual-consistency-session1.test.tsx` | Hex/opacity literals → `PHONG_CACH_SCENE3D` constants; shell = FrontSide + BackSide(0.75×); plane border dashed and visible with a closed section, also after the span pass (fault-injected → red) | Owner-requested palette and plane-border behaviour; "curved = polyhedral palette", "section ≠ base color" and "fat-line hierarchy section > edge > hidden" assertions retained |

## Machine results at `852f6501` (source tree identical to the commit)

| Gate | Result |
|---|---|
| `tsc -b` | 0 errors |
| Vitest (full frontend) | 76 files, 1195 / 1195 |
| `npm run build` | PASS |
| `scene3d-orbit-gate` p1/p6/p7 | **DAT**, `capPhat = 0`, snap 0, 449° orbit. The owner's V6.2 checkpoint failed this gate (p1 312, p6 662 allocations); root causes fixed: Line2 `setPositions`/`computeLineDistances` per span change; curved-rim `BufferGeometry` per view change |
| Section-fill distinguishability probe (gate's own `deltaE76` + thresholds, final step, 6 scenes; obstacles excluded as in the gate) | PASS, mean ΔE76 20.42–20.44, min ≥ 20.41 at fill 0.32 (0.27: 16.9–17.2 FAIL). Measured before `656759fc`/`852f6501`, which change only marks, labels and tests, not the fill. The official `compiler-scene-suite` measures the first closed-and-filled step and requires a suite manifest bound to a frozen candidate; it was not run (see FINAL_OWNER_HANDOFF) |

Full T3 and post-freeze verification: see FINAL_OWNER_HANDOFF.md.

# Right-angle marker validation

Owner-confirmed defect: right-angle markers were too large. Root cause: both builders sized marks in **world** units. The segment-witness mark used `clamp(0.22·|segment|, 0.12, 0.35)`, and on the SA segment of `CORPUS-DEV03` it drew ≈ 30 × 60 px (pre-port capture). The reference uses world size 0.34–0.36, which is ≈ 36 px at its own default framing.

## Design

| Requirement | Implementation |
|---|---|
| Two-segment square like the HTML | `dauGocVuong`: `foot + s·u → foot + s·(u+v) → foot + s·v` |
| Directions certified by backend | Segment marks: `u`, `v` from `perpendicular_witness` / `annotation.witness`, existing orthogonality check (`|u·v| ≤ 1e-4·|u||v|`) kept. Distance/projection witness marks: the backend witness directions via the existing `huongChanVuongGoc`, unchanged. Only the size is new |
| Adaptive to camera, viewport and related edge | `datCoGocVuong`: target leg = 0.014 × canvas height, clamped to **8–12 px**, converted with each foot's view depth and the camera FOV; world size capped at 0.3 × the related segment (`maxLegRatio`) |
| Must not cover labels or edges | Cap above keeps the mark inside its segment; label placement already avoids marks (`gocVuongPts` → `tinhViTriNhanDiem`); `corner` is refreshed with the scale |
| Several marks in one figure | Duplicates (same world foot and direction pair) are hidden; the strongest (non-faded) mark wins (review I1) |
| Orbit and zoom | Recomputed on zoom/refit/resize/parent move; **frozen during a pure orbit**, so no coordinates are rewritten (orbit gate `capPhat = 0`) |

## Measurements (browser, real mouse drag and wheel, freeze commit `13d28b84`, `verification/right-angle/receipt.json`)

Three scenes (PERP-square-third, CORPUS-DEV03, CORPUS-DEV10 prism), 1440×900 and 390×844, 14 visible marks per state.

| State | Longer on-screen leg (px) | World size vs. target (non-orbit) |
|---|---|---|
| Default fit | 6.7–10.1 | 0.998–1.007 |
| After orbit drag (~30°) | 8.3–14.6 | frozen by design |
| Wheel zoom in | 7.1–10.5 | 0.998–1.007 |
| Wheel zoom out | 6.5–10.2 | 0.998–1.007 |

The world size hits the 8–12 px target at the foot's depth, within ±0.7 %. The visible length can still read below 8 px. That happens because a leg lying in a plane tilted to the view is foreshortened by perspective. For example, a leg along the base seen at the SGK elevation 22° shows only ~40–60 % of its length. The reference has the same effect.

While orbiting, sizes drift with depth until the next zoom or refit. The worst case measured was 14.6 px, after a large drag that brought the foot toward the camera. This trade-off keeps orbit free of GPU allocation.

Unit test `scene3d.test.tsx` "SGK: ký hiệu vuông góc…" locks the following:
- 10.08 px legs and on-screen orthogonality;
- hidden duplicates and the corner update;
- orbit keeps size, zoom recomputes;
- world-space dedupe with strongest-wins.

It was fault-injected 4 times, red each time.

## Limits

- No per-leg foreshortening compensation. Compensating would distort the mark's geometry.
- One mark per foot and direction pair; marks with different direction pairs at the same foot are all kept.
- Mobile canvases below ~570 px tall use the 8 px floor.

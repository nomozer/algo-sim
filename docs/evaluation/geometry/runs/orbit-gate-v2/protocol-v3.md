# Orbit gate v3: pre-registered protocol

Registered 2026-10-11, **before** any v3 code or measurement.

v2 ([protocol.md](protocol.md), results in `results/`) failed its own pre-registered validation:
- **What failed:** the historical known-good build classified `TRUC_TROI` (axis consistency 0.960–0.977 < 0.99); p1/p7 on `main` timed out as `KHONG_ON_DINH`.
- **What worked:** rotation was measured correctly (449–450°), and both known-bad injections were refused with their declared status.
- **Why** (two instrument defects that v2's settle wait exposed):
  1. **Unweighted axis average.** `trucQuay` averages one unit axis per frame pair without weights. The settle wait admits hundreds of near-static damping-tail frames whose float32 axes are noise, and they count as much as real rotation.
  2. **Settle criterion too strict.** Relative view-matrix motion ≤ 1e-9 within 10 s is stricter than OrbitControls' geometric damping decay reaches at this machine's frame rate.

The user chose to register v3 (2026-10-11). v2 stays on record as failed; nothing of v2 is rescored.

## Gate identity

`GATE_VERSION = "scene3d-orbit-gate/3"`. Results go under `docs/evaluation/geometry/scene3d-orbit-gate/v3/` by default.

## Changes from v2 (only these)

| Item | v2 | v3 |
|---|---|---|
| Axis consistency (`trucQuay`) | mean of unit axes, unweighted | **angle-weighted**: `vec = Σ θᵢ·uᵢ / Σ θᵢ`, `chuan = ‖vec‖`, θᵢ = rotation angle between consecutive recorded poses (same formula as `tongGocKhung`). A frame pair contributes in proportion to how much it rotates |
| Settle criterion | `settleCamera` (relative matrix motion ≤ 1e-9, 5 samples, ≥ 30 frames, 10 s) | every recorded pose carries its animation-frame number; settled when, over the last **30 animation frames**, every per-frame rotation is **< 0.01°** (frames with no new pose count as 0°). **Budget 20 s**, timeout ⇒ `KHONG_ON_DINH` |

## Unchanged from v2

- Drag `round(1.25 × clientHeight)`.
- `KHUNG_HEP`.
- `NGUONG` (360°, 0.99, 0.9, 25°).
- Classification order.
- Fixtures, viewport, vertical drags, still window.

## Validation (same five builds as v2) and expected outcomes

| Build | Expected |
|---|---|
| historical `eb6d7d5a` (known-good) | `DAT` ×3 |
| injection `chan-phuong-vi` (known-bad) | `KHONG_DU_VONG` ×3 |
| injection `khong-on-dinh`, `autoRotate` (known-bad) | `KHONG_ON_DINH` ×3. Default `autoRotateSpeed` 2 is about 12°/s, far above 0.01°/frame |
| `main` `28ac1d61` | observed. p1 showed `cấp phát` 93–111 during orbit under v1/v2 (historical: 0), so `TU_KHOP_KHUNG` on p1 is possible and would be a **product** finding |
| candidate (branch HEAD) | same as `main` |

## Stop rule

If the known-good build is not `DAT` ×3, or an injection is not refused with its declared status, then v3 is not trusted either and **no v4 is attempted in this wave**. The orbit gate is then reported as having no validated instrument.

Parameters are not changed after seeing v3 results.

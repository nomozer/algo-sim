# Orbit gate v2: pre-registered protocol

Registered 2026-10-11, **before** implementation or any v2 measurement. The user approved the direction: drag proportional to canvas height, condition-based settle with a timeout, 360° kept, a new gate identity, no rewrite of history.

## Why

v1 (`scene3d-orbit-gate.mjs`, results in `docs/evaluation/geometry/scene3d-orbit-gate/`, unchanged) has two problems:

1. **Fixed drag length.** One horizontal drag is 700 px. OrbitControls rotates `2π·dx/clientHeight`, so on today's 683 px canvas (545 px when v1 was calibrated) a full drag nominally gives only 369°.
2. **Fixed read time.** The gate reads 250 ms after release, while damping is still running, which drops another 24–33°.

Evidence: [`final-integration-gates/report.md`](../final-integration-gates/report.md) §1.

## Gate identity

- **Version:** `GATE_VERSION = "scene3d-orbit-gate/2"`, recorded in every result file.
- **Results:** written under `docs/evaluation/geometry/scene3d-orbit-gate/v2/` by default. v1 files are never overwritten.

## Changes (only these)

| Item | v1 | v2 |
|---|---|---|
| Horizontal drag (steps ②, ③) | 700 px | `round(1.25 × canvas clientHeight)` px. That is 450° nominal by OrbitControls' own definition, a fixed margin above 360° |
| Wait after each drag | `sleep(250)` | `settleCamera` from `compiler-scene-replay-lib.mjs`, reused: the last recorded view matrix unchanged (relative motion ≤ 1e-9) for 5 samples spanning ≥ 30 animation frames, **timeout 10 s** |
| Settle never reached | n/a | named status `KHONG_ON_DINH` (fail) |
| Drag does not fit inside the canvas (`dx > width − 40`) | n/a | named status `KHUNG_HEP` (fail), never clipped silently |
| Hook | `__QUAY__` | plus an animation-frame counter `raf` (for the settle window) |

## Unchanged

- **Thresholds:** `NGUONG` exactly as in v1: `VONG_NGANG_DO = 360`, `CHUAN_TRUC = 0.99`, `COS_CUC = 0.9`, `SNAP_DO = 25`.
- **Classification:** order and all other statuses, including the allocation check (`TU_KHOP_KHUNG`), snaps, axis drift and view coverage.
- **Setup:** vertical drags, the still window (①), viewport 1440×900, fixtures p1/p6/p7.

## Validation plan and expected outcomes (declared now)

| Build | Expected | Why |
|---|---|---|
| historical `eb6d7d5a` (known-good window) | `DAT` (p1, p6, p7) | passes v1 today; v2 must not be stricter on what v1 accepted |
| injection `chan-phuong-vi`: current source + `minAzimuthAngle = −π/2`, `maxAzimuthAngle = π/2` (known-bad) | `KHONG_DU_VONG` | an azimuth wall must still fail |
| injection `khong-on-dinh`: current source + `autoRotate = true` (known-bad) | `KHONG_ON_DINH` | a camera that never settles must not pass |
| `main` `28ac1d61` | **observed, not tuned** | v1 runs showed `cấp phát = 93` on p1 during orbit (historical build: 0). If v2 measures rotation correctly, p1 may classify `TU_KHOP_KHUNG`. That would be a product finding to investigate, not a reason to change the gate |
| candidate (branch HEAD) | same as `main` for p1/p6/p7 (identical renderer for these fixtures) | |

**Stop rule:** if the known-good window is not `DAT`, or either known-bad injection is not refused with its declared status, v2 is not trusted. Report it; do not adjust parameters after seeing results.

## Out of scope

- Rescoring v1 results.
- Changing `NGUONG`.
- Changing the product renderer to satisfy the gate.

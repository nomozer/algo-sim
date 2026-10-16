# Handoff — `scene3d-architecture-visual-reliability` (W1–W3 Implementation)

- **Status:** `SCENE3D_ARCHITECTURE_IMPLEMENTATION_READY_FOR_REVIEW`
- **Issue:** `ISSUE-ARCH-SCENE3D-CONSTRUCTION-READABILITY`
- **Branch:** `research/scene3d-visual-parity-audit`
- **W0 Baseline Commit:** `f83b4ed14995c89d6cf00a643cd14c814c78004c`
- **W0 Audit Commit (Start Base):** `4b51fde81e79a7caf7bd4dbd69cfca266cabaa8e`

## 1. What Was Accomplished in W1–W3

1. **Resolved All 2 CRITICAL, 5 IMPORTANT, and 2 NONBLOCKING W0 Findings (`results/findings.json`):**
   - **`FINDING-B1` (`CRITICAL` — `scene3d-chart.ts`):** `veKhongGian` now transforms `o.perpendicular_witness` (`foot` and orthonormal `marker.{dinh, u, v}`) alongside `o.annotation.witness` and is idempotent via `_daVe = new WeakSet<Scene3D>()` while keeping `chart_metric` intact for `maTranKhung4`. World-space displacement between `H.perpendicular_witness.foot` and `H.xyz` dropped from `0.668–1.000` units to **`0.0`** across all 11 audited fixtures (`results/math_and_readability_oracle.json`).
   - **`FINDING-B2` (`CRITICAL` — `scene3d-auxiliary.ts`, `scene3d-view.tsx`):** Excluded `line3` target carriers referenced by `o.perpendicular_witness.on` (`duongChieu`) from disposable `loai: "dung"`, so `gt_g` and `derived_H_line` remain visible at the final step under default `aux=0` while `mp1_gt_g` and `mp2_gt_g` hide. Classified off-solid translated auxiliary points (`point3` with `vector3` dependency whose non-sub-entity semantic dependents `!x.parent` are all `plane3`) as `loai: "dung"`, hiding `H` and `H1` in `two-line-*` at the final step under `aux=0` and filtering `!anPhu.has(o.id)` in `coMatNhan`, `diemNen`, and `nhanDiem`.
   - **`FINDING-D1`..`D4` (`IMPORTANT` — `hybrid-section-visual.tsx`, `result-binding-visual-check.mjs`, `scene3d-view.tsx`):** Enabled `withSubEntities(daVe, objectsAt)` by default in `hybrid-section-visual.tsx`, added `Bước học` learner step selector + `Hình phụ` toggle, updated `result-binding-visual-check.mjs` to test default `aux=0` before `aux=1`, rendered unselected `face` sub-entities as transparent raycast hit proxies (`display_role: "hit_proxy"`), and gated section sub-entities (`td::face:0`, `td::edge:i`, `td::vertex:i`) on parent `geometry_progress` while deduplicating coincident section vertex markers.
   - **`FINDING-C2` (`IMPORTANT` — `scene3d-model.ts`, `scene3d-view.tsx`):** Scoped `surface` plane patch sizing to defining points / section vertices on the plane, removed the `PLANE_PATCH_MIN_SIZE` floor when `banKinh > 0` in `khungMatPhang`, and lowered passive `surface` plane opacity from `0.16` to `0.10`.
   - **`FINDING-E1` (`IMPORTANT` — `scene3d-presentation.ts`, `scene3d-view.tsx`, `hybrid-section-visual.tsx`):** Added `kyHieuDiem` to combine coincident visible point labels into `"B ≡ H"` (`0` label overlaps) and fixed selection details fallback (`o.label || o.notation || o.id`).
2. **Reconciled W0 Metadata (`11/11` Cases):**
   - Both `results/math_and_readability_oracle.json` and `results/parity_telemetry.json` cover all **11** locked fixtures (`section-MAB-trapezoid` included in both).
3. **Full Test & Browser Verification (`0` Live AI Calls):**
   - RED receipt: `red/vitest-red.txt` (6 failing assertions).
   - GREEN receipts: `results/vitest-green.txt` (`68` files / `1061` tests passed), `results/pytest-green.txt` (`7758` backend geometry tests passed), `results/result-binding-check/receipt.json` (`PASS_CORE_CAUSAL_RENDERING`), `results/parity_telemetry.json`, and `results/before_after_comparison.json`.

## 2. Next Step

Run an **independent code review** on branch `research/scene3d-visual-parity-audit` inspecting the 5 modified frontend product files (`scene3d-chart.ts`, `scene3d-auxiliary.ts`, `scene3d-presentation.ts`, `scene3d-model.ts`, `scene3d-view.tsx`), 3 harness files (`hybrid-section-visual.tsx`, `result-binding-visual-check.mjs`, `hybrid-section-visual-check.mjs`), 4 test files, and the `scene3d-architecture-visual-reliability` evidence package before candidate refreeze and authoritative T3.

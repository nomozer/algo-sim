# ALGOSIM — SCENE3D ARCHITECTURE & VISUAL RELIABILITY IMPLEMENTATION (W1–W3)

- **Run ID:** `scene3d-architecture-visual-reliability` (`scene3d-architecture-visual-reliability-w01`)
- **Resolves Baseline Audit:** [`scene3d-visual-parity-audit`](../scene3d-visual-parity-audit/report.md) (`4b51fde81e79a7caf7bd4dbd69cfca266cabaa8e`, W0 baseline `f83b4ed14995c89d6cf00a643cd14c814c78004c`)
- **Issue Addressed:** `ISSUE-ARCH-SCENE3D-CONSTRUCTION-READABILITY`
- **Status:** `SCENE3D_ARCHITECTURE_IMPLEMENTATION_READY_FOR_REVIEW`
- **Branch:** `research/scene3d-visual-parity-audit` (`main` untouched at `2a3c0787cc35d2e5530d77658225039ab4c5991e`)
- **Backend / Kernel / Planner / Ask-Grammar Changes:** `0` files modified
- **Live Model Calls:** `0` (`ALLOW_LIVE_AI=0`)

---

## 1. W0 Root-Cause Verification & Metadata Reconciliation

1. **W0 10/11 Case Count Reconciliation:**
   - In W0 (`scene3d-visual-parity-audit`), `results/parity_telemetry.json` audited **11** locked fixtures while `results/math_and_readability_oracle.json` audited **10** fixtures (omitting `section-MAB-trapezoid`).
   - In this implementation wave (`scene3d-architecture-visual-reliability`), both [`results/math_and_readability_oracle.json`](results/math_and_readability_oracle.json) and [`results/parity_telemetry.json`](results/parity_telemetry.json) audit all **11** locked fixtures identically (`all_cases_math_pass: true`, `zero_orphan_witness_targets: true`).
2. **Independent Code Verification of W0 Root Causes:**
   - Verified every W0 root cause directly in the frontend TypeScript/React source before editing:
     - **`FINDING-B1` (`scene3d-chart.ts:62-75`):** `doiDoiTuong(o, T)` transformed `o.annotation.witness` via Cholesky factor $T$ ($T^T T = G$) but omitted `o.perpendicular_witness`, leaving `o.perpendicular_witness.foot` and `marker.{u,v}` in raw chart coordinates while `o.xyz` was in world coordinates. Furthermore, `veKhongGian` was called in both `Scene3DExplorer.tsx:207` and `Scene3DWorkspace` (`scene3d-view.tsx:1777`) while preserving `chart_metric` for `maTranKhung4`, requiring idempotency via a `WeakSet<Scene3D>()` so $T$ is applied exactly once.
     - **`FINDING-B2` (`scene3d-auxiliary.ts:35-61`):** `auxiliaryObjects(scene)` classified any `line3` with `origin === "derived"` and single role `CONSTRUCT_AUXILIARY_GEOMETRY` that had a non-quantity dependent (`H`) as disposable (`loai: "dung"`), hiding the target carrier line (`gt_g` or `derived_H_line`) at the final step under default `aux=0` while `H` and `perpendicular:H` stayed visible. Conversely, `auxiliaryObjects` skipped `point3` objects, so off-solid translated auxiliary points (`H`, `H1` in `two-line-pyramid`, `two-line-prism`, `two-line-cuboid`) never hid after their dependent cutting plane `(P)` was constructed. Crucially, when `withSubEntities` ran, synthetic section vertices (`td_q::vertex:i` with `parent: "td_q"`) depended on `H`/`H1`, so `auxiliaryObjects` must filter `!x.parent` when inspecting semantic dependents of `point3`.
     - **`FINDING-D1`..`D4` (`Scene3DExplorer.tsx` vs `hybrid-section-visual.tsx` & `scene3d-view.tsx`):** `hybrid-section-visual.tsx` omitted `withSubEntities`, lacked a learner-step (`Bước học`) selector and `Hình phụ` toggle, and `result-binding-visual-check.mjs` hardcoded `&aux=1`. In `scene3d-view.tsx`, unselected `face` sub-entities rendered as visible translucent meshes (double-tinting solids), `td::face:0` rendered on the first section edge step before polygon closure, and `td::vertex:i` duplicated already-named points (`M`).
     - **`FINDING-C2` & `FINDING-E1` (`scene3d-model.ts`, `scene3d-view.tsx`, `scene3d-presentation.ts`):** `khungMatPhang` enforced a `PLANE_PATCH_MIN_SIZE = 2.5` floor even when `banKinh > 0`, `surface` planes sized across all solid vertices at `0.16` opacity, coincident points `B` and `H` rendered separate labels, and `hybrid-section-visual.tsx` formatted `o.label` without falling back to `o.notation || o.id`.

---

## 2. Summary of W1–W3 Architectural & Readability Changes

| Wave | Scope | Files Modified | Exact Changes Implemented |
|---|---|---|---|
| **W1** | Chart-Metric Witness Mapping, Target Carrier Persistence & Product–Harness Parity | `frontend/src/simulations/domains/geometry/scene3d-chart.ts`<br>`frontend/src/simulations/domains/geometry/scene3d-auxiliary.ts`<br>`frontend/src/simulations/domains/geometry/scene3d-view.tsx`<br>`frontend/scripts/hybrid-section-visual.tsx`<br>`frontend/scripts/result-binding-visual-check.mjs`<br>`frontend/scripts/hybrid-section-visual-check.mjs` | 1. Extracted `nhanChung(w, T)` in `scene3d-chart.ts` to transform both `o.annotation.witness` and `o.perpendicular_witness` (`foot` and orthonormal `marker.{dinh, u, v}`), and guarded `veKhongGian` with `_daVe = new WeakSet<Scene3D>()` so repeated calls are idempotent while preserving `chart_metric` for `maTranKhung4`.<br>2. Excluded `line3` objects referenced by any `o.perpendicular_witness.on` (`duongChieu`) from disposable `loai: "dung"` in `scene3d-auxiliary.ts`, keeping `gt_g` and `derived_H_line` visible at the final step under default `aux=0` while `mp1_gt_g` and `mp2_gt_g` hide.<br>3. Enabled `withSubEntities(daVe, objectsAt)` by default in `hybrid-section-visual.tsx`, added `Bước học` learner step selector + `Hình phụ` toggle, and updated `result-binding-visual-check.mjs` to assert `aux=0` target/foot visibility and plane hiding before toggling `aux=1`.<br>4. Assigned `display_role: "hit_proxy"` to unselected `face` sub-entities when their parent solid/section is rendered (`colorWrite: false, depthWrite: false, opacity: 0`), eliminating solid face double-tinting while preserving face raycasting. |
| **W2** | Off-Solid Auxiliary Point Lifecycle & Plane Patch Framing | `frontend/src/simulations/domains/geometry/scene3d-auxiliary.ts`<br>`frontend/src/simulations/domains/geometry/scene3d-model.ts`<br>`frontend/src/simulations/domains/geometry/scene3d-view.tsx` | 1. Classified off-solid translated auxiliary points (`point3` with `origin === "derived"`, single role `CONSTRUCT_AUXILIARY_GEOMETRY`, no `perpendicular_witness`, `vector3` dependency, and all non-sub-entity semantic dependents `!x.parent` of type `plane3`) as `loai: "dung"` (`xongTai` = step of the plane), hiding `H` and `H1` in `two-line-*` at the final step under `aux=0`.<br>2. Filtered `!anPhu.has(o.id)` in `coMatNhan`, `diemNen`, and `nhanDiem` in `scene3d-view.tsx`.<br>3. Scoped `surface` plane patch sizing (`diemMp`) to finite defining points or section vertices on the plane when $\ge 3$ points exist, removed the `PLANE_PATCH_MIN_SIZE` clamp when `banKinh > 0` in `khungMatPhang` (`scene3d-model.ts:905`), and reduced passive `surface` plane opacity from `0.16` to `0.10`. |
| **W3** | Progressive Section Sub-Entities, Coincident Point Labels & Selection Hygiene | `frontend/src/simulations/domains/geometry/scene3d-presentation.ts`<br>`frontend/src/simulations/domains/geometry/scene3d-view.tsx`<br>`frontend/scripts/hybrid-section-visual.tsx` | 1. Gated section sub-entities (`td::face:0`, `td::edge:i`, `td::vertex:i`) on parent `geometry_progress` (`progressCha.closed && progressCha.fill_visible`, `visible_edge_ids`) and skipped unselected `::vertex:i` markers that coincide with already-rendered named points.<br>2. Added `kyHieuDiem(o, tatCaDiem)` in `scene3d-presentation.ts` to combine coincident visible points ($\le 10^{-3}$ world units) into `"B ≡ H"` without duplicate DOM badge overlap.<br>3. Updated selection details in `hybrid-section-visual.tsx` to `[o.label \|\| o.notation \|\| o.id, o.role].filter(Boolean).join(" · ")`. |

---

## 3. Product vs. Harness Parity Before / After Table

All measurements come from [`results/parity_telemetry.json`](results/parity_telemetry.json) and [`results/before_after_comparison.json`](results/before_after_comparison.json) (`console_errors: 0`, `page_errors: 0`):

| Case ID | W0 Sub-Entities Only in Product (`aux=0`) | W1–W3 Sub-Entities Only in Product (`aux=0`) | W1–W3 `same_all_rendered_objects` (Product vs Harness `aux=0`) | W1–W3 `same_all_rendered_objects` (Product vs Harness `aux=1`) | W0 Canvas Diff Ratio (`aux=0`) | W1–W3 Canvas Diff Ratio (`aux=0`) |
|---|---:|---:|:---:|:---:|---:|---:|
| `section-MAB-trapezoid` | `18` | **`0`** | **`true`** (`30 / 30`) | **`true`** (`30 / 30`) | `0.2166` | `0.1582` |
| `aux-foot-S-to-BD` | `13` | **`0`** | **`true`** (`26 / 26`) | **`true`** (`26 / 26`) | `0.1203` | `0.0821` |
| `intersection-SAB-SCD` | `13` | **`0`** | **`true`** (`27 / 27`) | **`true`** (`27 / 27`) | `0.2714` | `0.2255` |
| `derived-line-pyramid` | `13` | **`0`** | **`true`** (`27 / 27`) | **`true`** (`29 / 29`) | `0.1736` | `0.1353` |
| `derived-line-cuboid` | `18` | **`0`** | **`true`** (`36 / 36`) | **`true`** (`38 / 38`) | `0.3081` | `0.2564` |
| `derived-line-prism` | `14` | **`0`** | **`true`** (`29 / 29`) | **`true`** (`31 / 31`) | `0.2158` | `0.1619` |
| `two-line-pyramid` | `18` | **`0`** | **`true`** (`31 / 31`) | **`true`** (`33 / 33`) | `0.2731` | `0.1598` |
| `two-line-prism` | `19` | **`0`** | **`true`** (`33 / 33`) | **`true`** (`35 / 35`) | `0.4753` | `0.3350` |
| `two-line-cuboid` | `23` | **`0`** | **`true`** (`40 / 40`) | **`true`** (`42 / 42`) | `0.3816` | `0.3691` |

> Note: Remaining canvas pixel diff ratio between Product and Harness reflects only container aspect ratio (`1231×779` full-height focus stage in Product vs `1231×520` panel in Harness); rendered 3D objects, sub-entities, auxiliary hidden sets, camera pose, and FOV are **100% identical** (`same_all_rendered_objects: true` across all 9 harness cases).

---

## 4. Geometry & Readability Before / After Comparison Table (All 11 Cases)

| Case ID | Witness Endpoint Displacement $\|\text{foot} - H_{\text{world}}\|_2$ (W0 → W1–W3) | Product Final `auxiliary_hidden_ids` (`aux=0`) (W0 → W1–W3) | Target Carrier Visible at Final Step (`aux=0`)? (W0 → W1–W3) | Premature Section Fill at Intermediate Step? (W0 → W1–W3) | Product Final Point Labels (`aux=0`) (W0 → W1–W3) | Label Overlaps |
|---|---|---|---|---|---|:---:|
| `section-MAB-trapezoid` | `0.0` → **`0.0`** | `[]` → **`[]`** | Yes → **Yes** (`td_f6`) | No → **No** | `A,B,C,D,S,M` → **`A,B,C,D,S,M`** | `0` |
| `aux-foot-S-to-BD` | `0.707107` → **`0.0`** | `["derived_H_line"]` → **`[]`** | **NO** → **YES (`derived_H_line`)** | No → **No** | `A,B,C,D,S,H` → **`A,B,C,D,S,H`** | `0` |
| `intersection-SAB-SCD` | `0.0` → **`0.0`** | `[]` → **`[]`** | Yes → **Yes** (`gt_f5`) | No → **No** | `A,B,C,D,S` → **`A,B,C,D,S`** | `0` |
| `derived-line-pyramid` | `0.668153` → **`0.0`** | `["gt_g","mp1_gt_g","mp2_gt_g"]` → **`["mp1_gt_g","mp2_gt_g"]`** | **NO** → **YES (`gt_g`)** | No → **No** | `A,B,C,D,S,M,H` → **`A,B,C,D,S,M,H`** | `0` |
| `derived-line-cuboid` | `1.000000` → **`0.0`** | `["gt_g","mp1_gt_g","mp2_gt_g"]` → **`["mp1_gt_g","mp2_gt_g"]`** | **NO** → **YES (`gt_g`)** | No → **No** | `A,B,C,D,A′,B′,C′,D′,M,H` → **`A,B ≡ H,C,D,A′,B′,C′,D′,M`** | `0` |
| `derived-line-prism` | `1.000000` → **`0.0`** | `["gt_g","mp1_gt_g","mp2_gt_g"]` → **`["mp1_gt_g","mp2_gt_g"]`** | **NO** → **YES (`gt_g`)** | No → **No** | `A,B,C,A′,B′,C′,M,H` → **`A,B ≡ H,C,A′,B′,C′,M`** | `0` |
| `two-line-pyramid` | `0.0` → **`0.0`** | `[]` → **`["H","H1"]`** | Yes → **Yes** (`td_q`) | **YES (`td_q::face:0`)** → **NO** | `A..S,M,H,H1` → **`A,B,C,D,S,M`** (`H,H1` hidden) | `0` |
| `two-line-prism` | `0.0` → **`0.0`** | `[]` → **`["H","H1"]`** | Yes → **Yes** (`td_q`) | **YES (`td_q::face:0`)** → **NO** | `A..C′,M,H,H1` → **`A,B,C,A′,B′,C′,M`** (`H,H1` hidden) | `0` |
| `two-line-cuboid` | `0.0` → **`0.0`** | `[]` → **`["H","H1"]`** | Yes → **Yes** (`td_q`) | **YES (`td_q::face:0`)** → **NO** | `A..D′,M,H,H1` → **`A,B,C,D,A′,B′,C′,D′,M`** (`H,H1` hidden) | `0` |
| `rectangular_pyramid_positive` | `0.0` → **`0.0`** | `[]` → **`[]`** | Yes → **Yes** | N/A | `A,B,D,C,S` → **`A,B,D,C,S`** | `0` |
| `p1_chop_thiet_dien_khoang_cach` | `0.0` → **`0.0`** | `[]` → **`[]`** | Yes → **Yes** (`T`, `BD`) | No → **No** | `A,B,C,D,S` → **`A,B,C,D,S`** | `0` |

---

## 5. RED → GREEN Regression & Verification Receipts

1. **RED Phase ([`red/vitest-red.txt`](red/vitest-red.txt)):**
   - Added 6 targeted unit/component regression tests before modifying implementation files:
     - `scene3d-chart.test.ts`: `FINDING-B1: veKhongGian biến đổi cả perpendicular_witness sang không gian thế giới và giữ tính lũy đẳng` (FAILED in RED: `0.6681531047810609` displacement).
     - `scene3d-auxiliary.test.ts`: `FINDING-B2` (`gt_g` and `derived_H_line` must not be hidden at final step under `aux=0`) & `W2` (`H` and `H1` in `two-line-prism` must be classified as `loai: "dung"` and hidden at final step under `aux=0`) (both FAILED in RED).
     - `scene3d-presentation.test.ts`: `W3: kyHieuDiem gộp nhãn các điểm trùng tọa độ thành 'B ≡ H'` (FAILED in RED).
     - `scene3d.test.tsx`: `FINDING-D1 / W1: mặt con (face sub-entity) khi chưa chọn chỉ làm hit_proxy trong suốt` & `W3: thiết diện con (td_q::face:0) không tô mặt sớm ở bước mới dựng cạnh đầu` (both FAILED in RED).
2. **GREEN Phase ([`results/vitest-green.txt`](results/vitest-green.txt), [`results/pytest-green.txt`](results/pytest-green.txt), [`results/result-binding-check/receipt.json`](results/result-binding-check/receipt.json)):**
   - **Frontend Vitest Suite:** `68 passed (68)`, `1061 passed (1061)` (`0` failures).
   - **Backend Pytest Geometry Suite:** `7758 passed, 1 skipped` (`0` backend geometry failures; `0` backend files modified).
   - **Result-Binding Browser Check (`result-binding-visual-check.mjs`):** `{"verdict":"PASS_CORE_CAUSAL_RENDERING","scenes":4,"errors":0}` verifying both default `aux=0` (target line `gt_g` and foot `H` rendered, `mp1_gt_g` and `mp2_gt_g` hidden) and toggled `aux=1`.

---

## 6. Representative Before / After Visual Evidence Index

Full SHA-256 hashes for all 134 captured screenshots are recorded in [`results/parity_telemetry.json`](results/parity_telemetry.json). Key representative canvas captures inspected directly:

| Case & State | W0 Screenshot (`scene3d-visual-parity-audit`) | W1–W3 Screenshot (`scene3d-architecture-visual-reliability`) | Visual Verification Summary |
|---|---|---|---|
| `derived-line-pyramid` (Product Final `aux=0`) | `images/product/derived-line-pyramid_final_aux0_canvas.png` (`sha256=2ba9794c...`) | `images/product/derived-line-pyramid_final_aux0_canvas.png` (`sha256=419f7426...`) | Teal intersection line `gt_g` now passes through `S` and `H`; dashed perpendicular segment `MH` and right-angle symbol terminate cleanly at `H` on `gt_g`; solid faces are crisp slate-grey without double amber tinting. |
| `derived-line-cuboid` (Product Final `aux=0`) | `images/product/derived-line-cuboid_final_aux0_canvas.png` (`sha256=f35249cb...`) | `images/product/derived-line-cuboid_final_aux0_canvas.png` (`sha256=4988fc13...`) | Teal line `gt_g` passes through `B′` and `B ≡ H`; right-angle marker sits at vertex `B ≡ H` between `MH` and `gt_g`; single combined label **`B ≡ H`** replaces separate overlapping labels. |
| `two-line-prism` (Product Final `aux=0`) | `images/product/two-line-prism_final_aux0_canvas.png` (`sha256=89390512...`) | `images/product/two-line-prism_final_aux0_canvas.png` (`sha256=7327d586...`) | Off-solid translated points `H` and `H1` and their labels are hidden at the final step; cutting plane `(P)` is tightly framed around the section trapezoid at `0.10` opacity; section fill is crisp without double sub-entity overlay. |
| `two-line-prism` (Product Step 10 Intermediate `aux=0`) | `images/product/two-line-prism_step10_first_section_edge_aux0_canvas.png` (`sha256=1e5fc04b...`) | `images/product/two-line-prism_step10_first_section_edge_aux0_canvas.png` (`sha256=342f598d...`) | Premature section polygon fill (`td_q::face:0`) is gone at step 10; only the constructed section segments and their endpoints are shown. |
| `two-line-prism` (Harness Final `aux=0`) | `images/harness/two-line-prism_final_aux0_canvas.png` (`sha256=ee8b6fd7...`) | `images/harness/two-line-prism_final_aux0_canvas.png` (`sha256=dc44006c...`) | Harness now renders identical objects and sub-entities as Product (`33 / 33` objects, `H` and `H1` hidden under `aux=0`), and selecting `H` displays `"H · Điểm dựng phụ"`. |

---

## 7. Residual Non-Blocking Limitations & Review Readiness

1. **Legacy `Oxyz` Fixture (`p1_chop_thiet_dien_khoang_cach`):** As noted in W0, this legacy coordinate-geometry fixture does not emit a `perpendicular_witness` payload on `BD` (distance is computed algebraically in $Oxyz$), and its section `T` is pre-closed at construction step 7.
2. **Orbit Settling Gate (`ISSUE-OPS-ORBIT-GATE-UNSETTLED-LOCAL`):** Remains a separate tooling/environment issue outside the scope of `ISSUE-ARCH-SCENE3D-CONSTRUCTION-READABILITY`.
3. **Candidate Refreeze & T3 Gate:** Per task instructions, `EVALUATION_CANDIDATE.json` has **not** been refrozen and authoritative T3 has **not** been run prior to independent code review.

**Status:** `SCENE3D_ARCHITECTURE_IMPLEMENTATION_READY_FOR_REVIEW`

# Scene3D Educational Visual Quality Finalization — Audit, Implementation & Browser Verification

Run `scene3d-educational-finalization` · 2026-10-17 · LOCAL Windows 11 · branch `research/scene3d-educational-finalization`
from `main` (`76dca142d5b25c288863dae147943404f4184598`, merged onto `main` `bc0445ae4a4376c97af6ef9e1a21fa8fb0f5a3f8`) · `DEFAULT_MODE = LLM_ONLY` unchanged ·
`Hybrid_product_enablement = NO-GO` unchanged · 0 live Gemini calls · `HUMAN_VISUAL_REVIEW_PASS` (confirmed by user in session, 2026-10-17).

Status taxonomy:
- **IMPLEMENTED**: code exists in general frontend modules (`frontend/src/simulations/domains/geometry/*`, `frontend/src/styles/global.css`).
- **VERIFIED BY TESTS**: offline Vitest unit and regression tests (RED → GREEN; 68 files, 1,077 tests green).
- **MEASURED**: Playwright browser verification receipts in `visual/before/`, `visual/after/` (49 full-size `1280×900` frames including step-by-step construction), and `visual/receipts/`.
- **HUMAN_REVIEWED**: `HUMAN_VISUAL_REVIEW_PASS` (confirmed by user in session, 2026-10-17 after inspecting full-size acceptance images and step-by-step construction frames).
- **NOT_MEASURED**: Live provider extraction (out of scope for frontend visual finalization).

---

## 1. Visual Audit & Root-Cause Findings (Before Fix at `76dca142`)

We audited 12 representative benchmark and cross-section scenes (49 states at full application viewport `1280×900`: initial, step-by-step construction, final normal state, `aux=0`, `aux=1`, quantity/witness selection, orbit, zoom, reset):
1. `pyr-midpoint-to-plane` (including steps 3, 4, 5, selected `kq_q`)
2. `cube-midpoint-to-plane`
3. `prism-midpoint-to-plane`
4. `pyr-midpoint-to-named-line` (including steps 3, 5, 6, 7, selected `kq_q`)
5. `pyr-midpoint-to-result-line`
6. `cuboid-midpoint-to-result-line`
7. `rb-derived-line-prism`
8. `ge:pyramid-midpoint-A`
9. `section-cube-A1BD`
10. `section-MNP-mid-square` (including steps 6, 8, 9, 10, 11)
11. `section-MAB-trapezoid` (including steps 6, 7, 8, 9)
12. `intersection-SAC-SBD`

### Root Causes Identified

| ID | Symptom Observed in `visual/before/` | Root Cause in Code | General Fix Implemented |
|---|---|---|---|
| **EDU-1** | Selecting distance-to-line result `kq_q` (`d(M, BD) = 3/2` in `pyr-midpoint-to-named-line`, `d(M, d_q)` in `pyr-midpoint-to-result-line`, `cuboid-midpoint-to-result-line`, `rb-derived-line-prism`) drew the orange witness `MH` and right-angle marker, but **no measurement pill** `d(M, H)` appeared on the 3D canvas (`annotation_boxes: []`). | `doanCoMat(scene, present)` in `scene3d-annotations.ts` only registered endpoint pairs from `segment3`, `solid` edges, and `polygon` edges. For point-to-line distance witnesses where the foot `H` is carried on `point3.perpendicular_witness` (without a separate `segment3` object), `coDoan(M, H)` returned `false`, so `annotationsAt` suppressed the measurement pill. | `doanCoMat` in `scene3d-annotations.ts` now also registers `[o.id, o.perpendicular_witness.from]` when a present `point3` has a `perpendicular_witness` whose source point is also present. (**IMPLEMENTED**, **VERIFIED BY TESTS**, **MEASURED**) |
| **EDU-2** | In `pyr-midpoint-to-result-line` (`d(M, d_q)`), the foot of perpendicular `H = (-1, 2, 0)` lies outside the base edges. At `76dca142`, `diemHuuHan` excluded witness feet, and `chonHuongNhin` rotated the pyramid sideways (`pv = 70°`, making `SA` and `SC` nearly colinear in 2D); in `pyr-midpoint-to-plane` and `section-cube-A1BD`, the initial view had lower elevation/clearance. | (a) `diemHuuHan` and `cauTrucGocNhin` in `scene3d-model.ts` ignored `perpendicular_witness.foot` and `annotation.witness.foot`. (b) `chonHuongNhin` in `scene3d-camera.ts` used a very small textbook pose affinity (`0.15`) and uncapped minimum vertex distance (`t.tachDinh`), allowing an exterior witness foot to pull the camera away from the textbook front-right oblique viewpoint even when that viewpoint already passed all non-degeneracy thresholds (`datNguong`). | (a) `diemHuuHan` and `cauTrucGocNhin` in `scene3d-model.ts` include `perpendicular_witness.foot` and `annotation.witness.foot`. (b) `chonHuongNhin` in `scene3d-camera.ts` caps clearance saturation (`Math.min(t.tachDinh, 0.2)`, `Math.min(t.leCanh, 0.38)`) and increases textbook pose affinity (`0.85 * (1 - tich(huong, quen))`), keeping canonical textbook viewpoints when non-degenerate while rotating away from edge-on target planes (`pyr-midpoint-to-plane`, `section-cube-A1BD`). (**IMPLEMENTED**, **VERIFIED BY TESTS**, **MEASURED**) |
| **EDU-3** | When `auxiliaryShown = true` (`aux=1`) on `section-cube-A1BD` (and plane/section scenes), the purple auxiliary plane polygon border overlapped the amber section border on the same 3D segments (`A'B`, `BD`, `DA'`), causing dual-color stroke fighting. | `classifyWorldSegmentVisibility` in `scene3d-edge-visibility.ts` only yielded `yield_colinear_canonical_edges` against canonical solid edges, not against higher-priority non-canonical segments (`section` borders and explicit `segment3`). | Extended `classifyWorldSegmentVisibility` with `priority_segments?: ReadonlyArray< readonly [THREE.Vector3, THREE.Vector3] >` and passed active section/segment borders from `updateNonCanonicalVisibility` in `scene3d-view.tsx`. (**IMPLEMENTED**, **VERIFIED BY TESTS**, **MEASURED**) |
| **EDU-4** | Right-angle witness markers (`vatNhanChung`) had fixed max cap `0.34` independent of scene diameter `dk` and dash size `0.12`, appearing oversized on unit solids; furthermore, when a right-angle marker sat at a vertex (`H` or `B ≡ H`) pointing upward, the vertex label (`translate(-50%, -140%)`) or measurement pill (`prism-midpoint-to-plane`) could sit directly on the vertex dot or right-angle square corner. | `vatNhanChung` in `scene3d-view.tsx` did not scale `s` or `dashSize` by `duongKinhCanh(diemNen)`, and `chieuNhan` did not pass vertex marker discs or right-angle witness corners into `placeAnnotationLabels` or flip vertex labels below upward witness markers. | Scaled `vatNhanChung` marker size `s` (`<= 0.068 * dk`) and `dashSize` (`0.032 * dk`) by `duongKinhCanh(diemNen)`; recorded `foot` and `corner` in `userData`; flipped vertex label below (`translate(-50%, 40%)`, supported by `duoi?: boolean` in `locNhanChongNhau`) when an upward right-angle witness sits at that vertex; passed `chamDiem` + `gocVuongRects` to `placeAnnotationLabels` with safe fallback. (**IMPLEMENTED**, **VERIFIED BY TESTS**, **MEASURED**) |
| **EDU-5** | Canvas background had a warm yellow radial tint (`rgba(254, 243, 199, 0.35)`) and dark slate-brown solid faces (`0x475569` / `0xcbd5e1`), departing from the educational textbook aesthetic (clean near-white background, cool light slate-blue-grey solid faces). | `.geo3d-canvas` in `global.css` used warm amber radial gradients; `MAU.mesh` in `scene3d-view.tsx` and `MAU_VAI_TRO.nen_boi_canh` in `scene3d-roles.ts` used darker/neutral greys. | Updated `.geo3d-canvas` to clean near-white `#f8fafc -> #ffffff`, `.geo3d-label` to crisp `rgba(255, 255, 255, 0.88)`, `MAU.mesh` to `0x647a96`, and `MAU_VAI_TRO.nen_boi_canh` to `0xcfd6df`. (**IMPLEMENTED**, **MEASURED**) |
| **EDU-6** | `scene3d-orbit-gate.mjs` failed with `TU_KHOP_KHUNG` (`capPhat = 45,868` WebGL buffers allocated during orbit) and `KHONG_ON_DINH` (`ISSUE-OPS-ORBIT-GATE-UNSETTLED-LOCAL` on `p1`, `p6`, `p7`). | (a) `rebuildCanonicalEdgeOwner` and `updateNonCanonicalVisibility` created fresh `new THREE.BufferGeometry()` on every visibility span change during orbit, allocating thousands of WebGL VBOs and triggering lazy shader compilation when switching between solid and dashed materials. (b) In `OrbitControls.update()`, when `cam.up = (0, 0, 1)`, round-tripping `position - target` through `_quat` (`-90°` around X) and `setFromVector3` / `setFromSpherical` mutated `cam.position` and `cam.quaternion` by sub-`_EPS` float noise on every frame even after `dieuKhien.update()` returned `false`, dirtying `cam.matrixWorldInverse` forever near the poles. | (a) Added pre-allocated `BufferGeometry` span pools (`createSpanPoolGeometry`, `preallocateSpanGeoPool`, `acquireSpanGeometry`, `warmSpanPools`) in `scene3d-view.tsx` using in-place `BufferAttribute` updates (`needsUpdate = true`), reducing orbit buffer/program allocations from `45,868` to **`0`**. (b) Restored `cam.position` and `cam.quaternion` in `vong()` when `dieuKhien.update()` returns `false`, eliminating sub-`_EPS` view-matrix drift so `scene3d-orbit-gate.mjs` passes **`DAT`** on `p1`, `p6`, and `p7`. (**IMPLEMENTED**, **VERIFIED BY TESTS**, **MEASURED**) |
| **EDU-7** | In point-to-plane distance problems (`pyr-midpoint-to-plane`, `cube-midpoint-to-plane`, `prism-midpoint-to-plane`), `Scene3D` does not emit a separate `point3` object `H` in `scene.objects` (unlike point-to-line problems `04`–`07`), storing the exact foot coordinates in `kq_q.annotation.witness.foot`. Previously: (a) in normal final state (`selected_id = null`), `projectionWitnessesAt` only inspected `point3.perpendicular_witness`, so the perpendicular line and foot were completely hidden until the student clicked `kq_q`; (b) even when shown, `vatNhanChung` drew no point dot at `w.foot` and only drew 2 sides of the right-angle square (`[chan + u1, gocDinh, chan + v1]`), leaving the square open when `u1` pointed into a plane interior (`prism-midpoint-to-plane`) or when `doan` ended in a dash gap. | (a) `projectionWitnessesAt` in `scene3d-annotations.ts` did not include `FINAL_RESULT` quantity witnesses when `step` reached `FINAL_RESULT`. (b) `vatNhanChung` in `scene3d-view.tsx` lacked a foot marker sphere `chamChan` at `w.foot` and used a 3-vertex open L-polyline for `goc`. | (a) Extended `projectionWitnessesAt(scene, present, step?: number)` so that in normal timeline viewing (`step !== undefined`), any result quantity whose `FINAL_RESULT` step is reached and whose witness subjects are present emits `perpendicular:${o.id}` (`vai: "hinh_chieu"`). (b) Updated `vatNhanChung` to draw a 5-vertex closed right-angle square (`[chan + u1, gocDinh, chan + v1, chan, chan + u1]`) and a screen-space-scaled foot marker sphere (`chamChan`, red `MAU.derived` in normal state, blue `0x1d4ed8` when selected) at `w.foot` — without inventing any fake `point3` identity or label. (**IMPLEMENTED**, **VERIFIED BY TESTS**, **MEASURED**) |
| **EDU-8** | During step-by-step cross-section construction (`section-MNP-mid-square`, `section-MAB-trapezoid`), each `EXTEND` step highlights the parent section (`noiBat.has(o.parent)`), which highlighted the new section edge (`td::edge:i`) in amber (`MAU.highlight`), but did not highlight the newly reached section intersection vertex (`td::vertex:i` on `SD`) during the open `EXTEND` step. | In `scene3d-view.tsx`, `o.type === "point3"` only used `MAU.highlight` when `noiBat.has(o.id)`, ignoring `o.parent && progressCha && !progressCha.closed && noiBat.has(o.parent)`. | Highlighted section sub-entity vertices (`o.type === "point3" && o.parent`) in `MAU.highlight` (`0xf59e0b`) while their parent section is highlighted and still open (`!progressCha.closed`), settling to `MAU.derived` (`0xb91c1c`) once closed (`CLOSE_SECTION`), without inventing ungrounded letter names for unnamed intersection vertices. (**IMPLEMENTED**, **VERIFIED BY TESTS**, **MEASURED**) |

---

## 2. Offline Verification (RED → GREEN Tests & Production Build)

Added 5 targeted regression tests (verified RED before fix, GREEN after fix):
1. `frontend/src/simulations/domains/geometry/scene3d-annotations.test.ts`:
   - `hiện nhãn khoảng cách tới đường khi chọn đại lượng mà nhân chứng nằm trên point3.perpendicular_witness`
   - `projectionWitnessesAt hiện nhân chứng vuông góc từ quantity kết quả ở bước FINAL_RESULT ngay cả khi chưa chọn đối tượng`
2. `frontend/src/simulations/domains/geometry/scene3d-hidden-lines.test.tsx`:
   - `viền mặt phẳng phụ có yieldColinear nhường đoạn trùng với cạnh thiết diện để không vẽ chồng hai màu`
3. `frontend/src/simulations/domains/geometry/scene3d-camera.test.ts`:
   - `giữ góc nhìn sách giáo khoa ổn định cho chóp đáy vuông ngay cả khi có thêm chân vuông góc ngoài cạnh đáy`
4. `frontend/src/simulations/domains/geometry/scene3d.test.tsx`:
   - `diemHuuHan và cauTrucGocNhin bao gồm cả chân vuông góc (perpendicular_witness.foot và annotation.witness.foot)`

Full suite results in isolated worktree:
- `npx vitest run`: **68 test files passed (1,077 tests), 0 failed**.
- `npm run build` (`tsc -b && vite build`): **exit 0**.

---

## 3. Browser & Visual Verification (`MEASURED`)

1. **Full-Size Application Audit (`visual/before/` vs `visual/after/` at `1280×900`):**
   - 12 scenes × multiple states/steps = 49 PNG screenshots captured at full application size (`1280×900`) via Playwright (`visual/after/audit-summary.json`).
   - `console_errors = 0`, `page_errors = 0` across all 49 states.
   - `labelOverlapPairs = 0` and `unplaced = []` across all 49 states.
   - All point-to-plane and point-to-line distance scenes clearly show the projection foot dot, closed 4-sided right-angle square, and dashed perpendicular witness both in normal final state (`selected_id = null`) and when the result quantity is selected (`selected_id = "kq_q"`).
   - Step-by-step construction frames for `pyr-midpoint-to-plane`, `pyr-midpoint-to-named-line`, `section-MNP-mid-square`, and `section-MAB-trapezoid` verify clear progressive construction of midpoints, planes/lines, perpendicular feet, and named/unnamed section intersection vertices.
2. **Orbit Gate v3 (`visual/receipts/orbit-gate.json`):**
   - `node scripts/scene3d-orbit-gate.mjs`: **ĐẠT** (`dat: true`) on `p1`, `p6`, `p7`:
     - `p1`: `DAT`, `vong = 449°`, `truc = Z[0,0,1] ‖1.000‖`, `cos ∈ [-1.00, 1.00]`, `snap = 0`, `capPhat = 0`, `yen = 0.0°`
     - `p6`: `DAT`, `vong = 449°`, `truc = Z[0,0,1] ‖1.000‖`, `cos ∈ [-1.00, 1.00]`, `snap = 0`, `capPhat = 0`, `yen = 0.0°`
     - `p7`: `DAT`, `vong = 449°`, `truc = Z[0,0,1] ‖1.000‖`, `cos ∈ [-1.00, 1.00]`, `snap = 0`, `capPhat = 0`, `yen = 0.0°`
3. **Hybrid Section Visual Check (`visual/receipts/browser-check.json`):**
   - `node scripts/hybrid-section-visual-check.mjs`: **PASS** across all 8 scenes (`failures: []`, `net_retries: 0`), verifying own-pixel contribution, orbit, zoom, and camera reset (`residual_vs_start: 0`).

---

## 4. Architectural Distinction: Missing `point3` vs Existing Foot Coordinate in `Scene3D`

| Case | What Exists in `Scene3D` (`scene.objects`) | How `Scene3D` Renders It Now | Why No Fake Label Is Invented |
|---|---|---|---|
| **Point-to-Line Distance** (`pyr-midpoint-to-named-line`, `pyr-midpoint-to-result-line`, `cuboid-midpoint-to-result-line`, `rb:derived-line-prism`) | Explicit `point3` object `H` (`role: "auxiliary"`, `perpendicular_witness: { from: "M", foot: [...], on: ... }`) introduced at step `construct_foot_H`. | Renders vertex sphere `H`, label `H` (or merged `B′ ≡ H`, `B ≡ H` when coincident with a base vertex), dashed perpendicular `MH`, and closed 4-sided right-angle square from the step `H` is constructed. | `H` is an explicit `point3` in `scene.objects` with `label: "H"`. |
| **Point-to-Plane Distance** (`pyr-midpoint-to-plane`, `cube-midpoint-to-plane`, `prism-midpoint-to-plane`) | **No `point3` object `H` exists in `scene.objects`**. However, `kq_q.annotation.witness` carries the exact 3D projection foot `foot: [x, y, z]`, source `from: "M"`, target `on: "mp_q"`, and orthonormal plane basis `marker: { u, v }`. | At the `FINAL_RESULT` step (both in normal state and when `kq_q` is selected), renders the dashed perpendicular from `M` to `w.foot`, the closed 4-sided right-angle square on the target plane, and a screen-space-scaled foot marker dot (`chamChan`) at `w.foot`. | Inventing a label `"H"` when no `point3` `H` exists in `scene.objects` would violate the strict presentation-only contract. The foot marker dot + closed right-angle square makes the exact projection foot unmistakable for students. |
| **Cross-Section Intersection Vertices** (`section-cube-A1BD`, `section-MNP-mid-square`, `section-MAB-trapezoid`) | `section` polygon stores ordered 3D vertices `vertices: Vec3[]`. `deriveSectionSubEntities` derives `td::vertex:i` (`point3`) for any section vertex that does not coincide with an existing named `point3`. | Named vertices (`A′, B, D` or `M, N, P` or `A, B, M`) show their exact labels. Unnamed intersection vertices (e.g., 4th vertex on `SD` in `section-MNP-mid-square` at step 10/11 and `section-MAB-trapezoid` at step 8/9) appear at the exact `EXTEND` step when the section edge reaches `SD`, lighting up in amber (`MAU.highlight`) during construction and settling to derived red (`MAU.derived`) when closed. | The compiler IR does not assign a letter name to unnamed intersection vertices on `SD`; the frontend renders the exact 3D intersection dot on `SD` at each step without fabricating ungrounded point labels. |

---

## 5. Independent Review (`review.md`) & Human Visual Review

An independent read-only review subagent (`d5b4214c-190a-45e8-b81b-9a42318492e5`) audited the full final worktree diff (`EDU-1` through `EDU-8`), test suite (68 files, 1,077 tests), and 49 full-size (`1280×900`) visual artifacts against all 7 mandatory gates (`review.md`): **PASS (7/7)**. The human user inspected the full-size acceptance package and confirmed **`HUMAN_VISUAL_REVIEW_PASS`** in session on 2026-10-17.

---

## 6. Authoritative T3 Verification & Integration (`verification/t3-pass.json`, `integration.md`)

- **Product Commit:** `22df95d6561084e410e7d2598213c99f8f45cf94`
- **Merge with `origin/main` (`bc0445ae`):** `d4947610bedf7723e24d33903f62a55f49e10606` (zero conflicts)
- **Candidate Refreeze:** `7dc609bd5d4d437bf6dd5838b65186fbbbd06561` (`product_commit_sha = 22df95d6…`, `measured_system.tree_hash = 57c7f5dbedaa7b21c66345fa4d6f0e1ea461a425293d44035b5678e12d76f96e`, 110 files unchanged)
- **Authoritative T3 (`D:/tmp/s3d-edu-t3` detached at `8aabb4b976c3dfc23149c7f90b841e74aa297a57`):** **`FULL_PRODUCT_GATE_PASS`** (`488.9s`; `pytest` `10,263 passed, 1 skipped, 2 deselected, 9 xfailed`; `vitest` `68 files, 1,077 passed`; `typecheck + build` `PASS`; `replay_demo_cases.py` `PASS`; `audit_demo_crash_surface.py` `6/6 PASS, 0 HTTP 500`; `verification/t3-pass.json`, `verification/t3-authoritative.log`, `sha256: 0bd3bc8d826c5838b4fd4f897c344801c95471d7ee7016f932db0d0435f35256`).


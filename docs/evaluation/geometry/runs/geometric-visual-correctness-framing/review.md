# Independent Read-Only Review Report — `geometric-visual-correctness-framing`

- **Verdict:** `INDEPENDENT_REVIEW_PASS`
- **Reviewer Conversation ID:** `589da610-17c3-4526-9684-a0d41700ccb0`
- **Reviewed Worktree:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\geometric-visual-correctness-framing`
- **Branch / HEAD:** `research/geometric-visual-correctness-framing` @ `7868db0aef3810e2089b5f8b8d6aecfb8b3e1400` (clean working tree)
- **Ancestry & Candidate Identity Verified:** Branched from `research/visual-ux-final-quality` (`164a5e25ad25bf42d689df115ade5d74b5c733e9`), candidate ancestry `9343e8d0d4c4cdf5bf0865e0a550c13f238f28b5`, previous product commit `56328b17462e9c4e903dc17687da07243d06846d`, new product commit `ca84337e32c27c1116f5b1065ca45f2fcdf3e13c`, measured system hash `9bf35a1d6f4c3b3e90228964a3b5ee96288de29efcb3f580f22c6f126489bd9a` across `114` files.
- **Live Provider Calls:** `0` (`ALLOW_LIVE_AI = 0`).

---

## Item-by-Item Verification Findings (1..5)

1. **Adaptive Camera Framing & Safe-Area Awareness (P2) — VERIFIED PASS:**
   - `scene3d-model.ts::diemHuuHan` (lines 853–915) computes true radius-$R$ surface boundary points using 8 unit-circle perimeter directions (4 axial $\pm r u_i$ + 4 normalized diagonal $\pm (r/\sqrt{2}) u_1 \pm (r/\sqrt{2}) u_2$) for `cylinder`/`cone` and 14 unit-sphere directions (6 cardinal $\pm r e_i$ + 8 normalized octant $\pm (r/\sqrt{3})(e_1 \pm e_2 \pm e_3)$) for `ball`, keeping every boundary point at Euclidean distance $\le R(1 + 10^{-12})$ without hardcoding demo IDs.
   - `scene3d-camera.ts::khungNhinSuPham` (lines 323–379) and `scene3d-view.tsx::tinhTuyChonKhung` (lines 2673–2708) compute adaptive vertical/horizontal fill ratios (`tiLeDoc`, `tiLeNgang`) and safe-area target offsets (`dichTamNgang`, `dichTamDoc`) from projected aspect ratio and DOM safe-area geometry.
   - `scene3d-view.tsx::diemKhungNhin(goc, daCoDiemCanh)` (lines 1027–1054) skips tessellated `curvedRimLoop` and `curvedSolidVolume` vertices when analytical `diemCanh` points are present, achieving `resetCamDiff = 0.0` across all 7 served scenes in `after/measurements.json`.
   - `MutationObserver` on `.geo3d-san` (`scene3d-view.tsx` lines 2728–2743) re-centers the framing into the left safe viewport when `#geo3d-bang-phan-tich` opens, achieving `panelOverlapPx = 0` across `1440×900`, `1024×768`, and `820×640`, with default `geometryHeightRatioSafe` in `0.566..0.585` (`0.585`, `0.585`, `0.566`, `0.569`, `0.579`, `0.581`, `0.569`).

2. **Edge & Dash Semantics for Polyhedra & Curved Solids (P3) — VERIFIED PASS:**
   - `scene3d-view.tsx` renders `circle3` (lines 1461–1548) and `ellipse3` (lines 1550–1646) with restrained inward ribbon thickness (`0.36x` for `BASE_REGION`, `0.46x` for `SECTION_REGION`) and zero fill-to-border gap (`bkTo = Math.max(2e-5, trongR)` for circles and `mepTo.push(pTrong)` for ellipses).
   - `scene3d-edge-visibility.ts::diemVanhCongBiChe` (lines 385–449) and `scene3d-view.tsx::capNhatHinhHocVanhCong` (lines 630–664, 945–963) dynamically classify 96-segment curved rims per camera pose using analytical quadric ray occlusion (`ball`, `cylinder`, `cone`) with 24 uniform dash-gap cycles (`dashCycle = 4`) rather than static half-circle parameter slices.
   - `scene3d-edge-visibility.ts::classifySolidEdgeVisibility` (lines 201–210) excludes coplanar shared faces from cross-solid occlusion, and `scene3d-view.tsx::updateCanonicalEdgeVisibility` (lines 880–896) passes multi-solid `localOccluders`, while secondary solids receive distinct muted teal-slate styling (`0x0d9488` fill, `0x0f766e` edges) and duplicate shared canonical edge owners are suppressed (`duplicate_visual_owner_ids = []`).

3. **Section Presentation — Normal vs. X-Ray Mode (P4) — VERIFIED PASS:**
   - `scene3d-view.tsx::lopChieuSau` (`BackSide`, `renderOrder = 5`, lines 318–328) and `lopChieuSauMatTruoc` (`FrontSide`, `renderOrder = 7.5` on `curved_solid`, lines 332–344, 1681–1687) allow interior section fills (`renderOrder = 7`, `depthTest: !xray`) to render honestly inside their parent solid in Normal mode while still being occluded by an opaque wall in front (`changed = 0` on all `firstHit: "opaque_wall"` probes in `after/measurements.json::depth` vs `changed > 0` in `after/measurements.json::xrayDepth`, and `report.md` records `frontVisibleFillPixels = 5163`, `occludedVisibleFillPixels = 0` in Normal mode vs `xrayOccludedVisibleFillPixels = 5163` in X-ray mode).
   - `scene3d-view.tsx` (lines 1688–1714) adds 3 subtle orthogonal great-circle wireframe contours (`opacity = 0.18 / 0.13 / 0.13`, `userData.voHan = true`) to `ball` (`curved_kind === "ball"`).

4. **Scene & Demo Identity Reconciliation & Student-Facing Quality (P5/P6) — VERIFIED PASS:**
   - `backend/app/ai/adapter3_simulation.py` emits clean subscripted vertex notation `D1` (`obj["notation"] = c_sym`, line 1824) instead of `D(pyr2)` on multi-solid symbol collisions (verified in `backend/tests/geometry/test_typedfact_next_adapter3.py` line 580) and cleans `, đi qua đại lượng` / `, qua đại lượng` via `_clean_curved_text` (lines 2718–2765) without altering exact mathematical authority.
   - `demos/audit_scenes.json` (via `build_audit_scenes.py` lines 179, 206) reconciles `family05_prism` (`5. Hình lăng trụ đứng ABC.DEF`) and `family07_multi_solid_composition` (`7. Tổ hợp đa khối (Hai hình chóp S.ABC và D.ABC chung đáy ABC)`).
   - `Scene3DExplorer.tsx` (lines 423–430, 531–543) displays `"Đã dựng xong (bước N/N): ..."` and `"Mô hình đã hoàn chỉnh · Kéo để xoay hình · Bấm vào đối tượng hoặc mở Phân tích toán học để khám phá"` at the final step while hiding `"Xem mô hình đầy đủ"`, and keeps Mode A (Simulation) default with `#geo3d-bang-phan-tich` closed on entry and zero final-answer leakage.

5. **Governance & Preservation Invariants (P8/P9) — VERIFIED PASS:**
   - `CHE_DO_MAC_DINH = "LLM_ONLY"` (`routing.py` line 30), `RESPONSE_CONTRACT = flat` (`hybrid-Flat-preview/1`), `HYBRID_PRODUCT_ENABLEMENT = NO-GO`, `ALLOW_LIVE_AI = 0`, and `CACHE_VERSION = "127"` (`main.py` line 824, `EVALUATION_CANDIDATE.json` line 9, `candidate_divergence.json` line 26) are all preserved.
   - `git diff --name-only 164a5e25ad25bf42d689df115ade5d74b5c733e9..HEAD` confirms `0` files modified in any historical run directory under `docs/evaluation/geometry/runs/`.

---

## Severity Summary

- `0 BLOCKER, 0 IMPORTANT, 0 MINOR`

# Independent Code & Visual Review (v2 — Final Diff Including EDU-7 & EDU-8) — `scene3d-educational-finalization`

- **Reviewer:** Independent read-only `research` subagent (`d5b4214c-190a-45e8-b81b-9a42318492e5`)
- **Date:** 2026-10-17
- **Branch:** `research/scene3d-educational-finalization` (base `main` = `76dca142d5b25c288863dae147943404f4184598`)
- **Scope:** Full diff across all 12 modified frontend files (`EDU-1` through `EDU-8`), 68 Vitest test files (**1,077 tests**), and **49 full-size (`1280×900`) browser states** across 12 benchmark and cross-section scenes (`visual/after/audit-summary.json`).
- **Verdict:** **PASS (7 / 7 mandatory gates + EDU-7 & EDU-8 verified)**

## 1. Mandatory 7-Gate Verification

| Gate | Verdict | Summary |
|---|---|---|
| 1. No hardcoding by fixture ID / vertex label / coordinates | **PASS** | Inspected full diffs across all 8 modified production files (`scene3d-annotations.ts`, `scene3d-camera.ts`, `scene3d-edge-visibility.ts`, `scene3d-model.ts`, `scene3d-presentation.ts`, `scene3d-roles.ts`, `scene3d-view.tsx`, `global.css`). Zero hardcoded fixture IDs, case IDs, vertex labels (`S`, `A`, `B`, `C`, `H`, `M`, etc.), or problem-specific coordinates exist in production code. |
| 2. Canonical edge identity preserved | **PASS** | `edge_ownership`, `visualOwnerId`, and `doanNhuongCanh` are untouched; `duplicate_visual_owner_ids = []` across all 49 captured frames in `audit-summary.json`; `scene3d-hidden-lines.test.tsx` (32/32 passed). |
| 3. Presentation-only frontend boundary preserved | **PASS** | `scene3d.test.tsx` guard (55/55), `scene3d-annotations.test.ts` (29/29), `scene3d-camera.test.ts` (30/30), `scene3d-hidden-lines.test.tsx` (32/32), and all 68 Vitest files (**1,077 tests**) pass. `projectionWitnessesAt`, `diemHuuHan`, `cauTrucGocNhin`, and `vatNhanChung` read only backend-emitted exact coordinates (`perpendicular_witness.foot`, `annotation.witness.foot`, `marker.u`, `marker.v`). |
| 4. Backend / Planner / Compiler / Kernel / Prompts untouched | **PASS** | Zero backend, Planner, Compiler, Registry, Kernel, or provider prompt files touched (`git diff 76dca142 --name-only`). |
| 5. `DEFAULT_MODE = LLM_ONLY` preserved | **PASS** | `CHE_DO_MAC_DINH = "LLM_ONLY"` unchanged; `Hybrid_product_enablement = NO-GO` unchanged; 0 live provider calls. |
| 6. No self-stamped `HUMAN_VISUAL_REVIEW_PASS` before user review | **PASS** | At review time, `run.json` and `report.md` recorded `HUMAN_VISUAL_REVIEW_PENDING` until the human user confirmed `HUMAN_VISUAL_REVIEW_PASS` in session. |
| 7. Visual comparison sheets & 49 full-size browser states verified | **PASS** | Inspected all 7 comparison sheets (`cmp-01`..`cmp-09`), the 49 full-size (`1280×900`) screenshots in `visual/after/` (including step-by-step construction frames for `01`, `04`, `09b`, `09c`), `audit-summary.json` (`errors: []`, `unplaced: []`, `overlaps: []`, `duplicate_visual_owner_ids: []`), `orbit-gate.json` (`DAT` on `p1`, `p6`, `p7`, `capPhat = 0`), and `browser-check.json` (`failures: []`, `net_retries: 0`). |

## 2. Specific Verification of EDU-7 and EDU-8

1. **EDU-7 (`projectionWitnessesAt` & `vatNhanChung`):**
   - `projectionWitnessesAt(scene, present, step?: number)` in `scene3d-annotations.ts` checks `step !== undefined`, finds `FINAL_RESULT` events up to `clampStep(scene, step)`, and emits `perpendicular:${o.id}` (`vai: "hinh_chieu"`) for any result quantity with `ann.anchor === "witness"` whose `from` and `subject_ids` are present, deduplicating by `${from}|${foot}` against `point3.perpendicular_witness` entries and deduplicating in `scene3d-view.tsx` against `witnessesShown(scene, nhanSoDo)`.
   - `vatNhanChung` in `scene3d-view.tsx` draws a 5-vertex closed square (`[chan + u1, gocDinh, chan + v1, chan, chan + u1]`) and adds a screen-space-scaled foot marker sphere `chamChan` (`userData.dauDinh = "thuong"`, `raycast = () => {}`, `renderOrder = 11`) at `w.foot`, scaled each frame by `datCoDauDinh(nhanChung, cam, wCss, hCss)`. Because `__geo3d_vertex_markers` only traverses `goc` (not `nhanChung`), existing vertex-marker harness contracts on `goc` remain unaffected.
   - Visually verified on `01-pyr-midpoint-to-plane-final.png`, `02-cube-midpoint-to-plane-final.png`, and `03-prism-midpoint-to-plane-final.png` that the dashed perpendicular, closed 4-sided right-angle square, and red foot marker dot at `w.foot` are clearly visible in normal final state (`selected_id = null`) without inventing an ungrounded `H` label.
2. **EDU-8 (Section Sub-Entity Vertex Highlighting During Open `EXTEND` Steps):**
   - In `scene3d-view.tsx` lines 2482–2484, `sangBuoc` highlights derived section vertices (`td::vertex:i`) in `MAU.highlight` (`0xf59e0b`) while their parent `section` is open (`!progressCha.closed`) and highlighted at an `EXTEND` step (`noiBat.has(o.parent)`), then settles to `MAU.derived` (`0xb91c1c`) once `progressCha.closed` becomes `true`.
   - Visually verified on `09b-section-MNP-step10-edge3-v3.png` vs `09b-section-MNP-final.png` and `09c-section-MAB-step8-edge3-v3.png` vs `09c-section-MAB-final.png` without fabricating ungrounded point labels.

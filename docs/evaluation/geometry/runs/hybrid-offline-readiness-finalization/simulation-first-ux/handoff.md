# Handoff — Simulation-First Learner UX Correction (`hybrid-offline-readiness-finalization`)

## 1. Executive Summary & Final Decision

- **Final Decision:** **`SIMULATION_FIRST_UX_READY_FOR_HUMAN_REVIEW`**
- **Scope & Authorization:** `SIMULATION_FIRST_UX_IMPLEMENTATION_ONLY` on existing branch `research/hybrid-offline-readiness-finalization` (`main` = `origin/main` = `f2b00ed3ec1e333e3b5c18c046ac5beec1f7b6fb`, no merge/push, `ALLOW_LIVE_AI = 0`).
- **Why not `HUMAN_VISUAL_REVIEW_PASS`:** By project governance, only the project owner grants final visual/pedagogical acceptance (`HUMAN_VISUAL_REVIEW_PASS`). All automated contract tests, real-browser visual checks (desktop `1440×900` and compact `390×844` across both Path A and Path B), clean detached Authoritative Full T3 (`c2cf643b578ee83ddd661c6c93000985a3358da8`), and independent read-only review (`11b6ebfd-d5b2-4527-a655-5f1c7a97fec0`) are `PASS`.

---

## 2. Commit & Freeze Lineage

- **Base (`main` = `origin/main`):** `f2b00ed3ec1e333e3b5c18c046ac5beec1f7b6fb`
- **Previous Authoritative Candidate (preserved untouched):** `f8423d4b87f942d3d850970c741bcf4ee6d2c634` (previous product commit `2af99e0eddb67da253adcf6dc0aa7ac4fd08b05d`, closure commit `302ae67d30fda14e35710507389f1af4edb1a3ff`)
- **Simulation-First UX Commits:**
  1. `aa458cc34e327ac5e42c675e0853870a5ad722c4` (`aa458cc3`) — `feat(scene3d): enforce simulation-first learner UX across product and hybrid paths` (**new `product_commit_sha`**)
  2. `c603b489f3ae7ac2b06095e03799397c6746db50` (`c603b489`) — `test(scene3d): verify simulation-first learner UX across product and hybrid browser paths`
  3. `c2cf643b578ee83ddd661c6c93000985a3358da8` (`c2cf643b`) — `chore(eval): refreeze offline readiness candidate after simulation-first UX correction` (**new Authoritative T3 Candidate**)
- **Measured System (`111` files):** `cb11bc7757466bd6c52cd063e975c4540514bac6c49acc70c4d4dfca7fff660c` (`MATCH` before and after Authoritative T3)
- **Frontend Source Tree (`HEAD:frontend/src`):** `dbb441c4ecf564905dfe8827f348ec4de5bbcaeb`
- **Backend App Tree (`HEAD:backend/app`):** `1f0bbce73c970f083797df1db7b9c1a4f97df923`

---

## 3. Summary of Simulation-First UX Corrections (P1–P2)

1. **Unified Final-Result Quantity Identification (`tapKetQuaCuoi(scene, hybrid)` in `frontend/src/simulations/domains/geometry/scene3d-model.ts`):**
   - Collects all final-result quantity IDs across:
     - `hybrid?.answers` (`kq_<id>`),
     - `solutionAt(scene, last).results`,
     - `FINAL_RESULT` events (`object` and `alias_object`),
     - `quantity` objects with `annotation.role === "result"`, `annotation.category === "result"`, `formation_roles.includes("FINAL_RESULT")`, or `display_group.includes("target")`.
   - Expands bidirectionally over `annotation.same_as` and `alias_of` so both primary result quantities (e.g., `V_S_ABCD`, `d_SA_BC`, `kq_f2`, `kq_f3`) and their bound aliases (`V`, `d`) are suppressed in learner UI.
   - Pure model functions (`solutionAt`, `quantityChoices`, `annotationsAt`) and `hybrid-preview-adapter.ts` (`docPhanHoiHybrid`, Adapter `/2` invariants) remain 100% intact.
2. **Learner Narration Guard (`learnerTextIsSafe(scene, text)` in `scene3d-model.ts`):**
   - Rejects raw `"Gán X = ..."` narration strings on untyped `MEASURE` events (such as `Gán V = 16/3.` and `Gán d = 4.` in `GEOMETRY_SAMPLES` `the-tich-chop`), falling back cleanly to `"Tính <label>."` (`"Tính Thể tích của S.ABC."`, `"Tính Khoảng cách giữa S và (ABC)."`).
3. **Simulation-First Learner UI (`frontend/src/simulations/domains/geometry/Scene3DExplorer.tsx` & `frontend/src/styles/global.css`):**
   - Removed `dapAnDaMo` / `hienDapAn` state, the `"Xem đáp án"` / `"Ẩn đáp án"` button, and `[data-hybrid-answer]` answer cards from `.geo3d-noi`.
   - Filtered `daiLuong` (`results`, `steps`, `givens`) by `!dapAnAn.has(id)` so `Khám phá → Đại lượng` never renders a `"Kết quả"` section or final problem answers, while preserving given and intermediate construction quantities (`AB = 3`, `AD = 4`, `SA = 6`, `S(ABCD) = 12` in `w11_rectangular_pyramid`).
   - Passed `annotationView={{ ...xem, hiddenIds: dapAnAn }}` to `Scene3DPlayer` so final-result `.geo3d-so-do` badges (`V = a³`, `d(A, C') = a√3`, `cos² = 1/4`, etc.) never appear on the 3D canvas (even when `Hiện tất cả số đo` is toggled on or an entity is selected), while preserving certified 3D distance witness segments (`distance_witness:kq_f6` in `H02`) and perpendicular markers (`witnessesShown`).
   - Retained `Tỉ lệ dựng: a = 1 đơn vị dựng` (`[data-length-unit]`) and timeline-anchored `observations` (`[data-route-d-observation]`).
   - Added a concise, non-overlapping learner observation guidance bar (`.geo3d-huong-dan` / `[data-learner-guidance]`) between `.geo3d-thanh` and `.geo3d-san`, displaying current step guidance (`[data-guidance-step]`) and manipulation hints (`[data-guidance-hint]: "Kéo để xoay hình · Bấm đỉnh, cạnh hoặc mặt trên hình để quan sát quan hệ"`).

---

## 4. Verification Summary & Screenshot Index (P3–P4)

| Gate | Status | Key Metrics & Receipt |
|---|---|---|
| **Contract & Unit Tests (Vitest)** | `PASS` | `70/70` files (`1145/1145` tests passed, `0` failed), including `hybrid-preview-contract.test.tsx` (`41/41` passed) |
| **Dual-Path Real-Browser Verification (Playwright Chromium)** | `PASS` | `allPassed: true, failures: []`, `live_ai_calls: 0` across Path A (`index.html`) and Path B (`hfoi-harness.html`, `12/12` `served-*` sweep) at desktop (`1440×900`) & compact (`390×844`) viewports (`simulation-first-ux/simulation-first-ux-browser-report.json`, `sha256: c872927ce3289a54c99718c602f562bc35239d2c094ae346a1ab417186d12c3d`) |
| **Authoritative Full T3 (Clean Detached Worktree)** | `FULL_PRODUCT_GATE_PASS` | Detached `.superpowers/worktrees/t3-hybrid-offline-readiness-final` at `c2cf643b`: Backend `10950 passed, 0 failed`, Frontend `70 files / 1145 passed`, Build `PASS`, Demo `5/5`, Crash `6/6` (`simulation-first-ux/authoritative-t3.json`, `raw_log_sha256: 06dfdce860d1698604fc7c2928bd9771c2067fd9f3d5a5151a1d03c89f8b076a`) |
| **Independent Read-Only Review** | `PASS` | Subagent `11b6ebfd-d5b2-4527-a655-5f1c7a97fec0` at `c2cf643b`: `0` critical, `0` important, `0` minor findings (`simulation-first-ux/review.md`) |

### Representative Screenshot Paths (`docs/evaluation/geometry/runs/hybrid-offline-readiness-finalization/simulation-first-ux/screenshots/`)

- **Path A (Default Learner Product UI — `index.html`):**
  - Cube (`served-H01_CUBE`):
    - Desktop (`1440×900`): `screenshots/pathA_cube_desktop_1_initial.png`, `screenshots/pathA_cube_desktop_2_final_default.png`, `screenshots/pathA_cube_desktop_3_final_menus.png`
    - Compact (`390×844`): `screenshots/pathA_cube_compact_1_initial.png`, `screenshots/pathA_cube_compact_2_final_default.png`, `screenshots/pathA_cube_compact_3_final_menus.png`
  - Regular Square Pyramid (`served-H03_REGULAR_SQUARE_PYRAMID_ROLE_LENGTHS`):
    - Desktop (`1440×900`): `screenshots/pathA_pyramid_desktop_1_initial.png`, `screenshots/pathA_pyramid_desktop_2_final_default.png`, `screenshots/pathA_pyramid_desktop_3_final_menus.png`
    - Compact (`390×844`): `screenshots/pathA_pyramid_compact_1_initial.png`, `screenshots/pathA_pyramid_compact_2_final_default.png`, `screenshots/pathA_pyramid_compact_3_final_menus.png`
  - Elongated Cuboid Distance (`served-H02_CUBOID_DISTANCE`, with 3D perpendicular distance witness):
    - Desktop (`1440×900`): `screenshots/pathA_elongated_cuboid_desktop_1_initial.png`, `screenshots/pathA_elongated_cuboid_desktop_2_final_default.png`, `screenshots/pathA_elongated_cuboid_desktop_3_final_menus.png`
    - Compact (`390×844`): `screenshots/pathA_elongated_cuboid_compact_1_initial.png`, `screenshots/pathA_elongated_cuboid_compact_2_final_default.png`, `screenshots/pathA_elongated_cuboid_compact_3_final_menus.png`
  - Rectangular Pyramid with Given & Intermediate Construction Quantities (`w11_rectangular_pyramid`):
    - Desktop (`1440×900`): `screenshots/pathA_w11_intermediate_pyramid_desktop_1_initial.png`, `screenshots/pathA_w11_intermediate_pyramid_desktop_2_final_default.png`, `screenshots/pathA_w11_intermediate_pyramid_desktop_3_final_menus.png`
    - Compact (`390×844`): `screenshots/pathA_w11_intermediate_pyramid_compact_1_initial.png`, `screenshots/pathA_w11_intermediate_pyramid_compact_2_final_default.png`, `screenshots/pathA_w11_intermediate_pyramid_compact_3_final_menus.png`
  - Offline Starter Sample (`the-tich-chop`):
    - Desktop (`1440×900`): `screenshots/pathA_offline_sample_desktop_final.png`
    - Compact (`390×844`): `screenshots/pathA_offline_sample_compact_final.png`
- **Path B (Injected Hybrid Fixture UI in Learner Mode — `hfoi-harness.html`):**
  - Cube (`served-H01_CUBE`):
    - Desktop (`1440×900`): `screenshots/pathB_cube_desktop_1_initial.png`, `screenshots/pathB_cube_desktop_2_final_default.png`, `screenshots/pathB_cube_desktop_3_final_menus.png`
    - Compact (`390×844`): `screenshots/pathB_cube_compact_1_initial.png`, `screenshots/pathB_cube_compact_2_final_default.png`, `screenshots/pathB_cube_compact_3_final_menus.png`
  - Regular Square Pyramid (`served-H03_REGULAR_SQUARE_PYRAMID_ROLE_LENGTHS`):
    - Desktop (`1440×900`): `screenshots/pathB_pyramid_desktop_1_initial.png`, `screenshots/pathB_pyramid_desktop_2_final_default.png`, `screenshots/pathB_pyramid_desktop_3_final_menus.png`
    - Compact (`390×844`): `screenshots/pathB_pyramid_compact_1_initial.png`, `screenshots/pathB_pyramid_compact_2_final_default.png`, `screenshots/pathB_pyramid_compact_3_final_menus.png`
  - Elongated Cuboid Distance (`served-H02_CUBOID_DISTANCE`):
    - Desktop (`1440×900`): `screenshots/pathB_elongated_cuboid_desktop_1_initial.png`, `screenshots/pathB_elongated_cuboid_desktop_2_final_default.png`, `screenshots/pathB_elongated_cuboid_compact_2_final_default.png`
  - Elongated Skew Distance Composition (`served-H11_SKEW_DISTANCE_COMPOSITION`):
    - Desktop (`1440×900`): `screenshots/pathB_elongated_skew_desktop_1_initial.png`, `screenshots/pathB_elongated_skew_desktop_2_final_default.png`, `screenshots/pathB_elongated_skew_desktop_3_final_menus.png`
    - Compact (`390×844`): `screenshots/pathB_elongated_skew_compact_1_initial.png`, `screenshots/pathB_elongated_skew_compact_2_final_default.png`, `screenshots/pathB_elongated_skew_compact_3_final_menus.png`

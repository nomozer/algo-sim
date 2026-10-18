# Independent Mathematical & Visual Review — `scene3d-plane-grid-camera` (Final Safety Check `P0` – `P3`)

- **Reviewer:** Independent Scene3D Reviewer Subagent (`d5b4214c-190a-45e8-b81b-9a42318492e5`)
- **Worktree:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\scene3d-plane-grid-camera`
- **Branch:** `research/scene3d-plane-grid-camera` (base commit `4abc4afbb976babc4740bf22e42dc368a24c1b13`)
- **Overall Verdict:** **PASS (All Mathematical, Visual, and Governance Gates PASS)**

---

## 1. Classification & Mathematical Audit (`P0` & `P1`)

| Audit Item | Classification | Independent Verification Summary | Verdict |
| :--- | :---: | :--- | :---: |
| **P0 — Right-Angle Marker Audit** (`projectionWitnessesAt` in `scene3d-annotations.ts`, lines 174–279) | **`CONFIRMED_BUG` → `FIXED`** | Confirmed all 3 pre-fix bugs and verified the mathematical & pedagogical fix:<br>1. **Certified activation gate (`chungNhanDuongMp`):** Line–plane perpendicular markers no longer fire prematurely at Step 4/5 (`CREATE bc`); they require a present measurement/conclusion at `step` (`daTinh` / `ketLuan`) referencing both `d.id` and `mp.id` with perpendicular certification (`⊥`, `90°`, or `cos... = 0`).<br>2. **No Gram-Schmidt fabrication:** Removed `u = uRaw - (uRaw·v)v`. Raw vectors `uRaw = pMp - chan` from `mp.depends` are checked directly with scale-aware relative tolerances: `\|dot(uRaw, np)\| <= 1e-4 * nu * nnp`, `\|dot(uRaw, v)\| <= 1e-4 * nu * nv`, and `\|dot(uRaw, vd)\| <= 1e-4 * nu * nd`, requiring `daHuong.length >= 2` non-collinear raw directions (`\|dot(u1, u2)\| <= 0.98`, i.e. `‖u1 × u2‖ >= 0.199`).<br>3. **Single non-overlapping glyph:** Emits exactly 1 right-angle marker (`perpendicular:${d.id}`, `u: daHuong[0].raw`, `v`) at `B`, eliminating the 2D projection overlap of two markers sharing vertex `B` and leg `BC`. | **PASS** |
| **P1 — Plane Sheet Coplanarity Audit** (`moRongDaGiacMatPhang`, `daGiacMatPhang`, `catDaGiacTheoDay` in `scene3d-model.ts`, lines 943–1150) | **`CONFIRMED_BUG` → `FIXED`** | Confirmed the pre-fix coplanarity bug on nearly horizontal planes (`0.98 < \|u_z\| < 1`, where `if (ngang)` previously flattened `z = diemMp[2]`, causing `\|dot(vertex - origin, u)\| ≈ 0.0276 >> 1e-8`) and fixed-scale thresholds.<br>• **True in-plane orthonormal basis:** `if (ngang)` now constructs `e1 = normalize([1 - u_x^2, -u_x u_y, -u_x u_z])` (`dot(e1, u) === 0` identically, `‖e1Raw‖ >= 0.98`) and `e2 = ±normalize(u × e1)`, mapping `(s, t) -> diemMp + s*e1 + t*e2` so `\|dot(vertex - origin, u)\| <= 1e-15 * scale` for all planes while reducing to `e1 = [1,0,0], e2 = [0,1,0]` when `u = [0,0,±1]`.<br>• **Scale & representation invariance:** Tolerances in `daGiacMatPhang`, `catDaGiacTheoDay`, and `moRongDaGiacMatPhang` scale with `dk = duongKinhCanh(diem)`, preserving coplanarity and 4-vertex polygon geometry across `scale ∈ {1e-3, 1, 1e3}`, point permutations, origin shifts, and `±n`. | **PASS** |

---

## 2. Counterexample & Property Test Audit

Executed in `D:\Documents\projects\algo-sim\.superpowers\worktrees\scene3d-plane-grid-camera\frontend`:
- `npx vitest run src/simulations/domains/geometry/scene3d.test.tsx src/simulations/domains/geometry/scene3d-annotations.test.ts src/simulations/domains/geometry/interaction-state.test.ts src/simulations/domains/geometry/scene3d-hidden-lines.test.tsx`
- **Result:** **4 test files passed, 169 tests passed, 0 failed** (full Vitest suite: **68/68 files, 1,087/1,087 tests PASS**).
- Verified counterexample coverage in `scene3d-annotations.test.ts` (lines 400–567):
  - Step 3/5 (`sab` only) and Step 4/5 (`sab` + `bc`, before `MEASURE kl`): `projectionWitnessesAt` returns `[]`.
  - Step 5/5 (`MEASURE kl` present): returns 1 marker `perpendicular:bc` at `[4, 0, 0]` with `|dot(u, v)| < 1e-9`.
  - Gram-Schmidt counterexample (`S_lech = [0, 2, 4]` where `BS_lech = [-4, 2, 4]` is not orthogonal to `BC = [0, 3, 0]`): returns `[]`.
  - Line in plane (`AB` in `(SAB)`) and oblique line (`SC` vs `(SAB)`, `cos² = 1/6`): returns `[]`.
  - Uncertified perpendicular coordinates (no `MEASURE` / conclusion object): returns `[]`.
  - Degenerate collinear plane points (`A, B, M` on `Ox`): returns `[]`.
- Verified property test coverage in `scene3d.test.tsx` (lines 1018–1080):
  - Exact horizontal, vertical, general oblique, nearly horizontal (`0.98 < |u_z| < 1`), nearly vertical, scale invariance (`1e-3, 1, 1e3`), and point-order / origin / normal-sign invariance all satisfy `|dot(vertex - origin, u)| <= 1e-8 * scale`.

---

## 3. Visual Comparison Audit (`cmp-01` .. `cmp-15`)

- **`cmp-12-p0-sab-steps-3-4-5.png`:** Confirms that at Step 4/5 (`CREATE bc`), no premature right-angle marker appears at `B` (`witness_ids = []`).
- **`cmp-13-p0-closeup-vertex-B.png`:** 2× close-up at vertex `B` at Step 5/5 clearly contrasts the previous overlapping dual right-angle markers (left) against the single, crisp, unambiguous right-angle marker with `cos²(BC, (SAB)) = 0` readout (right).
- **`cmp-14-p1-nearly-horizontal-plane.png`:** Confirms exact coplanarity (`max|dot| = 0`) and clean 4-vertex parallelogram rendering for both exact horizontal (`(MNP)`) and nearly horizontal (`normal = [0.15, -0.08, 1]`, `|u_z| = 0.985856 > 0.98`) planes.
- **`cmp-15-p0-oblique-line-no-false-marker.png`:** Confirms that oblique line `SC` (`direction = [2, 2, -4]`) intersecting base plane `(ABC)` at `C` produces zero false right-angle markers (`witness_ids = []`).
- **`cmp-02`, `cmp-03`, `cmp-05`, `cmp-10`:** Confirm `(SAB)` balanced 4-vertex sheet, `(SAB)` / `(MNP)` badges, single right-angle marker at `B` in both neutral and selected-conclusion states, and full preservation of the closed amber cross-section `MNP` at Step 11/11.

---

## 4. Governance & Safety Gates (7 / 7 PASS)

1. **No Hardcoding:** **PASS**
2. **Canonical Edge Ownership & `yieldColinear`:** **PASS**
3. **Deterministic Backend / Presentation-Only Frontend Boundary:** **PASS**
4. **Backend / Planner / Kernel / Prompts Untouched:** **PASS**
5. **`DEFAULT_MODE = LLM_ONLY` Preserved:** **PASS**
6. **`HUMAN_VISUAL_REVIEW_PENDING` Respected:** **PASS**
7. **Visual Evidence Package Complete:** **PASS**

---

## 5. Independent Read-Only Review — Hybrid Frontend Readiness (`F1`–`F6` + 41 Fixtures, merged with `main = 90fe44df`)

- **Reviewed Commit:** `ec72eda08f46e79b6720832762df4c44fd13f356` (merged with `main = 90fe44df9fd600bf0eded87a316b8e6dddc29cc5`)
- **Overall Verdict:** **PASS (8 / 8 Gates PASS)**

| Gate | Requirement | Independent Verification Summary | Verdict |
| :--- | :--- | :--- | :---: |
| **Gate 1 — F1 (`ISSUE-ARCH-HYBRID-HEURISTIC-PERP-MARKER`)** | No heuristic `perp_marker` from `"cao"`, `"chiều cao"`, or `a.z <= b.z` | `scene3d-view.tsx` removes all string/coordinate heuristics; `perp_marker:${o.id}` renders only when `o.perpendicular_witness ?? o.annotation?.witness` supplies a valid orthogonal certificate (`\|dot(u, v)\| <= 1e-4 * \|\|u\|\| * \|\|v\|\|`). | **PASS** |
| **Gate 2 — F2 (`ISSUE-ARCH-HYBRID-CHART-METRIC-UNVALIDATED`)** | Validate `chart_metric` as 3×3 finite rational SPD (Cholesky pivots `> 0`) | `scene3d-chart.ts`, `scene3d-model.ts`, and `store.ts` validate 3×3 finite rational entries, symmetry (`<= 1e-12`), and strictly positive Cholesky pivots (`d0, d1, d2 > 1e-12`), failing closed before scene initialization. | **PASS** |
| **Gate 3 — F3 (`ISSUE-ARCH-HYBRID-LENGTH-UNIT-IGNORED`)** | Display `scene3d.length_unit.display_scale` honestly | `scene3d-model.ts` (`SceneLengthUnit`) and `Scene3DExplorer.tsx` (`data-length-unit=""`) render `Tỉ lệ dựng: {display_scale}` without fabricating numeric lengths. | **PASS** |
| **Gate 4 — F4 (`ISSUE-ARCH-HYBRID-ROUTE-D-NOT-WIRED`)** | Honest configuration-only observation copy for `route_d` | `trichQuanSatRouteD` and `nhanQuanSatCauHinh` wire `route_d` through `SimulationWorkspace.tsx` to `Scene3DExplorer.tsx` (`data-route-d-observation=""`), never claiming `"Đã chứng minh"` unless `can_present_as_proven === true && proof_status === "PROVEN"`. | **PASS** |
| **Gate 5 — F5 (`ISSUE-ARCH-HYBRID-VERIFICATION-GAP-MISLABELED`)** | Distinct neutral copy for `reason_code: "verification_gap"` | `SimulationWorkspace.tsx` renders eyebrow `"CHƯA ĐỦ BẰNG CHỨNG KIỂM CHỨNG"` and neutral hint without blaming learner or problem statement. | **PASS** |
| **Gate 6 — F6 (`ISSUE-ARCH-HYBRID-INSUFFICIENT-SPEC-BLAMES-USER`)** | Guard missing-premise hint by `refusal_cause === "SOURCE"` | `SimulationWorkspace.tsx` shows the missing-premise hint only when `unsupported.refusal_cause === "SOURCE"`, and shows neutral retry copy when `"UNKNOWN"` or omitted. | **PASS** |
| **Gate 7 — 41 Frozen Contract Fixtures** | Lock all 41 fixtures in `fixtures-adapter-2/` | `hybrid-preview-contract.test.tsx` (28 tests) verifies SHA-256 canonical JSON hashes against `manifest.json` and exercises all `12` `served-*`, `25` `refusal-*`, and `4` `gate-*` fixtures. | **PASS** |
| **Gate 8 — Governance & Boundary Invariants** | No browser caller to `/api/preview/hybrid`, no operator token, `DEFAULT_MODE = LLM_ONLY`, backend untouched, `HUMAN_VISUAL_REVIEW_PENDING` | Confirmed via `git grep` and `git diff 90fe44df..HEAD --name-only`. | **PASS** |


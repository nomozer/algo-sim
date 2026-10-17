# Independent Code & Visual Review — `scene3d-annotation-correctness`

- **Reviewer:** Independent Research Subagent (`d5b4214c-190a-45e8-b81b-9a42318492e5`)
- **Worktree reviewed:** `d:\Documents\projects\algo-sim\.superpowers\worktrees\scene3d-annotation-correctness`
- **Branch:** `research/scene3d-annotation-correctness` (based on `main` = `8427c87989487fdbcbb547ec16039d439528eb51`)
- **Overall Verdict:** **PASS on all code, boundary, mathematical, and visual gates**

---

## 1. Code & Boundary Verification (`scene3d-model.ts`, `scene3d-view.tsx`, Tests)

| Check | Status | Verification Details |
|---|---|---|
| **1a. No Hardcoding in Production Code** | **PASS** | Inspected full `git diff 8427c87989487fdbcbb547ec16039d439528eb51` across `scene3d-model.ts` and `scene3d-view.tsx`. Zero hardcoded fixture IDs, case IDs, vertex labels (`S`, `A`, `B`, `C`, `H`, `M`, etc.), or problem-specific coordinates exist in production code. |
| **1b. `huongChanVuongGoc(chan, u, diem, v)` Boundary & Generality** | **PASS** | In `scene3d-model.ts` (lines 1033–1074), `huongChanVuongGoc` remains a pure display-orientation helper without `three` imports or forbidden methods (`.cross(`, `.dot(`, `Plane(`, etc. — verified by `scene3d.test.tsx`, 56/56 green). When `chan` is not already in the interior of a segment along `u` (`!(tMin < -1e-4 && tMax > 1e-4)`) and the witness normal `v` is provided, it checks points of `diem` lying in the plane through `chan` orthogonal to `v` (`Math.abs(dx * vx + dy * vy + dz * vz) <= 1e-4 * Math.max(1, kc)`) and, if `chan` lies in the interior of a segment between two such points (`cung < -1 + 1e-5`), aligns the display tangent `u` along the longer side of that boundary segment. |
| **1c. `vatNhanChung` 3-Point Textbook L-Bracket & Dash Origin at `chan`** | **PASS** | In `scene3d-view.tsx` (lines 1759–1773):<br>• `s` is capped at `dk * 0.042` (`Math.min(v.length() * 0.18, Math.max(v.length() * NHAN_CHUNG_GOC.tiLe, dk * 0.032), dk * 0.042, NHAN_CHUNG_GOC.toiDa)`).<br>• `chuKy` guarantees `chuKy >= s * 1.05` (`Math.max(0.045, Math.min(0.16, dk * 0.034), s * 1.05)`).<br>• `doan` is constructed from `[chan, tu]` (`H -> M`) instead of `[tu, chan]`, so the first solid dash always starts at `chan` (`H`) and extends past `chan + v1`, eliminating the dash gap at the right-angle corner.<br>• `goc` is a 3-vertex (2-segment) L-bracket `[chan.clone().add(u1), gocDinh, chan.clone().add(v1)]`, forming a textbook right-angle symbol together with the target edge/line and the first solid dash of `HM` rather than a standalone 4-sided box. |
| **1d. `chieuNhan` Midpoint Segment Obstacles (`±10px`)** | **PASS** | In `scene3d-view.tsx` (lines 1785–1789, 2029–2040, 2077–2091), `vatNhanChung` records `from: w.from` in `userData`, and `chieuNhan` projects `ud.from` to `(tx, ty)`. When the projected witness segment length `d = Math.hypot(fx - tx, fy - ty) > 24`, two `4×4 px` obstacle rects are added at `mx ± ux`, `my ± uy` (`10px` from midpoint along the segment). Verified by `scene3d-annotations.test.ts` (`P2-5`, 30/30 green) and visual inspection of `p1-cmp-05` & `p1-cmp-07`. |
| **2. Backend / Planner / Kernel / Prompts & `DEFAULT_MODE = LLM_ONLY`** | **PASS** | `git diff 8427c87989487fdbcbb547ec16039d439528eb51 --name-only` shows only 4 modified files (`scene3d-model.ts`, `scene3d-view.tsx`, `scene3d.test.tsx`, `scene3d-annotations.test.ts`). Zero backend, Planner, Compiler, Registry, Kernel, or provider prompt files were touched, and `DEFAULT_MODE = LLM_ONLY` is unchanged. |

---

## 2. Mathematical Audit & Visual Comparison Verification (`report.md` & `visual/p1-cmp-*.png`)

1. **P1 Orthogonality & Visual Comparison Sheets (`p1-cmp-01`..`p1-cmp-07`):**
   - **`p1-cmp-03-prism-midpoint-to-plane.png` (`d(M, (ABB')) = √3/2`):** In BEFORE (`8427c879`), `u = A - H = (-1.5, 0, -3)` pointed diagonally down to `A(0,0,0)` and the 4-sided closed loop looked like a skewed parallelogram hanging below `A'B'`. In AFTER, `huongChanVuongGoc` aligns `u` along `A'B'` (`(-1.5, 0, 0)`), and the 2-segment L-bracket + initial dash from `H` forms a textbook right-angle marker on `(ABB')`.
   - **`p1-cmp-01-pyr-midpoint-to-plane.png` & `p1-cmp-04-pyr-midpoint-to-named-line.png`:** The 2-segment L-bracket connects seamlessly to the first dash starting at `H` without double-stroking the target edge or leaving a gap on `HM`.
   - **`p1-cmp-05-pyr-midpoint-to-result-line.png` (`d(M, H) = √13/2`):** In BEFORE, the measurement pill sat directly across the steep dashed segment `MH`. In AFTER, the `±10px` segment obstacles push the pill cleanly to the right of `MH`, exposing the entire dashed perpendicular and the L-bracket at `H`.
   - **`p1-cmp-06-cuboid-midpoint-to-result-line.png` & `p1-cmp-07-rb-derived-line-prism.png`:** Crisp 2-segment L-brackets at `B' ≡ H` and `B ≡ H`, with pills cleanly separated from the witness segments.
2. **P2 Mathematical Audits & Correction Layer in `report.md`:**
   - **Table 1.1 (`dot(u_world, v_world)`):** Accurately documents all 8 witness scenes with `dot(u_world, v_world) = 0.000000` and $\max_{P \in \text{target}} |\text{dot}(\overrightarrow{HM}, \overrightarrow{HP})| = 0.000000$.
   - **Section 2.1 & 2.2 (Midpoint $M$ & Distance Label Semantics):** Accurately verifies all 7 scenes against `compiler-scene-suite.mjs` prompts and explains the architectural distinction between point-to-plane (`d(M, (SAB))` with `anchor: "witness"`) and point-to-line with explicit `CONSTRUCT_FOOT_POINT` (`d(M, H)` with `anchor: "segment"`).
   - **Section 2.3 ($C'$ vs $(A'BD)$ 3D Distance Proof):** Mathematically exact: plane $(A'BD)$ through $A'(0,0,2), B(2,0,0), D(0,2,0)$ has equation $x + y + z = 2$, so $C'(2,2,2)$ has $x + y + z = 6 \ne 2$ and Euclidean distance $d_{3D}(C', (A'BD)) = |6 - 2|/\sqrt{3} = 4/\sqrt{3} \approx 2.3094 > 0$, supported visually by `visual/after/09-section-cube-A1BD-orbit.png`.
   - **Correction Layer (`CORRECTED_BY`):** Header line 8 of `report.md` explicitly records the correction of `scene3d-educational-finalization/report.md` §2.3 (`EDU-4`) regarding `marker: { u, v }` semantics in `quantity_annotations.py::_nhan_chung`.

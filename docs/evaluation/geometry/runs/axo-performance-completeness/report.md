# Axo — Performance, Mathematical Completeness & Cross-Family Acceptance

Date: 2026-11-04–05 (Asia/Bangkok). Status: **READY FOR USER REVIEW** (takeover completed from interrupted Codex session; no automatic human approval, merge, or push).

## A. Repository & Scope Hygiene

- **Worktree:** `.superpowers/worktrees/axo-pedagogical-integration`
- **Branch:** `integration/axo-pedagogical-construction-hardening`
- **Baseline (`START_BASE`):** `4ed8cb3e262280fe3bf6caab0045185a9bc0e52d` (clean detached baseline `.superpowers/worktrees/axo-performance-baseline`)
- **Product commit:** `34c779e1eb258240c595315db2219c788ba9462a` (`34c779e1`)
- **Protected user file:** `frontend/index.html` unstaged and untouched (`SHA256 = 3B8A5566454E42BA624C4611C82B792EC8ED1CAFC062C0041ADC11DEEB44A69F` verified before and after all steps).
- **Backend & live AI safety:** `0` backend product edits (`measured_system` unchanged: `118` files, `6809d79b51f6e47be1e8af03ae065563b2028fcd823c22a91b61600b242d7fad`, `CACHE_VERSION = 131`), `0` provider calls (`ALLOW_LIVE_AI = 0`). Root `main` (`bb61a804`) untouched.

## B. Root Causes & Minimal Fixes

| Symptom | Before evidence | Root cause | Minimal root-cause fix | After evidence | Verdict |
|---|---|---|---|---|---|
| Severe 3D orbit lag (~3–4 FPS) | `before-symmetric/receipt.json`, `before-complete-scenes/receipt.json`: 243–451 median renders inside one RAF timestamp (up to 941 max); 234.9–320.5 ms CPU/frame | `vong` cleared `rafId=0`, ran `renderSingleFrame(true)` whose `controls.update()` synchronously dispatched `change` and queued a frame via `wakeRenderLoop()`, and then `vong` unconditionally called `requestAnimationFrame(vong)` again, compounding pending RAF callbacks; raw `wheel` also bound `danhDauNguoiDungChinhCam` latching `controlsInteracting` after wheel end | Route loop tail through `wakeRenderLoop()` and bind raw `wheel` to `xuLyDoiDieuKhien` (`scene3d-view.tsx`) | `scene3d-frame-scheduling.test.ts` (RED → GREEN); `after-final/` + `after-dense-complete/`: `renders/frame = 1` (median & max), 6.9–7.0 ms median frame interval (142.9–144.9 FPS) | **PASS** |
| Thick-line rim GPU buffer churn during step scrubbing | `scene3d-rim-reuse.test.ts` RED (`rim-red.log`); `before-symmetric` leaked 192–384 uncollected buffers across 24 step toggles on curved-rim scenes (`createBuffer > deleteBuffer`) | `rimSegMap` keyed companions by `${node.uuid}:${pass.suffix}`; step-owner rebuilds allocate new Three.js UUIDs, orphaning previous companions | Key `rimSegMap` semantically by `${uniqueRimLabel}:${rim.objectId}:${pass.suffix}` while keeping in-place geometry/material updates (`scene3d-edge-visibility.ts`) | `scene3d-rim-reuse.test.ts` GREEN (same nodes/buffers across 30 alternating-radius rebuilds, disposed once); `stepResources` `createBuffer == deleteBuffer` on all 7 scenes | **PASS** |
| Verified requested numeric conclusions absent at final step | `goalCompletion` certified sphere `3` / `36π` and section `4` / `16π`, but `StudentPresentationPolicy` suppressed them even after construction completed | No final-step consumer for certified requested targets | Populate `finalConclusions` in `scene3d-student-presentation-policy.ts` and render `#dock-goal-conclusion` in `SimulationWorkspace.tsx` only when `completed` (`cuoi && !dangPhat`), `goalCompletion.status === "reached"`, `tapKetQuaCuoi` contains target ID, `provenance === "DERIVED_VERIFIED"`, and excluding `intermediate`/`measurement` auxiliaries | `scene3d-final-conclusions.test.tsx`, 6 updated policy/regression suites, `ui-final/receipt.json`, `visual-final/*.png` | **PASS** |
| Synthetic polygon test fixtures omitted section fill | `before-corrected-fixtures/receipt.json`: `cube-hexagon` `td_hex` not rendered when fixture used `render: "surface"` | Test-only synthetic fixtures in `axo-cross-family-scene3d-acceptance.test.tsx` used `"surface"` instead of backend Scene3D `"polygon"` carrier contract | Align synthetic `polygon3`/`section` test fixtures to `render: "polygon"` and lock full-pipeline visibility in `axo-cross-family-scene3d-acceptance.test.tsx` | `cube-pipeline.log`, `visual-final/cube-hexagon-angle-{0,1,2}.png` | **PASS** |

## C. Symmetric Performance & Resource Evidence

Environment: Production build (`tsc -b && vite build`), Chrome `157.0.8103.38` headed, `1440×900` CSS px, `DPR = 1`, ANGLE Intel UHD Graphics D3D11 (`0` network/provider calls). Frame intervals are computed from raw RAF draw timestamps in `continuous-orbit` with the first inter-phase interval excluded; `medianCadenceFps = 1000 / median_frame_ms`.

Authoritative symmetric baseline/candidate pairs on identical complete-polygon inputs:
- Baseline (`4ed8cb3e`): `before-symmetric/receipt.json` (`thiet-dien-chop`, `cau-cat-mat-phang`, `non-thiet-dien-truc`, `tru-thiet-dien-tron`, `dense-multi-solid`) + `before-complete-scenes/receipt.json` (`cube-hexagon`, `oblique-prism` with `render: "polygon"`).
- Candidate (`34c779e1`): `after-final/receipt.json` (scenes 1–6; interrupted at Codex rate-limit before scene 7 variants finished) + `after-dense-complete/receipt.json` (scene 7 `dense-multi-solid` completed on identical hardware/build), corroborated by full 7-scene `after-hardware/receipt.json`. Earlier `before-gpu/`, `before-hardware/`, `before-scenarios/`, `before-corrected-fixtures/`, `before-cube-complete/`, and `ui-acceptance/` are diagnostic runs and are excluded from acceptance claims.

### 1. Continuous 15-Second Orbit & 24 Step Toggles (Per Scene)

| Scene | Frame Median ms (Before → After) | Frame P95 ms (Before → After) | Median Cadence FPS (Before → After) | CPU/Frame Median ms (Before → After) | Renders/Frame Med/Max (Before → After) | Step Toggle Median / P95 ms (Before → After) | Step `createBuffer/deleteBuffer` (Before → After) |
|---|---|---|---|---|---|---|---|
| `thiet-dien-chop` | 256.9 → **6.9** | 465.3 → **7.1** | 3.9 → **144.9** | 252.5 → **3.8** | 382/785 → **1/1** | 71.2/112.6 → 91.0/144.6 | 5712/5712 → **5712/5712** |
| `cau-cat-mat-phang` | 257.0 → **7.0** | 2875.0 → **14.0** | 3.9 → **142.9** | 253.0 → **5.3** | 243/623 → **1/1** | 72.4/90.0 → 81.4/152.8 | 2700/2412 → **2412/2412** |
| `non-thiet-dien-truc` | 291.7 → **7.0** | 486.1 → **13.9** | 3.4 → **142.9** | 283.7 → **5.2** | 408/802 → **1/1** | 45.0/61.4 → **44.2/58.2** | 1932/1740 → **1740/1740** |
| `tru-thiet-dien-tron` | 312.6 → **7.0** | 944.5 → **14.0** | 3.2 → **142.9** | 317.0 → **6.3** | 297/640 → **1/1** | 50.8/68.5 → 68.8/103.8 | 2748/2364 → **2364/2364** |
| `cube-hexagon` | 312.5 → **7.0** | 555.6 → **13.9** | 3.2 → **142.9** | 312.6 → **5.9** | 297/630 → **1/1** | 78.2/88.8 → **77.6**/90.0 | 10004/9984 → **9984/9984** |
| `oblique-prism` | 236.1 → **6.9** | 444.5 → **7.1** | 4.2 → **144.9** | 234.9 → **3.2** | 451/941 → **1/1** | 46.1/60.0 → **43.8**/60.5 | 5064/5064 → **5064/5064** |
| `dense-multi-solid` | 319.5 → **6.9** | 590.2 → **7.0** | 3.1 → **144.9** | 320.5 → **2.5** | 404/803 → **1/1** | 61.8/85.9 → **55.2/65.6** | 5376/5376 → **5376/5376** |
| **Pooled (7 scenes)** | **270.8 → 7.0** (`n=401 → 13797`) | **548.6 → 13.9** | **3.7 → 142.9** | — | **— → 1/1** | **58.6/87.1 → 65.5/132.8** (`n=168`) | **0 net buffer leak after fix** |

Note on step-toggle latency: on `cau-cat-mat-phang`, `tru-thiet-dien-tron`, and `thiet-dien-chop`, toggling into the final step now mounts `#dock-goal-conclusion` (`MathDisplay`) in the dock, shifting pooled step-toggle median from `58.6 ms` to `65.5 ms` while eliminating `192–384` leaked GPU rim buffers per 24 toggles.

### 2. Interaction Variants, Navigation & Memory (`after-final`, `after-dense-complete`, `nav-before`, `nav-after`, `memory-final`)

- **8 Orbit/State Variants (pooled across all 7 scenes):** `reverse` (`7.0 ms` med / `13.9 ms` P95), `zoom` (`7.0 / 13.9 ms`), `selected` (`7.0 / 13.9 ms`), `hidden` (`6.9 / 13.9 ms`), `isolated` (`7.0 / 13.7 ms`), `collapsed` (`7.0 / 13.9 ms`), `after-steps` (`7.0 / 7.2 ms`), `returned` (`6.9 / 7.2 ms`) — all sustain **142.9–144.9 FPS** median cadence.
- **Navigation Latency (`n = 12` cycles, Before `nav-before/` → After `nav-after/`):**
  - Cold `/library` paint (`0` WebGL canvases mounted): `135.2 → 137.6 ms` median (`196.8 → 191.7 ms` P95).
  - Cold `/simulation/pyramid-cross-section` first 3D draw: `171.4 → 168.4 ms` median (`252.7 → 261.8 ms` P95).
  - Warm sample switch: `110.5 → 112.6 ms` median (`161.0 → 122.4 ms` P95).
  - Browser `Back` / `Forward`: `71.7 → 71.2 ms` / `108.9 → 109.7 ms` median.
  - Loading strategy assessment (`plan.md` item E): navigation is already ~71–171 ms median with `/library` mounting zero 3D canvases; no speculative bundle-splitting change was warranted.
- **22 Problem Switches + 3 Warmup Scenes (`memory-final/receipt.json`):** `WebGL contexts = 1` throughout; post-GC JS heap bounded (`15.40 MiB` at switch 0 → `17.94 MiB` at switch 12 → `18.67 MiB` at switch 21).
- **Unmeasured items (honest `NOT TESTED`):** Hardware GPU disjoint timer query elapsed time (`EXT_disjoint_timer_query_webgl2`) and React profiling-build component durations remain **NOT TESTED**; production React Fiber commit counts (`commits = 3` per 15s orbit) and main-thread RAF CPU callback durations were measured instead.

## D. Independent Mathematical & Pedagogical Audit

Independent Python `fractions.Fraction` oracle (`check-mathematics.py` → `mathematics.json`, zero application imports): **8/8 PASS**:
1. `cau-the-tich`: $R^2 = |A - I|^2 = 9 \Rightarrow R = 3$, $V = \frac{4}{3}\pi R^3 = 36\pi$.
2. `cau-cat-mat-phang`: $d^2 = 9, R^2 = 25 \Rightarrow r^2 = 16 \Rightarrow r = 4, S = 16\pi$.
3. `thiet-dien-chop`: exact midpoints $M, N, P$ and 4-vertex coplanar section at $z = 2$ (construction-only: `finalConclusions = []`).
4. `cube-hexagon`: 6 coplanar midpoint vertices on cube edges, uniform squared edge length $2$, strict cyclic turn sign, `render = "polygon"`.
5. `oblique-prism`: parallel translated bases $(1,1,4)$, $A'H \perp (ABC)$ with $|A'H|^2 = 16$, lateral edge $AA' \not\perp (ABC)$.
6. `tru-thiet-dien-tron`: cutting plane normal parallel to cylinder axis $OO'$, $r^2 = R^2 = 4 \Rightarrow r = 2$.
7. `non-thiet-dien-truc`: independent cross-product triangle area $\frac{1}{2}|AB \times AS| = 12$ (`area² = 144`).
8. `mp-vuong-goc-duong`: exact point-to-plane distance $d(S, (\alpha))^2 = \frac{50}{3} \Rightarrow d = \frac{5\sqrt{6}}{3}$.

Sphere-plane boundary regimes (`ui-final/receipt.json`):
- $d = 0$ (`greatCircleScene`): great circle passing through center $I$, zero duplicate reference equator, no fabricated numeric readout (`PASS`).
- $0 < d < R$ (`cau-cat-mat-phang`): orthogonal witness at $H$, right triangle $IHM$, solid/dashed intersection circle, final `4` and `16π` masked at steps 1–4 and shown at step 5/5 (`PASS`).
- $d = R$ (`tangentScene`): tangent foot $H$ with $KH \perp (\alpha)$, zero intersection circle rendered (`PASS`).
- $d > R$ (`nonIntersectingScene`): `.ws-math-contradiction-note` diagnostic shown, zero `#dock-goal-conclusion` (`PASS`).

## E. Visual, Interactive & Responsive Verification

- **Multi-angle 3D inspection (`visual-final/`):** 12 scenes × 3 camera angles = 36 screenshots inspected (`cau-cat-mat-phang`, `cau-the-tich`, `thiet-dien-chop`, `mat-cheo-sac`, `mp-vuong-goc-duong`, `non-thiet-dien-truc`, `tru-thiet-dien-tron`, `tru-truc-xien`, `true-oblique-cylinder`, `cube-hexagon`, `oblique-prism`, `dense-multi-solid`). Camera-dependent hidden-edge dashing flips cleanly across angles; tilted right circular cylinder (`tru-truc-xien`) preserves `OO' ⊥ OA` right-angle witness while genuine oblique cylinder (`true-oblique-cylinder`) omits perpendicular axis witness.
- **Interactive & Responsive Checks (`ui-final/`, `ui-mobile-recheck/`, `ui-width-1280/`, `zoom-check/`):**
  - 1-step sphere (`cau-the-tich`) Play/Pause formation progress (`0 < progress < 1` → `1`) with 1 WebGL context: `PASS`.
  - Reference point `X` selection keeping radius `IX`, hiding `X` keeping sphere `cau`, Undo button, `Ctrl+Z` scene undo vs `<input>` text-editing `Ctrl+Z` isolation: `PASS`.
  - Dock collapse/reopen preserving exact camera position, zoom reversal, and reset to geometric center: `PASS`.
  - Vietnamese slug → canonical English URL normalization + per-problem `Back` / `Forward` / `F5` step restoration: `PASS`.
  - **7 viewport widths (`360, 390, 430, 768, 1024, 1280, 1440 px`) × 5 families:** all pass card bounds, zero horizontal document overflow, `touch-action: none` on canvas, and selectable chips across steps (`responsive 360 cau-cat-mat-phang` had 1 locator timeout in `ui-final` and passed `3/3` consecutive repeats in `ui-mobile-recheck`).
  - **110% Zoom (`zoom-check/receipt.json`):** `PASS` via CDP effective CSS viewport/DPR (`1310 px`, `DPR = 1.1`, `scrollWidth <= innerWidth`); native Chrome browser UI `Ctrl+=` shortcut inside Playwright automation is recorded as `NOT TESTED`.

## F. Regression & Governance Gates

- Frontend Vitest: `121` files / `1,787` tests **PASS** (`0` failures), including `code-index-sync.test.ts` and `rules-hygiene.test.ts`.
- Production build: `npx tsc -b && npx vite build` **PASS** (`exit 0`).
- Candidate seal & offline governance: `EVALUATION_CANDIDATE.json` refreshed to `34c779e1`, `candidate_divergence.json` chained cleanly, `freeze_evaluation_candidate.py --verify` **PASS**, `check_publication_safety.py` **PASS** (`0` violations), and offline backend docs/seal/thesis-matrix pytest suites **PASS**.

## G. Acceptance Matrix & Next-Step Note

| Gate | Status | Evidence |
|---|---|---|
| Continuous 3D orbit & frame coalescing | **PASS** | `before-symmetric`, `before-complete-scenes`, `after-final`, `after-dense-complete`, `scene3d-frame-scheduling.test.ts` |
| Rim GPU buffer reuse & WebGL context stability | **PASS** | `scene3d-rim-reuse.test.ts`, `memory-final/receipt.json` |
| Independent `Fraction` math oracle & final verified conclusions | **PASS** | `check-mathematics.py`, `mathematics.json`, `scene3d-final-conclusions.test.tsx` |
| Cross-family 3D visuals (12 scenes × 3 angles) & sphere `d = 0, <R, =R, >R` | **PASS** | `visual-final/*.png`, `ui-final/{greatCircleScene,tangentScene}.png` |
| Responsive 7 widths (`360–1440 px`), interactions, URL & history | **PASS** | `ui-final`, `ui-mobile-recheck`, `ui-width-1280`, `nav-before`, `nav-after` |
| Desktop 110% zoom (CDP DPR=1.1 equivalent / native Chrome UI shortcut) | **PASS / NOT TESTED** | `zoom-check/receipt.json` (CDP DPR=1.1 PASS; native UI zoom shortcut NOT TESTED) |
| Hardware GPU disjoint timer & React profiler build durations | **NOT TESTED** | Production RAF callback CPU & Fiber commit counts measured instead |

**Pending Unimplemented Follow-up (For User Decision):** Per handover constraint, `#dock-goal-conclusion` (`KẾT LUẬN`) currently renders visible at the paused final step as scoped in this run. The user-discussed follow-up to **not automatically open the `KẾT LUẬN` panel at the final step** has **not** been implemented yet and awaits the user's explicit prompt.

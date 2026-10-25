# Final Scene3D acceptance — decision report

**SCENE3D_VISUAL_PARTIAL_WITH_GAPS. NO-GO for merging.**

Continuation on `research/scene3d-visual-correction`, from handoff `16b46d38`. Product remains `b8b3311b`; frozen candidate remains `c84e8620`. This run changes evaluation scripts and documentation only. No new renderer fix is claimed.

## F2 policy and the locked gate

Owner F2 is now explicit: normal section fill terracotta `#c85a32`; selected section fill remains terracotta; selected boundary cobalt `#2563eb`; hover boundary uses the existing teal `#0f766e`, distinguished from selection. On changing selection the previous section must lose cobalt. Polygon, circle and ellipse share this rule. A context-dimmed unselected boundary may be grey; it must not retain selected cobalt. Selection does not change dash policy.

`frontend/scripts/compiler-scene-replay-lib.mjs::assessCausalCanvasHues` lines 683–692 admits orange only if a rendered object has tier `du_kien_so` or `trung_gian`. It uses `max(40, round(total*2e-4))` as pixel tolerance. A selected section is `dich`; its legitimate terracotta fill therefore exceeds the tolerance while `cam.allowed=false`. Fill and boundary are not separated by that predicate. This is the precise conflict; changing the product fill would violate F2.

**Official Visual Suite remains 7/8**, inherited from the unchanged built candidate's official receipt. The failing family is `cross_section`, desktop/mobile, `canvas_role_hues.cam` and dependent gates. No official oracle, fixture, threshold, skip or result was changed. A new Full Official Suite was not run: no product/build/official-tool change occurred, and a new partial result cannot authorize replacing that gate.

On the **same 30 fresh selected-section captures**, replay of the locked hue predicate fails 30/30; V1 gives 19 PASS / 0 FAIL / 11 UNCERTIFIABLE; final proposed V2 gives **4 PASS / 1 FAIL / 25 UNCERTIFIABLE**. This 0/30 is a predicate-only comparison on three selected section scenes, not an Official Suite score. See `baseline-final.json` and the source receipt hashes. Polygon: 0/10 certified, circle: 4/10, ellipse: 0/10. No UNCERTIFIABLE became PASS merely because a label hid the boundary.

## Proposed V2 and negative controls

`section-role-oracle-v2.mjs` reuses V1's palette-composite distance and per-object fill/boundary measurements. Conics use source center/normal/axes/radii, an independent cross-product frame, 257 intervals with a different phase, and analytic outward normals versus the eye in payload coordinates. It does not import renderer geometry or use renderer hidden flags as expected mathematics. Polygon face visibility reuses the existing independent evaluator with validated parent faces; it does not invent visibility without a supporting face.

Local missing-ink runs supplement global arc coverage. For curved dashed boundaries the permitted blank interval derives from the declared two-off-in-96-slot presentation cadence, projected maximum angular speed, the unchanged pixel search windows and raster rounding. The curve's independent discretization does not adopt the renderer's 96-chord frame/phase. A hidden polygon without an independent dash-gap bound remains UNCERTIFIABLE. Unsupported other regions, partially masked boundaries, and edge-on front/back overlap remain UNCERTIFIABLE. Entire masking is not evidence of a missing boundary.

This is **a presentation measurement, not a proof of exact backend mathematics or general visibility correctness**. Source contracts and source conic parameters still require backend authority. Normal/hover behavior is checked by existing product material tests, not certified by this selected-state pixel evaluator.

| Negative control | Evidence | Outcome and limit |
|---|---|---|
| Contiguous 20% loss of a hidden arc | Node synthetic independent conic | V1 false PASS reproduced; V2 FAIL |
| 56 px missing from a 160 px hidden polygon edge | Node synthetic, declared 20 px dash bound | V1 false PASS reproduced; V2 FAIL; absent bound is UNCERTIFIABLE |
| Partial label masking / complete overlay | Node synthetic | UNCERTIFIABLE, not full certification |
| Edge-on front/back coincidence | Node synthetic | UNCERTIFIABLE |
| Tilted model / camera | Node source conic inverse-model rotation | Independent normal classification agrees with transformed eye |
| Tiny second boundary incorrectly cobalt | Node synthetic | Per-object FAIL, irrespective of global blue share |
| Wrong parent / malformed face / degenerate face | Node source scenes | No invented visibility or crash; source unsupported |
| Correct fill, wrong boundary (terracotta or wrong blue inside hue band) | Real browser shader swap, circle high view at both widths | 4/4 detected |
| Correct boundary, wrong fill (wrong orange inside hue band or hidden fill) | Real browser shader/fill hook | 4/4 detected |
| Select another point after selecting the circle | Real browser click | 2/2 detected; target identity differs |
| Wrong displayed point name | Corrected real DOM control, 9 scenes × 2 widths | 18/18 detected; source notation compared as exact merged-name tokens |

The browser fault campaign has 2/2 certified baselines and **10/10 detected faults**, no retries/errors. It does not certify faults on polygon/ellipse views that were not certified unfaulted. Curved missing-arc controls are synthetic; no claim of a real shader-injected partial arc erasure.

## Unresolved transition discrepancy: stop checkpoint

`baseline/ellipse-cylinder-p6-1440-low-none.png`: V1 PASS; V2 FAIL. Source-analytic front interval 91 is ~4.07 CSSpx long and has 4/12 cobalt-covered samples. The hidden arc itself scores 0.7188 and passes; local missing-run check finds no long gap; no label masking caused this failure.

The discrepancy is consistent with the renderer's 96-chord midpoint visibility switch versus the finer analytic transition. **Cause is not established**; no renderer repair, threshold relaxation or FAIL→PASS reinterpretation was applied. Exact transition handling needs a separately reproducible mathematical regression or an Owner decision on the permissible rendering approximation. This is the requested checkpoint before a wider visibility rewrite.

## Camera, labels and performance

Fresh motion evidence covers 9 scenes × 2 widths (1440×900 DPR1; 390×844 DPR2), default, quarter turn, back, high and low. Actual camera vectors/matrices are in each receipt; these are relative OrbitControls views, not asserted cardinal camera calibrations. Scenes: pyramid section, triangular prism, cuboid, sphere cut, oblique cylinder, cone generator, cone axial section, multi-solid composition and cylinder ellipse. The old 52-row family matrix is retained separately; it is not a new measurement of every family.

- Scene JSON unchanged in 18/18 sequences; no duplicate visual owners in recorded snapshots. Source point names matched in sampled frames. Corrected second-selection transitions: 18/18.
- Existing solid-edge IDs changed across 3–5 recorded states in polyhedron scenes. Curved primitives are not fully represented by that edge-ID hook; one ID signature on a curved scene does not prove frozen visibility.
- CPU synchronous callback time summed by rAF timestamp: per-row p95 **1.8–6.7 ms**, max observed 17 ms, SwiftShader and instrumented desktop. This excludes GPU completion and is not real-device certification.
- WebGL creations in the mixed sequence: **64–566 buffers**, plus programs/shaders. Mouse hover, reset and UI work are included; this is **not** an isolated orbit-allocation verdict. Frozen T3 orbit evidence is unchanged. Allocation-free motion is not certified here.
- A screen-space heuristic found **112 suspected layout jumps** (offset changes >20 CSSpx with source anchor movement <5 CSSpx in ≤100ms). It compares source-projected anchors, not rederived geometry. They are review flags, not 112 confirmed bugs; no temporal continuity PASS. Multi-solid composition and mobile cuboid dominate. Captures cap label traces at 240 snapshots per sequence, so some later frames are unobserved.
- Right-angle witness ID is present for the pyramid distance case, and its square mark was visually inspected. Mathematical certification of every mark's two operands/foot under all views remains incomplete. Existing 82 targeted tests include certificate-driven annotations, prime notation and hover for all three region types.

`motion/receipt.json` retains an **invalid original wrong-name control**: the substring comparator accepted letters in `WRONG_LABEL_NEGATIVE_CONTROL` (e.g. A/O). Its `row.pass` must not be cited as complete acceptance. `label-controls/receipt.json` uses exact `≡`-separated tokens and an invalid name; all 18 controls and second-selection checks pass. `motion-summary.json` distinguishes these attempts. No failed output was overwritten.

## Verification and provenance

`provenance-verified.json` freshly verifies detached `svc-cand` at `c84e8620`, clean, candidate hash match (118 measured files), no product diff, and identical frontend/backend trees. The three served product modules match their complete local source hashes after LF normalization. Existing Vite on 3156 was reused; no process/cache/dist of another account was changed. The candidate retains `cacheDir: ".vite-cache"`.

Previous Full T3 is valid for the unchanged product: 11,923 pytest passed, 1 skipped, 2 deselected, 15 xfailed; 1,378 Vitest passed; build/typecheck PASS. The original stdout/stderr hashes were rechecked against their receipt and match. Full T3 was **reused, not rerun** for evaluation/docs-only work. No new T3 skipped test or threshold change.

Fresh checks: 40/40 Node oracle tests; 82/82 existing targeted product tests (unified materials, presentation, annotations); syntax checks and `git diff --check`. Initial system-Python lacked FastAPI; the existing project venv verified successfully. Provenance attempt 1 failed to parse Vite's single-quoted raw source export; the corrected verifier's separate output passes. These were harness/environment failures, not product failures.

Measurement class is development visual evaluation, not blind or independent. Evaluation scripts were uncommitted at capture; corrected evaluation is replayed against original hashed PNGs and pins the final oracle hash. This does not change product candidate identity or promote development captures to official evidence.

## Decision

F2 design is resolved by the Owner instruction; official gate adoption is unresolved. V2 is useful for finding errors and explicitly exposing uncertainty, **not ready to replace the official gate**: polygon completeness lacks a dash bound and the ellipse transition remains red. Therefore no adoption patch is recommended for execution in this run. The conceptual gate diff is to measure fill/boundary and each selected/unselected object separately; the existing global orange count cannot be simply exempted without that evidence pipeline.

`INDEPENDENT_REVIEW_PENDING`. `HUMAN_VISUAL_APPROVED=PENDING`. Internal AI review found and prompted evaluator fixes, and is not independent Owner review. No merge, push, Hybrid production activation, default-mode change or live provider request occurred. Stop at the Owner gate; see `handoff.md`, `visual-review.md`, `independent-review-packet.md`, and `hybrid-plan.md`.

# Scene3D Claude → Codex takeover

Status: **SCENE3D_VISUAL_PARTIAL_WITH_GAPS**. This is not Owner visual approval or permission to merge. Start with [the 15-frame review sheet](owner-review.png); open the original PNGs below for detail.

## Preserved takeover

Claude source: `.superpowers/worktrees/scene3d-visual-correction`, branch `research/scene3d-owner-math-visual-final`, candidate `08929b893337e770649b9d854c8c71c4434edc29`. Preserved commits `fd0073e9`, `63daf8bc`, `a5fbb026`: plane border classification, readable/minimal witnessed right-angle marks, auxiliary plane presentation and label hysteresis/offset continuity.

The dirty root at `fe9f5554` was not edited. Binary working/staged patches and file contents, including untracked and relevant ignored Claude evidence, are in root `.superpowers/preservation-scene3d-codex-20261026/`: 1,679 files, no read errors, ZIP and per-file SHA256 verification MATCH. See its `manifest.json` and `checksums.json`. The only uncommitted tracked Claude diff removed a blank line from `FIXED_ISSUES.md`; it was preserved, not reverted or committed here. Its untracked handoff still contained `INTERNAL_REVIEW_PLACEHOLDER`; it is not treated as completed review.

Continuation: `.superpowers/worktrees/scene3d-codex-takeover`, branch `research/scene3d-codex-takeover`. Product `511a48c777c187ff92d219185214f882e09726b0` (initial fix `7c4162cc`, internal-review fixes `511a48c7`). Frontend source Git tree `102ccee8e3a47f6706472de40ca41dd7e2904e1b`. Clean detached freeze `e1ebc72cd3968abfe752303089efc8cb7441abe6`, measured hash `ee474c819688426f8959daf2129f0273eb3217f039909b8ad9cade0ed740ae9d` (118 files). The manifest was generated with `cay_lam_viec_sach=true`; verification runs in the separate Codex-owned `verify-scene3d-codex-takeover` worktree.

Visual/B3/Sphere and Vite candidates were inspected; their branches/worktrees were not merged, modified or deleted. Existing `cacheDir: ".vite-cache"` retained. No web design/CSS/layout files changed. `LLM_ONLY`, cache129, Mode A/B and inference architecture retained; live provider requests 0. The reference HTML exists at `C:\Users\Bunny\Downloads\matphang.html`; selected drawing functions were inspected as presentation examples, not imported as algorithms or controls.

## Renderer changes and verification

- True conic sampling plus bisection replaces whole-chord midpoint classification. The independent cylinder tangency regression was RED at a boundary error of 0.0698187 world units (limit 0.0002), then GREEN.
- Standalone spheres show one world-space great circle with `REFERENCE_CURVE`, source object ID and `authoritative:false`. It is not inserted into the scene, has no picking, no invented point or label, and uses camera-dependent front/back spans. Plane/real-section scenes suppress it. The sample's authoritative centre is **I**, not O; the renderer does not rename it.
- Internal review found a subprobe visible arc near sphere tangency and stale classification after a fixed-camera object transform. Both have new RED → GREEN tests. Host-quadric tangent roots seed arbitrarily short host front arcs; rim/occluder matrices invalidate cached visibility.
- Point occluders compile lazily and once per uncached update. Camera-independent rim buffer capacity is reused. Existing camera controls and labels were retained.

Focused conic/reference regression: **6/6**. Geometry domain: **847/847 across 43 files**. Build/typecheck: **PASS**. Independent exact rational geometry checks: **56/56** (`verification/math.json`). Machine summary and source hashes: `verification/product.json`.

Internal review: first round 2 Important + 1 Minor; delta review all addressed, targeted 18/18, no new Important findings. **Independent review PENDING; human visual approval PENDING.** Detached execution is a machine verification, not an independent review.

## Visual evidence and gates

`before/receipt.json`: 48 baseline frames, product frontend archived from `08929b89`, isolated server 3172. `after/` is an interrupted exploratory capture with mixed HMR source and is **not acceptance evidence**. `final/receipt.json` contains 204 final-code frames: 17 fixtures × 6 camera gestures × 2 viewports, 0 page errors. `steps/receipt.json` contains 18 construction-step frames, 0 page errors. Camera matrices, viewport and source commit are retained. The capture filename `half` is the rear view (~180°); inherited filename `back` is a full-turn closure (~360°), not a rear-view certificate. See `verification/camera-interpretation.json`.

Mandatory review frames:

- A: [standalone sphere](final/cau-the-tich-1440-default.png): source centre I, front solid/back dashed reference, no cutting plane. Compare [before](before/cau-the-tich-1440-default.png).
- B: [sphere cut by (P)](final/cau-cat-mat-phang-1440-default.png): actual section circle, no extra reference. Compare [before](before/cau-cat-mat-phang-1440-default.png).
- [Plane (MNP)](steps/thiet-dien-chop-step06.png): visible front border solid; occluded rear border dashed; illustration border distinct from construction.
- Cone base: `final/non-duong-sinh-1440-default.png`.
- Oblique cylinder: `final/tru-truc-xien-1440-default.png`.
- Ellipse transition: `final/family12_cylinder_ellipse_section-1440-low.png` and proposed role-aware observations.
- Prism/cuboid/right angles: `final/triangular_prism_positive-390-half.png`, `final/cuboid_positive-1440-default.png`.
- Selection fill/boundary: `role-aware/`, kept separate from Official Visual Suite.
- Labels/orbit/resources: `motion/receipt.json`, 18/18 checks: source JSON unchanged, no duplicate edge owners, zero label-source errors, Mode A final-label suppression and selection/negative controls. Seven heuristic jump flags remain (cuboid and multi-solid); these need visual review, not a false zero-jitter claim. Timing is an observation under SwiftShader and concurrent verification, not a device performance certificate. Mixed-sequence GPU maxima are 566 buffer creations, 12 programs, 24 shaders, 0 textures; selection/reset rebuilds are included, so this is not an orbit-only zero-allocation certificate. Camera-orbit buffer reuse is separately covered by the conic regression.

Official scenario results: **7/8** on this product. `cross_section` fails `canvas_role_hues.cam` and dependent evidence gates on desktop/mobile: the locked hue gate conflicts with the retained terracotta fill/cobalt boundary policy. The oracle and thresholds were not changed. `verification/official-scenarios.json` explicitly aggregates five completed scenario records from an interrupted run and three from its scoped continuation, with hashes and failure paths; it does not masquerade as one uninterrupted full-run receipt. Two earlier sandbox transport attempts (`WS_OPEN_TIMEOUT`, then `CDP_TIMEOUT: Page.enable`) did not complete a scenario and contribute no PASS result. The complete scoped continuation ran outside that sandbox transport restriction. Forty-nine inputs were rebound with **zero envelope and zero oracle changes** (`official-inputs-rebinding.json`). Owner decision on F2 remains required.

Proposed role-aware V2 observations remain separate: **2 PASS / 10 UNCERTIFIABLE / 0 FAIL**, all 12 rows completed, 0 runtime errors. They do not replace the Official result or certify the other ten views. The selected ellipse at desktop/low is [FAIL before](ellipse-before/ellipse-cylinder-p6-1440-low-none.png) on archived `08929b89` and [PASS after](role-aware/ellipse-cylinder-p6-1440-low-none.png). These use identical source conic and gestures, with damping residuals rather than bit-identical camera floats: independently projected boundary positions differ by at most 0.000806 CSS px (desktop) / 0.000375 px (mobile). See `verification/ellipse-projection-comparison.json`; the analytic regression supplies the exact mathematical comparison. Mobile/low remains UNCERTIFIABLE.

## Full T3 and freeze

**FULL_PRODUCT_GATE_PASS** on clean detached candidate `e1ebc72cd3968abfe752303089efc8cb7441abe6`:

| Gate | Result |
|---|---|
| Backend | 11,923 passed, 1 skipped, 2 deselected, 15 xfailed, 2 warnings |
| Frontend | 1,386 passed across 81 files |
| Typecheck / production build | PASS |
| Thesis demo replay / crash surface | PASS |
| Source tree before and after | Clean |
| Post-freeze verification | MATCH, exit 0 |

Receipt: [verification/t3.json](verification/t3.json), with SHA256 and byte lengths of both streams. Raw logs remain in root `.superpowers/scene3d-codex-t3-clean/`; no raw tracebacks/provider outputs were added to Git. Reproduction wrapper: `tools/run-t3.py`, calling the unchanged `frontend/scripts/full-gate.mjs` with Python 3.12, `ALLOW_LIVE_AI=0` and an isolated temp path. No product edits were made after freezing.

The first invocation was interrupted and has **no valid final T3 receipt**. Its Windows backslash temp argument was parsed incorrectly, producing Codex-owned temporary files inside the verification checkout. Those files were preserved outside the candidate, not deleted (`verification/temp-preservation.json`). A subsequent pre-flight refused the dirty checkout before running any tests. Four focused environment checks then passed, the checkout was confirmed clean, and the valid final invocation above completed. The first attempt's final counts/exit/termination cause remain UNKNOWN; its logs and observed failure hint are retained in `verification/t3-interrupted-attempt.json`. No report, oracle, threshold or product source was altered to make it pass.

`npm run dev` was verified with the preserved `.vite-cache` setting. The Codex-owned review server at **http://127.0.0.1:3173/** serves the correct source including the sphere reference (`verification/dev-server.json`). It was started with a hidden window; no root checkout or other agent's server was replaced.

## Remaining gaps and acceptance limits

| Area | Result / limitation |
|---|---|
| Pyramid + (MNP), triangular pyramid | Official families PASS; 18 step frames and final multi-camera frames, including a readable MNP solid/dashed border |
| Right prism and cuboid | Official families PASS; final camera and witness evidence. Prism cutting-plane browser coverage is not certified here |
| Oblique prism | Not certified by this run's browser matrix; no invented right-prism assumptions |
| Standalone sphere | Reference regression passes; images A and rotated views require Owner review |
| Sphere–plane | Real circle preserved, reference suppressed; image B requires Owner review |
| Cylinder, oblique ellipse | Analytic transition regression and selected ellipse desktop/low role check PASS; final frames cover horizontal/oblique cylinder and ellipse |
| Cone and axial section | Existing finite-solid construction retained; default/rotated/high/low desktop/mobile frames and motion checks, no fake closed conic added |
| Orthogonality | Backend certificates remain the authority; no screen-space inference |
| Labels/selection | Motion controls 18/18; seven heuristic label flags remain. Fill/boundary policy retained; Official F2 unresolved |

Known gaps carried from Claude: G1 missing BC ⟂ (SAB) witness; G2 internal `Plane3(...)` learner text/incorrect event kind; G3 unnamed `mpb`; G4 no complete line–plane/projection/angle product scene. These require authoritative producer changes and were not invented in the frontend. G7 existing `o.id === "day"` in auxiliary classification remains. G9 curved offline scenes do not establish live NL E2E. General thin unrelated occluders can produce intervals below the finite curve probes; analytic seeding guarantees here apply to curves on their host quadric. Full label-overlap/all-scene certification is not claimed.

The standalone-sphere/real-cut images and the current-step suppression path were exercised in the product. Tangent/no-intersection sphere-plane and clipped finite-conic browser variants, oblique-prism cutting planes and a complete all-label overlap oracle are not certified by this run. Therefore the full P10 READY label is not issued even though T3/MATCH pass. Reused modules: existing renderer, visibility, conic primitive, style roles and capture/oracle tools. Created product modules: none. Duplicate/dependency-cycle check: new helpers extend the existing visibility module; no reverse import into the renderer or parallel geometry authority.

## Next campaign proposal (not started)

Propose **Hybrid source-to-scene authority and reasoning closure**, after Owner accepts the Scene3D gaps or they are closed. First produce a scoped contract and independently authored offline holdout for NL → TypedFacts V2 → Registry/Planner/Engine → Scene3D. Cover distance, angle, finite sections and volume/area combinations with exact independent oracles, source spans, consistency checks and honest refusal. Close witness/notation/event provenance at the producer rather than synthesising it in the renderer.

GO only when the chosen offline holdout has zero wrong-served cases, preregistered family/refusal criteria pass, all rendered entities have source authority, end-to-end envelopes retain the visual gates, and Owner approves scope. NO-GO on ungrounded/contradictory facts, unsupported geometry disguised as a closed conic, or contaminated holdout. Live pilot, default-route replacement and production require separate Owner GO and the migration gates. No Hybrid implementation was started here.

Do not remove root, Claude, B3, Sphere, continuation, baseline archive or verification worktrees/evidence automatically. The two Codex-owned worktrees and isolated baseline archive can be considered for cleanup only after Owner approval and evidence preservation.

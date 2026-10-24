# Final owner handoff: Scene3D high-fidelity HTML visual port

Authorization `GO_SCENE3D_HTML_VISUAL_FIDELITY_PORT_LOCAL_ONLY` (2026-10-24).

**Classification:** `SCENE3D_HTML_VISUAL_FIDELITY_READY_FOR_OWNER_REVIEW`. Human visual approval is **NOT_APPROVED** (owner review pending). No merge, no push, no live provider, Hybrid production unchanged (NO-GO).

## Identity

| Item | Value |
|---|---|
| Branch | `research/scene3d-html-visual-port` (local only) |
| Base | `research/scene3d-unified-visual-language` `8618d84c` + verbatim checkpoint of the owner's uncommitted V6.2 session `3bfc8dd0` |
| Product commits | `60b556bc` (port), `656759fc` (mark sizing), `852f6501` (review fixes) |
| Candidate freeze | `13d28b84` (114 files, `9bf35a1d6f4c3b3e…`, product `852f6501`) |
| Full T3 | **FULL_PRODUCT_GATE_PASS** at `13d28b84`, clean detached worktree; pytest 11442, vitest 1195, build, demo 5/5, crash 6/6; post-T3 `--verify` MATCH |
| Root checkout | untouched; the owner's uncommitted V6.2 files remain there byte-identical to `3bfc8dd0` |

## P0: work protection

The `PHONG_CACH_SCENE3D` campaign was found in two layers:
- committed on `research/scene3d-unified-visual-language`;
- a further ~650-line uncommitted V6.2 session in the root checkout (on branch `wave3a`), with no owner record and no live writer.

The owner confirmed it as theirs and handed it over. It was committed verbatim (20/20 files blob-identical, vitest 1194/1194, tsc clean) on a new branch from `research/scene3d-unified-visual-language`. The root checkout was not modified. No reset/clean/force/ACL action was taken.

## Answers

1. **Reproduced from the HTML.** Porcelain shell, unlit and two-pass (front 0.12, back 0.09). Terracotta section and outline. Violet plane at 0.065 with an always-dashed border. Slate visible and dashed hidden edges at the reference stroke/figure ratio and dash cycle. Teal auxiliary ink. Two-segment right-angle squares. Role-styled labels (vertex, section vertex, derived point, plane). Ivory canvas gradient. SGK elevation (22.4°) as the camera pull. Mapping: HTML_VISUAL_PORT_MAPPING.md.
2. **Still different, and why.**
   - Figure shape: the HTML shears its base and fakes section points; AlgoSim renders true geometry.
   - Strokes are screen-space at the reference ratio, not world-space.
   - Marks are 8–12 px, not the reference's ≈ 36 px.
   - Section fill is 0.32, not 0.27 (gate, owner decision).
   - The plane shows when requested ("Hình phụ" or selection).
   - The default camera keeps the scored, degenerate-proof view.
   - The demo's toolbar and opacity slider were not ported (no UI redesign in scope).
   Details: HTML_VS_ALGOSIM_SCREENSHOTS.md.
3. **Unlit materials for color-keeping layers.** Yes: shells (polyhedral and curved), section, plane and faces are all `MeshBasicMaterial`. Only point markers stay lit.
4. **12 % opacity close to the reference.** Yes: same color, same two-pass alpha model; side-by-side in `verification/html-vs-algosim/`.
5. **Right-angle marks small and clear.** World size equals the 8–12 px target within ±0.7 % at default, zoom in and zoom out. On screen the longer leg measures 6.5–10.5 px, lower where perspective foreshortens. During a pure orbit the size is frozen (up to 14.6 px seen) to keep the orbit allocation-free. Duplicates are suppressed. RIGHT_ANGLE_MARKER_VALIDATION.md.
6. **Violet plane works.** Yes, when requested: engine-derived patch, violet fill, dashed border kept after span splitting (test with fault injection). The old suppression of the border when a closed section existed is removed.
7. **Is the SGK camera easier to read?** It is modest. The scorer already chose 15–35° elevation; the stronger pull to 22.4° changed few scenes (e.g. DEV03 azimuth 40° → 30°). Forcing the HTML direction exactly produces a degenerate view on DEV03, which the scorer avoids, so the fixed preset was not adopted.
8. **Effect on geometry or provenance.** None. Frontend only, 0 backend files. No coordinate, name, provenance, topology or step change. The boundary guard (no geometric inference in the view) passes. GEOMETRY_SEMANTICS_REGRESSION.md.
9. **LLM_ONLY regressions.** None: no backend, route, cache or model-surface change; Full T3 PASS; `CACHE_VERSION` unchanged (frontend-only).
10. **Candidate, Full T3 and browser results.**
    - Candidate `13d28b84`; Full T3 PASS (above).
    - `scene3d-orbit-gate` p1/p6/p7 **DAT** with 0 GPU allocations, on the frozen build. The V6.2 checkpoint failed this gate (312/662 allocations); two root causes were fixed.
    - Section-fill distinguishability probe PASS on 6 scenes (ΔE76 20.42–20.44 ≥ 20).
    - 12 default-camera and 16 paired captures with 0 console/page errors and 0 forbidden requests; 24 marker captures (the marker probe does not record console output).
    - Independent review **PASS_WITH_LIMITS**; all actionable findings fixed (INDEPENDENT_REVIEW.md).
11. **Ready for owner visual review.** Yes, as `SCENE3D_HTML_VISUAL_FIDELITY_READY_FOR_OWNER_REVIEW`. The machine gates are green and the screenshots are in place. The owner's eye is the remaining gate.

## Limits and open items

- The official `compiler-scene-suite` (which owns SECTION_FILL_DISTINGUISHABLE at the first closed-and-filled step) was not run: it needs a suite manifest bound to the new candidate. The probe used the same ΔE and thresholds at the final step.
- The fixes in `852f6501` were verified by tests, fault injection and gates, not by a second independent review.
- The branch is 59 commits behind `main` (inherited from its base). Integrating requires a merge, with likely conflicts in `scene3d-view.tsx`; not attempted.
- Changing the default view pull and the stroke widths makes older stored browser baselines stale; they were not re-recorded.
- Worktrees kept: `.superpowers/worktrees/scene3d-html-port` (branch) and `.superpowers/worktrees/t3-b1b2` (measurement, detached). Both have `frontend/node_modules` as a junction: `rmdir` it before `git worktree remove`.

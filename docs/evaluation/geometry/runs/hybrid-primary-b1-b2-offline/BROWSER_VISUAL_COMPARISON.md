# Browser visual comparison (owner visual reference)

Status: `SCENE3D_VISUAL_SPEC_ONLY` with runtime previews. **HUMAN_VISUAL_APPROVED is not claimed**; the owner has not reviewed these images.

## What was captured

Real screenshots of the running product (Vite dev server, headless Chrome with SwiftShader), not generated images. Evidence lives in `verification/visual-reference/`: PNGs, `receipt.json` (per-capture SHA-256, camera, step, override counts), `capture.mjs` and `vite.capture.config.mjs`.

| Field | Value |
|---|---|
| Source commit | `f72ccc82` (product = `c3c1eb80`, measured hash `71dd6aa6…`, same tree as the T3 attempt-4 PASS) |
| Tree | no tracked change; one untracked docs file (attempt-4 T3 receipt) during capture, so receipt says `tree_clean: false` |
| Input | actual B1/B2 service wrappers, `results/offline/fixtures.json`, SHA-256 `1abad7c5…` (same file as Codex's browser acceptance) |
| Loading | `docPhanHoiHybrid` -> `store.loadEnvelope` / `loadUnsupported`, as in `check-adapter4-browser.mjs` |
| Network | only `/api/health` and `/api/auth/me` mocked; 0 forbidden requests, 0 console/page errors in 62 captures |
| Step | final construction step (slider max) for every served scene |
| Camera | product default fitted camera; identical across all variants of the same case and viewport (10/10 groups) |
| Viewports | 1440×900 and 390×844, deviceScaleFactor 1 |
| Vite cache | private `cacheDir` (`vite.capture.config.mjs`), because shared `node_modules/.vite` is Codex-ACL'd and cannot be rewritten |

## Variants (no product file changed)

The product scene is reached through three.js's `__THREE_DEVTOOLS__` observe hook, installed by Playwright init script, and materials are changed after the scene settles.

- `before`: unmodified product C0.
- `after`: reference tokens as a preview only. Shell `#7C8B9E` at 0.12; section fill `#C85A32` at 0.27; section lines `#F59E0B -> #C85A32`; plane `#7C3AED -> #6D28D9`; derived points `#DC2626 -> #C85A32`; canvas gradient `#FFF -> #F8F6F1 -> #EFECE4`.
- `shell-0.04 / 0.12 / 0.20 / 0.30`: only shell opacity changed (color unchanged).

Geometry, visibility classification, depth layers and labels are untouched in every variant.

## Scenes

| Case ID (fixture) | Owner requirement | Captures |
|---|---|---|
| CORPUS-DEV01-construct | S.ABCD, quadrilateral section | 6 variants × 2 viewports |
| CORPUS-DEV03-construct | S.ABC, triangular section | 6 × 2 |
| CORPUS-DEV10-prism-area | prism with section | 6 × 2 |
| PARA-0 | DERIVED_FRESH section vertices + derived pyramid S.MNPQ | 6 × 2 |
| PERP-square-third | hidden edges and perpendicular/altitude marks | 6 × 2 |
| NEG-missing-height | refusal | before × 2 (page) |

## Observations (Claude, from viewing the images; not owner review)

1. **Hidden section edges are hard to read in C0.** In the prism, section edges from M run behind the front lateral face and are dashed. In amber on an amber fill they read as nearly continuous; terracotta dashes stand apart from the fill (`zoom-prism-section-edge-before-after.png`). This is the strongest evidence for changing section **outline** color.
2. **Lit section fill does not reproduce the reference hue.** With 0.27 under `MeshStandardMaterial`, fill renders as dull red-brown rather than terracotta. Hue must be tuned in the lit renderer, and fill opacity is guarded by `SECTION_FILL_DISTINGUISHABLE`. Do not copy numbers from the unlit reference.
3. **Shell at 0.12 is clearly lighter than C0's 0.22.** Edges and dashed hidden edges stay legible. At 0.30, the lower half of the pyramid greys out and hidden dashes lose contrast, matching the computed 2.73:1 (SCENE3D_VISUAL_SPEC.md §3). At 0.04 the solid nearly disappears as a volume.
4. **Face/section color collision (C0 and preview).** The prism top face A′B′C′ is filled with the same `MAU.polygon` family as the section. A base or face can therefore read like a section. The uncommitted root-checkout rework adds `vaiTroMien` base/section roles, which addresses exactly this.
5. **Labels.** Section vertices (incl. DERIVED_FRESH) show construction dots but no label at the final step in both before and after. This is product behaviour, not theme. Coincident points do occur: in PERP-square-third and CORPUS-DEV03 the foot coincides with A, and the product merges them into one label `A ≡ H ≡ H1` instead of overlapping text. No overlapping labels were seen in the inspected images. The derived foot dot is still C0 red `#DC2626` in `before`.
6. **Depth artifacts.** None observed: the plane never covers the section, and shell overlap is bounded. The preview did not change render order.
7. **Refusal** shows the learner reason, no canvas and no technical code (1440 and 390).
8. **Mobile 390×844** (inspected: CORPUS-DEV03 `after` page, NEG-missing-height). The scene fits the canvas below the controls; the merged label stays readable. Not every mobile image was inspected individually.

Images Claude viewed directly: CORPUS-DEV01 1440 before/after/shell-0.30, CORPUS-DEV10 1440 before/after (+ zoom), PARA-0 1440 after, PERP-square-third 1440 before, CORPUS-DEV03 390 after page, NEG-missing-height 390 page. Others are recorded with hashes but were not individually reviewed.

## Limits

- The preview cannot test a real BackSide/FrontSide two-pass shell (that requires code), so `after` keeps the product's single DoubleSide mesh.
- No dark-mode, orbit sequence or construction-step series were captured. Only the final step at the default camera.
- No independent visual reviewer; no owner approval.

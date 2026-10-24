# Browser acceptance (visual–Hybrid integration)

## Setup

- Source: clean detached worktree `t3-b1b2` at `b99afd32` (product `a9d05dda`). `git status --porcelain` was empty before and after every run.
- Server: Claude's own Vite dev server on `127.0.0.1:3115`. It used a private dep-cache dir (the shared `node_modules/.vite` is Codex-ACL'd) and was stopped afterwards.
- Codex's server on 3117 serves the old `13d28b84` and was not used or stopped.
- Browser: Chrome headless, SwiftShader.
- Network: every non-local request is aborted; `/api/health` and `/api/auth/me` are stubbed offline.
- 0 model calls.

Receipts are under `verification/browser/`.

| Check | Command | Viewports | Result | Receipt |
|---|---|---|---|---|
| Adapter /4 consumer | `node scripts/check-adapter4-browser.mjs <out> ../docs/evaluation/geometry/runs/visual-hybrid-integration/integrated/offline/fixtures.json` | 1440×900, 390×844 | **`FRONTEND_CONSUMER_ACCEPTANCE_PASS`**: 94 rows (44 SERVED, 50 REFUSED = 22 + 25 cases per viewport), 0 errors, `tree_clean: true`, fixtures sha256 `b2e87009…` | `adapter4/receipt.json` |
| Orbit gate | `node scripts/scene3d-orbit-gate.mjs --ra <scratch>` (builds `dist/` from the clean tree) | gate default | **ĐẠT**: p1, p6, p7 each 449° about Z, snap 0, allocations 0 | `orbit-gate/ORBIT_GATE.json`, `stdout.log` |
| Default scenes | capture script (offline samples + integrated B1/B2 service fixtures, unmodified page code) | 1440×900, 390×844 | 12 captures, 0 page errors, 0 forbidden requests | `default-scenes/receipt.json` + 4 PNGs |
| Label authority | label probe (served source + visible label text) | 1440×900 | `cau-cat-mat-phang`: served `scene3d-presentation.ts` has no `/I\d/` filter and no `(HUW)` rewrite. Visible labels `I`, `A`, `H` and plane `(HUW)` equal the backend notations | `labels/receipt.json` + PNG |

## What the captures show

- **SGK styling intact after the merge:**
  - ivory canvas;
  - unlit shells;
  - terracotta section with a solid front border and dashed hidden border;
  - dashed hidden edges;
  - right-angle mark at A.
- **B1/B2 identity intact:** the coincident vertex label `A ≡ H ≡ H1` (`PERP-square-third`, mobile).
- **Mobile line widths** scale down. Section border 2.79 px against 4.48 px on desktop; the receipt records widths for every scene.

## Not covered in the browser

**`I1` / `MI1I2I3` notation.**
- Neither the integrated `/4` fixtures nor `geometry-samples.json` contains any notation with `I` + digit.
- The only scene with `MI1I2I3` is an Adapter `/3` export (`geometric-visual-correctness-framing/demos/audit_scenes.json`, `family04_derived_sub_pyramid`). The current product accepts only `/4` and has no envelope for it.
- The probe's second case therefore timed out waiting for a canvas; its receipt keeps only the first row.
- This part rests on the RED/GREEN unit test and the served-source check. No envelope was synthesized to force a browser pass.

**Official Visual suite.** See REGRESSION_RESULTS.md: it is an inherited oracle/UX mismatch and was not re-run here.

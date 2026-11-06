# Handoff — axo-hybrid4-capability-scene3d-reliability (final: READY_FOR_OWNER_REVIEW)

Branch `integration/axo-hybrid4-reliability` (worktree `.superpowers/worktrees/axo-hybrid4-integration`). Wave base
`d3da429b`; `main` = `bb61a804`, fully contained. Not merged, not pushed. 0 provider calls. User's uncommitted
`frontend/index.html` (old worktree `axo-pedagogical-integration`) and `.playwright-mcp/` (main checkout) untouched.

## Done (commits)

| commit | what |
|---|---|
| `555802da` | P0 three-point plane: `/2` `constrained` with ONLY `contains_points` of 3 labels → planner three-point section (bridge); prompt rule 4; cache identity re-locked, `CACHE_VERSION` 132 kept (only refused inputs change); Case C served end to end (11√6/8); `test_hybrid4_three_point_plane_sections.py` (8 served vs independent oracle, 5 refusals) |
| `e3960bd2` | orbit gate v4: frame counter = display frames (gate heartbeat); allocations = deletes(both passes) + creates(repeat pass); thresholds unchanged; evidence windows: per-frame rebuild ⇒ TU_KHOP_KHUNG, never-settling damping ⇒ KHONG_ON_DINH |
| `286e4820` | scene3d: drag start no longer clears `hoveredObject` (was full scene rebuild, 262 GPU objects/drag on pyramid → 0); projection step titles skip unnamed feet; `axo-camera-views-browser-check.mjs`; E2E drag-rebuild check; real /4 fixtures in `fixtures/` |
| `abf3d403` | node harness: frozen oracle blobs (deleted by main `52205f45`) repinned, SHA-256 unchanged → 153/155, 0 fail (2 env skips) |
| `e23e3983` | telemetry per-request token accounting (was 200 vs 100 for overlapping requests); Postgres opt-in test (PASSED on postgres:16); single-process deployment lock test |
| `ac8e610d` | candidate frozen at `e23e3983` (103 files `f75779e2…`), templates rebound |
| `69c5e910` | evidence (tested tree: T3 FULL_PRODUCT_GATE_PASS, node harness 0 fail) |
| (next) | docs-only gate results |

## Status

Everything in the brief is implemented and verified; see `report.md` (A–M). Remaining = owner decisions only
(publication exceptions/98 pending, merge/push) plus the measured open items in report §L (hover-in rebuild,
three-point step text, telemetry write-after-response, single-process idempotency, three-point capability limits).
Untracked builds left on disk (reproducible): `frontend/dist-perf`, `dist-twotab`, `dist-diag`, `dist-inject`,
`dist-int`; raw perf receipts (13 MB each, committed gzipped) and extra traces/screenshots in `perf/`.
Docker Desktop was started for the PostgreSQL tests and stopped afterwards (`wsl --shutdown`).

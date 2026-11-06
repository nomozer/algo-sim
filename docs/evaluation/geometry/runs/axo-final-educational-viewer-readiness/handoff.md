# Handoff — axo-final-educational-viewer-readiness (resumed by Claude after Codex hit its usage limit)

Branch `integration/axo-hybrid4-reliability`, worktree `.superpowers/worktrees/axo-hybrid4-integration`. Main
`bb61a804` fully contained. Not merged, not pushed. 0 provider calls. User's uncommitted `frontend/index.html` (old
worktree `axo-pedagogical-integration`) and `.playwright-mcp/` (main checkout) untouched.

## Commits

| commit | by | what |
|---|---|---|
| `0fb49397` | Codex | hover as draw-time material change; scene-build effect no longer depends on hover; vitest ≤ 4 workers |
| `5558b1ba` | Codex | restored camera pose re-applied after the scene fit (keeps fit-derived zoom/clip bounds) |
| `21ab6fa7` | Codex | section narration names engine-certified cuts through unnamed vertices + certified face traces |
| `6dbbd019` | Claude | kept Codex's uncommitted harness edits (820/1280 px widths, `--skip-recovery`); CODE_INDEX entry |
| `a994790f` | Claude | candidate frozen (product 21ab6fa7, measured_system unchanged f75779e2…) |
| `703f3b5d` | Claude | registry: "mặt phẳng (đi) qua (ba điểm) U, V, W" and "(UVW) đi qua ba điểm U, V, W" grounded (held-out 8/16 → 16/16) |
| `4e7ea0dc` | Claude | candidate frozen at 703f3b5d (103 files 5ef50761…), K-1/R-1/S-2 templates rebound |
| `bac9e065` | Claude | evidence (tested tree: T3 FULL_PRODUCT_GATE_PASS, node harness 0 fail) |

## Final status: BLOCKED_BY_OWNER_DECISION

All technical work of the brief is done and verified on the final tree (see `report.md`). Remaining = owner decisions
only: publication exceptions (`6533b586` and the 98 pending entries, classified in `publication-audit.json`) and
merge/push. Not run on this HEAD: PostgreSQL opt-in tests (no persistence change; Docker not started by instruction).
Untracked and reproducible: `frontend/dist-*` builds; raw perf receipts (13 MB each, committed gzipped) and extra
traces/screenshots in `perf/`; `resume-geometry-suite.log` (raw, has local paths — summary committed).
Process note: one pytest run overlapped two perf runs; those runs are excluded and re-measured. Docker/WSL untouched.

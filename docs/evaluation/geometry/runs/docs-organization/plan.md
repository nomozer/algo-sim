# Plan — final documentation organization

1. Reuse the verified 167-report classification from `docs-cleanup-2026-10-08`.
2. Move registered wave reports beside their existing artifact package where the destination is unambiguous.
3. Move remaining historical/topic reports to `docs/evaluation/reports/`.
4. Keep only explicitly path-bound reports/contracts at `docs/`, with file-level reasons in `inventory.md`.
5. Preserve report bytes, update live consumers/catalog/indexes, and verify links and hashes.
6. Run the complete backend suite once in a clean detached worktree with a persistent log and polling.

Excluded: prompt/IR vocabulary removal, new geometry families, OCR, redesign, live provider calls, screenshots.

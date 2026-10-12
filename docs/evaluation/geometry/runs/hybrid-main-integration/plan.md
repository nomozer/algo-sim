# Hybrid main integration plan

Goal: integrate the reviewed Hybrid S0, sections, S1 and S2 locally, then verify the integrated main before question-local givens work.

Authority: user request, 2026-10-12. Only `git merge --ff-only research/hybrid-semantic-hardening` is authorized for Phase 1. No push.

- [x] Verify main, remote main, ancestry, clean tracked trees, candidate and divergence receipts.
- [x] Preserve frontend/public/favicon.svg, locked A/B evidence, existing research refs and old scratch/databases.
- [x] Fast-forward main a6e27a78 to 22edf7ff.
- [x] Verify candidate, focused Hybrid tests, provider surfaces, benchmark 30 cases and full T3 in a clean detached worktree at 22edf7ff.
- [x] Replay representative Scene3D scenes using the existing Playwright harness (7 completed, optional eighth variant expansion interrupted; no full-harness claim).
- [x] Record results and hash receipts in this run; update living context and run documentation gates.
- [ ] Commit the integration record separately; only then start Phase 2 on a new research branch from integrated main.
- [x] Remove this turn's expired verification worktrees, junctions and processes; record actual bytes freed. Scratch cleanup follows the record commit.

Stop: any product gate failure prevents Phase 2. Environment failures are recorded and investigated; historical evidence and benchmark labels remain unchanged.

# Hybrid main integration — LOCAL Windows, 2026-10-12

User authorized a single local fast-forward of the reviewed Hybrid branch. No push is authorized.

## Preflight and integration

- Main and origin/main: `a6e27a785f952142d0d30cc4604434617a62494f`; `git ls-remote origin refs/heads/main` agrees.
- Research tip: `22edf7ffe79db4dc9df9d1426dc62f8d2dc2e322`. Main is an ancestor. Its product includes S0, sections/intersection lines, S1 and S2.
- Main working tree: only the user's untracked `frontend/public/favicon.svg`; research working tree clean.
- `git merge --ff-only research/hybrid-semantic-hardening` advanced main to `22edf7ff`. No merge commit, rebase, cherry-pick or history rewrite.
- Candidate verified before and after integration: `d1410731542f4d0c04b133e2a514e1207976d2bfbdd35610bf577f73af6cd614`, 110 files; product commit `624e7fc5`. Historical divergence receipt remains `../hybrid-semantic-hardening/candidate_divergence.json`.

## Verification

Authoritative source: clean detached worktree at `22edf7ff`, using the existing Python 3.12 venv and a removable frontend node_modules junction.

- Focused Hybrid tests: 449 passed, 4 xfailed. Includes provider surfaces pinned to A `912b22ef…`, B `396f1c9c…`, declarations `f2ec9698…`.
- Benchmark: 30 cases, both typed-facts and fake-provider pipeline arms: 19 correct served / 9 correct refusals / 0 false serves / 2 known false refusals. New metrics and historical `hybrid-goal-decomposition/after/metrics.json` have the same SHA256 `febb5b602fcb194c502e07ea47fe4200ed4083f0b09bac12784b2536940ab12e`.
- T3 at `22edf7ff`: **FULL_PRODUCT_GATE_PASS**, exit 0. Backend 8675 passed / 0 failed / 1 skipped / 2 deselected / 5 xfailed; frontend 1053 passed (68 files); typecheck/build PASS; demo 5/5 and reduced-chain 1/1; crash-surface 6/6, no escaped exception. Full gate took 591.6 seconds.
- Scene3D Playwright representative smoke: **7 completed scenes**, 0 console errors; sections of pyramid/cube, both plane intersections and auxiliary foot. Own target pixels, dependency order and orbit/zoom/reset checks passed. The optional eighth unit-scene variant expansion was interrupted to bound this quick check; this is not a full eight-scene harness PASS. The earlier eight-scene acceptance at the same product remains unchanged. This is the product renderer with actual Hybrid scene data, not the product page/API and not human visual acceptance.
- First local test attempt encountered an inaccessible Windows pytest temp directory. Focused tests were rerun successfully with an isolated temp directory in the workspace. The first T3 was interrupted; it is not a completed product verdict.

## Preserved boundaries

No bytes changed in locked A/B evidence, historical candidate/divergence records or benchmark packages. `LLM_ONLY`, `CACHE_VERSION = 125`, provider surfaces, M4 and default production routing remain unchanged. LIVE Gemini requests = 0. The two real-model refs, compact DSL HOLD ref and old scratch/databases remain intact.

Main is local only; remote remains `a6e27a78`. The Hybrid branch is retained as a protective ref until a separately approved push.

Question-local givens remains an open semantic correctness issue at this integration point. Phase 1 product gate passed; Phase 2 is authorized on a new research branch.

Documentation audit PASS; documentation/current-state tests 45 passed. Receipts: `verification/t3.log` SHA256 `569894f51fd5d7660cedfc87967d20e54f7fc72d3d7f3d067c0b8cb453cb0733`; `verification/browser-smoke.json` SHA256 `4f52ec678eec43f1b0308721ec652756a21c9c58d70f31228286d19661bb03a7`.

## Housekeeping

Registered worktrees: 3 before, 3 after. `main-integration-verify` removed after its junction was detached (target intact), releasing 1,704,684,873 bytes. `git worktree remove` deregistered the worktree but could not delete every file; the exact expired directory was then removed with native PowerShell under its creating sandbox account, without ACL changes or force flags to Git. This turn's scratch was measured separately in `run.json`. Server/browser sessions stopped; process check found no remaining task process.

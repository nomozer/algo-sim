# Goal-directed section planning — final review, main integration and push, LOCAL Windows, 2026-10-13

The user authorised, for this task, fast-forwarding `research/goal-directed-section-planning` into `main`, pushing
`main` and deleting the merged branch, after gates. No Hybrid enablement, no live model, no DSL work.

## Final targeted review (before integration)

The previous independent reviews did not cover the last product state (`68fbc844`). One fresh LOCAL reviewer
(read-only, own detached worktree, 0 provider calls) reviewed `b2376055`: **BLOCKING**.

| Finding | Ruling |
|---|---|
| C1 (introduced by `68fbc844`): the anaphor "thiết diện đó/này/trên" was bound to (P) from the quotes only; an extraction omitting "Xác định thiết diện … với (MAB)." served the (P) area for the (MAB) question | Fixed `39896b6e`: the nearest "thiết diện" before the anaphor in the SOURCE must be the bound section |
| I1 (pre-existing): the rest of the definition sentence was read inside the quote; a quote cut after "(ABCD)" hid "… và song song với (SBC)" | Fixed `39896b6e`: the rest is read in the source to the real sentence end |
| Minor: Q whose first three labels are collinear; "… rồi so sánh với diện tích đáy" (`AMBIGUOUS_FACT`) | Kept as conservative refusals (`ISSUE-ARCH-HYBRID-DERIVED-PLANE-LIMITS`) |

A second fresh verifier at `39896b6e`: both closed (28 cut-point × continuation combinations refused; controls served),
**non-blocking**, plus one Important introduced with the anaphor: "thiết diện đó của hình chóp … với (SBD)" served the
(P) area. Fixed `4a4f065b` (the anaphor must close the asked object). All fixes RED → GREEN (4 + 3 failing tests);
Phase B tests 45, Hybrid cluster 1288 passed / 5 xfailed. No further independent review after `4a4f065b`.

## Candidate, integration, verification

- Candidate refrozen in a clean detached worktree at `4a4f065b`, committed separately as `b653d381`:
  `fd80c8c9400882822e31008c6e839bd1750a47074f9b543164cf3f14f2f2c128`, 110 files, `--verify` PASS; divergence chain
  extended in `inputs/candidate_divergence.json` (corrects `goal-directed-section-planning`).
- Preflight: `main` = `origin/main` = `ls-remote` = `132e9b23`; branch ahead 13, behind 0; only the user's untracked
  `frontend/public/`; no tooling consumer of the branch name. `git merge --ff-only`: `132e9b23` → `b653d381`.
- Clean detached T3 at `b653d381`: **FULL_PRODUCT_GATE_PASS**, exit 0; backend 8934 passed / 0 failed / 1 skipped /
  2 deselected / 5 xfailed; frontend 1053 passed (68 files); typecheck/build PASS; demo 5/5; crash surface PASS.
  `verification/t3.log` SHA256 `abc3e3810f40a8097b49e371684ca779f6ccc2e252663542513cb732e6864ac3`.
- Benchmark 30 cases, both arms 19/9/0/2, metrics SHA256 `febb5b60…` byte-identical.
- Provider surfaces: route A `912b22ef…` and declarations `f2ec9698…` unchanged; route B `4a20601f…` (set by the slice).
- `CACHE_VERSION` 125, default `LLM_ONLY`, Hybrid not wired into `/api/analyze`, renderer unchanged; LIVE requests 0.
  The derived-plane scenes are unchanged by the review fixes (gate-only), so the slice's SwiftShader/GPU harness
  evidence still applies; no new Playwright run.

Push, remote verification and branch cleanup are recorded in this run's `run.json` after they happen.

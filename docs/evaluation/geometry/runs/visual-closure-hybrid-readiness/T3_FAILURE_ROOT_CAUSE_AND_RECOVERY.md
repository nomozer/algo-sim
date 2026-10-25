# Full T3 failure — root cause and recovery

Failed run: Codex `t3-owner-diagnostic`, target `c84392c1` (clean detached, product `53fe3d25`), 2026-10-25
01:24–01:32 UTC, `FULL_PRODUCT_GATE_FAIL`, receipt sha256
`b6763ca81a64d7aa6d8ff6e0dc76daaf26ac95cbf40992b1e972d6f6ab82be94` (preserved byte-for-byte as
`verification/full-t3/codex-t3-owner-diagnostic-receipt.json`).

| Gate | Result in the failed run |
|---|---|
| pytest | 1 failed, 11855 passed, 1 skipped, 2 deselected, 15 xfailed |
| vitest | 80 files / 1354 tests passed |
| typecheck + production build | **exit 1** — `tsc -b` passed, `vite build` failed before writing |
| demo replay / crash-surface audit | ran (output present), overall gate still FAIL |
| post-run `freeze --verify` | exit 0 (manifest matched the code — it was the manifest *content* that was wrong) |

The two failures are independent. Neither is a product or geometry defect.

## A — manifest recorded a dirty tree (procedure error, the test was right)

`tests/semantic_program/test_evaluation_candidate.py::test_candidate_ghi_dung_commit_va_cay_sach` asserts
`EVALUATION_CANDIDATE.json["cay_lam_viec_sach"] is True`. The manifest committed in `c84392c1` says
`"commit": "53fe3d25…"`, `"cay_lam_viec_sach": false`.

Root cause: `freeze_evaluation_candidate.py` was run with HEAD at `53fe3d25` while the run fixtures that were
then committed **together with** the manifest in `c84392c1` (≈50 files under
`docs/evaluation/geometry/runs/visual-closure-hybrid-readiness/`) were still uncommitted. The script's clean-tree
check excludes only the manifest itself, `favicon.svg` and the freeze script, so it truthfully recorded `false`.
The repository rule is: freeze on a clean tree, commit the manifest alone.

The earlier attempts `t3-final` and `t3-final-complete` also contain this failure; Codex's notes did not identify it
as the cause.

Recovery (no receipt or manifest edited by hand):

1. In the clean measurement clone, at `c84392c1`, `git status --porcelain` empty.
2. `backend/scripts/freeze_evaluation_candidate.py` (no flags) → `commit c84392c1 (cây sạch: True)`.
3. Diff of the manifest: only `dong_bang_luc`, `commit`, `commit_ngan`, `cay_lam_viec_sach` changed.
   `product_commit_sha` stays `53fe3d25243fe1e99410dfc52546e16225f19e75`; measured system stays 118 files /
   `8be632679307a94ce4525ad576a05a9eccffc8ba2bdbf02d4c7dc93c208b7c41`; taxonomy, primitive set, schema, DEV
   fingerprints unchanged.
4. Committed that one file as `c6bdfbcb` *chore(eval): re-freeze visual closure candidate on a clean tree at
   c84392c1*; `--verify` → match.

Because product code is unchanged, browser evidence bound to product `53fe3d25` (official suite, Adapter /4,
refusal, orbit, hover, owner camera) stays valid; the freeze commit only fixes the identity record.

Latent weakness noted, not changed: `_git()` in the freeze script ignores Git's exit code. In a clone Git refuses as
"dubious ownership", `git status` prints nothing and the tree would be recorded as clean; `commit` would then be
empty and `len(commit) == 40` would still catch it. Hardening is a one-line `check=True`; left for the Owner because
it is not needed for this candidate.

## B — `frontend/dist` not removable (environment, not product)

`stderr.log`: `EPERM, Permission denied: …\visual-closure-hybrid-readiness\frontend\dist\assets` from Vite
`emptyDir → rmSync`. `dist` in the Codex clone was produced by an earlier build running as `CodexSandboxOffline`;
the later run executed as `Bunny`, which may read but not delete that directory. `tsc -b` had already passed.

Recovery without touching permissions: run the gate in `.superpowers/verify-visual-closure`, a fresh clone created
by Codex at 08:35 as `Bunny`, which has no `dist`, no Vite cache and no process attached. The ACL-locked `dist` was
left where it is. No `takeown`/`icacls`/forced delete, no change to the T3 definition (`full-gate.mjs` unchanged and
runs every gate).

Shared dependency note: `frontend/node_modules` in that clone is a symlink to the root install (immutable packages).
Mutable outputs are clone-local (`frontend/dist`, `backend/algosim.db`), pytest `--basetemp` is a new directory
`D:/tmp/algo-t3/bt-c6bdfbcb`. Vitest/Vite may write their own cache below the shared `node_modules/.vite`; that is
the established practice of this repository's junction worktrees and holds no evidence.

## Earlier attempts (preserved, never counted)

| Attempt | State | Failures seen | Class |
|---|---|---|---|
| `t3` | stopped at 29 % | none yet | interrupted |
| `t3-final` | completed pytest portion, then stopped | `test_branch_independent_harness` ×9 (clone had no `main` ref), `test_tien_kiem_kho`, 2 Windows watchdog tests, manifest A | environment + A |
| `t3-final-complete` | stalled at 96 % in the sandbox | 2 Windows watchdog tests (sandbox logon), manifest A | environment + A |
| `t3-owner-complete` | stalled at 5 % | none | interrupted |
| `t3-owner-diagnostic` | completed | manifest A + build EPERM B | A + B |

The two watchdog tests passed outside the sandbox (Codex targeted re-run 2/2); the branch-harness failures
disappear once a `main` ref exists.

## Authoritative run

**`FULL_PRODUCT_GATE_PASS` at `c6bdfbcb3a685e356ee5091a53c75a3dad8dc01a`** (clean detached, product `53fe3d25`),
2026-10-25 01:45:30–01:53:54 UTC, exit 0, executor Claude (machine verification, not independent review),
`ALLOW_LIVE_AI=0`, 0 provider calls. Receipt: `verification/full-t3/receipt.json`.

| Gate | Result |
|---|---|
| pytest (whole backend) | 11856 passed, 0 failed, 1 skipped, 2 deselected, 15 xfailed — 480.3 s |
| vitest (whole frontend) | 80 files / 1354 tests passed — 11.0 s |
| typecheck + production build | PASS — 9.9 s |
| thesis demo replay | PASS |
| demo crash surface | PASS |
| `source_tree_before` / `source_tree_after` | both empty |
| post-run `freeze --verify` | exit 0, 118 files `8be632679307a94c…` |

`stdout.log` sha256 `7f674b3ed09f7a5ef1e6bd2e58f9df35efb1671863d3646657f5e38961daab12` (1557561 bytes, kept in the
measurement clone's ignored `.superpowers/closure/t3-claude-c6bdfbcb/`, too large to commit); `stderr.log` sha256
`aa9b7207d2d2d42fbf4e013331ee76fc39b9b042505b38551893c1f60f35b63a` (only the Vite chunk-size warning) is committed.

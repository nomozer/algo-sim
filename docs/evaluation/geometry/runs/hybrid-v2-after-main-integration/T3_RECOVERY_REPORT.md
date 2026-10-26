# T3 recovery

Status: `FULL_PRODUCT_GATE_PASS`; `OWNER_VISUAL_APPROVAL_PENDING`.

Targeted watchdog and receipt suites: 26 PASS; three independent process repetitions: 26/26 each; actual job members verified stopped. Related schema/runtime suite: 153 PASS. Source changes are confined to offline tooling and its tests; product identity remains e047235e, measured tree 118 files / 3850e787d86f81be….

The previous `sphere-visual-polish/full-t3/receipt.json` remains FAIL (11993 passed / 2 watchdog failures). Its receipt, raw stdout/stderr and all prior sphere evidence were checked unchanged. It has not been rewritten.

## Authoritative result

Harness fix: `5961b814`; frozen candidate: `3d6351d81deb8c1cea1d7210f53101cfc1ea26bb`. Complete detached checkout: `.superpowers/worktrees/t3-sphere-visual-polish`. Git tree before/after: `1f458860b6f5a90ec3c03d816d3e9826399080ca`; source status empty before and after. One Full T3 run was made after stabilization, under the ordinary sandbox environment that reproduced taskkill denial.

| Gate | Result |
|---|---|
| Backend pytest | 12009 passed, 1 skipped, 2 deselected, 15 xfailed; no new skip/xfail |
| Frontend Vitest | 83 files / 1417 tests passed |
| Typecheck and production build | PASS |
| Demo replay | PASS, 5/5 plus reduced chain 1/1 |
| Crash/refusal surface | PASS, 6/6 |
| Post-run freeze | MATCH, exit 0 |
| Full product gate | PASS, exit 0 |

Receipt: `full-t3/receipt.json` (SHA-256 `bd881629fb9594c35acf49f69d3836c31d61dc26bf0b7ee69a062414ea89f34a`). Freeze SHA-256 before/after: `7034f1b4fd32fa4f0f2f3d98c0ec7ce671ada6ff9b9a1aaca242179008376b47`. Full source inventory (backend, frontend and the run-local T3 tool): `afc9e513fc64ac3c42e90f900452c6731104925318a0a7b916ca39abb5e35b4d`; see `source-identity.json` for scope and subtree IDs. Final result annotations add only documentation/receipts after this tested source; source inventory must still match before integration.

Raw logs remain at `.superpowers/worktrees/windows-watchdog-recovery/.superpowers/t3-recovery-3d6351d8/`, outside the tested checkout and Git. Stdout: 1576874 bytes, SHA-256 `f3f91d932a9adeae37d577787366ecc2b179ba7d529c895ff32916ea51f1cccd`; stderr: 332 bytes, SHA-256 `ccb6bf354a0674eeb1e49df9a880a000b75240079fdb849282bb899d81eeb58c` (Vite chunk-size notice). Retain these unique ignored logs or back them up with checksums before future worktree removal.

Both originally failing watchdog tests and all new Job Object regressions passed in this Full T3. The receipt publisher completed with the actual exit code and no cp1252 exception. Cache is 130, `CHE_DO_MAC_DINH = LLM_ONLY`, Hybrid V2 local flag unset, ALLOW_LIVE_AI=0, provider calls 0, and frontend `.vite-cache` configuration unchanged.

Final preservation checks matched all 79 Owner dirty files, 65 geometry frontend files, 274 prior sphere artifacts and both old failed-run raw log hashes. Main remains `9978e512a8a2a087475d792c0bd9db639c36acaa`. No merge, cleanup, backend slice or push was performed because Owner Visual GO is still absent.

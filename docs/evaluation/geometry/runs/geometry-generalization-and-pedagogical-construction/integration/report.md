# W4 integration and safe repository cleanup

Date: 2026-10-30. Owner authorization: ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT and the direct confirmation that the Owner personally edited the W4 exception registry. No agent wrote the approval value.

## Integration

`W4_REMOTE_VERIFIED`: `main`, `origin/main` and live GitHub `refs/heads/main` all matched `94055c98350289c54a2cf15311a20fbabf08f0d1` after `git push origin main:main`, without force. Baseline was `e5dc3d28b8ff1a5bf34e1e7637a020f20e921c31`; integration was fast-forward. See `remote-verification.json` for the actual read-back.

The Owner's registry change was verified structurally: one entry's decision only, exactly 1 insertion/1 deletion, no other semantic change. It was committed separately as `94055c98`. Scanner code was unchanged. The exact range scan at that commit reported 184 blobs, 21 messages, zero violations, PASS. The post-integration head scan reported 104 historical pending findings, BLOCKED, and its complete finding set exactly equalled the pre-approval W4 finding set. There were zero unexcepted findings. This is the scoped W4 publication decision; it does not exempt new content in future commits.

## Technical identity and checks

Product `61ade29e11d41417ff10efdcb4dd1e19cb69e910`; freeze commit `182a7785`; measured system 118 files, SHA-256 `54b5b565ef65a8e9a8faee5a63a19aca14749bc0edce2bf054b6846be322043c`; cache131; LLM_ONLY; zero provider calls. Candidate verification passed before and after integration. T0/T1/T2 and Full T3 attempt 2 log hashes matched the original receipts. Full T3 was not repeated for this product-identical integration.

Fresh clean detached verification at `a0a4fdd4`: 160 targeted tests passed, Wave 3 replay 67/72 served-correct, 72/72 negatives refused, 62/72 refusal-reason agreement, zero wrong-served; all 144 case rows identical to the final-review replay; locked96/96; 203 probes unchanged with no served negatives or internal errors. Post-integration checks: 176 tests passed initially; one additional test failed during pytest temporary-directory setup because the sandbox denied the system temp directory. That exact node passed with workspace `--basetemp`; no product fix. Metadata and hashes are in `verification.json`; local logs remain outside tracked evidence.

F1 remains a disclosed historical local-path exposure, with no history rewriting. F2's superseded freeze is recoverable at `84c61334`; its replacement at `182a7785` is justified by the product change and remains explicitly disclosed. The original research reports and receipts are unchanged.

## Whole-repository cleanup

`SAFE_CLEANUP_COMPLETE_WITH_RETAINED_EXCEPTIONS`. See `cleanup-inventory.json` for before/after counts, every remaining registered worktree, branches and residuals.

- Registered worktrees: 16 before, 12 after. Removed directories: W3-F2 final T3, W3-F2 main baseline and W4 final T3. Every removed commit is an ancestor of main. Generated local DBs were copied to ignored backups and SHA-256 checked. Tracked evidence remains in Git.
- W4 research worktree: junction safely unlinked; Git unregistered it, but directory deletion returned Permission denied. Residual retained; no force, ACL change or manual recursive removal. The merged W4 branch was deleted safely.
- Port3017: current owner/process/creation/command were checked, with zero established connections; only the completed W4 Vite process PID9616 was stopped. The historical parent PID was not used as authority.
- Dirty worktrees, unmerged research, local evidence, nested worktrees with uncertain contents, ACL failures and all unregistered residuals were retained with individual dispositions. Active root dependencies, user files, backups and historical receipts remain. No global `git clean` was used.
- Living status documents now identify W4 as current and earlier dated snapshots as historical. The existing `ARCHITECTURE_MAP.md` remains the single current map. No historical research document was deleted or rewritten to simplify navigation.

## Continuation

W4 integration and safe cleanup no longer block the backend-only Master Hybrid Epic. Next: audit actual Hybrid code and establish `docs/architecture/HYBRID_BACKEND_MASTER_ARCHITECTURE_CONTRACT.md`, with one plan and persistent checkpoint in the Master task run. Hybrid is not yet production-primary; legacy retirement and live real-text/token/latency acceptance remain unfulfilled. No live-provider budget has been granted.

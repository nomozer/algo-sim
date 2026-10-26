# Recovery handoff

Active development worktree: `.superpowers/worktrees/windows-watchdog-recovery`, branch `research/windows-watchdog-t3-recovery`, continuing candidate `9b99ad40`. Large image/video files are excluded only from this development checkout; the complete sphere visual package remains in `s3d-hybrid-v2-claude`.

P0–P1 complete: original watchdog failures reproduced, taskkill Access denied captured, old orphan explicitly reaped, Job Object fix tested. Targeted watchdog/receipt tests 26/26, three independent repetitions 26 each, related schema/runtime 153/153. Native internal review has no remaining findings after correcting cleanup timeout persistence. No independent review/holdout PASS.

P2 complete: harness fix `5961b814`; frozen candidate `3d6351d81deb8c1cea1d7210f53101cfc1ea26bb`; complete detached `.superpowers/worktrees/t3-sphere-visual-polish` checkout. One authoritative Full T3 PASS: backend 12009, frontend 1417, build/demo/crash gates PASS, clean before/after, freeze MATCH. See `full-t3/receipt.json` and `source-identity.json`. Raw logs remain in the recovery worktree's ignored `.superpowers/t3-recovery-3d6351d8/`; preserve or checksum-back-up them before any later cleanup. Old FAIL receipt/logs remain unchanged. No further T3 is needed solely for the final documentation annotations while the recorded source inventory matches.

Owner Visual GO is absent. Status: `OWNER_VISUAL_APPROVAL_PENDING`. All preflight renderer/evidence/Owner hashes matched after recovery. Present the six existing images and stop before P5. The execution directive explicitly excludes implicit image approval. Once explicit GO binds those images/renderer e047235e to recovery candidate 3d6351d8, recheck refs, status, source inventory, ancestry, active processes and protected hashes, then continue P4–P9 using the already authorized local-only actions.

Main remains `9978e512`; Owner root branch `research/hybrid-wave3a-volume-reasoning`, HEAD `fe9f5554`, protected 19 modified / 60 untracked files. Live Vite worktrees and preflight inventory are recorded in `preflight.json`; take fresh process/inventory checks before any future operation. No ACL changes or deletion occurred.

## Required campaign answers at this gate

| Question | Answer |
|---|---|
| 1. What caused the two watchdog failures? | taskkill process-tree termination returned Access denied; the fallback owned only the parent and left a child alive. Spawning and timeout detection worked. |
| 2. Source or test fix? | Offline runner source plus a Windows Job API helper; tests preserve/strengthen safety and failure assertions. No backend/app or renderer change. |
| 3. Orphans? | The old reproduction's owned orphan was explicitly reaped. Three independent fixed runs observed stopped parent/child/grandchild handles and zero active job members. |
| 4. Latest Full T3? | PASS at 3d6351d8; receipt full-t3/receipt.json, exit 0, freeze MATCH. |
| 5. Owner Visual GO? | Absent; OWNER_VISUAL_APPROVAL_PENDING. |
| 6. Main before/after? | Both 9978e512a8a2a087475d792c0bd9db639c36acaa; no merge. |
| 7. Official Visual? | Inherited 7/8, known F2 only; renderer/evidence hashes unchanged; no oracle rewrite. |
| 8. Removed worktrees/branches? | None. All dirty/active trees and 11 missing-path metadata entries retained. New isolated recovery worktree/branch added. |
| 9. Owner data affected? | No protected-file change: all 79 preflight dirty-file hashes matched. |
| 10. New backend branch commit? | NOT_CREATED; research/hybrid-v2-backend-generalization awaits verified main and safe cleanup. |
| 11. New Hybrid slice E2E? | NOT_STARTED; no new Hybrid capability claim. |
| 12. Failures/refusals verified? | Normal/nonzero exit, timeout tree, parent exit race, spawn/job/terminate/query failures, cleanup timeout persistence and runtime-vs-geometry taxonomy. Existing sphere oracle 5/5 reused. |
| 13. 18-family coverage change? | None claimed. Inherited 0 FULL / 9 PARTIAL / 7 RENDER_ONLY / 2 UNSUPPORTED has not been re-audited here. |
| 14. Independent evidence? | No new independent holdout/review; internal review only, independent review DEFERRED. |
| 15. Remaining blockers? | Immediate: explicit Owner Visual GO before main. Before replacing LLM_ONLY: fresh gap audit, verified generalizing Hybrid E2E slice(s), independent evidence and migration/production gates. Live NL extraction remains UNKNOWN. |

Next read-only recheck: `git -C <recovery-worktree> status --short`, `git rev-parse main`, `git merge-base --is-ancestor main HEAD`, and `python backend/scripts/freeze_evaluation_candidate.py --verify` (use root Python 3.12 and exact session-only safe.directory as needed). Compare `git ls-tree -r HEAD -- backend frontend docs/evaluation/geometry/runs/hybrid-v2-after-main-integration/tools/run_t3.py` against the recorded inventory SHA-256. After Owner GO, use a separate main worktree for ff-only integration and targeted smoke. Disk space is limited; the source-only sparse development checkout avoids copying multi-gigabyte unchanged image evidence. Cleanup must still wait until verified local main integration and use a fresh inventory.

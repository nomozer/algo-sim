# Recovery handoff

Active development worktree: `.superpowers/worktrees/windows-watchdog-recovery`, branch `research/windows-watchdog-t3-recovery`, continuing candidate `9b99ad40`. Large image/video files are excluded only from this development checkout; the complete sphere visual package remains in `s3d-hybrid-v2-claude`.

P0–P1 complete: original watchdog failures reproduced, taskkill Access denied captured, old orphan explicitly reaped, Job Object fix tested. Targeted watchdog/receipt tests 26/26, three independent repetitions 26 each, related schema/runtime 153/153. Native internal review has no remaining findings after correcting cleanup timeout persistence. No independent review/holdout PASS.

P2 next: commit allowlisted harness/test/run changes; refreeze; use the complete clean detached `.superpowers/worktrees/t3-sphere-visual-polish` checkout at the new freeze commit (no process currently uses it), preserving old failed receipts and logs. Run `tools/run_t3.py` once with Python 3.12 and a unique ignored output directory outside the detached checkout. Record stdout/stderr hashes, receipt, full Git tree, post-freeze MATCH and source status. Do not run T3 from the sparse checkout.

Owner Visual GO is absent. After P2 passes, verify all preflight renderer/evidence/Owner hashes, present the six existing images and stop before P5. No merge, cleanup, backend implementation or push is authorized until the required visual gate is explicitly satisfied. Once it is, the execution directive authorizes continuing P4–P9 without asking again for already granted local actions.

Main remains `9978e512`; Owner root branch `research/hybrid-wave3a-volume-reasoning`, HEAD `fe9f5554`, protected 19 modified / 60 untracked files. Live Vite worktrees and preflight inventory are recorded in `preflight.json`; take fresh process/inventory checks before any future operation. No ACL changes or deletion occurred.

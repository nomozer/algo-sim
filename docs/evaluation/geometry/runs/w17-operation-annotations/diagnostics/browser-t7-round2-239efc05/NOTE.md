# Task 7 browser round 2 (confirm round) — 239efc05 (diagnostic, not acceptance evidence)

This round confirms the round-1 fix batch. It ran on the scratch worktree `D:/tmp/w17-t7` at
239efc05, with the committed suite and the same fixtures (0 model calls).

- **Result:** 5 of 6 families PASS.
- **Remaining failure:** on the triangular pyramid's default desktop view, `S(ABC) = 6` was
  still hidden. Every one of its eight positions 6 px from the anchor touched `AB = 3` or
  `AC = 4`, one of them by half a pixel
  (`screenshots/triangular-pyramid_desktop_neutral_final.png`).
- **Fix:** commit 240ecba5 (rings 6/12/18 px).
- **Verification:** the filtered browser baseline of the frontend fault-injection run 2
  (`../logs/FAULT_INJECTION_W17_FRONTEND_R2.log`, triangular_pyramid/desktop PASS at
  dbb38b95). There was no third full round: the full 6×2 acceptance run is the one at the
  measurement commit (`../../results/BROWSER_EVIDENCE.json`).

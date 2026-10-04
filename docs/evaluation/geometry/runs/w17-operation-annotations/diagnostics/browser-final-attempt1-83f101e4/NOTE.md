# Failed acceptance attempt 1 on the final candidate — measurement 83f101e4 (kept, superseded)

This is the first browser suite run on the final candidate `d63d6fd4…` (product commit d3817d5f). It ran
at the measurement commit 83f101e4 in the clean detached worktree `D:/tmp/w17-evidence2`. Its log is
`../logs/BROWSER_SUITE_83f101e4.log`.

**Result: FAIL, exit 1.** Five families passed; cube failed. Exactly one assertion is red: cube/mobile
`causal_restore` with `CANVAS_NOT_RESTORED`.

| | neutral | restored |
|---|---|---|
| canvas sha256 | `b9c334f7…` | `2090af68…` |
| at rest (two identical captures in a row) | yes | **no** — no two identical captures within the window |
| scroll | 19 | 19 |
| selection | none | none (reset) |
| camera | — | not moved (within `CAMERA_SETTLE_TOLERANCE`) |

Every other part of the attempt passed:
- positives 11/12 (cube/desktop included);
- negatives 40/40;
- served correct plane 2/2.

The cross-section mobile neutral and restored frames were also not at rest. Its two hashes were still
equal, so that assertion passed.

## Why it was not a product change

- **Same inputs as the passing run.** The product code and the fixtures equal those of the passing
  measurement c5592c1a; the fixtures differ only in their identity fields (product commit, tree hash,
  sha256). That run passed this exact assertion, with `45e45c71…` at both ends.
- **Frames vary between runs.** Two runs of the same code differ in 56 of 282 recorded frame hashes
  (formation captures and screenshots). In this attempt the cube/mobile final-step frame appears as
  `e5525cad…` at formation, `b9c334f7…` at neutral and `2090af68…` at restore. All three differ
  from the at-rest frame of every other run.

## Diagnostic runs (`diag-cube-mobile/`)

Each run used the same commit, a scratch worktree (`D:/tmp/w17-diag-cube`) and this attempt's
fixtures, with a one-family/one-viewport filter.

| Run | Patch | Result |
|---|---|---|
| `run1` | `diag_patch.mjs`: 40 captures, 100 ms apart, at the neutral and the restored points | PASS. Both ends are `45e45c71…`. The restored series holds `d3184a20…` twice in 40 |
| `run2-load` | the same, with ten busy-loop processes on 12 logical CPUs | PASS. Both ends are `45e45c71…`. The neutral series holds `d3184a20…` twice in 40 |
| `run3-forced` | `diag_patch_forced.mjs`, on the FIXED harness | The frame-difference path ran in a real browser: `max_channel_delta` 0, both frames saved |

**What `d3184a20…` is.** It differs from `45e45c71…` over the whole canvas (bounding box 680 × 836).
47,791 pixels differ, and no channel differs by more than 1 (`PIXEL_DIFF_45e45c71_d3184a20.txt`).
Across the series, the camera, the label boxes, the label opacities and the scroll are identical at
those captures. So at-rest captures of an unchanged figure carry 8-bit noise of at most 1, and
comparing bytes reads that noise as "not restored".

## What changed

The rule is registered before the re-measurement in
`docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md` §15.5 ("Đính chính cách đo — lượt đo nghiệm
thu đầu trên candidate cuối"). The harness now compares the two frames by bytes first.

- **Different bytes:** the harness measures the per-channel difference in the page.
  - It saves both frames as `causal_restore_neutral_frame.png` and
    `causal_restore_restored_frame.png`.
  - The canvas counts as restored only when the two frames are the same size and no channel differs
    by more than `NHIEU_KHUNG_TOI_DA` = 1.
- **No measured difference:** the result is `CANVAS_NOT_RESTORED`.

The change touches the harness only, so the candidate `d63d6fd4…` is unchanged. The test log is
`../logs/RED_CAUSAL_RESTORE_NOISE.log`; the test failed before the fix and passes after it (60/60).
The re-measurement repeats every acceptance run on the same candidate at a new measurement commit.

## Not recoverable

This attempt saved no canvas frames, so the actual difference between `b9c334f7…` and `2090af68…` is
`NOT_RECOVERABLE`. The full-page screenshot `images/cube/mobile/causal_restored.png` differs from the
one c5592c1a took in 50 pixels, each by at most 1, all outside the canvas.

## Contents

| Path | Content |
|---|---|
| `results/BROWSER_EVIDENCE.json` | the evidence of this attempt, unchanged |
| `images/cube/mobile/` | the screenshots of the failing viewport, unchanged |
| `diag-cube-mobile/` | the patches, series, distinct frames, the `causal_restore` excerpt and the log of each diagnostic run |

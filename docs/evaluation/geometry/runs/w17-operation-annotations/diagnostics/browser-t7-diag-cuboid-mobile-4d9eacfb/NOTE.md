# Diagnostic rerun: cuboid, mobile — 4d9eacfb (scratch-patched harness, diagnostic only)

**Question.** Was round 1's `CANVAS_NOT_RESTORED` (cuboid, mobile) a product defect, or a
capture-timing artefact?

**Method.** The suite in the scratch worktree `D:/tmp/w17-t7` was patched in place and never
committed. The patch added:
- a run filter: `DIAG_ONLY=cuboid` and `DIAG_VP=mobile`;
- three frame dumps: `screenshots/diag_neutral.png`, `diag_selected.png` and
  `diag_restored.png`.

The patch was reverted with `git checkout` before any further use of that worktree.

**Result.** `causal_restore` PASS: the neutral and restored canvas frames are byte-identical
(c157b77d…), which is also round 1's restored frame. The round-1 neutral frame was taken
mid-transition. The harness now captures both ends at rest (`khungOnDinh`, ca6c4107). The
`CAUSAL_CANVAS_ROLE_HUE` failure recorded here is the round-1 measurement defect, fixed in the
same commit.

Because of the patch, this evidence JSON comes from a modified harness. It is kept only as
proof of the cause, never as acceptance evidence.

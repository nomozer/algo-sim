# Branch ancestry and diff audit

Authority: live local Git audit on 2026-10-24, full SHAs and path sets in `ancestry.json`. No fetch/push or main mutation. `origin/main` is a local remote-tracking observation, not a freshly contacted remote.

| Ref | Observed commit |
|---|---|
| Root checkout, research/hybrid-wave3a-volume-reasoning | fe9f555437498432427ae6bbd54402cdd59c7eb7 |
| main | 9978e512a8a2a087475d792c0bd9db639c36acaa |
| Visual branch | 7f90d9b398329d9fb99867ea784d3d126b005e31 |
| Visual candidate | 13d28b844925ee0c9adb02698b54597c8f9d6eee |
| Visual product | 852f650158635b6dc402d4cfc905cbdcbbaebe43 |
| B1/B2 branch | 97d59bf95c0c87eae827e48148c1a5957195a82e |
| C0 | 5ee973406b75e19503158549a22bb3b24c5d9bf5 |
| Visual–B1/B2 common base | 43247c9e9375a3dbf2b5223324a58e6f932ca596 |

Main is an ancestor of B1/B2 (0 main-only / 22 B1/B2-only commits). C0 is already in B1/B2 and must not be replayed separately. Main and Visual diverge (59 main-only / 28 Visual-only commits). Visual branch tip adds documentation/evidence after 13d28b84: no `backend/app` or `frontend/src` difference. Root owner changes are a separate, preserved workspace layer; they are not the integration input.

The Visual stack contains earlier visual/UX work, including backend Adapter /3 display naming and curved display metadata. The last SGK port alone is frontend-only; the full branch is not. Both must be distinguished when assessing integration impact.

Nine overlapping paths since common base: Adapter /3 source and its test; section subentities; CODE_INDEX, CURRENT_STATE, EVIDENCE_INDEX, ROADMAP, architecture README and candidate manifest. The expected semantic merge combines B1/B2's certified coincident section-point identity with Visual's current-frame role styling; neither may replace the other. Adapter /3 must retain B1/B2 source/closure authorities together with Visual display naming. The candidate manifest is regenerated after the product merge, not selected as authoritative from either parent.

Integration method: create one local branch from verified main in the dedicated worktree, include B1/B2 history once, then merge Visual preserving both parents and resolve only actual overlapping hunks. No rebase, cherry-pick duplication, force, main merge or other-agent worktree mutation.

All worktrees (including dirty ones) were inventoried read-only in `worktree-inventory.json`. Root status/ref snapshots and SHA-256 hashes of 79 modified/untracked owner files are retained for final preservation checks. The newly created worktree is owned by this task; all pre-existing worktrees remain untouched.

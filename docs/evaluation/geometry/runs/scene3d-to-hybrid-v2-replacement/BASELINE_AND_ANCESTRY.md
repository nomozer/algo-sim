# Baseline and ancestry

Recorded 2026-10-26 before any product edit. Read-only inspection, no Git state changed except the new worktree/branch.

## Source of truth

The candidate line is linear, each tip an ancestor of the next (`git merge-base --is-ancestor`, all true):

```
main 9978e512
 └─ integration/visual-b3-sphere-candidate fe5f40b7   (visual closure + B3 distance bridge + sphere source fix, CACHE 129)
     └─ research/scene3d-visual-correction 26225cba   (Claude: F2 policy, role-aware proposal)
         └─ research/scene3d-owner-math-visual-final 08929b89   (Claude: plane border, witnessed marks, label hysteresis)
             └─ research/scene3d-codex-takeover 11188e7a   (Codex: conic visibility, sphere reference; freeze e1ebc72c)
                 └─ research/scene3d-to-hybrid-v2-replacement   (THIS campaign; starts at 11188e7a)
```

`e1ebc72c` (Codex clean freeze, Full T3 PASS, official visual 7/8) is an ancestor of the takeover tip; the two commits after
it (`ce023570`, `11188e7a`) are evidence/docs only. Nothing newer exists on any branch (`git for-each-ref --sort=-committerdate`).

Campaign worktree: `.superpowers/worktrees/s3d-hybrid-v2` (owner Bunny), `frontend/node_modules` = junction to the root
install (`rmdir` the junction before any `git worktree remove`). `vite.config.ts` keeps `cacheDir: ".vite-cache"`, and
`.gitignore` keeps `.vite-cache/`.

## Preserved, not touched

| Location | State | Receipt |
|---|---|---|
| Root checkout | `research/hybrid-wave3a-volume-reasoning` @ `fe9f5554` (91 behind `main`); 19 modified frontend files (+1989/−328), 60 untracked files | `git diff --binary` sha256 `326493ea…c953`, 170265 bytes = **byte-identical** to Codex's `.superpowers/preservation-scene3d-codex-20261026/root-working.patch`; untracked-file hash list sha256 `aae9544d…967f` |
| `.superpowers/worktrees/scene3d-visual-correction` | Claude's uncommitted `scene3d-owner-math-visual-final` docs (1 modified, 9 untracked) | already preserved by Codex in the same archive; diff sha256 `7f6b9bae…2d2f` |
| Other 31 worktrees, Codex clones, ACL-locked dirs | unchanged | — |

The root's modified files sit between `visual-b3-sphere` and `main` (e.g. `global.css` is 15 lines from `main`, 68 from the
candidate). They may include the Owner's own web redesign, so this campaign never builds, edits or stages in the root.

## Known defects at baseline (from the takeover handoff, re-read in source)

| # | Defect | Layer | Evidence |
|---|---|---|---|
| G1 | No right-angle mark for BC ⊥ (SAB) (`vuong-goc-chop`) | producer | scene has no witness |
| G2 | Learner text "Ghi nhận mpb = Plane3(point=Vec3(x=Fraction(2, 1)…" and a MEASUREMENT event for a construction | producer | `geometry-samples.json` step 3 |
| G3 | Constructed plane `mpb` has `notation: null`, so the right-angle mark at its foot H sits next to the only visible plane label "(ABC)" | producer | `final/mp-vuong-goc-duong-1440-default.png` |
| G3b | Base plane authored `(ABCD)` displays notation `(ABC)` (4-point name silently reduced to 3) | producer | `day.notation = "(ABC)"`, `display_label = "(ABCD)"` |
| G7 | `o.id === "day"` hard-coded in `scene3d-auxiliary.ts` | frontend | source |
| F2 | Official Visual suite 7/8: locked role-hue gate vs Owner fill/boundary policy | governance | `verification/official-scenarios.json` |
| — | Independent review, human visual approval | governance | PENDING |

Witness mathematics in `mp-vuong-goc-duong` was checked exactly: foot H = (5/3, 5/3, 2/3) lies on SC and on (B ⟂ SC),
u = B − H ⟂ n, v = S − H ∥ n. The glyph geometry and its scaling about the foot are correct; the defect is identification
(which plane, which in-plane line), not the anchor coordinate.

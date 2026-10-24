# Final owner handoff: visual–Hybrid integration

**Status: `VISUAL_HYBRID_INTEGRATION_READY_FOR_OWNER_REVIEW`**

This means ready for the owner's review, not cleared to merge. The open items in §12 are owner decisions, not failures of this integration.

Authorization `GO_CLAUDE_TAKEOVER_VISUAL_HYBRID_INTEGRATION_LOCAL_ONLY`.
- Branch: `integration/hybrid-visual-candidate`, in worktree `.superpowers/worktrees/hybrid-visual-candidate`.
- Local only: not merged to `main`, not pushed, no history rewritten, 0 model calls.
- Stops at the owner gate.

## Answers to the 13 questions

**1. Were all 7 Codex files found?**
Every edit that exists on disk was found. Git shows 4 tracked files (+18/−9), plus 156 untracked run files:
- `scene3d-presentation.ts`
- `scene3d-presentation.test.ts`
- `compiler-scene-suite.mjs`
- Codex's dirty-tree `EVALUATION_CANDIDATE.json`

The count "7" in the Codex UI cannot be reproduced from Git. See CODEX_TO_CLAUDE_TAKEOVER.md.

**2. Which changes are committed and which are not?**
Committed on the branch:
- `78e88470` merge (Codex);
- `a9d05dda` label fix (Codex's edit, verified);
- `1fcbe7e5` harness hunk (Codex's);
- `aec7b183` clean freeze;
- `b99afd32` evidence and join layer;
- the reports commit after it.

Codex's dirty-tree freeze is kept as `codex-dirty-freeze-78e88470.EVALUATION_CANDIDATE.json`. Not committed, by design:
- in the `visual-hybrid-integration` worktree: the same harness hunk, its private Vite cache and the untracked evidence (copied, byte-identical, into the run directory);
- in the root checkout: the owner's own work.

**3. What did Claude continue?**
- Verified and committed the label fix, with RED proof.
- Committed the harness hunk.
- Made a clean candidate freeze.
- Found and fixed the merge's correction-chain fork defect (T3 attempt 1).
- Ran Full T3, the browser acceptance and an internal review.
- Wrote the reports.

No reimplementation.

**4. Are I1 and (HUW)/(P) handled with correct authority?**
Yes, in the frontend. `kyHieu` prints the backend notation verbatim: no regex, no exception list. The learner now sees `(HUW)` and, where a section cycles through unnamed intersections, `MI1I2I3`.

These are backend display-identity gaps. The proposal is in GEOMETRY_LABEL_AUTHORITY_FIX.md §"Backend display-identity proposal":
- section notation must not fall back to ids;
- enable `prefer_declared_plane_names` on LLM_ONLY.

It is not implemented; it needs an owner GO, a `CACHE_VERSION` decision and regenerated samples.

**5. Any geometry/provenance impact?**
None. The only product change after the merge is a frontend display function. No backend file changed after `78e88470`, and the backend suite passes in T3.

**6. LLM_ONLY unchanged?**
Yes. `CACHE_VERSION = "127"` (NO_BUMP). `main..HEAD` changes nothing in `app/ai/skills`, `main.py`, `ai/pipeline.py` or `geometry_compiler/routing.py`. Hybrid stays offline research with no HTTP endpoint; the default-mode lock passes.

**7. Scene3D improvements?**
The SGK visual port from `research/scene3d-html-visual-port` is now combined with the B1/B2 coincident-identity labels (`A ≡ H ≡ H1`):
- unlit two-pass shells;
- terracotta section at 0.32;
- dashed violet plane border;
- screen-sized right-angle marks;
- role-styled labels;
- ivory canvas;
- 0-allocation orbit.

The label rewrite is gone.

**8. Final candidate SHA?**
- Product `a9d05dda4576e1968738760e382951e755ff8be4`.
- Freeze `aec7b183a888e2ca18c53b624c458714234b93a5`: 118 files, measured tree `d22d27e7d06228ccc440f25b18137c0fd835e068fca106ce61d828b3a87af9cc`.
- T3 target `b99afd32`.

**9. Full T3 PASS/FAIL/NOT_RUN?**
**PASS** on attempt 2: `FULL_PRODUCT_GATE_PASS`, pytest 11839, Vitest 1337, build, demo, crash surface. Freeze `--verify` after T3 matched. Attempt 1 failed on the merge defect and its receipt is kept.

**10. Browser acceptance?**
PASS:
- Adapter /4 consumer: 94 rows, desktop and mobile.
- Orbit gate: ĐẠT, 0 allocations.
- Default scenes: 12 captures, 0 errors.
- Label probe: `(HUW)` shown verbatim.

Not covered in the browser: `I1`/`MI1I2I3`, because no loadable `/4` envelope or sample contains it (unit test only). The official Visual suite is an inherited FAIL. See BROWSER_ACCEPTANCE.md.

**11. Review blockers?**
None. The integrated review is **INTERNAL**: a fresh read-only Claude subagent, not independent. Verdict PASS_WITH_FINDINGS, with 0 BLOCKER, 0 MAJOR and 2 MINOR findings:
- F1: missing doc write-back; fixed.
- F2: an inherited diagnostics drawer shows `reason_code` in `<details>`; left for the owner.

See INDEPENDENT_REVIEW.md.

**12. What remains open before owner merge?**
- Owner decision on the official Visual suite: the oracle expects final answers in the quantity drawer, while the learner UX from `aa458cc3` removes them. One of the two must change.
- Owner GO or NO-GO on the backend display-identity proposal (`MI1I2I3`, `(HUW)`).
- Owner decision on the diagnostics drawer that shows `reason_code` (review F2, inherited from `7ce563b3`).
- Human visual approval: NOT_GRANTED.
- The 27 publication exceptions: pending, untouched.
- `adapter3_simulation.py` (+61/−9 from the merge): verified by tests, not re-read hunk by hunk.
- A truly independent review, if the owner wants one; this one is internal.
- The merge itself: `integration/hybrid-visual-candidate` is ahead of `main` (`main` is an ancestor; 55 commits at `b99afd32`, plus the reports commit), and the owner decides.

**13. Which worktrees exist and hold uncommitted data?**
27 worktrees are registered; none was created, removed or cleaned in this task.

Worktrees with uncommitted data:

| Worktree | Uncommitted |
|---|---|
| root `D:/Documents/projects/algo-sim` (`research/hybrid-wave3a-volume-reasoning`) | owner's 19 tracked + 8 untracked; the 79 hashed files are re-checked and unchanged |
| `visual-hybrid-integration` (Codex, detached `13d28b84`) | harness hunk (now committed on the branch as `1fcbe7e5`) + `.visual-closure-vite-cache/` + run evidence; Codex's Vite server on 3117 still running |
| `scene3d-unified-visual-language` | 15 tracked + 287 untracked (older session, not touched) |
| `extraction-v2-safety` | 2 tracked + 1 untracked (not touched) |
| `freeze-scene3d-metric-boundary`, `freeze-scene3d-metric-final` | 1 tracked each (not touched) |
| `simulation-coverage-visual-validation` | 1 tracked + 1 untracked (not touched) |
| `hybrid-backend-s1` | 8 untracked (not touched) |
| `scene3d-plane-grid-camera` | 1 untracked (not touched) |
| `t3-scene3d-pre-main`, `t3-scene3d-pre-main-2` | 2 untracked each (not touched) |

Clean, used here:
- `hybrid-visual-candidate`: clean after the reports commit.
- `t3-b1b2`: detached `b99afd32`, measurement tree.
- `scene3d-html-port`.
- `hybrid-primary-b1-b2-offline`.

## Reports in this run

- CODEX_TO_CLAUDE_TAKEOVER.md
- VISUAL_HYBRID_INTEGRATION_REPORT.md
- GEOMETRY_LABEL_AUTHORITY_FIX.md
- REGRESSION_RESULTS.md
- BROWSER_ACCEPTANCE.md
- INDEPENDENT_REVIEW.md (internal review)
- this file

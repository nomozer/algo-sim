# Visual–Hybrid integration report

Branch `integration/hybrid-visual-candidate` (worktree `.superpowers/worktrees/hybrid-visual-candidate`), local only.

## History

| Commit | Made by (session) | Content |
|---|---|---|
| `78e88470` | Codex | Merge. First parent: Hybrid B1/B2 `97d59bf9` (main `9978e512` is its ancestor). Second parent: Scene3D SGK visual port `7f90d9b3`. History preserved, no rebase or cherry-pick |
| `a9d05dda` | Claude (Codex's fix, verified) | `kyHieu` shows backend notation verbatim (GEOMETRY_LABEL_AUTHORITY_FIX.md) |
| `1fcbe7e5` | Claude (Codex's hunk) | `compiler-scene-suite.mjs` harness: export `sectionFillEvidence`, record aborted served runs, per-scenario JSON |
| `aec7b183` | Claude | Clean-tree candidate freeze (product `a9d05dda`, 118 files, `d22d27e7…`) |
| `b99afd32` | Claude | Run evidence + correction-chain join layer |

## Overlapping paths and how the merge resolved them (verified)

| Path | Result in `78e88470` |
|---|---|
| `frontend/src/.../scene3d-subentities.ts` | Keeps Visual's `diemTaiDinhThietDien` (current-step label role) **and** B1/B2's certified coincident section-vertex identity in `deriveSectionSubEntities`; `scene3d-section-vertex-identity.test.ts` included |
| `backend/app/ai/adapter3_simulation.py` (+ test) | +61/−9 vs the B1/B2 parent (Visual's display naming brought in). Verified by the full backend suite (Full T3) and by Adapter /3 / B1/B2 tests passing; Claude did not re-read every merged hunk line by line |
| Index docs and the candidate manifest | Docs merged; manifest regenerated (Codex's dirty-tree freeze superseded by the clean freeze `aec7b183`) |

**Defect found after the merge (fixed).** Both parents had independently corrected `runs/simulation-demo6b-renderer-fix/candidate_divergence.json`:
- Visual corrected it via `simulation-visual-consistency-learning-ux`;
- B1/B2 corrected it via `typedfactnext-planner-bridge`.

The merged tree therefore had two current declarations, and `tests/geometry/test_thesis_acceptance_matrix.py` failed at collection. That is Full T3 attempt 1, receipt `verification/full-t3-attempt1/`. The fix is the repository's own fork mechanism: one join layer `runs/visual-hybrid-integration/candidate_divergence.json` with `corrects` = both fork successors, declaring the current hash `d22d27e7…` and product `a9d05dda`, as the existing `wave3a-adapter3-integration` join does. `test_thesis_acceptance_matrix.py`: 52/52.

## What the integrated product contains

- **Hybrid B1/B2, disabled.**
  - Source-bound TypedFacts V2 extraction (offline replay only).
  - Product Adapter /4 wrapper and the internal `run_hybrid_offline` service behind the existing research policy.
  - No HTTP endpoint or client flag; LLM_ONLY default; cache 127.
  - Fresh export at `78e88470`: 47 cases, 22 served, 25 refused, 0 wrong-served, 0 false-refused.
- **Scene3D SGK visual port.** Unlit two-pass shells, terracotta section, dashed violet plane border, screen-sized right-angle marks, role-styled labels, ivory canvas, orbit allocation fixes.
- **Label authority.** Notation is backend-owned and shown verbatim.

## Scope respected

- Not done here: no renderer rewrite, no new geometry families, no backend change in this takeover, no oracle or threshold change.
- Kept off: no live provider; Hybrid production stays NO-GO.
- No main merge or push.

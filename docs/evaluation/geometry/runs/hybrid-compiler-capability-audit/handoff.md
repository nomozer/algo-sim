# Hybrid compiler capability audit: handoff

Status: `HYBRID_GOAL_DIRECTED_COMPILER_DESIGN_AWAITING_APPROVAL`.
Next action: `HYBRID_GOAL_DIRECTED_COMPILER_DESIGN_APPROVAL_DECISION` (the user's decision).
LIVE GEMINI CALLS = 0. PRODUCTION DEFAULT = UNCHANGED (`LLM_ONLY`, cache 125).

## 1. Deliverables

| # | Item | Where |
|---|---|---|
| 1 | ADR Hybrid B | [`docs/architecture/HYBRID_B_TARGET_ARCHITECTURE_DECISION.md`](../../../../architecture/HYBRID_B_TARGET_ARCHITECTURE_DECISION.md) |
| 2 | Compiler capability matrix | [`report.md`](report.md) §3 |
| 3 | Benchmark and oracle | `backend/tests/geometry/hybrid_compiler_benchmark.py`, `test_hybrid_compiler_benchmark.py` (pre-registered `267eeb58`); `backend/scripts/measure_hybrid_compiler_benchmark.py`; [`baseline/metrics.json`](baseline/metrics.json) |
| 4 | Cases the compiler composes itself | 18 served (B01–B16, B29, B30). Multi-step composition comes from the engine's fixed-point resolution of **stated** constructions: chains (B09, B10), derived inputs (B11, B12), reversed order (B13, B14) and renamed labels (B15, B16) |
| 5 | Library has the parts, compiler does not compose them | B26 (point→line distance), B27 (unnamed derived operand); B28 is a cue gap, not composition |
| 6 | Root causes | [`report.md`](report.md) §5 |
| 7 | Proposed minimal change | [`design.md`](design.md): option B, bounded decomposition rules with auxiliary objects inside `planner.py`; [`plan.md`](plan.md) |
| 8 | Code/tests | Benchmark and measurement script only. **No compiler change**: every fix touches the source gate or the Typed Facts schema, so it is not a small rule |
| 9 | Regression | §3 below |
| 10 | Open research limits | [`report.md`](report.md) §6; `ISSUE-ARCH-HYBRID-COMPILER-NO-GOAL-COMPOSITION`, `ISSUE-ARCH-HYBRID-SOURCE-CUE-CENTRE-OF-SQUARE` |
| 11 | Git and worktrees | §2 and §4 below |
| 12 | Next priority work | §5 below |

## 2. Git

| Item | Value |
|---|---|
| `main` | `548066a8` = `origin/main`, unchanged. Only `?? frontend/public/` is untracked; it belongs to the user and was not touched |
| Research branch | `research/hybrid-compiler-capability-audit`: `267eeb58` (benchmark), then the docs commit of this run. Not merged, not pushed, no PR |
| Old branches (audited, kept) | `docs/real-model-e2e-readiness` `4cfa547f` (synced with `origin`); `feat/real-model-pilot-tooling` `471a2c79` (1 unpushed commit that records a live run, so do not delete it). Both merge cleanly into `main`; see [`report.md`](report.md) §2 |
| Candidate | `a8dc02fc…` (product `74df2a78`); `--verify` exit 0. No change under `backend/app` or `frontend/src`. A/B `12da4768…` untouched |
| Commit rules | Files staged one by one; no `Co-Authored-By` trailer; `267eeb58` not amended (its "19/8" message is corrected in the report) |

## 3. Regression (this worktree, 0 model calls)

| Command (from `backend/`) | Result |
|---|---|
| `pytest tests/geometry/test_hybrid_compiler_benchmark.py test_geometry_library_expansion.py test_text_to_geometry_functions.py test_ai_function_route.py test_hybrid_compiler_selection.py test_projection_scene_topology.py test_structured_geometry_relations.py test_hybrid_ab_branch_readiness.py` | 485 passed, 6 xfailed (the 3 gaps × 2 evaluations, strict) |
| `pytest tests/geometry/test_docs_information_architecture.py tests/test_current_state_identity.py` | 45 passed |
| `scripts/audit_docs_information_architecture.py` | PASS |
| `scripts/freeze_evaluation_candidate.py --verify` | candidate matches, 110 files `a8dc02fc…` |

- The full backend suite and T3 were not run. No production code changed, and the brief makes them conditional on such a change.

## 4. Worktree clean-up

| | Before | After |
|---|---|---|
| Registered worktrees | 2 (main checkout and `hybrid-compiler-audit`) | 2. The research worktree is kept because the design awaits approval and the work continues there |
| `git worktree prune --dry-run` | nothing to prune | — |
| Space freed | — | 0 bytes |

- No `--force` was used and nothing was deleted.
- **Leftover outside git:** `.superpowers/worktrees/geometry-library-expansion/` is about 551 KB (21 readable files plus an unreadable `.pytest_cache`).
  - It is not a registered worktree. It is left over from the worktree removed in the main-integration run, and its files belong to `CodexSandboxOffline`.
  - This account cannot delete it, and ACLs were not changed. Removing it needs an administrator. The same files are in the merged history of `main`.

## 5. Next work, in priority order

1. **The user decides on design option B** (`design.md`).
   - Approve slice 1 (B26), and optionally slice 2 (B27, schema change), or choose option A/C or none.
2. If approved, implement slice 1 test-first on this branch.
   - Then rerun the benchmark into a **new** directory, run the full backend + T3 in a clean worktree, and refreeze the candidate in its own commit.
3. Separately, and still open: `ISSUE-ARCH-ORBIT-P1-SECTION-SCENE-DOES-NOT-SETTLE` (P1 on `main`).
4. A real-model A/B pilot still needs its own approval and re-registration (current surface NO-GO).

# Goal decomposition slice 1: handoff

Status: `HYBRID_GOAL_DECOMPOSITION_SLICE1_AWAITING_REVIEW`.
Next action: `HYBRID_GOAL_DECOMPOSITION_SLICE1_REVIEW` (the user's).
LIVE GEMINI CALLS = 0. PRODUCTION DEFAULT = UNCHANGED (`LLM_ONLY`, cache 125).

## 1. Before / after

| | before | after |
|---|---|---|
| Benchmark (30 cases, both evaluations): correct served / correct refusal / **wrong served** / false refusal | 18 / 9 / **0** / 3 | 19 / 9 / **0** / 2 |
| B26 "khoảng cách từ S đến BD" | `UNSUPPORTED_CAPABILITY` | √11 (oracle 11) |
| Planner | geometry-fact-planner/2, one fact → one call | /3, plus one bounded decomposition rule |
| Candidate | `a8dc02fc…` (product `74df2a78`) | `cac3022f…` (product `f874b4dd`), refreeze `d8d636b5`, divergence declared |
| Provider surfaces A / B, function declarations | `1e3f71ea…` / `a4f368cb…` / `41e090cd…` | identical (pinned in a test) |

Details, the source decision for every auxiliary, and the limits are in [`report.md`](report.md).

## 2. Verification

| Check | Result |
|---|---|
| RED at `4a3a4938` (unchanged code, clean worktree) | 38 failed, 96 passed, 4 xfailed ([log](red-baseline-at-4a3a4938.txt)) |
| Focused `test_hybrid_goal_decomposition.py` | 40 passed: 9 source mutants killed, 6 gate tampers refused |
| Hybrid / function-route cluster (11 files) | 629 passed, 4 xfailed (B27, B28 × 2) |
| Candidate | `--verify` exit 0 at `d8d636b5` and `76a60617` |
| T3 #1 at `d8d636b5` (clean worktree) | **FULL_PRODUCT_GATE_FAIL**: pytest 8333 passed, 1 failed. `test_C2b_candidate_hien_tai_phai_duoc_KHAI`: the candidate divergence was not declared yet. Vitest 1051, build, demo replay and crash surface all PASS |
| T3 #2 at `76a60617` (clean worktree, after the declaration) | **FULL_PRODUCT_GATE_PASS**: pytest 8334 passed, 0 failed, 1 skipped, 2 deselected, 4 xfailed; vitest 1051; build; demo replay; crash surface |
| Docs gate | `test_docs_information_architecture` + `test_current_state_identity` + `test_thesis_acceptance_matrix`: 97 passed; audit PASS |

- Not run: the browser gates. The frontend did not change and route D is not wired to the UI.
- Human visual review: not performed.

## 3. Git

| Item | Value |
|---|---|
| Branch | `research/hybrid-compiler-capability-audit`: `267eeb58` → `4a3a4938` → `f874b4dd` (product) → `d8d636b5` (refreeze) → `76a60617` (docs + declaration) → the T3 record commit |
| `main` | `548066a8` = `origin/main`, unchanged; no merge, no push, no PR |
| Commit rules | files staged one by one; no `Co-Authored-By` trailer; no amend |
| Untouched | `frontend/public/` of the main checkout, user backups, the locked A/B candidate `12da4768`, historical evidence (the capability-audit baseline `metrics.json` is byte-for-byte unchanged; the new measurement is in [`after/`](after/metrics.json)) |

## 4. Clean-up

| Worktree | Purpose | Removed | Size |
|---|---|---|---|
| `goal-decomp-red` (detached `4a3a4938`) | RED baseline | yes | ≈ 1.6 GB (`du -sh`) |
| `goal-decomp-verify` (detached `d8d636b5` → `76a60617`) | refreeze, T3 ×2 | yes | 1 700 483 287 bytes |

- **Registered worktrees:** 2 → 4 during the work → 2 after (the main checkout and `hybrid-compiler-audit`).
- **Freed:** ≈ 3.3 GB in total.
- **How:**
  - `git worktree remove` without `--force`, then `git worktree prune`.
  - The `node_modules` junction was removed first with `rmdir`; its target is intact.
  - In the RED worktree, the two test files I had copied in were restored or cleaned one by one before removal.
- **Research worktree:** kept, because the slice is not integrated.
  - Its test-generated `backend/algosim.db` (159 744 bytes) was removed with `git clean -X` on that one path.
- **Not touched:** `.superpowers/worktrees/geometry-library-expansion/` (≈ 551 KB, unregistered, owned by CodexSandboxOffline). It needs an administrator.
- **T3 logs** are in the session scratchpad, outside the repository.

## 5. GO / NO-GO

- **Integrating slice 1 into `main` (offline): GO, conditional on your review.**
  - T3 PASS and the candidate is verified.
  - The benchmark gains one case with 0 wrong served; the other 29 are unchanged.
  - Provider surfaces are unchanged, and the default route does not reach the new code.
  - Procedure if approved: fast-forward from `main`, as in the main-integration run.
- **Any claim about real Gemini, or a pilot: NO-GO.** There is no real-model evidence; extraction of (point, line) distance questions was not measured.
- **Slice 2 (B27): NO-GO until separately approved.** It changes the Typed Facts schema and B's provider surface.

## 6. Open after this run

- `ISSUE-ARCH-HYBRID-AUXILIARY-POINT-LIMITS`:
  - the label is fresh but not syntactically reserved;
  - one wording only;
  - a point on the line gives a coinciding foot.
- `ISSUE-ARCH-HYBRID-COMPILER-NO-GOAL-COMPOSITION`: B27 still open.
- `ISSUE-ARCH-HYBRID-SOURCE-CUE-CENTRE-OF-SQUARE`: B28.
- `ISSUE-ARCH-ORBIT-P1-SECTION-SCENE-DOES-NOT-SETTLE`: P1 on `main`, unrelated to this run.

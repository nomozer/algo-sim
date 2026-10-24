# Regression results (visual–Hybrid integration)

Candidate: product `a9d05dda`, freeze `aec7b183` (118 files, tree `d22d27e7…`), evidence commit `b99afd32`. All authoritative runs were made in the clean detached worktree `.superpowers/worktrees/t3-b1b2` at `b99afd32`, with `git status --porcelain` empty before and after.

## Full T3 (`frontend/scripts/full-gate.mjs`)

| Attempt | Commit | Verdict | Receipt |
|---|---|---|---|
| 1 | `aec7b183` | **FAIL** after 38 s: collection error in `test_thesis_acceptance_matrix.py` (two current correction layers of `simulation-demo6b-renderer-fix`) | `verification/full-t3-attempt1/execution.json` |
| 2 | `b99afd32` | **`FULL_PRODUCT_GATE_PASS`**, 543 s, exit 0 | `verification/full-t3-attempt2/execution.json` (sha256 `629e960c…`) |

Attempt 1 is kept because it found a real merge defect. VISUAL_HYBRID_INTEGRATION_REPORT.md describes the defect and the join-layer fix.

Attempt 2 stages:

| Stage | Result |
|---|---|
| pytest (whole backend) | 11839 passed, 1 skipped, 2 deselected, 15 xfailed |
| Vitest | 79 files, 1337 tests passed |
| typecheck + production build | pass |
| thesis demo replay | pass |
| demo crash surface | pass (six refusal boundaries refuse with the right kind, no 500) |
| `freeze_evaluation_candidate.py --verify` after T3 | "Candidate khớp bản đã đóng băng (118 file, d22d27e7…)" |

## Outside T3

| Check | Result |
|---|---|
| `node --test "scripts/*.node-test.mjs"` (clean worktree) | 112 tests: 110 pass, 2 skipped, 0 fail |
| Label authority `scene3d-presentation.test.ts` | RED on the old V6.2 code: 4 failures (`I1`, `I12`, `AI2`, `(HUW)`). GREEN 19/19 after `a9d05dda` |
| Correction chain `test_thesis_acceptance_matrix.py` | 52/52 after the join layer |
| Integrated B1/B2 offline export at `78e88470` (Codex) | 47 cases: 22 served, 25 refused, 0 wrong-served, 0 false-refused |

## Owner regression list (P3)

| Area | Evidence | Status |
|---|---|---|
| Presentation / SGK styling | Vitest (Scene3D suites), orbit gate, default-scene captures | PASS |
| Label authority | unit RED/GREEN; browser shows `(HUW)` verbatim; served source has no `/I\d/` and no `(HUW)` rewrite | PASS (browser part covers `(HUW)` only, see BROWSER_ACCEPTANCE.md) |
| Aliases / coincident identity | B1/B2 `A ≡ H ≡ H1` label shown in the integrated scene; `scene3d-section-vertex-identity.test.ts` in Vitest | PASS |
| Plane names | `(α)` / `(HUW)` shown as the backend sends them | PASS (`(HUW)` is a backend gap, see GEOMETRY_LABEL_AUTHORITY_FIX.md) |
| Sections | section fill and border in captures; section suites in Vitest and pytest | PASS |
| Provenance | backend suite (pytest) unchanged and green; no backend file changed after the merge | PASS |
| LLM_ONLY default | `CACHE_VERSION = "127"`; `main..HEAD` changes nothing in `app/ai/skills`, `main.py`, `ai/pipeline.py` or `geometry_compiler/routing.py`; the default-mode lock test passes in T3 pytest | PASS |
| Adapter /4 consumer | browser acceptance 94 rows (47 cases × desktop + mobile), `FRONTEND_CONSUMER_ACCEPTANCE_PASS` | PASS |
| Browser desktop / mobile | 1440×900 and 390×844 in every browser check | PASS |
| Existing scenes | offline samples `thiet-dien-chop`, `mp-vuong-goc-duong`, `cau-cat-mat-phang` load and render with 0 page errors | PASS |

## Known red, not caused by this integration

**Official Visual suite `compiler-scene-suite.mjs`** was run by Codex on the Visual candidate `13d28b84`, before the merge (receipts in `visual/official-suite-complete/`). All 8 scenarios fail:
- **7 scenarios have HARNESS-class aborts**: `quantity_picker` / `solution_final` / `show_all_toggle`, and `CAUSAL_TARGET_NOT_CLICKABLE`.
  - Root cause: commit `aa458cc3` (2026-10-19, in `main`). Its simulation-first learner UX removes final answers from the quantity drawer, and the suite oracle still expects them.
- **2 scenarios have ENVIRONMENT-class aborts**: `cross_section` (`POLL_TIMEOUT`) and `regular_triangular_pyramid`. `regular_triangular_pyramid` also has a HARNESS abort, so the count is 8 scenarios, not 9.
- Not re-run on the integrated candidate. It would hit the same oracle/UX mismatch, and resolving that means changing either the oracle or the learner UX, which is an owner decision. The takeover report's "7 HARNESS + 2 ENVIRONMENT" counts scenarios with overlap.

**Dirty-tree full pytest** (working tree, `-x`, before the T3 run) stopped at `test_holdout_readiness.py::test_bao_cao_da_sinh_va_KHONG_TROI`. The cause is "CÂY LÀM VIỆC BẨN": the test requires a clean tree, so it is environmental. It passes inside Full T3 on the clean tree.

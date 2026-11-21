# Merge Readiness, Impact & Rollback Audit — AXO HYBRID /19

**Run:** `model1-final-text-acceptance` (2026-11-21) · **Branch:** `feat/model1-final-text-acceptance` (`b10c0a1e4` + `/19` docs commit) · **Target:** `main` (`bc6ff5e333e32d1d53dc7435fba64fe12b6dd651`).
**Read-only audit:** Zero merge, push, tag, or `main` modification performed.

---

## 1. Repository & Protected `main` Integrity

| Item | Verified State |
|---|---|
| `main` (`origin/main`) | `bc6ff5e333e32d1d53dc7435fba64fe12b6dd651` (`merge-base main HEAD = bc6ff5e33`, fast-forwardable) |
| Protected untracked `main` folder | `docs/evaluation/geometry/runs/post-merge-cleanup-closure/` (6 files, all SHA-256s match `/18` baseline byte-for-byte after temporary detached worktree cleanup) |
| Commits `bc6ff5e33..b10c0a1e4` | `404` commits (`402` up to `/18` `cf0b646f5` + `98163cce5` + `b10c0a1e4` `.gitattributes` LF rule for `V12_ACCEPTANCE_MANIFEST.json`, plus final `/19` docs commit) |
| Temporary measurement worktree `measure-model1-c158` | Created in `/19`, used clean at `b10c0a1e4`, verified clean, cleanly removed via `git worktree remove` (without `--force`) |

### Protected `main` Untracked Checksums (`post-merge-cleanup-closure/`)
- `AXO-POST-MERGE-CLEANUP-CLOSURE-REPORT.md`: `2c9b77afa09b3c4b4a3916333fa1ebe504cabe1da54585107e4a0a547280407c`
- `report.md`: `943d4e29fb42cd751608597f6afed7de74a7af5e7464679363ca63d1f5d31a63`
- `results/backup-and-cleanup-verification.json`: `915e54d3f30641084798f3760d3edddf3308d98ef21ad22061cab7a8f614ffa2`
- `results/before-after-inventory.json`: `372c29bc0ce4907fcf138827ae72febdf6c28b5e1b5d29d59ffe35abce580bff`
- `results/runtime-and-regression-verification.json`: `93bdcd22c6c930ec5fb37a2b89f2becf13e46a59be2cfe28ff5861bad4dfc8e6`
- `run.json`: `8a3cb34a76b38221f491da27d6798f75258f57cc9357aafa13871afa4afed7a3`

---

## 2. Diff Scope & Contract Safety (`bc6ff5e33..HEAD`)

- `git diff --shortstat bc6ff5e33..b10c0a1e4`: `2,853 files changed, +1,676,622 insertions, -56,325 deletions` (plus final `/19` run docs & 5 canonical docs).
- **Zero product change since Candidate 158 (`2bb0211a1`):** `git diff 2bb0211a1..HEAD -- backend/app frontend/src` = **empty (`0` bytes changed)**.
- **Database migrations:** `0` changes (`backend/alembic/**`, `backend/app/persistence/**` untouched).
- **Default route mode:** `HYBRID_ROUTE_MODE = "live"` unchanged; local modes (`local-only-scoped`, `local-only-general`, etc.) remain opt-in.
- **Shared core contracts:** `TypedFactNext /2`, `Source Gate /33`, `Planner /26`, `Exact Kernel /24`, and `Adapter /4` retain schema/contract integrity, while code fixes in those shared modules also affect `live` Gemini requests once merged (see offline replay compatibility in `GEMINI_LIVE_COMPATIBILITY_AUDIT.json`: `82/82` identical across 5 historical corpora; live Gemini API smoke remains `NOT_MEASURED`).
- **Environment checkout fix:** Root `.gitattributes` pins `docs/evaluation/geometry/runs/axo-hybrid-compositional-geometry-language-grounded-simulation/V12_ACCEPTANCE_MANIFEST.json text eol=lf` so Windows `core.autocrlf=true` clones do not corrupt the byte-locked `/12` manifest while keeping CRLF behavior intact for all Windows-pinned fixtures (`test_exporter_idempotence`, `test_benchmark_seal`, `test_counter_decomposition`, `test_step_math_validation`).

---

## 3. Authoritative Measurement, Publication & Merge Readiness Gates

| Gate | Status | Evidence |
|---|---|---|
| Candidate 158 freeze & cache lock | **PASS** | `bdb737bba9ab94d0274b57e25089c01d4cb47935d5989658e7c13aad1e79b132` (`127` files), `CACHE_VERSION = 158` |
| Authoritative Detached Full T3 (`measure-model1-c158`, `b10c0a1e4`) | **PASS (`VERIFIED`)** | `15,178` pytest (`0` failed), `203 files / 2,345` Vitest (`0` failed), build, demo `5/5+1/1`, crash `6/6` (`AUTHORITATIVE_FULL_T3_RECEIPT.json`) |
| Prospective Acceptance (`Holdout-7`, Class B) | **FAIL** | End-to-end `46/58 (0.7931 < 0.85)`, SLM fallback `3/15 (0.2000 < 0.50)`, SLM independent `25/58 (0.4310 < 0.60, gate_pass=false)` (`PROSPECTIVE_TEXT_ACCEPTANCE.json`) |
| External Independent Validation (Class C) | **NOT_MEASURED** | No rights-cleared text external source or third-party evaluator (`EXTERNAL_INDEPENDENCE = NOT_MEASURED`) |
| Gemini Live Compatibility | **PARTIAL (`NOT_MEASURED` live)** | Offline downstream replay `82/82` parity vs `main`; live Gemini API smoke (`ALLOW_LIVE_AI=1`) `NOT_MEASURED` |
| Publication Safety (`bc6ff5e33..HEAD`) | **BLOCKED (`OWNER_DECISION`)** | `0` hits in `/19` (`cf0b646f5..HEAD` `0` violations); `12` hits (`11` path/blob pairs) in frozen `/10`–`/12` tools + `96` pending on `main`; `0` true secrets |
| `MAIN_MERGE_READY` | **`FALSE`** | Blocked by failed prospective Model 1 acceptance on 158, unapproved publication exceptions (D4), unrun live smoke/waiver (D7), and explicit owner D1/D2 approval |

---

## 4. Merge Procedure (ONLY After Owner Resolves All Blockers & Grants Explicit Permission)

1. Confirm owner decisions **D1–D7** and explicit acceptance decision regarding Candidate 158's failed Holdout-7 (`46/58`) vs remediation wave vs dormant-flag merge of shared fixes.
2. Tag rollback anchor on clean `main`: `git tag pre-model1-merge bc6ff5e33`.
3. Ensure `check_publication_safety.py --range bc6ff5e33..<tip>` exits `0` (after owner approves exact `publication_exceptions.json` entries or chooses an approved alternative).
4. Execute local `--no-ff` merge (no PR, no push without separate permission):
   - `git switch main && git merge --no-ff feat/model1-final-text-acceptance` (producing a single merge commit `M` with first parent `bc6ff5e33`).
5. Run verification on merged `main` while protecting `docs/evaluation/geometry/runs/post-merge-cleanup-closure/`.
6. Cleanup old branch/shared worktree and create the two post-merge session worktrees ONLY after explicit owner merge/post-merge authorization.

---

## 5. Rollback Plan (Forward-Only, Zero History Rewrite)

1. **Fastest Operational / Deployment Rollback (Zero Git Change):**
   - Redeploy `bc6ff5e33` (tag `pre-model1-merge`). Zero DB schema migrations exist on the branch, so `bc6ff5e33` reads the existing schema cleanly.
   - Cache rows are strictly isolated by `ROUTE_D_CACHE_POLICY` (`132:route-d` on `main` vs `158:route-d` on branch), preventing cross-version replay.
   - Leave `HYBRID_ROUTE_MODE` unset (`"live"` default). Note: missing/invalid local GGUF triggers fail-closed `503 MODEL_RUNTIME_UNAVAILABLE` / `MODEL_CHECKSUM_MISMATCH` (`no-store`) without affecting parser-readable requests, while `ALLOW_LIVE_AI=0` stops cloud calls cleanly.
2. **Git Forward-Only Revert (`--no-ff` merge commit `M`):**
   - Run `git revert -m 1 M` on `main` (single commit restoring `bc6ff5e33` tree). Re-merging later requires reverting the revert commit first.
   - If ever fast-forwarded instead of `--no-ff`, restore via `git commit-tree bc6ff5e33^{tree} -p main -m "revert: restore pre-model1 tree bc6ff5e33"` + `git merge --ff-only <commit>` (never range-revert across the 5 interleaved merge commits).

---

## 6. Post-Merge Parallel Session Boundaries (§VIII, Inactive Until Merge Approved)

- **Session 1 (Model 1 architecture & performance):** `local_geometry_parser.py`, `slm_verified_normalizer.py`, `local_slm_extractor.py`, `local_slm_runtime.py`, `adaptive_input_router.py`, `compositional_clause_analysis.py`, `local_failure_diagnostics.py`, `hybrid_offline.py` (`local-only-*`), caching/queue/concurrency/Linux readiness — priority item surfaced by Holdout-7: colloquial & multi-clause grounding (`learner_colloquial 1/10`, `teacher_wording 12/15`, `SLM_UNRESOLVED` 19 cases + Source Gate quote-binding 12 cases).
- **Session 2 (Dynamic Construction Planner /2 + Model 2):** `backend/experimental/construction_planner/**`, `construction_continuity.py`, `step_editor.py`, and Model 2 modules behind existing `Registry /33` & `Exact Kernel /24` contracts.
- **Shared locked contracts (`TypedFactNext /2`, `Registry /33`, `Planner /26`, `Exact Kernel /24`, `Adapter /4`, `CACHE_VERSION`, `live-acceptance` harness):** serialized contract-proposal process only; OCR remains outside both sessions.

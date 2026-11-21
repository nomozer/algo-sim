# HANDOFF_STATE — AXO HYBRID /19 (`model1-final-text-acceptance`)

- **Timestamp:** 2026-11-21T23:25:00+07:00
- **Shared worktree:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\simulation-intent-slm-recovery`
- **Branch:** `feat/model1-final-text-acceptance`
- **Measured commit:** `b10c0a1e4022dfd5af93aeb6ebf75de61078a901` (`b10c0a1e4`, Candidate 158 unchanged vs `2bb0211a1` / freeze `b92b68a94`, tree `bdb737bba9ab94d0274b57e25089c01d4cb47935d5989658e7c13aad1e79b132`, `127` files, `CACHE_VERSION = 158`)
- **Temporary detached measurement worktree:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\measure-model1-c158` — cleanly verified empty `git status` and removed via `git worktree remove` (without `--force`)
- **Main checkout:** `D:\Documents\projects\algo-sim` on `main` = `origin/main` = `bc6ff5e33`, untouched; all 6 files in `docs/evaluation/geometry/runs/post-merge-cleanup-closure/` verified byte-for-byte intact

## Workstream Completion Status

- **Candidate 158 integrity:** `PASS` (`freeze --verify`, `lock --verify`, `0` diff `backend/app` / `frontend/src` since `2bb0211a1`).
- **`test_holdout_freeze_is_intact()` root cause:** Diagnosed & fixed without modifying frozen harness or Candidate 158 — Windows `core.autocrlf=true` converted frozen `V12_ACCEPTANCE_MANIFEST.json` to CRLF in detached checkout; reverted previous agent's invalid uncommitted edits to `aggregate.py` & `test_shared_live_harness.py` and added root `.gitattributes` (`text eol=lf` for `V12_ACCEPTANCE_MANIFEST.json`).
- **Authoritative Detached Full T3:** `PASS` (`AUTHORITATIVE_DETACHED_COMPLIANCE = VERIFIED`, `FULL_PRODUCT_GATE_PASS`, `15,178` pytest / `203 files / 2,345` vitest / build / demo `5/5+1/1` / crash `6/6` in `1346.9s`, log SHA-256 `95b1b4dbb2c546b39d8db7d2a9dfcc823f8b47ed809869283a4596eb62949a7b`).
- **Prospective Text Acceptance (`Holdout-7` `58+22`, Class B, `EXTERNAL_INDEPENDENCE = NOT_MEASURED`):** `FAIL` on Candidate 158 (`END_TO_END_SYSTEM_SCORE = 46/58 = 0.7931 < 0.85` [95% Wilson `0.6723..0.8775`], `CANDIDATE_FALLBACK_SCORE = 3/15 = 0.2000 < 0.50` [`0.0705..0.4519`], `INDEPENDENT_SLM_SCORE = 25/58 = 0.4310 < 0.60` [`0.3118..0.5588`, `gate_pass = false`], `22/22` neg safe, `10/10` UI, `46/46` valid served scenes, `0` external network hits).
- **Gemini live-route compatibility:** Offline downstream replay parity `82/82` (`0` deltas, `0` crashes vs `bc6ff5e33` across 5 corpora); live Gemini API smoke (`ALLOW_LIVE_AI=1`) = `NOT_MEASURED`.
- **Publication safety:** `BLOCKED_OWNER_DECISION` (`0` new hits in `/19`; `12` hits / `11` path-blob pairs in frozen `/10`–`/12` tools + `96` pending on `main`; `0` true secrets).
- **Merge readiness & rollback audit:** Complete; `MAIN_MERGE_READY = FALSE`.

## Active Processes & Restrictions

- Zero `/19` processes running (measurement ports `:8019`, `:4173`, `:18999` closed cleanly; unrelated foreign `:8000` uvicorn & `axo-hero-enter-portals` left untouched).
- Not authorized to merge `main`, push remote, create PRs/tags, delete branches/shared worktree, or start Session 1 / Session 2.
- No secrets written to any file.

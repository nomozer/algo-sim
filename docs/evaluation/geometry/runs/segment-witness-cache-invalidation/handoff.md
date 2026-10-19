# Handoff — `segment-witness-cache-invalidation`

- **Status:** `PENDING_FINAL_T3_AND_REVIEW` (updated after the authoritative gate and the independent re-review)
- **Branch:** `research/hybrid-architecture-wave1-exact-certificates-planner` (worktree
  `.superpowers/worktrees/hybrid-architecture-wave1-exact-certificates-planner`); base `main` = `origin/main` = `f0560449`
- **Corrects:** `hybrid-architecture-wave1-exact-certificates-planner` (its receipts at `fd310cd9` / `77b05def` / `14cc4eb4`
  are unchanged)
- **Product commits:** `2635cbd672d6b146cbd237912ee9d254860e80cf` (cache 127 + labels) and
  `008918cb916ff3e4f9fb49492889da3b5c636849` (prism branch, final) — 112 measured files,
  `8cb9857f10f4a62788f7ddc099133eb31d903a36abccea5e5432b8b7e8e37f7d`
- **Invariants:** `CACHE_VERSION = 127`, `DEFAULT_MODE = LLM_ONLY`, response `flat`, `ADAPTER_VERSION =
  "hybrid-preview-adapter/2"`, Hybrid product NO-GO, `ALLOW_LIVE_AI = 0`, 0 provider requests
- **Report:** [`report.md`](report.md); cache decision: [`cache/decision.json`](cache/decision.json)

## History of this run's candidates

| freeze | product | outcome |
|---|---|---|
| `96cf9e6f` | `2635cbd6` | not measured: this run's `candidate_divergence.json` did not exist yet, so `test_C2b` would fail; the T3 started there was stopped (no receipt) |
| `f8ac1ec7` | `2635cbd6` | T3 `FULL_PRODUCT_GATE_PASS` (`verification/superseded-t3-f8ac1ec7.json`, log sha256 `db1d3ff3…`); superseded — the independent review returned `INDEPENDENT_REVIEW_FAIL` (IMPORTANT-1, dead prism branch) |

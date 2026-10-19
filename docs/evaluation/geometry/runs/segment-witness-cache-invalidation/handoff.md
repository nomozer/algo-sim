# Handoff — `segment-witness-cache-invalidation`

- **Verdict:** **`WAVE1_CACHE127_READY_FOR_GO_MAIN`** — merge/push NOT done; awaits owner `GO_MAIN_HYBRID_WAVE1`
- **Branch:** `research/hybrid-architecture-wave1-exact-certificates-planner` (worktree
  `.superpowers/worktrees/hybrid-architecture-wave1-exact-certificates-planner`); base `main` = `origin/main` = `f0560449`
  (fast-forward possible)
- **Corrects:** `hybrid-architecture-wave1-exact-certificates-planner` (its receipts at `fd310cd9` / `77b05def` / `14cc4eb4`
  are unchanged)
- **Product commits:** `2635cbd672d6b146cbd237912ee9d254860e80cf` (cache 127 + labels) and
  `008918cb916ff3e4f9fb49492889da3b5c636849` (prism branch, **final product**)
- **Candidate:** `1117cfd4a2f3fea9c4c6524009eca9fee8300285` — 112 measured files,
  `8cb9857f10f4a62788f7ddc099133eb31d903a36abccea5e5432b8b7e8e37f7d`, `freeze_evaluation_candidate.py --verify` MATCH
- **Authoritative T3** (clean detached worktree at `1117cfd4`, removed afterwards): **`FULL_PRODUCT_GATE_PASS`** — backend
  10986 passed / 0 failed, frontend 70 files / 1146 tests, typecheck + build PASS, demo 5/5 + reduced chain 1/1, crash
  surface 6/6 with 0 unhandled 500 ([`authoritative-t3.json`](authoritative-t3.json), log sha256 `e2fcbcee…`,
  `verification/t3-head.txt`)
- **Independent review:** round 1 `INDEPENDENT_REVIEW_FAIL` (IMPORTANT-1, dead prism branch) → fixed → round 2
  **`INDEPENDENT_REVIEW_PASS`** (0 blockers, 0 important; NB-A/B/C) — [`review.md`](review.md)
- **Cache:** `CACHE_VERSION = 127`; genuine v126 rows (9 served problems) miss, v127 rows hit with the witness, envelope
  otherwise byte-identical — [`cache/decision.json`](cache/decision.json)
- **Invariants:** `DEFAULT_MODE = LLM_ONLY`, response `flat`, `ADAPTER_VERSION = "hybrid-preview-adapter/2"`, Hybrid
  product NO-GO, model surface unchanged (`b1714b56…`), `ALLOW_LIVE_AI = 0`, 0 provider requests
- **Report:** [`report.md`](report.md)

## History of this run's candidates

| freeze | product | outcome |
|---|---|---|
| `96cf9e6f` | `2635cbd6` | not measured: this run's `candidate_divergence.json` did not exist yet, so `test_C2b` would fail; the T3 started there was stopped (no receipt) |
| `f8ac1ec7` | `2635cbd6` | T3 `FULL_PRODUCT_GATE_PASS` (`verification/superseded-t3-f8ac1ec7.json`, log sha256 `db1d3ff3…`); superseded — review round 1 FAIL |
| `1117cfd4` | `008918cb` | **authoritative**: T3 PASS + review round 2 PASS |

## Open after this run

NB-A label wording in composite prism + pyramid scenes (none exist); offline samples `geometry-samples.json` not rebuilt;
Path A markers limited to a pyramid `CONSTRUCT_HEIGHT` segment or a `PRISM_LIKE` height / lateral edge against the
`CONSTRUCT_BASE` polygon (e.g. regular hexagonal pyramids get none); HFOI-F4; route D unwired;
`ISSUE-OPS-CACHE-HISTORICAL-MODE-UNKNOWN`.

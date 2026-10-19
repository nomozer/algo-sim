# Handoff — `segment-witness-cache-invalidation`

- **Status:** `PENDING_T3_AND_REVIEW` (updated after the authoritative gate and the independent review)
- **Branch:** `research/hybrid-architecture-wave1-exact-certificates-planner` (worktree
  `.superpowers/worktrees/hybrid-architecture-wave1-exact-certificates-planner`); base `main` = `origin/main` = `f0560449`
- **Corrects:** `hybrid-architecture-wave1-exact-certificates-planner` (its receipts at `fd310cd9` / `77b05def` / `14cc4eb4`
  are unchanged)
- **Product commit:** `2635cbd672d6b146cbd237912ee9d254860e80cf` — 112 measured files,
  `0fd9ffe5e5e43ffd427bed1f629de540b3692ada807b74fdc4799baa3c1a3981`
- **Invariants:** `CACHE_VERSION = 127`, `DEFAULT_MODE = LLM_ONLY`, response `flat`, `ADAPTER_VERSION =
  "hybrid-preview-adapter/2"`, Hybrid product NO-GO, `ALLOW_LIVE_AI = 0`, 0 provider requests
- **Report:** [`report.md`](report.md); cache decision:
  [`../hybrid-architecture-wave1-exact-certificates-planner/cache/decision.json`](../hybrid-architecture-wave1-exact-certificates-planner/cache/decision.json)

## Intermediate freeze not measured

`96cf9e6f` froze the candidate right after the product commit, before this run's `candidate_divergence.json` layer
existed; `test_thesis_acceptance_matrix.py::test_C2b` requires the newest layer to declare the live hash, so a T3 there
was stopped before completion (no receipt) and the candidate is refrozen after the docs commit.

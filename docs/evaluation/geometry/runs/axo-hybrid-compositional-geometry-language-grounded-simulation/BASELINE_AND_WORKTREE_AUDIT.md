# Baseline & Worktree Audit (AXO HYBRID /12 — P0/P1)

## 1. Worktree & Branch State

- **Active workspace:** `D:/Documents/projects/algo-sim/.superpowers/worktrees/simulation-intent-slm-recovery`
- **New campaign branch:** `feat/compositional-geometry-grounding` (branched cleanly from `/11` tip `ef1075e7df4727e895a913ef4e6fdd8382b8d671`)
- **Main branch (`main`):** `bc6ff5e333e32d1d53dc7435fba64fe12b6dd651` — untouched (no merge, no push, no rebase).
- **`/10` reference commit (`2f12b96b0`):** `2f12b96b0afc6377ca5913953d373e28455f4fcc`
- **Construction `/2` lock check:** `git diff --stat 03200886a HEAD -- backend/experimental/construction_planner/` -> `EMPTY (0 bytes diff)`
- **`backend/tests/geometry/test_axo_construction_v2_integrity_and_integration.py`:** **18/18 PASSED** at branch creation.

### Git Worktree Inventory
```text
worktree D:/Documents/projects/algo-sim
HEAD bc6ff5e333e32d1d53dc7435fba64fe12b6dd651
branch refs/heads/main

worktree D:/Documents/projects/algo-sim/.superpowers/worktrees/axo-landing-page-design
HEAD bc6ff5e333e32d1d53dc7435fba64fe12b6dd651
branch refs/heads/feat/axo-landing-page-design

worktree D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding
HEAD 38c6efbdb439723fbdb56d826677d16e69dada9b
branch refs/heads/feat/local-first-geometry-understanding

worktree D:/Documents/projects/algo-sim/.superpowers/worktrees/simulation-intent-slm-recovery
HEAD ef1075e7df4727e895a913ef4e6fdd8382b8d671
branch refs/heads/feat/compositional-geometry-grounding
```

## 2. Frozen Baseline Artifacts (/11 Entry State)

| Hạng mục | Giá trị đo được |
|---|---|
| Frozen Candidate (`EVALUATION_CANDIDATE.json`) | commit `547423291538e4c839b2743dd4b1c4216d67d594`, `product_commit_sha=31e6b47c90087229346be010111d790fa9a5e4cb`, `cache_version=146`, `cay_lam_viec_sach=True` |
| Cache Lock (`backend/cache_identity.lock.json`) | `cache_version=146`, `semantic_environment_hash=6233c43c395c9b493d31d3dbb5d0ca952604730f6185cf541d2f179c077f955b` |
| Local SLM Provisioning (`provision_local_slm.py --status`) | `active=qwen3-0.6b-axo-v9-q4_k_m` (`sha256=73f1484b08b97ed2...`), `llama.cpp b12470`, cache `C:\Users\Bunny\AppData\Local\axo-slm` |
| Live AI Default (`route_policy.py`) | `HYBRID_ROUTE_MODE = live` kept untouched; `/12` offline runs use `HYBRID_ROUTE_MODE=local-only-scoped`, `ALLOW_LIVE_AI=0`, `GEMINI_API_KEY` unset |

## 3. Baseline /11 Measured Performance & Gaps

- **In-scope Simulation Completion:** `56/85` = **`65.88%`** (Gate target `>= 85%` -> **FAIL** in `/11`).
- **`PARSER_COMPLETE` Stratum:** `52/55` = **`94.55%`**.
- **`SLM_REQUIRED` Stratum:** `4/30` = **`13.33%`** (Gate target `>= 30%` and `>= 5` SLM scenes -> **FAIL** in `/11`).
- **Visual OK of Served:** `56/58` = **`96.55%`** (`2` failures: `S07`, `Q01` — `V11-VIS-1` camera/label clipping).
- **Zero-Tolerance Safety Gates:** `wrong_served_scenes = 0`, `served_numeric_mismatch = 0`, `fabricated_math_goal_on_simulate_only = 0`, `safe_refusal_negatives = 24/24` (**100%**), `interaction_ops = 232/232` (**100%**).
- **Network Isolation & Latency (/11 Host Reference):** `egress_proxy.records = 0`, `tcp_sampler.non_loopback_records = 0`, `browser_external_requests = 0`; `fast_path p50 = 32.0 ms`, `slm_path p50 = 2796.4 ms`, `stack_ws_total_max_mb = 2223.2 MB`.

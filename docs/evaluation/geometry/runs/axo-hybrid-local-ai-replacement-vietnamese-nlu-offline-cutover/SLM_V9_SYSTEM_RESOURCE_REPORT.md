# AXO HYBRID /9 — Phase P4 CPU Runtime, Memory & Ablation Report

> **Model Under Test:** `qwen3-0.6b-axo-v9-q4_k_m` (`llama.cpp b12470`, `-b 512 -ub 512`, `max_tokens=256`)  
> **Scope Disclosures:** `PHYSICAL_TARGET_HARDWARE = NOT_MEASURED` · `FRONTEND_MEMORY = NOT_MEASURED_BACKEND_ONLY` · `external_ai_calls = 0`

---

## 1. Latency & Throughput Summary

| Workload | Count | Served | `p50` E2E (ms) | `p95` E2E (ms) | Mean E2E (ms) | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Cold Start (`AxoV9-Q4_K_M`) | `1` | `1/1` | `6104.96` | `6104.96` | `6104.96` | Server load `970.24` ms, `Scene3D=True` |
| Pure Warm Uncached SLM (`use_cache=False`, `t=6`) | `100` | `100/100` | `4011.93` | `5411.75` | `4011.01` | SLM inf `p50=3954.9` ms, `p95=5344.92` ms, `33.0` tok/s |
| Mixed Warm Uncached (`50` fast + `50` SLM) | `100` | `100/100` | `1270.35` | `4109.98` | `1604.66` | Fast-path `50`, SLM `50` |
| Warm Cached (`use_cache=True` w/ `runtime=rt`) | `25` hits | `25/25` | `29.24` | `33.87` | `30.93` | Single-flight `4`-thread duplicate coalesce hits=`3/4` |
| Deterministic Fast-Path (`v9`/`v3`) | `30` | `30/30` | `33.9` | `36.28` | `34.75` | `0` SLM calls |

---

## 2. Win32 Process & OS Memory Accounting

- **Total Physical RAM:** `16163.3` MiB (`PHYSICAL_TARGET_HARDWARE = NOT_MEASURED`)
- **Before Model Load:** Combined WS `65.38` MiB
- **After Cold Load:** Combined WS `969.01` MiB
- **Peak Combined Working Set (Backend + `llama-server.exe`) over `n=100`:** **`973.28` MiB**
- **Peak Combined Private Commit:** **`637.5` MiB**
- **Min OS Available Physical RAM:** `5455.33` MiB | **Peak System Committed:** `16360.44` MiB
- **Q1 vs Q4 Memory/Latency Drift:** First 25 E2E mean `3107.13` ms (`969.42` MiB) vs Last 25 `4409.37` ms (`972.37` MiB)

---

## 3. Concurrency, Saturation & Fault Recovery

- **`c=2` (4 batches, 8 reqs):** `served=8/8`, E2E `p50=6569.36` ms, `p95=8859.95` ms
- **`c=4` (2 batches, 8 reqs):** `served=8/8`, E2E `p50=11028.9` ms, `p95=17712.47` ms
- **`c=6` bounded queue (`max_queue=2`):** `completed_ok=2`, `rejected_busy=4`, `post_saturation_recovery_ok=True`
- **Crash recovery (`force_kill_server`, pid `9308`):** `crash_auto_restart_served=True`
- **Timeout recovery (`timeout_s=0.05` -> `LOCAL_SLM_TIMEOUT`):** `post_timeout_served=True`

---

## 4. Controlled Ablations (`n=24` Representative SLM Cases from `val_v9.jsonl`)

| Variant | Model | Threads | Grammar Mode | Oracle Exact | Wrong-Served | `p50` E2E (ms) | `p95` E2E (ms) | `p50` Inf (ms) | Retries | Peak WS (MiB) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `axov9_gbnf_t6_mt256` | `qwen3-0.6b-axo-v9-q4_k_m` | `6` | `gbnf` | `24/24` | `0` | `3912.89` | `5311.37` | `4485.4` | `0` | `975.98` |
| `axov9_retry_on_invalid_t6_mt256` | `qwen3-0.6b-axo-v9-q4_k_m` | `6` | `retry_on_invalid` | `22/24` | `0` | `4035.46` | `5344.93` | `4612.65` | `0` | `974.07` |
| `axov9_gbnf_t8_mt256` | `qwen3-0.6b-axo-v9-q4_k_m` | `8` | `gbnf` | `24/24` | `0` | `3886.34` | `4902.27` | `4180.85` | `0` | `975.65` |
| `axov9_gbnf_t2_ctx1536_mt256` | `qwen3-0.6b-axo-v9-q4_k_m` | `2` | `gbnf` | `24/24` | `0` | `7196.61` | `10196.66` | `8052.34` | `0` | `972.45` |
| `axov7_gbnf_t6_mt320` | `qwen3-0.6b-axo-v7-q4_k_m` | `6` | `gbnf` | `15/24` | `0` | `4720.78` | `7463.9` | `5616.02` | `0` | `977.47` |
